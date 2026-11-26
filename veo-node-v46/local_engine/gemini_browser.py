"""Paired browser transport only; existing Gemini jobs own prompts, scenes and files."""
import asyncio,json,secrets,time,re,os,hashlib
from pathlib import Path
from fastapi import HTTPException
PREFIX='/local-api/browser-bridge/gemini-'
PATHS={PREFIX+n for n in ('poll','result','disconnect','discover')}
class GeminiBrowser:
    def __init__(self,app,service):
        self.service=service;self.vault=service.vault;self.routes={r['id']:r for r in self.vault.secret('gemini-browser-routes')or []};self.jobs=self.vault.secret('gemini-browser-jobs')or {};self.queues={};self.futures={};self.online={};self.closed=False;self.auto_tasks={};self.auto_errors={}
        self.root=Path(service.data)/'gemini-browser-results';self.root.mkdir(exist_ok=True,mode=0o700);self.install(app)
    def save(self):
        self.vault.set_secret('gemini-browser-routes',list(self.routes.values()));self.vault.set_secret('gemini-browser-jobs',self.jobs)
    def issue(self):
        for rid,row in list(self.routes.items()):
            if not row['bound'] and time.time()-row['created']>180:self.revoke(rid)
        if len(self.routes)>=32:raise HTTPException(409,'Gỡ kết nối Gemini không dùng trước khi thêm.')
        rid=secrets.token_urlsafe(24);row={'id':rid,'key':secrets.token_urlsafe(32),'created':time.time(),'bound':False};self.routes[rid]=row;self.save();return {'id':rid,'browser_key':row['key']}
    def auth(self,body):
        row=self.routes.get(body.get('id'))if isinstance(body.get('id'),str)else None;key=body.get('key')
        if not row or not isinstance(key,str)or not secrets.compare_digest(row['key'],key):raise HTTPException(403,'Kết nối Gemini đã ngắt.')
        if not row['bound']and time.time()-row['created']>180:self.revoke(row['id']);raise HTTPException(403,'Mã Gemini đã hết hạn.')
        return row
    def revoke(self,rid):
        self.routes.pop(rid,None);self.online.pop(rid,None);self.save()
    def available(self,rid):return rid in self.routes and time.monotonic()-self.online.get(rid,-1e9)<50
    def read(self,jid):
        row=self.jobs.get(jid)
        if not row:return None
        path=self.root/(jid+'.json')
        if path.is_file():return json.loads(path.read_text())
    def retire(self,jid):
        if jid in self.jobs:
            self.jobs[jid]['completed']=True;self.save()
            (self.root/(jid+'.json')).unlink(missing_ok=True)
    async def request(self,route,jid,request,timeout=240):
        if not re.fullmatch(r'(?:gchat-[a-f0-9-]{36}|identity-[a-f0-9]{32}|receive-[a-f0-9]{32})',jid):raise HTTPException(400,'Mã lượt trình duyệt không hợp lệ.')
        old=self.jobs.get(jid)
        if old and old['route']!=route:raise HTTPException(409,'Lượt này thuộc kết nối khác.')
        cached=self.read(jid)
        if cached is not None:return cached
        if old and jid not in self.futures:raise HTTPException(409,{'code':'GEMINI_BROWSER_OUTCOME_UNKNOWN','sent':old['dispatched']})
        if not old:
            if not self.available(route):raise HTTPException(503,{'code':'GEMINI_BROWSER_OFFLINE','sent':False})
            self.jobs[jid]={'route':route,'dispatched':False};self.futures[jid]=asyncio.get_running_loop().create_future();self.save();self.queues.setdefault(route,asyncio.Queue()).put_nowait((jid,request))
        try:return await asyncio.wait_for(asyncio.shield(self.futures[jid]),timeout)
        except asyncio.TimeoutError:
            sent=self.jobs[jid]['dispatched']
            if not sent:
                self.jobs[jid]['cancelled']=True;self.save()
                future=self.futures.pop(jid,None)
                if future and not future.done():future.cancel()
                queue=self.queues.get(route);keep=[]
                if queue:
                    while not queue.empty():
                        item=queue.get_nowait()
                        if item is None or item[0]!=jid:keep.append(item)
                    for item in keep:queue.put_nowait(item)
            raise HTTPException(504,{'code':'GEMINI_BROWSER_OUTCOME_UNKNOWN','sent':sent})from None
    async def close(self):
        self.closed=True
        for task in self.auto_tasks.values():
            if not task.done():task.cancel()
        for f in self.futures.values():
            if not f.done():f.cancel()
        for q in self.queues.values():q.put_nowait(None)
    async def auto_register(self,route):
        try:
            result=await self.request(route,'identity-'+secrets.token_hex(16),{'operation':'identity'},45)
            if not result.get('ok'):raise ValueError('editor unavailable')
            aid='gchat-browser-'+route;rows=self.service.accounts();existing=next((r for r in rows if r['id']==aid),{})
            row={**existing,'id':aid,'service':'gemini_chat','name':existing.get('name','Gemini · Chrome/Edge'),'enabled':True,'active':existing.get('active',False),'state':'ready','session_verified':True,'transport':'browser','browser_route':route,'models':[],'priority':existing.get('priority',len(rows)),'checked_at':time.time()}
            self.vault.put('accounts',row);self.routes[route]['bound']=True;self.routes[route]['auto_verified']=True;self.save()
            active=next((r for r in rows if r.get('active')and r.get('enabled')and r.get('session_verified')and r.get('state')in ('ready','active')and r.get('transport')=='browser'and self.available(r.get('browser_route'))and self.routes.get(r.get('browser_route'),{}).get('installation_id')),None)
            if not active and not any(r.get('active')and r.get('enabled')and r.get('session_verified')and r.get('transport')=='native'for r in rows):self.service.pool.select({'mode':'selected','account_id':aid})
            self.auto_errors.pop(route,None)
        except asyncio.CancelledError:raise
        except Exception:self.auto_errors[route]='Mở Gemini trong Chrome/Edge và đăng nhập để tiện ích tự kết nối.'
    def auto_status(self):
        accounts=[r for r in self.service.accounts()if r.get('transport')=='browser'and self.routes.get(r.get('browser_route'),{}).get('installation_id')and self.available(r.get('browser_route'))]
        routes=[r for r in self.routes.values()if r.get('installation_id')and self.available(r['id'])]
        ready=any(r.get('enabled')and r.get('session_verified')and r.get('state')in ('ready','active')for r in accounts)
        return {'ready':ready,'account_ids':[a['id']for a in accounts],'extension_seen':bool(routes),'checking':any(not t.done()for t in self.auto_tasks.values()),'extension_version':next((r['extension_version']for r in routes if r.get('extension_version')),''),'message':'Đã tự kết nối Gemini qua tiện ích.'if ready else next(iter(self.auto_errors.values()),'Đang chờ tiện ích SceneForge trên Chrome/Edge tự kết nối.')}
    def install(self,app):
        @app.get('/local-api/gemini-chat/browser-status')
        async def browser_status():return self.auto_status()
        @app.post(PREFIX+'discover')
        async def discover(body:dict):
            ident=body.get('installation_id');version=body.get('version','')
            if not isinstance(ident,str)or not re.fullmatch(r'[a-f0-9-]{36}',ident):raise HTTPException(400,'Tiện ích chưa có định danh cài đặt hợp lệ.')
            row=next((r for r in self.routes.values()if r.get('installation_id')==ident),None)
            if not row:
                link=self.issue();row=self.routes[link['id']];row.update(installation_id=ident,bound=True);self.save()
            route=row['id'];self.online[route]=time.monotonic()
            if isinstance(version,str)and re.fullmatch(r'[0-9.]{1,20}',version):row['extension_version']=version
            present=any(a.get('browser_route')==route for a in self.service.accounts())
            task=self.auto_tasks.get(route)
            if not present and (task is None or task.done()):
                self.auto_tasks[route]=asyncio.create_task(self.auto_register(route))
            return {'service':'sceneforge-gemini-browser','relay':{'id':route,'browser_key':row['key']},'ready':present}
        @app.post(PREFIX+'poll')
        async def poll(body:dict):
            row=self.auth(body);rid=row['id'];self.online[rid]=time.monotonic()
            if body.get('hello')is True:return {'job':None}
            q=self.queues.setdefault(rid,asyncio.Queue())
            while not self.closed:
                try:item=await asyncio.wait_for(q.get(),15)
                except asyncio.TimeoutError:return {'job':None}
                if item is None:return {'job':None}
                jid,request=item;job=self.jobs.get(jid)
                if not job or job['dispatched'] or job.get('cancelled'):continue
                job['dispatched']=True;self.save();return {'job':{'id':jid,'request':request}}
            return {'job':None}
        @app.post(PREFIX+'result')
        async def result(body:dict):
            row=self.auth(body);jid=body.get('job_id');job=self.jobs.get(jid)if isinstance(jid,str)else None
            if not job or job['route']!=row['id']or not job['dispatched']:raise HTTPException(409,'Kết quả không thuộc lượt này.')
            value=body.get('result')
            if not isinstance(value,dict)or type(value.get('ok'))is not bool:raise HTTPException(400,'Kết quả không hợp lệ.')
            # Select fields only; never persist browser HTML, cookies or arbitrary objects.
            value={k:v for k,v in value.items()if k in {'ok','accepted','code','text','image','mime','identity','tab_id'}}
            data=json.dumps(value,sort_keys=True,separators=(',',':')).encode()
            if len(data)>34*1024**2:raise HTTPException(413,'Kết quả quá lớn.')
            digest=hashlib.sha256(data).hexdigest()
            if job.get('completed'):
                if job.get('result_hash')!=digest:raise HTTPException(409,'Lượt đã nhận kết quả khác.')
                return {'accepted':True}
            path=self.root/(jid+'.json')
            if path.is_file():
                if path.read_bytes()!=data:raise HTTPException(409,'Lượt đã có kết quả khác.')
            else:
                tmp=path.with_suffix('.tmp');tmp.write_bytes(data);os.replace(tmp,path)
            job['result_hash']=digest;self.save()
            future=self.futures.get(jid)
            if future and not future.done():future.set_result(value)
            self.futures.pop(jid,None)
            self.online[row['id']]=time.monotonic();return {'accepted':True}
        @app.post(PREFIX+'disconnect')
        async def disconnect(body:dict):
            row=self.auth(body);self.online.pop(row['id'],None);return {'ok':True}

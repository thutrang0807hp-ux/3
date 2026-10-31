"""SceneForge -> paired extension -> ordinary Flow DOM. No credential export.

A separate capability route is issued by the existing one-use pairing dialog.
No generated-media URLs supplied by the page are fetched by the local server.
"""
import asyncio,base64,hashlib,time
from .flow_ui_driver import UiFlowFailure

class FlowExtensionDriver:
    def __init__(self,legacy,relay,accounts):
        self.legacy,self.relay,self.accounts=legacy,relay,accounts
        self.vault=accounts.vault;self.lock=asyncio.Lock()
    async def release_account(self,aid):
        release=getattr(self.legacy,'release_account',None)
        if release:await release(aid)
    async def close(self):
        close=getattr(self.legacy,'close',None)
        if close:await close()
    def extension_binding(self,aid):
        return None  # forced: skip extension, use managed browser

    def binding(self,aid):return self.extension_binding(aid)or self.legacy.binding(aid)
    def acknowledge(self,rid):return self.legacy.acknowledge(rid)
    def register_extension(self,route,result):
        email=result.get('email');digest=result.get('account_hash')
        if result.get('status')!=200 or not isinstance(email,str)or '@'not in email or len(email)>320:
            raise UiFlowFailure('Tab Flow chưa nhận diện được tài khoản đăng nhập.')
        email=email.strip().casefold()
        if digest!=hashlib.sha256(email.encode()).hexdigest():raise UiFlowFailure('Danh tính tab Flow không khớp.')
        aid='flow-web-'+digest[:24]
        previous=self.vault.secret('flow-extension-ui')or{}
        if previous.get('route_id')and previous['route_id']!=route:self.relay.revoke(previous['route_id'])
        self.vault.set_secret('flow-extension-ui',{'account_id':aid,'email':email,'route_id':route,'account_hash':digest})
        old=next((a for a in self.accounts.pool.rows()if a['id']==aid),{})
        # Do not retain an old engine/native route on this UI-only account.
        row={k:v for k,v in old.items()if k not in {'native_route_id','engine_id'}}
        self.vault.put('accounts',{**row,'id':aid,'service':'flow','name':email+' · tab Flow','login_transport':'web_ui','enabled':True,'session_verified':True,'state':'ready','active':False,'priority':old.get('priority',len(self.accounts.pool.rows())),'credit':None})
        self.accounts.pool.select({'mode':'selected','account_id':aid})
        return aid
    async def command(self,binding,action,**kwargs):
        try:result=await self.relay.request(binding['route_id'],{'kind':'ui','action':action,**kwargs},5 if action=='release'else 90)
        except UiFlowFailure:raise
        except Exception as exc:raise UiFlowFailure('Mất kết nối trình duyệt Flow. Giữ lượt cũ nếu đã bấm tạo.')from exc
        if result.get('status')!=200:
            messages={
                'FLOW_UI_AGENT':'Chưa chuyển được giao diện Agent sang tạo nội dung.',
                'FLOW_UI_MODEL':'Chưa chọn/xác minh được model Veo Lite trong giao diện Flow.',
                'FLOW_UI_EDITOR':'Chưa nhận diện hoặc điền được ô prompt Flow.',
                'FLOW_UI_IMAGE':'Chưa xác nhận ảnh đầu đã tải xong trong Flow.',
                'FLOW_UI_SETTINGS':'Chưa xác nhận được video 8 giây, dọc 9:16, số lượng 1.',
                'FLOW_UI_SUBMIT':'Chưa nhận diện được nút tạo video.',
                'FLOW_UI_PROJECT_REQUIRED':'Mở đúng dự án trong cửa sổ Flow của SceneForge trước khi tạo video.',
                'FLOW_UI_CHANGED':'Trang Flow đã thay đổi; chưa gửi thêm.',
                'FLOW_UI_VERIFY':'Flow yêu cầu xác minh hoặc báo hoạt động bất thường. Hoàn tất trên web; app đã dừng.',
                'FLOW_UI_RESULTS':'Chưa xác định được duy nhất clip của lượt này.',
                'FLOW_UI_DOWNLOAD':'Đã thấy kết quả nhưng chưa tải được video từ tab Flow.',
                'FLOW_BROWSER_ACCOUNT_CHANGED':'Tài khoản trong tab Flow đã thay đổi.',
            }
            raise UiFlowFailure(messages.get(result.get('code'),'Cầu nối Flow chưa hoàn tất thao tác. Đã dừng, không tự gửi lại.'),result.get('uncertain',False))
        return result
    async def verify(self,aid):
        binding=self.extension_binding(aid)
        if not binding:return await self.legacy.verify(aid)
        r=await self.command(binding,'identity')
        if r.get('account_hash')!=binding['account_hash']:raise UiFlowFailure('Tài khoản tab Flow đã thay đổi.')
        return True
    async def generate(self,aid,model,prompt,references,target,on_sent):
        binding=self.extension_binding(aid)
        if not binding:return await self.legacy.generate(aid,model,prompt,references,target,on_sent)
        async with self.lock:
            blocked=self.vault.secret('flow-ui-blocked')or{}
            if blocked.get('account_id')==aid:raise UiFlowFailure('Lượt trước chưa rõ kết quả. Kiểm tra lịch sử Flow trước khi gửi mới.')
            if 'lite'not in model.lower()or len(references)!=1:raise UiFlowFailure('Cầu nối hiện hỗ trợ Lite, một ảnh đầu, 8 giây, dọc 9:16.')
            ref=references[0]
            if ref.get('mime_type')not in ('image/png','image/jpeg','image/webp'):raise UiFlowFailure('Ảnh đầu không đúng định dạng.')
            try:raw=base64.b64decode(ref.get('data',''),validate=True)
            except Exception:raise UiFlowFailure('Ảnh đầu không hợp lệ.')from None
            if not 0<len(raw)<=6*1024**2:raise UiFlowFailure('Ảnh đầu phải nhỏ hơn 6 MB.')
            if not isinstance(prompt,str)or not prompt.strip()or len(prompt)>60000:raise UiFlowFailure('Prompt trống hoặc quá dài.')
            await self.verify(aid)
            rid=target.stem;sent=False;done=False
            try:
                await self.command(binding,'prepare',request_id=rid,prompt='Create a video from this image. '+prompt,image=ref)
                # Conservatively persist uncertainty BEFORE a command can click Generate.
                on_sent();sent=True
                await self.command(binding,'submit',request_id=rid)
                deadline=time.monotonic()+600
                while time.monotonic()<deadline:
                    result=await self.command(binding,'status',request_id=rid)
                    if result.get('ready'):break
                    await asyncio.sleep(2)
                else:raise UiFlowFailure('Chưa nhận được video sau 10 phút. Kiểm tra lịch sử Flow, không tự gửi lại.',True)
                size=result.get('bytes')
                if type(size)is not int or not 0<size<=100*1024**2:raise UiFlowFailure('Kích thước video không hợp lệ.',True)
                digest=hashlib.sha256();offset=0
                with target.open('wb')as stream:
                    while offset<size:
                        part=await self.command(binding,'chunk',request_id=rid,offset=offset)
                        try:data=base64.b64decode(part.get('data',''),validate=True)
                        except Exception:raise UiFlowFailure('Dữ liệu video tải xuống không hợp lệ.',True)from None
                        if not 0<len(data)<=1024**2 or offset+len(data)>size:raise UiFlowFailure('Video tải xuống thiếu hoặc sai kích thước.',True)
                        stream.write(data);digest.update(data);offset+=len(data)
                if digest.hexdigest()!=result.get('sha256'):raise UiFlowFailure('Kiểm tra toàn vẹn video thất bại.',True)
                done=True
            finally:
                if sent and not done:self.vault.set_secret('flow-ui-blocked',{'account_id':aid,'request_id':rid})
                try:await self.command(binding,'release',request_id=rid)
                except Exception:pass

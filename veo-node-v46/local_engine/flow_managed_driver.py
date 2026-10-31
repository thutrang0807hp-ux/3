"""App-owned Chrome/Edge profile -> standard CDP -> shared normal DOM adapter.

No extension installation, private generation RPC, cookie export, CAPTCHA token
access, browser-identity changes or automatic retries.
"""
import asyncio,hashlib,json
from contextlib import asynccontextmanager
from contextvars import ContextVar
from pathlib import Path
from types import SimpleNamespace
from .flow_extension_driver import FlowExtensionDriver
from .flow_ui_driver import FlowUiDriver,UiFlowFailure
from .flow_ui_session import FlowUiSession

_context=ContextVar('flow_managed_context',default=None)

class FlowManagedDriver(FlowExtensionDriver):
    managed_browser=True
    def __init__(self,data,vault):
        self.data=Path(data);self.vault=vault;self.legacy=FlowUiDriver(data,vault)
        self.workers={};self.worker_locks={};self.closing=False
        self.lock=asyncio.Lock();self.relay=SimpleNamespace(request=self._request)
        self.source=(Path(__file__).resolve().parents[1]/'scripts/browser-extension/dom-flow.js').read_text()
    def extension_binding(self,aid):
        value=(self.vault.secret('flow-managed-profiles')or{}).get(aid)
        if not value:
            old=self.vault.secret('flow-ui-profile')or{}
            value=old if old.get('account_id')==aid else None
        if not value or value.get('account_id')!=aid:return None
        return {**value,'route_id':'managed-local','transport':'managed_browser'}
    def binding(self,aid):return self.extension_binding(aid)
    async def _drop_worker(self,aid):
        worker=self.workers.pop(aid,None)
        if worker:await worker['session'].disconnect()
    async def release_account(self,aid):
        lock=self.worker_locks.setdefault(aid,asyncio.Lock())
        async with lock:await self._drop_worker(aid)
    async def close(self):
        self.closing=True
        for aid,lock in list(self.worker_locks.items()):
            async with lock:await self._drop_worker(aid)
    @asynccontextmanager
    async def session(self,aid):
        current=_context.get()
        if current:
            if current.get('driver') is not self or current.get('owner') is not asyncio.current_task():
                raise UiFlowFailure('Tác vụ không sở hữu phiên worker Flow; chưa gửi thao tác.')
            if current['binding']['account_id']!=aid:raise UiFlowFailure('Phiên trình duyệt không khớp tài khoản.')
            yield current;return
        lock=self.worker_locks.setdefault(aid,asyncio.Lock())
        async with lock:
            if self.closing:raise UiFlowFailure('Worker Flow đang đóng; chưa nhận lượt mới.')
            # Re-read after queueing: an account may have been removed or rebound.
            binding=self.binding(aid)
            if not binding:
                await self._drop_worker(aid)
                raise UiFlowFailure('Đăng nhập Flow trên web trong SceneForge trước.')
            key=(binding.get('profile_key'),binding.get('email','').strip().casefold())
            worker=self.workers.get(aid)
            if worker and (worker['key']!=key or not worker['session'].browser or not worker['session'].browser.is_connected()):
                await self._drop_worker(aid);worker=None
            token=None;current=None
            try:
                if worker is None:
                    from playwright.async_api import async_playwright
                    session=FlowUiSession(self.data,binding.get('profile_key'))
                    try:await session.attach(async_playwright)
                    except BaseException:
                        await session.disconnect();raise
                    worker={'session':session,'key':key};self.workers[aid]=worker
                session=worker['session']
                await session.assert_ready()
                pages=[p for c in session.browser.contexts for p in c.pages if session.is_flow(p.url)]
                if len(pages)!=1 or pages[0]!=session.page:
                    raise UiFlowFailure('Giữ một tab Flow trong cửa sổ riêng để chọn đúng project.')
                if session.email!=key[1]:raise UiFlowFailure('Tài khoản trong cửa sổ web đã thay đổi.')
                # DOM state belongs to one operation, while the browser connection persists.
                current={'session':session,'binding':binding,'cdp':None,'world':None,'owner':asyncio.current_task(),'driver':self}
                token=_context.set(current)
                yield current
            except BaseException:
                await self._drop_worker(aid)
                raise
            finally:
                if token is not None:_context.reset(token)
                if current and current['cdp']is not None:
                    try:await current['cdp'].detach()
                    except Exception:pass
    async def identity(self,current):
        session=current['session'];await session.assert_ready()
        result=await session.page.evaluate(self.source+'\nsceneForgeFlowIdentity()')
        expected=hashlib.sha256(current['binding']['email'].strip().casefold().encode()).hexdigest()
        if result.get('status')!=200 or result.get('account_hash')!=expected:
            raise UiFlowFailure('Danh tính trong cửa sổ Flow không còn khớp tài khoản đã chọn.')
        return result
    async def verify(self,aid):
        async with self.session(aid)as current:await self.identity(current)
        return True
    async def generate(self,aid,model,prompt,references,target,on_sent):
        async with self.session(aid):
            return await super().generate(aid,model,prompt,references,target,on_sent)
    async def _request(self,unused_route,request,timeout):
        current=_context.get()
        if not current or current.get('driver') is not self or current.get('owner') is not asyncio.current_task():raise UiFlowFailure('Tác vụ chưa sở hữu cửa sổ Flow của lượt tạo.')
        identity=await self.identity(current)
        if request['action']=='identity':return identity
        binding=current['binding'];page=current['session'].page
        workspace=await page.evaluate(self.source+'\nsceneForgeFlowWorkspace('+json.dumps({'project_hash':binding.get('project_hash')})+','+json.dumps(identity)+','+json.dumps({'action':request['action']})+')')
        if not workspace.get('ok'):
            return {'status':422,'code':'FLOW_UI_PROJECT_REQUIRED'if identity.get('page_kind')!='project'else'FLOW_UI_CHANGED','uncertain':workspace.get('uncertain',False)}
        if workspace.get('pin'):
            binding['project_hash']=workspace['pin']
            profiles=self.vault.secret('flow-managed-profiles')or{}
            if binding['account_id']in profiles:
                profiles[binding['account_id']]['project_hash']=workspace['pin'];self.vault.set_secret('flow-managed-profiles',profiles)
        if current['cdp']is None:
            current['cdp']=await page.context.new_cdp_session(page)
            tree=await current['cdp'].send('Page.getFrameTree')
            world=await current['cdp'].send('Page.createIsolatedWorld',{'frameId':tree['frameTree']['frame']['id'],'worldName':'sceneforge-managed-flow'})
            current['world']=world['executionContextId']
        result=await asyncio.wait_for(current['cdp'].send('Runtime.evaluate',{'expression':self.source+'\nsceneForgeDomFlow('+json.dumps(request,ensure_ascii=True)+')','contextId':current['world'],'awaitPromise':True,'returnByValue':True}),timeout)
        if result.get('exceptionDetails'):raise UiFlowFailure('Giao diện Flow thay đổi hoặc thao tác chưa hoàn tất. Đã dừng.')
        return result.get('result',{}).get('value')or{'status':503,'code':'FLOW_BROWSER_UNAVAILABLE'}

"""Experimental normal-UI Flow driver; never calls private RPC/CAPTCHA endpoints."""
import asyncio,base64,re,time
from pathlib import Path
from .flow_ui_session import FlowUiSession,SessionUnavailable,VerificationRequired

class UiFlowFailure(RuntimeError):
    def __init__(self,message,sent=False):super().__init__(message);self.sent=sent

class FlowUiDriver:
    def __init__(self,data,vault):self.data=Path(data);self.vault=vault;self.lock=asyncio.Lock()
    def binding(self,account_id):
        row=self.vault.secret('flow-ui-profile')or{}
        return row if row.get('account_id')==account_id and isinstance(row.get('email'),str)and '@'in row['email']else None
    def acknowledge(self,request_id):
        blocked=self.vault.secret('flow-ui-blocked')or{}
        if blocked.get('request_id')!=request_id:return False
        self.vault.delete_secret('flow-ui-blocked');return True
    async def verify(self,account_id):
        binding=self.binding(account_id)
        if not binding:raise UiFlowFailure('Chưa có phiên web tương ứng.')
        from playwright.async_api import async_playwright
        session=FlowUiSession(self.data)
        try:
            await session.attach(async_playwright)
            if session.email!=binding['email'].strip().casefold():raise UiFlowFailure('Tài khoản trong cửa sổ web đã đổi.')
            return True
        finally:await session.disconnect()
    async def unique_visible(self,locator,message):
        matches=[x for x in await locator.all()if await x.is_visible()]
        if len(matches)!=1:raise UiFlowFailure(message)
        return matches[0]
    def _latest_project_id(self):
        """Best-effort: read the most recent ready project binding."""
        try:
            import sqlite3
            from pathlib import Path
            # Common location used by the app
            candidates = list(Path(self.data).rglob('*.sqlite')) + list(Path(self.data).rglob('*.db'))
            for dbpath in candidates:
                if 'binding' in dbpath.name or 'project' in dbpath.name or 'flow' in dbpath.name:
                    try:
                        con = sqlite3.connect(dbpath)
                        row = con.execute("SELECT project FROM binding WHERE state='ready' ORDER BY rowid DESC LIMIT 1").fetchone()
                        con.close()
                        if row and row[0]:
                            return row[0]
                    except Exception:
                        pass
        except Exception:
            pass
        return None

    async def generate(self,account_id,model,prompt,references,target,on_sent):
        async with self.lock:
            blocked=self.vault.secret('flow-ui-blocked')or{}
            if blocked.get('account_id')==account_id:raise UiFlowFailure('Lượt web trước chưa rõ kết quả. Kiểm tra lịch sử Flow và xác nhận bỏ lượt trước khi gửi mới.')
            binding=self.binding(account_id)
            if not binding:raise UiFlowFailure('Chưa nối phiên web cho tài khoản đã chọn.')
            # Trial: best-effort open project; never break the original flow
            pid = None
            try:
                from .google_login import open_flow_web_login
                pid = self._latest_project_id()
                url = ('https://flow.google.com/project/'+pid+'?pli=1') if pid else 'https://flow.google.com/'
                await open_flow_web_login(self.data, auto_connect=True, start_url=url)
            except Exception:
                pid = None
            if not re.search(r'lite.*i2v.*8s|i2v.*lite.*8s|i2v_lite_(?:portrait|8s)',model):
                raise UiFlowFailure('Bản thử giao diện chỉ hỗ trợ Lite I2V 8 giây. Chọn đúng model; chưa gửi.')
            if len(references)!=1:raise UiFlowFailure('Tạo video từ ảnh cần đúng một ảnh đầu.')
            from playwright.async_api import async_playwright
            session=FlowUiSession(self.data);sent=False;completed=False
            pid = self._latest_project_id()
            try:
                await session.attach(async_playwright)
                if pid:
                    try:
                        await session.goto_project(pid)
                    except Exception:
                        pass
                if session.email!=binding['email'].strip().casefold():raise UiFlowFailure('Cửa sổ Flow đang dùng tài khoản khác; chưa gửi.')
                page=session.page
                # Best-effort: open image menu and click Animate
                try:
                    img = page.locator('img').first
                    if await img.count():
                        await img.click(button='right')
                        await page.wait_for_timeout(500)
                        anim = page.get_by_role('menuitem', name='Animate')
                        if not await anim.count():
                            anim = page.get_by_text('Animate', exact=True)
                        if await anim.count():
                            await anim.first.click()
                            await page.wait_for_timeout(800)
                except Exception:
                    pass
                # Best-effort: leave Agent and pick 9:16 / Frames mode
                try:
                    for name in ('Agent', 'Tác nhân'):
                        btn = page.get_by_role('button', name=name)
                        if await btn.count():
                            el = btn.first
                            if await el.get_attribute('aria-pressed') == 'true':
                                await el.click()
                                await page.wait_for_timeout(500)
                    for label in ('9:16', 'Frames to Video', 'Từ khung hình', 'Khung hình thành video'):
                        b = page.get_by_role('button', name=label)
                        if await b.count():
                            await b.first.click()
                            await page.wait_for_timeout(300)
                except Exception:
                    pass
                # Fail closed on unknown UI: never guess which button spends credits.
                model_buttons=page.get_by_role('button',name=re.compile(r'Veo.*Lite|Lite.*Veo',re.I))
                chosen_model=await self.unique_visible(model_buttons,'Chưa nhận diện được nút model Lite trên web Flow. Giữ cửa sổ mở và gửi ảnh giao diện để kiểm tra; chưa gửi.')
                caption=(await chosen_model.inner_text()).casefold()
                visible_settings=' '.join([(await button.inner_text()).casefold()for button in await page.get_by_role('button').all()if await button.is_visible()])
                if not re.search(r'8\s*(?:s\b|sec|giây)',caption+' '+visible_settings)or not re.search(r'9\s*:\s*16|portrait|dọc',caption+' '+visible_settings):raise UiFlowFailure('Trên web chọn 8 giây và tỉ lệ 9:16 trước; chưa gửi.')
                await self.unique_visible(page.get_by_role('button',name=re.compile(r'^Frames to Video$|^Từ khung hình$|^Khung hình thành video$',re.I)), 'Trên web Flow cần chế độ Frames to Video. Chưa gửi.')
                editor=await self.unique_visible(page.get_by_role('textbox'),'Chưa xác định được duy nhất ô prompt của Flow. Chưa gửi.')
                submit=await self.unique_visible(page.get_by_role('button',name=re.compile(r'^Generate$|^Create video$|^Tạo video$|^Tạo$',re.I)),'Chưa xác định được nút tạo video của Flow. Chưa gửi.')
                uploads=[]
                for field in await page.locator('input[type=file]').all():
                    accept=(await field.get_attribute('accept')or'').lower()
                    if 'image'in accept or any(x in accept for x in ('.png','.jpg','.jpeg','.webp')):uploads.append(field)
                if len(uploads)!=1:raise UiFlowFailure('Chưa xác định được ô tải ảnh đầu trong Flow. Chưa gửi.')
                before=set(await page.locator('video').evaluate_all('(nodes)=>nodes.map(n=>n.currentSrc||n.src)'))
                ref=references[0];mime=ref.get('mime_type','')
                if mime not in ('image/png','image/jpeg','image/webp'):raise UiFlowFailure('Ảnh đầu không đúng định dạng.')
                raw=base64.b64decode(ref.get('data',''),validate=True)
                if not raw or len(raw)>6*1024**2:raise UiFlowFailure('Ảnh đầu phải nhỏ hơn 6 MB.')
                await uploads[0].set_input_files({'name':'sceneforge-start.'+{'image/png':'png','image/jpeg':'jpg','image/webp':'webp'}[mime],'mimeType':mime,'buffer':raw})
                await editor.fill(prompt)
                await session.assert_ready()
                # Persist unknown outcome before clicking, including click/connection timeouts.
                on_sent();sent=True
                await submit.click(timeout=15000)
                deadline=time.monotonic()+600
                while time.monotonic()<deadline:
                    await session.assert_ready()
                    new=[]
                    for video in await page.locator('video').all():
                        src=await video.evaluate('(n)=>n.currentSrc||n.src')
                        if src and src not in before and await video.is_visible():new.append(video)
                    if len(new)>1:raise UiFlowFailure('Có nhiều clip mới trên web; giữ lượt cũ để xác định đúng kết quả.',True)
                    if len(new)==1:
                        container=new[0].locator('xpath=ancestor::article[1]')
                        if await container.count()!=1:raise UiFlowFailure('Đã thấy video nhưng chưa nhận diện được thẻ kết quả để tải đúng clip.',True)
                        download=await self.unique_visible(container.get_by_role('button',name=re.compile(r'^Download$|^Tải xuống$|^Tải video$',re.I)),'Đã thấy video nhưng chưa nhận diện nút tải của đúng clip.')
                        async with page.expect_download(timeout=120000)as pending:await download.click()
                        item=await pending.value
                        await item.save_as(str(target))
                        completed=True
                        return
                    await asyncio.sleep(2)
                raise UiFlowFailure('Chưa thấy kết quả sau 10 phút. Giữ lượt cũ; không tự gửi lại.',True)
            except UiFlowFailure as exc:
                if sent:exc.sent=True
                raise
            except (SessionUnavailable,VerificationRequired)as exc:raise UiFlowFailure(str(exc),sent)from None
            except asyncio.CancelledError:raise
            except Exception:raise UiFlowFailure('Giao diện hoặc kết nối Flow thay đổi. Đã dừng; không tự mở trình duyệt khác hoặc gửi lại.',sent)from None
            finally:
                if sent and not completed:self.vault.set_secret('flow-ui-blocked',{'account_id':account_id,'request_id':Path(target).stem})
                await session.disconnect()

"""Read-only background-auth trial. Never uploads, generates, or exports cookies."""
import argparse,asyncio,json,sys,time
from pathlib import Path

MESSAGES={
 'BACKGROUND_SESSION_OK':'Phiên tài khoản được xác minh trong trình duyệt chạy nền. Chưa gửi tạo video.',
 'NO_WEB_ACCOUNT':'Chưa chọn tài khoản đăng nhập web trong tab Tài khoản.',
 'PROFILE_MISSING':'Không tìm thấy profile web đã lưu. Không tạo profile mới hoặc sao chép cookie.',
 'VISIBLE_FLOW_STILL_OPEN':'Cửa sổ Flow của app còn hoạt động. Đóng riêng cửa sổ đó rồi thử lại; công cụ không đóng trình duyệt thay bạn.',
 'PROFILE_IN_USE_OR_START_FAILED':'Chưa mở được profile ở chế độ nền. Có thể profile còn đang được dùng; không xóa hay ép đóng trình duyệt.',
 'AUTH_REQUIRED':'Phiên nền được chuyển tới trang đăng nhập Google. Chưa xác minh được đăng nhập nền; không gửi video.',
 'VERIFICATION_REQUIRED':'Trang yêu cầu xác minh. Công cụ đã dừng, không tự xử lý xác minh hoặc gửi video.',
 'ACCOUNT_MISMATCH':'Tài khoản trong phiên nền không khớp tài khoản đang chọn. Đã dừng.',
 'IDENTITY_UNREADABLE':'Đã mở nền nhưng chưa đọc được danh tính tài khoản. Chưa đủ bằng chứng kết luận phiên hợp lệ hay hết hạn.',
 'FLOW_NAVIGATION_FAILED':'Chưa tải được trang Flow trong chế độ nền. Chưa kiểm tra được phiên.',
 'BROWSER_INSTANCE_MISMATCH':'Thông tin cửa sổ đang lưu không khớp trình duyệt. Đã dừng, không dùng nhầm cửa sổ.',
 'INSTALLATION_ERROR':'Chưa đọc được cấu hình bản cài. Chưa mở browser hay thay đổi tài khoản.',
}
def result(code):return {'tool':'flow-background-auth-check-v1','code':code,'message':MESSAGES[code],'session_verified':code=='BACKGROUND_SESSION_OK','generation_attempted':False,'account_data_exported':False}

async def probe(data,vault,context_factory=None,identity_timeout=12):
 from local_engine.account_pool import AccountPool
 from local_engine.flow_account_session import AccountWebSession
 from local_engine.flow_browser_probe import probe_flow_browser
 from local_engine.google_login import flow_profile_path,installed_browser
 from types import SimpleNamespace
 pool=AccountPool(vault,'flow');bridge=AccountWebSession(data,SimpleNamespace(vault=vault,pool=pool))
 selected=bridge.selection();binding=bridge.binding(selected.get('account_id'))
 if not selected['available']or not binding:return result('NO_WEB_ACCOUNT')
 profile=flow_profile_path(data,binding.get('profile_key'))
 if not profile.is_dir():return result('PROFILE_MISSING')
 current=await probe_flow_browser(data,binding.get('profile_key'))
 if current['ready']:return result('VISIBLE_FLOW_STILL_OPEN')
 if current['code']=='FLOW_BROWSER_INSTANCE_MISMATCH':return result('BROWSER_INSTANCE_MISMATCH')
 context=pw=None
 try:
  try:
   if context_factory:context=await context_factory(profile)
   else:
    from playwright.async_api import async_playwright
    pw=await async_playwright().start()
    context=await pw.chromium.launch_persistent_context(str(profile),executable_path=installed_browser(),headless=True,timeout=20000)
  except Exception:return result('PROFILE_IN_USE_OR_START_FAILED')
  page=context.pages[0]if context.pages else await context.new_page()
  try:await page.goto('https://flow.google.com/',wait_until='domcontentloaded',timeout=45000)
  except Exception:return result('FLOW_NAVIGATION_FAILED')
  deadline=time.monotonic()+identity_timeout
  while time.monotonic()<deadline:
   from urllib.parse import urlsplit
   host=urlsplit(page.url).hostname
   if host=='accounts.google.com':return result('AUTH_REQUIRED')
   if host!='flow.google.com':return result('IDENTITY_UNREADABLE')
   for frame in page.frames:
    if 'google.com/recaptcha/'in frame.url and '/bframe'in frame.url:
     try:
      if await(await frame.frame_element()).is_visible():return result('VERIFICATION_REQUIRED')
     except Exception:pass
   for alert in await page.get_by_role('alert').all():
    if not await alert.is_visible():continue
    text=(await alert.inner_text()).casefold()
    if any(x in text for x in ('unusual activity','hoạt động bất thường')):return result('VERIFICATION_REQUIRED')
   email=await page.evaluate("()=>String(window.WIZ_global_data?.oPEP7c||'')")
   if isinstance(email,str)and '@'in email:
    return result('BACKGROUND_SESSION_OK'if email.strip().casefold()==binding['email']else'ACCOUNT_MISMATCH')
   await asyncio.sleep(.25)
  return result('IDENTITY_UNREADABLE')
 except Exception:return result('FLOW_NAVIGATION_FAILED')
 finally:
  try:
   if context:await context.close()
  finally:
   if pw:await pw.stop()

async def main():
 ap=argparse.ArgumentParser();ap.add_argument('--app',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);args=ap.parse_args()
 code=result('INSTALLATION_ERROR')
 try:
  app=args.app.resolve();settings=app.parent/'install-settings.json'
  cfg=json.loads(settings.read_text(encoding='utf-8-sig'));data=Path(cfg['data_directory'])
  if not data.is_absolute()or not(data/'vault.sqlite').is_file()or not(data/'vault.key').is_file():raise ValueError()
  sys.path.insert(0,str(app))
  from local_engine.vault import Vault
  code=await probe(data,Vault(data))
 except Exception as exc:code={**code,'error_type':type(exc).__name__}
 args.out.write_text(json.dumps(code,ensure_ascii=False,indent=2),encoding='utf-8')
 print(code['message'])
if __name__=='__main__':asyncio.run(main())

"""Use the existing Accounts web-login registry. No second browser/login/profile."""
from .flow_ui_session import FlowUiSession,SessionUnavailable

class AccountWebSession:
 def __init__(self,data,accounts):self.data=data;self.accounts=accounts
 def binding(self,aid):
  row=next((r for r in self.accounts.pool.rows()if r['id']==aid),None)
  if not row or row.get('login_transport')!='web_ui' or not self.accounts.pool.eligible(row):return None
  profile=(self.accounts.vault.secret('flow-managed-profiles')or{}).get(aid)
  if not profile:
   old=self.accounts.vault.secret('flow-ui-profile')or{}
   if old.get('account_id')==aid:profile=old
  if not profile or profile.get('account_id')!=aid or not isinstance(profile.get('email'),str)or '@'not in profile['email']:return None
  return {**profile,'email':profile['email'].strip().casefold()}
 def selection(self):
  selected=self.accounts.pool.status();binding=self.binding(selected.get('account_id'))
  usable=bool(selected['mode']=='selected'and selected['available']and binding)
  return {**selected,'available':usable}
 async def attach(self,aid):
  binding=self.binding(aid)
  if not binding:raise SessionUnavailable('Tài khoản Flow đã chọn chưa có phiên đăng nhập web dùng được. Đăng nhập web và chọn tài khoản trong Cài đặt → Tài khoản.')
  from playwright.async_api import async_playwright
  session=FlowUiSession(self.data,binding.get('profile_key'))
  try:
   await session.attach(async_playwright)
   if session.email!=binding['email']:raise SessionUnavailable('Nick trong cửa sổ Flow không khớp tài khoản đã chọn. Kiểm tra lại tại tab Tài khoản; chưa gửi tạo video.')
   return session,binding
  except BaseException:
   await session.disconnect();raise
 async def check(self,session,binding):
  current=self.binding(binding['account_id'])
  if not current or (current.get('profile_key'),current['email'])!=(binding.get('profile_key'),binding['email']):raise SessionUnavailable('Tài khoản/profile đã thay đổi hoặc bị tắt trong tab Tài khoản. Chưa gửi thêm thao tác.')
  await session.assert_ready()

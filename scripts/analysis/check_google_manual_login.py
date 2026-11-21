"""Sign-in ordering without Google credentials: native phase then blank capture."""
import asyncio,importlib,sys,tempfile,types
from pathlib import Path
from unittest.mock import Mock,AsyncMock,patch
from fastapi import HTTPException
ROOT=Path(__file__).resolve().parents[2]
async def main():
 with tempfile.TemporaryDirectory()as td:
  root=Path(td);pkg=root/'login_test';pkg.mkdir();(pkg/'__init__.py').write_text('')
  for name in ('google_login.py','browser_profiles.py','fingerprints.py'):(pkg/name).write_bytes((ROOT/'veo-node-v46/local_engine'/name).read_bytes())
  sys.path.insert(0,td);cache=types.ModuleType('login_test.profile_cache');cache.GATE=asyncio.Lock();sys.modules[cache.__name__]=cache
  mod=importlib.import_module('login_test.google_login');profiles=importlib.import_module('login_test.browser_profiles')
  process=Mock();process.pid=123;process.poll.return_value=None;process.wait.return_value=0
  profile=root/'profile';profile.mkdir();(profile/'marker').write_text('KEEP')
  capture=types.SimpleNamespace(cookies=AsyncMock(return_value=[{'name':'TEST','value':'FAKE'}]),close=AsyncMock())
  with patch.object(mod.subprocess,'Popen',return_value=process)as launch:
   login=await mod.open_google_login('https://gemini.google.com/',root,profile=profile,keep_profile=True,executable='/installed/chrome',device_profile={'enabled':True},manual_signin=True)
   args=launch.call_args.args[0];assert args[-1]=='https://gemini.google.com/'and '--disable-background-mode'in args
   assert not any('debugging'in a or 'automation'in a.lower()for a in args)
   with patch.object(mod,'open_google_login',AsyncMock(return_value=capture))as reopen:
    try:await login.cookies()
    except HTTPException as e:assert e.status_code==409 and 'đóng cửa sổ'in e.detail
    else:raise AssertionError('Read cookies before closing browser')
    reopen.assert_not_awaited();process.poll.return_value=0
    assert await login.cookies()==[{'name':'TEST','value':'FAKE'}]
    assert reopen.await_args.kwargs['capture_only']is True and reopen.await_args.kwargs.get('device_profile')is None
    await login.cookies();reopen.assert_awaited_once()
    released=[];login.profile_release=lambda:released.append(True);await login.close();await login.stop()
    capture.close.assert_awaited_once();assert released==[True]and(profile/'marker').read_text()=='KEEP'
  print('PASS no automation flags before manual sign-in, no early cookie read, capture only after close, profile retained and cleanup once')
  # Manager must not inject the saved cookie snapshot or fingerprint into native sign-in.
  vault=types.SimpleNamespace(secret=lambda _:None,rows=lambda _:[]);manager=profiles.Profiles(vault,root/'manager');entry=manager.reserve('gemini_chat')
  fake=types.SimpleNamespace(deferred_capture=True,cookies=AsyncMock(),close=AsyncMock(),profile_release=None)
  with patch.object(manager,'settings',return_value={'executable':'/chrome'}),patch.object(mod,'open_google_login',AsyncMock(return_value=fake))as open_login:
   result=await manager.native(entry,'https://gemini.google.com/',[{'name':'SAVED','value':'FAKE'}]);assert result is fake
   assert open_login.await_args.kwargs['manual_signin']is True and open_login.await_args.kwargs['device_profile']is None
   fake.cookies.assert_not_awaited();fake.profile_release()
  print('PASS saved-cookie and custom-device injection skipped for Gemini interactive login')
  # The capture phase starts about:blank, not Google, before cookies are read.
  process.poll.return_value=None
  def start(args,**kw):(profile/'DevToolsActivePort').write_text('12345\n/x');return process
  with patch.object(mod.subprocess,'Popen',side_effect=start)as launch:
   read=await mod.open_google_login('https://gemini.google.com/',root,profile=profile,keep_profile=True,executable='/chrome',capture_only=True)
   assert launch.call_args.args[0][-1]=='about:blank'and read.connection is None
  # Graceful Windows handoff sends WM_CLOSE only to the owned PID.
  import ctypes
  process.poll.return_value=None
  user=types.SimpleNamespace(GetWindowThreadProcessId=Mock(side_effect=lambda hwnd,out:setattr(out._obj,'value',123 if hwnd==44 else 999)),PostMessageW=Mock(),EnumWindows=Mock(side_effect=lambda callback,param:[callback(44,param),callback(45,param)]))
  with patch.object(mod.os,'name','nt'),patch.object(ctypes,'windll',types.SimpleNamespace(user32=user),create=True),patch.object(ctypes,'WINFUNCTYPE',lambda *args:lambda callback:callback,create=True):
   handoff=mod.ManualGoogleLogin('https://gemini.google.com/',root,profile,process,'/chrome')
   await handoff.finish_signin()
   user.PostMessageW.assert_called_once_with(44,0x0010,0,0)
   assert not handoff.closed and handoff.capture is None
   process.wait.side_effect=mod.subprocess.TimeoutExpired('chrome',12)
   try:await handoff.finish_signin()
   except HTTPException as e:assert e.status_code==409
   else:raise AssertionError('Stuck Chrome reported success')
   process.kill.assert_not_called();process.terminate.assert_not_called();process.wait.side_effect=None
  print('PASS owned-window graceful handoff only, timeout never force-kills or captures')
  print('PASS capture launch uses blank page and original browser/profile')
  with patch.object(mod.asyncio,'open_connection',AsyncMock(return_value=(Mock(),Mock()))),patch.object(mod.subprocess,'Popen')as launch:
   try:await mod.open_google_login('https://gemini.google.com/',root,profile=profile,keep_profile=True,executable='/chrome',manual_signin=True)
   except HTTPException as e:assert e.status_code==409 and 'lượt trước'in e.detail
   else:raise AssertionError('Reused a previously controlled browser')
   launch.assert_not_called()
  print('PASS active old controlled profile rejected before starting manual login')
asyncio.run(main())

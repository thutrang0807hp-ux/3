"""Compile and run the actual host lifecycle methods against deterministic shell/WebView seams.

Also compiles/checks the real Windows host separately. This does not execute Windows Shell.
"""
import hashlib,json,os,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'veo-node-v46/scripts/windows-installer/DesktopHost.cs'
s=SRC.read_text(encoding='utf-8-sig')
def method(text,name):
 a=text.index(name);b=text.index('{',a);depth=1;i=b+1
 while depth:
  depth+=(text[i]=='{')-(text[i]=='}');i+=1
 return text[a:i]
old=subprocess.check_output(['git','show','6794c13:veo-node-v46/scripts/windows-installer/DesktopHost.cs'],cwd=ROOT).decode('utf-8-sig')
for name in ['async Task RequestClose()','void StopBackend()','void OpenExternal(string uri)','public void Add(Process process)']:
 assert method(s,name)==method(old,name),'Unrelated lifecycle guard changed: '+name
assert 'if(startupStarted)return;startupStarted=true;'in s
assert 'TrySuspendAsync'not in s and 'view.Dispose()'not in method(s,'void HideToTray()')
for flag in ['--disable-background-timer-throttling','--disable-renderer-backgrounding','--disable-backgrounding-occluded-windows']:assert flag in s
assert 'RegisterWindowMessage("SceneForge.Desktop.Show."+hash)'in s and 'PostMessage(new IntPtr(0xffff),restoreMessage'in s
assert 'tray.Visible=false;tray.Dispose()'in method(s,'void Stop()')
a=s.index('FormClosing+=async(s,e)=>')+len('FormClosing+=async(s,e)=>');b=s.index(';FormClosed+=',a)
handler=s[a:b]
production='\n'.join(method(s,n)for n in ['void HideToTray()','void RestoreFromTray()','async Task RequestClose()','void StopBackend()','void Stop()'])
harness=r'''
using System;using System.IO;using System.Threading.Tasks;
enum FormWindowState{Normal,Minimized,Maximized}enum CloseReason{UserClosing,WindowsShutDown,ApplicationExitCall}
enum DialogResult{Yes,No}enum MessageBoxButtons{YesNo}enum MessageBoxIcon{Warning}
static class MessageBox{public static DialogResult Result=DialogResult.No;public static DialogResult Show(object x,string y,string z,MessageBoxButtons a,MessageBoxIcon b)=>Result;}
static class DesktopProgram{public static bool SetForegroundWindow(IntPtr h)=>true;}
sealed class FakeTray{public bool Visible=true,Disposed;public string BalloonTipTitle,BalloonTipText;public int Balloons;public void ShowBalloonTip(int ms){Balloons++;}public void Dispose(){Disposed=true;}}
sealed class FakeMenu{public bool Disposed;public void Dispose(){Disposed=true;}}
sealed class FakeBackend{public bool HasExited;public int Kills;public void Kill(){Kills++;HasExited=true;}}
sealed class FakeJob{readonly FakeBackend child;public int Disposes;public FakeJob(FakeBackend b){child=b;}public void Dispose(){Disposes++;child.HasExited=true;}}
sealed class FakeView{public bool Enabled=true,IsDisposed;public FakeCore CoreWebView2;}
sealed class FakeCore{readonly Harness h;public FakeCore(Harness h){this.h=h;}public Task ExecuteScriptAsync(string script){h.Flushes++;h.closeSaved.TrySetResult(h.SaveOK);return Task.CompletedTask;}}
sealed class ClosingArgs{public bool Cancel;public CloseReason CloseReason;}
sealed class Harness{
 public bool closing,allowClose,closeRequested,notifiedTray,IsDisposed,Visible=true,ShowInTaskbar=true,SaveOK=true;public int Flushes,Closes;public TaskCompletionSource<bool> closeSaved;
 public FormWindowState WindowState=FormWindowState.Normal,restoreState=FormWindowState.Normal;public FakeTray tray=new FakeTray();public FakeMenu trayMenu=new FakeMenu();public FakeBackend backend=new FakeBackend();public FakeJob job;public FakeView view;public string backendUrl="http://local/",Phase="ready";public IntPtr Handle=new IntPtr(1);StreamWriter log=null;readonly object logLock=new object();
 public Harness(){job=new FakeJob(backend);view=new FakeView();view.CoreWebView2=new FakeCore(this);}
 void WriteLog(string text){}void State(string phase,string url=null){Phase=phase;}void Hide(){Visible=false;}void Show(){Visible=true;}void Activate(){}void BeginInvoke(Action f){f();}void Close(){Closes++;Stop();IsDisposed=true;view.IsDisposed=true;}
 public async Task<bool> PressClose(CloseReason reason){var e=new ClosingArgs{CloseReason=reason};await Handler(e);return e.Cancel;}
 async Task Handler(ClosingArgs e)HANDLER
 METHODS
 public void Restore(){RestoreFromTray();}public Task Exit(){RestoreFromTray();return RequestClose();}
}
static class Test{
 static void Check(bool b,string message){if(!b)throw new Exception(message);}
 static async Task Main(){
  var h=new Harness();var backend=h.backend;var job=h.job;var view=h.view;h.WindowState=FormWindowState.Maximized;
  Check(await h.PressClose(CloseReason.UserClosing),"X was not cancelled");
  Check(!h.Visible&&!h.ShowInTaskbar&&h.Phase=="background","X did not hide to tray");
  Check(h.backend==backend&&h.job==job&&h.view==view&&!backend.HasExited&&job.Disposes==0&&!view.IsDisposed&&view.Enabled,"X destroyed backend/WebView/job");
  Check(h.Flushes==0&&h.Closes==0&&!h.closing,"X ran exit/save handshake");
  h.Restore();Check(h.Visible&&h.ShowInTaskbar&&h.WindowState==FormWindowState.Maximized&&h.Phase=="ready","Restore lost window state");
  await h.PressClose(CloseReason.UserClosing);Check(h.tray.Balloons==1,"Hide repeated the notification");
  var tray=h.tray;var menu=h.trayMenu;await h.Exit();
  Check(h.Flushes==1&&h.Closes==1&&backend.HasExited&&job.Disposes==1,"Explicit exit did not flush/stop once");
  Check(!tray.Visible&&tray.Disposed&&menu.Disposed&&h.tray==null,"Exit left tray icon alive");
  h=new Harness{SaveOK=false};tray=h.tray;await h.Exit();
  Check(!h.closing&&!h.allowClose&&!h.backend.HasExited&&h.view.Enabled&&!tray.Disposed,"Cancelled failed-save exit killed work");
  await h.PressClose(CloseReason.UserClosing);Check(!h.Visible&&!h.backend.HasExited,"X after failed exit did not hide");
  h=new Harness();await h.PressClose(CloseReason.WindowsShutDown);Check(h.Closes==1&&h.backend.HasExited,"OS close was hidden instead of exited");
  Console.WriteLine("PASS actual C# close/hide/restore/exit methods: X retains backend/job/WebView, no exit flush; restore maximized; explicit exit saves/stops/removes icon; failed-save cancellation retains work; OS shutdown exits.");
 }
}
'''.replace('HANDLER',handler).replace('METHODS',production)
deps=Path(os.environ.get('SCENEFORGE_NATIVE_DEPS','/tmp/sf-native-build'));dotnet=deps/'dotnet/dotnet';runtime=next((deps/'dotnet/shared/Microsoft.NETCore.App').iterdir())
with tempfile.TemporaryDirectory(prefix='sf-tray-test-')as td:
 td=Path(td);(td/'TrayHarness.cs').write_text(harness);out=td/'TrayHarness.dll'
 args=[str(dotnet),str(deps/'compiler/tasks/netcore/bincore/csc.dll'),'/nologo','/nostdlib+','/target:exe','/out:'+str(out)]
 args+=['/reference:'+str(p)for p in runtime.glob('*.dll')];args+=[str(td/'TrayHarness.cs')]
 subprocess.run(args,check=True,capture_output=True,text=True)
 (td/'TrayHarness.runtimeconfig.json').write_text(json.dumps({'runtimeOptions':{'tfm':'net8.0','framework':{'name':'Microsoft.NETCore.App','version':runtime.name}}}))
 subprocess.run([str(dotnet),str(out)],check=True)
# Real Windows binary: verify compiled artifact, Framework bindings and source checksum.
import dnfile
exe=ROOT/'veo-node-v46/windows-desktop/SceneForge.exe';meta=json.loads(exe.with_name('build.json').read_text());assert meta['source_sha256']==hashlib.sha256(SRC.read_bytes()).hexdigest();assert meta['exe_sha256']==hashlib.sha256(exe.read_bytes()).hexdigest()
pe=dnfile.dnPE(data=exe.read_bytes());assert pe.FILE_HEADER.Machine==0x8664 and pe.OPTIONAL_HEADER.Subsystem==2
assert list(pe.net.mdtables.Assembly)[0].RevisionNumber==46172
names={str(m.Name)for m in pe.net.mdtables.MethodDef};assert {'InitializeTray','HideToTray','RestoreFromTray','WndProc','RequestClose','StopBackend'}<=names
print('PASS actual Windows x64 .NET Framework host compiled and pinned to tested source; tray/IPC/background timer flags present. Windows Shell/WebView2 integration not executed on Windows.')

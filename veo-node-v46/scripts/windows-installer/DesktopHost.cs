using System;
using System.IO;
using System.Text;
using System.Linq;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using System.Net;
using System.Security.Cryptography;
using System.Runtime.InteropServices;
using System.Web.Script.Serialization;
using System.Windows.Forms;
using Microsoft.Web.WebView2.Core;
using Microsoft.Web.WebView2.WinForms;

[assembly: System.Reflection.AssemblyTitle("SceneForge")]
[assembly: System.Reflection.AssemblyVersion("2026.11.11.46109")]
internal static class DesktopProgram {
 [DllImport("user32.dll")] internal static extern bool SetForegroundWindow(IntPtr h);
 [DllImport("user32.dll")] static extern bool SetProcessDPIAware();
 [DllImport("shell32.dll", CharSet=CharSet.Unicode)] static extern int SetCurrentProcessExplicitAppUserModelID(string appID);
 [STAThread] static int Main(string[] args) {
  if(args.Contains("--check-runtime")){try{return String.IsNullOrEmpty(CoreWebView2Environment.GetAvailableBrowserVersionString())?2:0;}catch{return 2;}}
  // Establish taskbar identity before any HWND is created.
  try{SetCurrentProcessExplicitAppUserModelID("SceneForge.Desktop");}catch{}
  Application.EnableVisualStyles();SetProcessDPIAware();Application.SetCompatibleTextRenderingDefault(false);
  try {
   string root=AppDomain.CurrentDomain.BaseDirectory.TrimEnd('\\');
   var config=new JavaScriptSerializer().Deserialize<Dictionary<string,object>>(File.ReadAllText(Path.Combine(root,"install-settings.json"),Encoding.UTF8));
   string data=(string)config["data_directory"];Directory.CreateDirectory(data);
   string hash;using(var sha=SHA256.Create())hash=BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(Path.GetFullPath(data).ToLowerInvariant()))).Replace("-","").Substring(0,24);
   using(var mutex=new Mutex(false,"Local\\SceneForgeDesktop-"+hash)) {
    bool owned=false;try{owned=mutex.WaitOne(0);}catch(AbandonedMutexException){owned=true;}
    if(!owned){foreach(var p in Process.GetProcessesByName("SceneForge")){try{if(p.Id!=Process.GetCurrentProcess().Id&&p.MainModule.FileName==Application.ExecutablePath){SetForegroundWindow(p.MainWindowHandle);break;}}catch{}}return 0;}
    try{Application.Run(new DesktopWindow(root,data,config));}finally{mutex.ReleaseMutex();}
   }
   return 0;
  }catch(Exception e){MessageBox.Show("Chưa mở được SceneForge.\n"+e.Message,"SceneForge",MessageBoxButtons.OK,MessageBoxIcon.Error);return 1;}
 }
}
internal sealed class DesktopWindow:Form {
 readonly string root,data,logPath;readonly Dictionary<string,object> config;
 readonly JavaScriptSerializer json=new JavaScriptSerializer();readonly StartupSplash message=new StartupSplash();
 Process backend;OwnedProcessJob job;WebView2 view;StreamWriter log;readonly object logLock=new object();bool closing,allowClose,closeRequested;TaskCompletionSource<bool> closeSaved;
 public DesktopWindow(string root,string data,Dictionary<string,object> config){
  this.root=root;this.data=data;this.config=config;logPath=Path.Combine(data,"desktop-startup.log");
  Text="SceneForge";Width=1440;Height=960;MinimumSize=new System.Drawing.Size(1000,680);StartPosition=FormStartPosition.CenterScreen;
  ShowIcon=true;ShowInTaskbar=true;
  BackColor=System.Drawing.Color.FromArgb(16,19,24);ForeColor=System.Drawing.Color.White;
  try{string icon=Path.Combine(root,"app","dist","web-demo","icons","SceneForge.ico");if(File.Exists(icon))Icon=new System.Drawing.Icon(icon);else Icon=System.Drawing.Icon.ExtractAssociatedIcon(Application.ExecutablePath);}catch{}
  message.Dock=DockStyle.Fill;message.Font=new System.Drawing.Font("Segoe UI",13);message.Text="Đang mở SceneForge…";Controls.Add(message);
  Shown+=async(s,e)=>await StartApplication();FormClosing+=async(s,e)=>{if(allowClose)return;e.Cancel=true;await RequestClose();};FormClosed+=(s,e)=>Stop();
 }
 void WriteLog(string text){lock(logLock){if(log!=null){log.WriteLine(text);log.Flush();}}}
 void State(string phase,string url=null){
  var state=new Dictionary<string,object>{{"pid",Process.GetCurrentProcess().Id},{"window",Handle.ToInt64()},{"phase",phase},{"console",false},{"app_version","2026.11.11.46109"},{"backend_pid",backend==null?0:backend.Id}};
  if(url!=null)state["url"]=url;
  File.WriteAllText(Path.Combine(data,"desktop-state.json"),json.Serialize(state),new UTF8Encoding(false));
 }
 async Task StartApplication(){
  try{
   log=new StreamWriter(logPath,false,new UTF8Encoding(false));State("starting");
   bool missingRuntime=false;try{CoreWebView2Environment.GetAvailableBrowserVersionString();}
   catch(WebView2RuntimeNotFoundException){missingRuntime=true;}
   if(missingRuntime){
    message.Text="Đang chuẩn bị thành phần cửa sổ Windows…\nLần đầu cần kết nối mạng.";
    string setup=Path.Combine(root,"MicrosoftEdgeWebview2Setup.exe");if(!File.Exists(setup))throw new IOException("Thiếu bộ chuẩn bị WebView2. Hãy chạy lại bản cập nhật.");
    var installer=Process.Start(new ProcessStartInfo(setup,"/silent /install"){UseShellExecute=false,CreateNoWindow=true});
    await Task.Run(()=>{if(!installer.WaitForExit(300000)){installer.Kill();throw new IOException("Chưa tải xong WebView2. Kiểm tra mạng rồi mở lại ứng dụng.");}});
    if(closing)return;
    bool prepared=false;for(int i=0;i<100&&!closing;i++){try{CoreWebView2Environment.GetAvailableBrowserVersionString();prepared=true;break;}catch(WebView2RuntimeNotFoundException){}await Task.Delay(200);}
    if(!prepared)throw new IOException("Chưa chuẩn bị xong thành phần cửa sổ Windows. Kiểm tra mạng rồi mở lại app.");
   }
   message.Stage=0;message.Text="Đang khởi động bộ xử lý…";
   string python=Path.Combine(root,"runtime","python.exe"),script=Path.Combine(root,"app","windows_bootstrap.py");
   var info=new ProcessStartInfo(python,"-E -s -X utf8 \""+script+"\""){WorkingDirectory=Path.Combine(root,"app"),UseShellExecute=false,CreateNoWindow=true,RedirectStandardOutput=true,RedirectStandardError=true,StandardOutputEncoding=Encoding.UTF8,StandardErrorEncoding=Encoding.UTF8};
   info.EnvironmentVariables["SCENEFORGE_NO_BROWSER"]="1";info.EnvironmentVariables["SCENEFORGE_DESKTOP"]="1";
   backend=new Process{StartInfo=info};backend.OutputDataReceived+=(s,e)=>{if(e.Data!=null)WriteLog(e.Data);};backend.ErrorDataReceived+=(s,e)=>{if(e.Data!=null)WriteLog(e.Data);};
   job=new OwnedProcessJob();if(!backend.Start())throw new IOException("Không khởi động được phần xử lý.");job.Add(backend);
   backend.BeginOutputReadLine();backend.BeginErrorReadLine();
   string url=null;
   for(int i=0;i<150&&!closing;i++){
    if(backend.HasExited)throw new IOException("Phần xử lý dừng khi khởi động. Nhật ký: "+logPath);
    try{
     var instance=json.Deserialize<Dictionary<string,object>>(File.ReadAllText(Path.Combine(data,"instance.json"),Encoding.UTF8));
     int pid=Convert.ToInt32(instance["pid"]),port=Convert.ToInt32(instance["port"]);
     if(pid!=backend.Id)throw new IOException("SceneForge đang chạy từ cửa sổ khác. Đóng bản đó rồi mở lại.");
     string address="http://127.0.0.1:"+port+"/";
     bool ready=await Task.Run(()=>{try{var request=(HttpWebRequest)WebRequest.Create(address+"local-api/health");request.Proxy=null;request.Timeout=500;using(var response=request.GetResponse())using(var reader=new StreamReader(response.GetResponseStream()))return reader.ReadToEnd().Contains("sceneforge-local");}catch{return false;}});
     if(ready){url=address;break;}
    }catch(IOException){}catch(ArgumentException){}
    await Task.Delay(200);
   }
   if(closing)return;if(url==null)throw new IOException("Phần xử lý chưa sẵn sàng. Nhật ký: "+logPath);
   message.Stage=1;message.Text="Đang chuẩn bị cửa sổ…";
   var options=new CoreWebView2EnvironmentOptions();string debug=Environment.GetEnvironmentVariable("SCENEFORGE_DESKTOP_TEST_PORT");
   int debugPort;if(Int32.TryParse(debug,out debugPort)&&debugPort>=1024&&debugPort<=65535)options.AdditionalBrowserArguments="--remote-debugging-port="+debugPort;
   var environment=await CoreWebView2Environment.CreateAsync(null,Path.Combine(data,"desktop-profile"),options);
   if(closing)return;view=new WebView2{Dock=DockStyle.Fill,DefaultBackgroundColor=BackColor};Controls.Add(view);message.BringToFront();
   await view.EnsureCoreWebView2Async(environment);
   view.CoreWebView2.Settings.AreDevToolsEnabled=debugPort>=1024;view.CoreWebView2.Settings.IsStatusBarEnabled=false;
   view.CoreWebView2.NewWindowRequested+=(s,e)=>{e.Handled=true;OpenExternal(e.Uri);};
   view.CoreWebView2.NavigationStarting+=(s,e)=>{if(e.Uri!="about:blank"&&!e.Uri.StartsWith(url,StringComparison.OrdinalIgnoreCase)){e.Cancel=true;if(e.IsUserInitiated)OpenExternal(e.Uri);}};
   view.CoreWebView2.WebMessageReceived+=(s,e)=>{try{var value=json.Deserialize<Dictionary<string,object>>(e.WebMessageAsJson);if(value.ContainsKey("type")&&(string)value["type"]=="sf-desktop-flush"&&closeSaved!=null)closeSaved.TrySetResult(value.ContainsKey("ok")&&(bool)value["ok"]);}catch{}};
   view.CoreWebView2.NavigationCompleted+=(s,e)=>{if(closing)return;if(e.IsSuccess){if(view.CoreWebView2.Source.StartsWith(url,StringComparison.OrdinalIgnoreCase)){message.Visible=false;view.BringToFront();}}else{message.Text="Chưa mở được giao diện.\n"+e.WebErrorStatus+"\nNhật ký: "+logPath;message.Visible=true;message.BringToFront();}};
   message.Stage=2;message.Text="Đang mở không gian sáng tạo…";
   view.CoreWebView2.Navigate(url);State("ready",url);
  }catch(Exception e){
   if(closing)return;WriteLog(e.ToString());State("error");message.Text="Chưa mở được SceneForge.\n"+e.Message+"\n\nNhật ký: "+logPath;
   if(view!=null){Controls.Remove(view);view.Dispose();view=null;}message.Visible=true;message.BringToFront();StopBackend();
  }
 }
 async Task RequestClose(){
  if(closeRequested)return;closeRequested=true;
  try{
   bool saved=true;
   if(view!=null&&view.CoreWebView2!=null){
    view.Enabled=false;closeSaved=new TaskCompletionSource<bool>();
    await view.CoreWebView2.ExecuteScriptAsync(@"(async()=>{try{await window.SceneForgeApp?.flush?.();await window.SceneForgeStorage?.flush?.();window.chrome.webview.postMessage({type:'sf-desktop-flush',ok:true});}catch(e){window.chrome.webview.postMessage({type:'sf-desktop-flush',ok:false});}})()");
    var done=await Task.WhenAny(closeSaved.Task,Task.Delay(20000));saved=done==closeSaved.Task&&closeSaved.Task.Result;
   }
   if(!saved&&MessageBox.Show(this,"Chưa lưu xong thay đổi hoặc đang có việc xử lý. Thoát ngay có thể mất phần chưa lưu. Vẫn thoát?","SceneForge",MessageBoxButtons.YesNo,MessageBoxIcon.Warning)!=DialogResult.Yes)return;
   allowClose=true;closing=true;BeginInvoke(new Action(Close));
  }catch(Exception e){WriteLog(e.ToString());if(MessageBox.Show(this,"Chưa lưu xong. Vẫn đóng ứng dụng?","SceneForge",MessageBoxButtons.YesNo,MessageBoxIcon.Warning)==DialogResult.Yes){allowClose=true;closing=true;BeginInvoke(new Action(Close));}}
  finally{closeRequested=false;if(view!=null&&!view.IsDisposed)view.Enabled=true;}
 }
 void OpenExternal(string uri){Uri parsed;if(Uri.TryCreate(uri,UriKind.Absolute,out parsed)&&(parsed.Scheme=="https"||parsed.Scheme=="http"))Process.Start(new ProcessStartInfo(uri){UseShellExecute=true});}
 void StopBackend(){if(job!=null){job.Dispose();job=null;}if(backend!=null){try{if(!backend.HasExited)backend.Kill();}catch{}}}
 void Stop(){closing=true;StopBackend();lock(logLock){if(log!=null){log.Dispose();log=null;}}}
}
internal sealed class OwnedProcessJob:IDisposable {
 [StructLayout(LayoutKind.Sequential)] struct BasicLimits {public long PerProcessUserTimeLimit,PerJobUserTimeLimit;public uint LimitFlags;public UIntPtr MinimumWorkingSetSize,MaximumWorkingSetSize;public uint ActiveProcessLimit;public UIntPtr Affinity;public uint PriorityClass,SchedulingClass;}
 [StructLayout(LayoutKind.Sequential)] struct IoCounters {public ulong ReadOperationCount,WriteOperationCount,OtherOperationCount,ReadTransferCount,WriteTransferCount,OtherTransferCount;}
 [StructLayout(LayoutKind.Sequential)] struct Limits {public BasicLimits BasicLimitInformation;public IoCounters IoInfo;public UIntPtr ProcessMemoryLimit,JobMemoryLimit,PeakProcessMemoryUsed,PeakJobMemoryUsed;}
 [DllImport("kernel32.dll",CharSet=CharSet.Unicode)] static extern IntPtr CreateJobObject(IntPtr attributes,string name);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool SetInformationJobObject(IntPtr job,int type,ref Limits limits,uint size);
 [DllImport("kernel32.dll",SetLastError=true)] static extern bool AssignProcessToJobObject(IntPtr job,IntPtr process);
 [DllImport("kernel32.dll")] static extern bool CloseHandle(IntPtr handle);
 IntPtr handle;
 public OwnedProcessJob(){handle=CreateJobObject(IntPtr.Zero,null);var limits=new Limits();limits.BasicLimitInformation.LimitFlags=0x2000;if(handle==IntPtr.Zero||!SetInformationJobObject(handle,9,ref limits,(uint)Marshal.SizeOf(typeof(Limits))))throw new IOException("Không quản lý được tiến trình ứng dụng.");}
 public void Add(Process process){if(!AssignProcessToJobObject(handle,process.Handle)){process.Kill();throw new IOException("Không quản lý được tiến trình xử lý.");}}
 public void Dispose(){if(handle!=IntPtr.Zero){CloseHandle(handle);handle=IntPtr.Zero;}}
}

// Native startup surface: available before Python and WebView2 are ready.
internal sealed class StartupSplash:Control {
 readonly System.Windows.Forms.Timer pulse=new System.Windows.Forms.Timer();int tick;int stage;
 public int Stage{get{return stage;}set{stage=value;Invalidate();}}
 public StartupSplash(){SetStyle(ControlStyles.UserPaint|ControlStyles.AllPaintingInWmPaint|ControlStyles.OptimizedDoubleBuffer|ControlStyles.ResizeRedraw,true);BackColor=System.Drawing.Color.FromArgb(13,17,23);pulse.Interval=50;pulse.Tick+=(s,e)=>{tick=(tick+1)%32;Invalidate();};}
 protected override void OnVisibleChanged(EventArgs e){base.OnVisibleChanged(e);pulse.Enabled=Visible;}
 protected override void OnHandleCreated(EventArgs e){base.OnHandleCreated(e);pulse.Enabled=Visible;}
 protected override void OnTextChanged(EventArgs e){base.OnTextChanged(e);Invalidate();}
 protected override void Dispose(bool disposing){if(disposing)pulse.Dispose();base.Dispose(disposing);}
 static System.Drawing.Drawing2D.GraphicsPath Rounded(float x,float y,float w,float h,float r){var p=new System.Drawing.Drawing2D.GraphicsPath();p.AddArc(x,y,r*2,r*2,180,90);p.AddArc(x+w-r*2,y,r*2,r*2,270,90);p.AddArc(x+w-r*2,y+h-r*2,r*2,r*2,0,90);p.AddArc(x,y+h-r*2,r*2,r*2,90,90);p.CloseFigure();return p;}
 protected override void OnPaint(PaintEventArgs e){
  base.OnPaint(e);var g=e.Graphics;float scale=g.DpiX/96f;g.ScaleTransform(scale,scale);g.SmoothingMode=System.Drawing.Drawing2D.SmoothingMode.AntiAlias;
  bool failed=Text.StartsWith("Chưa");float width=ClientSize.Width/scale,height=ClientSize.Height/scale,cw=Math.Min(420,width-48),ch=failed?410:300,x=(width-cw)/2,y=(height-ch)/2;
  var lime=System.Drawing.Color.FromArgb(212,245,60);var muted=System.Drawing.Color.FromArgb(137,151,166);
  using(var path=Rounded(x,y,cw,ch,24))using(var fill=new System.Drawing.SolidBrush(System.Drawing.Color.FromArgb(20,27,34)))using(var border=new System.Drawing.Pen(System.Drawing.Color.FromArgb(43,52,60))){g.FillPath(fill,path);g.DrawPath(border,path);}
  using(var pen=new System.Drawing.Pen(lime,2)){
   float bx=x+36,by=y+34;g.DrawRectangle(pen,bx,by+7,34,28);g.DrawLine(pen,bx,by+17,bx+34,by+17);g.DrawLine(pen,bx+5,by+7,bx+11,by+17);g.DrawLine(pen,bx+16,by+7,bx+22,by+17);
   g.DrawPolygon(pen,new[]{new System.Drawing.PointF(bx+13,by+22),new System.Drawing.PointF(bx+23,by+27),new System.Drawing.PointF(bx+13,by+32)});
  }
  using(var brand=new System.Drawing.Font("Segoe UI",18,System.Drawing.FontStyle.Bold))using(var heading=new System.Drawing.Font("Segoe UI",12,System.Drawing.FontStyle.Bold))using(var detail=new System.Drawing.Font("Segoe UI",9))using(var small=new System.Drawing.Font("Segoe UI",8))using(var white=new System.Drawing.SolidBrush(System.Drawing.Color.FromArgb(237,242,244)))using(var grey=new System.Drawing.SolidBrush(muted))using(var accent=new System.Drawing.SolidBrush(lime)){
   g.DrawString("SceneForge",brand,white,x+85,y+33);g.DrawString(failed?"Chưa mở được SceneForge":"Mở không gian sáng tạo",heading,white,x+36,y+101);
   g.DrawString(Text,detail,grey,new System.Drawing.RectangleF(x+36,y+135,cw-72,failed?240:78));
   if(failed)return;
   using(var track=new System.Drawing.SolidBrush(System.Drawing.Color.FromArgb(41,49,58)))g.FillRectangle(track,x+36,y+223,cw-72,3);
   float available=cw-72,segment=available*.28f,offset=(float)((Math.Sin(tick*Math.PI/16)+1)*.5)*(available-segment);g.FillRectangle(accent,x+36+offset,y+223,segment,3);
   string[]steps={"Bộ xử lý","Cửa sổ","Giao diện"};for(int i=0;i<3;i++)g.DrawString(steps[i],small,i==stage?accent:grey,x+36+i*105,y+247);
  }
 }
}

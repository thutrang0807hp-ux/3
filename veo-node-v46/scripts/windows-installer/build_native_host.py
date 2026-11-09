"""Cross-compile the .NET Framework 4.8 Windows host with Microsoft Roslyn.

--dependencies contains the official runtime/compiler/refs/webview packages.
No build runtime or SDK is shipped to the user's application.
"""
import argparse,hashlib,json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--dependencies',type=Path,required=True);args=ap.parse_args();p=args.dependencies
 out=ROOT/'veo-node-v46/windows-desktop/SceneForge.exe';out.parent.mkdir(exist_ok=True)
 refs=p/'refs/build/.NETFramework/v4.8';sdk=p/'webview/lib/net462'
 command=[str(p/'dotnet/dotnet'),str(p/'compiler/tasks/netcore/bincore/csc.dll'),'/nologo','/nostdlib+','/target:winexe','/platform:x64','/optimize+','/deterministic+','/win32icon:'+str(ROOT/'icons/SceneForge.ico'),'/out:'+str(out)]
 command+=['/reference:'+str(refs/(n+'.dll'))for n in ['mscorlib','System','System.Core','System.Windows.Forms','System.Drawing','System.Web.Extensions']]
 command+=['/reference:'+str(sdk/n)for n in ['Microsoft.Web.WebView2.Core.dll','Microsoft.Web.WebView2.WinForms.dll']]
 source=Path(__file__).with_name('DesktopHost.cs');command+=[str(source)];subprocess.run(command,check=True)
 meta={'target':'.NET Framework 4.8, Windows x64','compiler':'Microsoft.Net.Compilers.Toolset 4.11.0','webview_sdk':'1.0.3537.50','source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'exe_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'native_windows_run':False,'packages':{n:hashlib.sha256((p/n).read_bytes()).hexdigest()for n in ['runtime.tar.gz','compiler.zip','refs.zip','webview.zip']}}
 out.with_name('build.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))
if __name__=='__main__':main()

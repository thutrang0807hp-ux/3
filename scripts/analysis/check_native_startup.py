"""Static native-host/package checks; does not execute a Windows GUI."""
from pathlib import Path
import hashlib,io,json,zipfile
import dnfile
ROOT=Path(__file__).resolve().parents[2]
s=(ROOT/'veo-node-v46/scripts/windows-installer/DesktopHost.cs').read_text(encoding='utf-8-sig')
with zipfile.ZipFile(ROOT/'downloads/v46-flow-cli-direct/SceneForge-v46.50-Full-Source.zip')as z:old=z.read('SceneForge-v46.50/scripts/windows-installer/DesktopHost.cs').decode('utf-8-sig')
def method(source,name):
 start=source.index(name);a=source.index('{',start);depth=1;b=a+1
 while depth:
  depth+=(source[b]=='{')-(source[b]=='}');b+=1
 return source[start:b]
for name in ['async Task RequestClose()','void StopBackend()','void Stop()','void OpenExternal(string uri)','public void Add(Process process)']:
 assert method(s,name)==method(old,name),name
assert 'class StartupSplash:Control'in s and 'OptimizedDoubleBuffer'in s
assert 'message.BringToFront();\n   await view.EnsureCoreWebView2Async'in s
assert 'NavigationCompleted+='in s and 'Source.StartsWith(url,StringComparison.OrdinalIgnoreCase)'in s
assert 'pulse.Dispose()'in s and 'if(failed)return;'in s
exe=ROOT/'veo-node-v46/windows-desktop/SceneForge.exe';pe=dnfile.dnPE(data=exe.read_bytes())
assert pe.FILE_HEADER.Machine==0x8664 and pe.OPTIONAL_HEADER.Subsystem==2
refs=[str(r.Name)for r in pe.net.mdtables.AssemblyRef]
assert 'mscorlib'in refs and 'Microsoft.Web.WebView2.WinForms'in refs and 'System.Runtime'not in refs,refs
assembly=list(pe.net.mdtables.Assembly)[0];assert assembly.RevisionNumber==46101
meta=json.loads((ROOT/'downloads/v46-native-startup/patch-build.json').read_text());package=dnfile.dnPE(data=(ROOT/'downloads/v46-native-startup'/meta['file']).read_bytes())
with zipfile.ZipFile(io.BytesIO(next(r.data for r in package.net.resources if r.name=='SceneForgePatch.zip')))as z:
 assert z.read('files/SceneForge.exe')==exe.read_bytes()
 for item in meta['files']:assert hashlib.sha256(z.read('files/'+item['path'])).hexdigest()==item['sha256']
print('PASS compiled Windows x64 host, Framework references, native loading handoff, unchanged close/process guards, verified EXE payload. No Windows GUI run.')

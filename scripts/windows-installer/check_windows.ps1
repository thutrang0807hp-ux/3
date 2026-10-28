param([Parameter(Mandatory=$true)][string]$InstallerUrl,
      [Parameter(Mandatory=$true)][string]$InstallerSha,
      [Parameter(Mandatory=$true)][string]$Version)
$ErrorActionPreference='Stop'
$root=Join-Path $env:RUNNER_TEMP ('SceneForge thu nghiem ' + [char]0x1EC7)
New-Item -ItemType Directory -Path $root -Force | Out-Null
$env:LOCALAPPDATA=Join-Path $root 'Local AppData'
$env:SCENEFORGE_LOCAL_DATA=Join-Path $root 'Du lieu rieng'
$env:SCENEFORGE_NO_BROWSER='1'
$env:SCENEFORGE_INSTALL_TEST='1'
$report=@{version=$Version;os=[Environment]::OSVersion.VersionString;passed=$false;checks=@();installer_sha256=$InstallerSha}
$launcher=$null;$installer=$null
try {
    $file=Join-Path $root 'SceneForge Setup.exe'
    Invoke-WebRequest -Uri $InstallerUrl -OutFile $file
    if ((Get-FileHash $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $InstallerSha) {throw 'Downloaded installer hash mismatch'}
    $installer=Start-Process -FilePath $file -PassThru -RedirectStandardOutput (Join-Path $root 'install.log') -RedirectStandardError (Join-Path $root 'install-error.log')
    $null=$installer.Handle
    if (!$installer.WaitForExit(180000)) {throw 'Installer timeout'}
    $report.installer_exit_code=$installer.ExitCode
    if ($null -ne $installer.ExitCode -and $installer.ExitCode -ne 0) {throw ('Installer failed: '+(Get-Content (Join-Path $root 'install.log') -Raw))}
    $home=Join-Path $env:LOCALAPPDATA "SceneForge\releases\$Version"
    $marker=Get-Content (Join-Path $home 'installation.json') -Raw | ConvertFrom-Json
    if($marker.version -ne $Version){throw 'Installer marker missing/wrong'}
    $exe=Join-Path $home 'SceneForge.exe'
    $python=Join-Path $home 'runtime\python.exe'
    $report.checks+='native installer: extract, hash verify, Unicode/spaces in paths'
    & $python -E -s -X utf8 -m pip check
    if ($LASTEXITCODE -ne 0) {throw 'Windows bundled dependency check failed'}
    $report.checks+='bundled Python and pip dependency consistency'
    $launcher=Start-Process -FilePath $exe -WorkingDirectory $home -PassThru -RedirectStandardOutput (Join-Path $root 'app.log') -RedirectStandardError (Join-Path $root 'app-error.log')
    $ready=$false
    for ($i=0;$i -lt 90;$i++) {
        Start-Sleep -Seconds 1
        $instance=Join-Path $env:SCENEFORGE_LOCAL_DATA 'instance.json'
        if (Test-Path $instance) {
            $port=(Get-Content $instance -Raw | ConvertFrom-Json).port
            $base="http://127.0.0.1:$port"
            try {$health=Invoke-RestMethod "$base/local-api/health";if($health.service -eq 'sceneforge-local'){$ready=$true;break}}catch{}
        }
        if ($launcher.HasExited) {break}
    }
    if (!$ready) {throw ('App not ready: '+(Get-Content (Join-Path $root 'app-error.log') -Raw))}
    $report.checks+='native launcher -> bundled Python -> real Windows loopback health'
    $null=Invoke-WebRequest $base -SessionVariable session
    foreach($page in @('/photos.html','/workflow.html','/native/index.html')) {
        $response=Invoke-WebRequest ($base+$page) -WebSession $session
        if ($response.StatusCode -ne 200 -or $response.Content.Length -lt 10000) {throw "Page missing: $page"}
    }
    $caps=Invoke-RestMethod "$base/local-api/analysis/local/capabilities" -WebSession $session
    if ($caps.whisper_model) {throw 'Unexpected model bundled or user data was reused'}
    $report.capabilities=$caps
    $report.checks+='real frontend routes, session cookie, SQLite/vault startup, honest missing model capability'
    $uiProbe=Join-Path $root 'windows-ui-check.py'
    @'
import os,sys,json
from pathlib import Path
from playwright.sync_api import sync_playwright
candidates=[Path(os.environ.get(k,''))/r for k in ['PROGRAMFILES','PROGRAMFILES(X86)','LOCALAPPDATA'] for r in ['Microsoft/Edge/Application/msedge.exe','Google/Chrome/Application/chrome.exe']]
exe=next((p for p in candidates if p.is_file()),None)
if not exe:raise RuntimeError('No installed browser for Windows UI verification')
with sync_playwright()as pw:
 b=pw.chromium.launch(executable_path=str(exe),headless=True)
 p=b.new_page(viewport={'width':1600,'height':1050});errors=[];posts=[]
 p.on('pageerror',lambda e:errors.append(str(e)))
 p.on('request',lambda r:posts.append(r.url)if r.method=='POST'and any(s in r.url for s in ['/flow/jobs','/muse/jobs','/gemini-chat/jobs','/web-images/jobs'])else None)
 p.goto(sys.argv[1]);p.wait_for_function('appBootReady&&SceneForgeStorage.state.active',timeout=60000)
 p.evaluate("async()=>{prefs.package5WelcomeDone=true;await savePrefs();document.querySelector('#shellDialog').close();}")
 for mode in ['reference','photos']:
  p.evaluate("async mode=>{const r={id:'windows-check-'+mode,name:'Windows check',mode,stage:'review',productId:products[0].id};rooms.push(r);await persistRoom(r);await openRoom(r.id,'analysis');}",mode)
  f=p.locator('#workflowFrame').element_handle().content_frame()
  f.wait_for_function('!!window.SFPromptPipeline'if mode=='reference'else'loaded&&!!window.SFPhotoPromptPipeline',timeout=60000)
  f.wait_for_function('!!window.SceneForgeWorkflow?.workspaceAutoPlan?.()',timeout=30000)
  assert len(f.evaluate('SceneForgeWorkflow.workspaceAutoPlan().scopes'))==3
  assert p.locator('#workspaceAuto').count()==1
 assert not errors,errors
 assert not posts,posts
 b.close()
print('PASS real Windows browser boots app, reference canvas and photo canvas; no generation requests')
'@ | Set-Content -LiteralPath $uiProbe -Encoding UTF8
    & $python -E -s -X utf8 $uiProbe $base
    if($LASTEXITCODE -ne 0){throw 'Windows browser UI check failed'}
    $report.checks+='actual Windows Edge/Chrome boots shell, reference and photo canvases; no generation requests'
    $again=Start-Process -FilePath $exe -WorkingDirectory $home -PassThru
    $null=$again.Handle
    if (!$again.WaitForExit(15000) -or ($null -ne $again.ExitCode -and $again.ExitCode -ne 0)) {throw 'Second launch should reuse current instance'}
    $report.checks+='second launcher reuses the OS-owned instance lock'
    $installer=Start-Process -FilePath $file -PassThru
    $null=$installer.Handle
    if (!$installer.WaitForExit(180000) -or ($null -ne $installer.ExitCode -and $installer.ExitCode -ne 0)) {throw 'Idempotent reinstall failed'}
    if (!(Test-Path (Join-Path $env:SCENEFORGE_LOCAL_DATA 'instance.json'))) {throw 'Reinstall removed data'}
    $report.checks+='same installer runs again without replacing existing release/user data'
    $report.passed=$true
} catch {
    $report.error="$_"
    throw
} finally {
    if($launcher -and !$launcher.HasExited){taskkill /PID $launcher.Id /T /F | Out-Null}
    if($installer -and !$installer.HasExited){taskkill /PID $installer.Id /T /F | Out-Null}
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath 'windows-check-report.json' -Encoding UTF8
}

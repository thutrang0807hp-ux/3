$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
$package=$env:SF_PATCH_ROOT
$manifest=Get-Content -LiteralPath (Join-Path $package 'patch-manifest.json') -Encoding UTF8 -Raw|ConvertFrom-Json
$script:failed=$null;$script:working=$false
$form=New-Object Windows.Forms.Form;$form.Text='Cập nhật SceneForge';$form.Size=New-Object Drawing.Size(700,360);$form.StartPosition='CenterScreen';$form.Font=New-Object Drawing.Font('Segoe UI',10);$form.FormBorderStyle='FixedDialog';$form.MaximizeBox=$false
$label=New-Object Windows.Forms.Label;$label.Text="Cập nhật gộp .62 → .115: gồm toàn bộ các bản .63–.96.`r`nGiữ dự án, tài khoản, Python và model đã cài.";$label.SetBounds(24,20,640,65);$form.Controls.Add($label)
$path=New-Object Windows.Forms.TextBox;$path.SetBounds(24,105,530,30);$form.Controls.Add($path)
$pick=New-Object Windows.Forms.Button;$pick.Text='Chọn…';$pick.SetBounds(565,103,95,32);$pick.Add_Click({$d=New-Object Windows.Forms.FolderBrowserDialog;$d.Description='Chọn thư mục có SceneForge.exe';if($d.ShowDialog($form)-eq 'OK'){$path.Text=$d.SelectedPath};$d.Dispose()});$form.Controls.Add($pick)
$status=New-Object Windows.Forms.Label;$status.Text='Chọn thư mục đang chạy SceneForge rồi bấm Cập nhật. Không cần cài từng bản trung gian.';$status.SetBounds(24,155,640,80);$form.Controls.Add($status)
$go=New-Object Windows.Forms.Button;$go.Text='Cập nhật';$go.SetBounds(430,260,135,35);$form.Controls.Add($go)
$cancel=New-Object Windows.Forms.Button;$cancel.Text='Đóng';$cancel.SetBounds(575,260,85,35);$cancel.Add_Click({if(!$script:working){$form.Close()}});$form.Controls.Add($cancel)
function ShowInstalledBuild {
 try {
  $build=Join-Path $path.Text 'app-build.json'
  if(Test-Path -LiteralPath $build){$found=Get-Content -LiteralPath $build -Encoding UTF8 -Raw|ConvertFrom-Json;$status.Text='Thư mục đang chọn: phiên bản '+$found.version+'. Gói gộp nhận từ .62 trở lên; giữ model và dữ liệu.'}
  else{$status.Text='Chọn thư mục có SceneForge.exe, install-settings.json và app-build.json. Chưa thay đổi tệp nào.'}
 }catch{$status.Text='Chưa đọc được phiên bản ở thư mục này. Hãy kiểm tra lại đường dẫn.'}
}
$path.Add_TextChanged({if(!$script:working){ShowInstalledBuild}})
$known=Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\SceneForge-*' -ErrorAction SilentlyContinue|Select-Object -First 1
if($known){$releases=Join-Path $known.InstallLocation 'releases';if(Test-Path $releases){$candidate=Get-ChildItem $releases -Directory|Where-Object {Test-Path (Join-Path $_.FullName 'SceneForge.exe')}|Sort-Object Name -Descending|Select-Object -First 1;if($candidate){$path.Text=$candidate.FullName}}}
function Inside([string]$file,[string]$parent){return $file.StartsWith($parent.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)}
function MinimumPatchVersion([string]$text){
 # v46.1/v46.2 accidentally wrote five components; the fifth was a hotfix.
 # This conversion is only for the minimum baseline check, not update ordering.
 if($text -match '^([0-9]+\.[0-9]+\.[0-9]+\.[0-9]+)\.[0-9]+$'){$text=$Matches[1]}
 return [version]$text
}
function ApplyUpdate {
 $script:working=$true;$go.Enabled=$false;$pick.Enabled=$false
 $backup=$null;$changes=@();$root=$null
 try{
  $root=[IO.Path]::GetFullPath($path.Text).TrimEnd('\')
  if(!(Test-Path (Join-Path $root 'install-settings.json'))){throw 'Chọn thư mục có SceneForge.exe và install-settings.json (bên trong releases).'}
  $owner=Get-Content (Join-Path $root 'installation.json') -Encoding UTF8 -Raw|ConvertFrom-Json
  if($owner.app_id -ne 'SceneForge' -or $owner.payload_sha256 -notin $manifest.supported_payloads){throw 'Bản vá dành cho bộ cài v2 đã phát hành. Chưa thay đổi tệp nào.'}
  if($manifest.minimum_patch){
   $buildPath=Join-Path $root 'app-build.json'
   if(!(Test-Path -LiteralPath $buildPath)){throw ('Không tìm thấy app-build.json trong thư mục đã chọn. Cần bản .62 trở lên. Hãy chọn đúng thư mục đang chạy SceneForge. Chưa thay đổi tệp nào.')}
   $installed=Get-Content -LiteralPath $buildPath -Encoding UTF8 -Raw|ConvertFrom-Json
   if((MinimumPatchVersion $installed.version) -lt (MinimumPatchVersion $manifest.minimum_patch)){throw ('Thư mục đang chọn có bản '+$installed.version+'; gói này cần '+$manifest.minimum_patch+' trở lên. Hãy chọn đúng thư mục app hoặc cập nhật .62 trước. Chưa thay đổi tệp nào.')}
  }
  if($installed -and (MinimumPatchVersion $installed.version) -gt (MinimumPatchVersion $manifest.version)){throw ('Thư mục đang chọn đã có bản mới hơn: '+$installed.version+'. Không hạ phiên bản; chưa thay đổi tệp nào.')}
  $busy=@(Get-CimInstance Win32_Process|Where-Object {$_.ExecutablePath -and(Inside $_.ExecutablePath $root)})
  if($busy.Count){
   if($env:SCENEFORGE_UPDATE_TEST -ne '1' -and [Windows.Forms.MessageBox]::Show($form,'Cần đóng SceneForge để cập nhật. Việc xử lý trên máy đang chạy sẽ dừng. Tiếp tục?','Đóng app để cập nhật','YesNo','Warning') -ne 'Yes'){return}
   $previousPreference=$ErrorActionPreference;$ErrorActionPreference='Continue'
   try{foreach($process in $busy){if(Get-Process -Id $process.ProcessId -ErrorAction SilentlyContinue){taskkill /PID $process.ProcessId /T /F 2>$null|Out-Null}}}finally{$ErrorActionPreference=$previousPreference}
   Start-Sleep -Milliseconds 700
   $remaining=@(Get-CimInstance Win32_Process|Where-Object {$_.ExecutablePath -and(Inside $_.ExecutablePath $root)})
   if($remaining.Count){throw 'Chưa đóng được SceneForge. Đóng app rồi chạy lại bản cập nhật.'}
  }
  $status.Text='Đang kiểm tra bản vá…';[Windows.Forms.Application]::DoEvents()
  foreach($item in $manifest.files){
   $source=[IO.Path]::GetFullPath((Join-Path (Join-Path $package 'files') $item.path));$target=[IO.Path]::GetFullPath((Join-Path $root $item.path))
   if(!(Inside $source (Join-Path $package 'files'))-or !(Inside $target $root)){throw 'Đường dẫn bản vá không hợp lệ.'}
   if((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256){throw ('Tệp cập nhật sai checksum: '+$item.path)}
  }
  $backup=Join-Path $root ('updates\'+$manifest.version+'-'+[guid]::NewGuid().ToString('N'))
  [void][IO.Directory]::CreateDirectory($backup)
  foreach($item in $manifest.files){
   $target=Join-Path $root $item.path;$old=Join-Path $backup $item.path;$existed=Test-Path -LiteralPath $target
   if($existed){[void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($old));[IO.File]::Copy($target,$old,$false)}
   $changes+=@{target=$target;backup=$old;existed=$existed}
  }
  $status.Text='Đang thay mã ứng dụng; giữ nguyên model và dữ liệu…';[Windows.Forms.Application]::DoEvents()
  foreach($item in $manifest.files){$target=Join-Path $root $item.path;[void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target));[IO.File]::Copy((Join-Path (Join-Path $package 'files') $item.path),$target,$true)}
  try {
  # Runs after the normal verified patch; only changes icons on shortcuts for this installation.
  $icon=Join-Path $root 'app\dist\web-demo\icons\SceneForge.ico'
  if(Test-Path -LiteralPath $icon) {
   $shell=New-Object -ComObject WScript.Shell
   $folders=@([Environment]::GetFolderPath('DesktopDirectory'),[Environment]::GetFolderPath('StartMenu'),(Join-Path $env:APPDATA 'Microsoft\Internet Explorer\Quick Launch\User Pinned'))
   foreach($folder in $folders) {
    if(!(Test-Path -LiteralPath $folder)){continue}
    foreach($link in @(Get-ChildItem -LiteralPath $folder -Filter '*SceneForge*.lnk' -File -Recurse -ErrorAction SilentlyContinue)) {
     try {
      $shortcut=$shell.CreateShortcut($link.FullName);$target=[IO.Path]::GetFullPath($shortcut.TargetPath)
      $targetFolder=[IO.Path]::GetDirectoryName($target).TrimEnd('\')
      $owned=[IO.Path]::GetFileName($target) -ieq 'SceneForge.exe' -and ($targetFolder -ieq $root -or $root.StartsWith($targetFolder+'\',[StringComparison]::OrdinalIgnoreCase))
      if($owned){$shortcut.IconLocation=$icon+',0';$shortcut.Save()}
     }catch{}
    }
   }
  }

  }catch{}
  @{version=$manifest.version;installed_at=[DateTime]::UtcNow.ToString('o');backup=$backup}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $root 'app-build.json') -Encoding UTF8
  $status.Text='Đã cập nhật gộp lên .115. Mở SceneForge dùng bình thường; không cần chạy lại .63–.96.'
  $go.Text='Mở SceneForge';$go.Tag=Join-Path $root 'SceneForge.exe';$go.Enabled=$true
  if($env:SCENEFORGE_UPDATE_RESULT){@{passed=$true;version=$manifest.version;release=$root;files=$manifest.files.Count}|ConvertTo-Json|Set-Content $env:SCENEFORGE_UPDATE_RESULT -Encoding UTF8}
 }catch{
  foreach($item in $changes){try{if($item.existed){[IO.File]::Copy($item.backup,$item.target,$true)}elseif(Test-Path -LiteralPath $item.target){Remove-Item -LiteralPath $item.target -Force}}catch{}}
  $script:failed=$_.Exception.Message;$status.Text='Chưa cập nhật được: '+$script:failed
  if($env:SCENEFORGE_UPDATE_RESULT){@{passed=$false;error=$script:failed}|ConvertTo-Json|Set-Content $env:SCENEFORGE_UPDATE_RESULT -Encoding UTF8}
  if($env:SCENEFORGE_UPDATE_TEST -ne '1'){[void][Windows.Forms.MessageBox]::Show($form,$status.Text,'SceneForge')}
 }finally{$script:working=$false;$pick.Enabled=$true;if(!$go.Tag){$go.Enabled=$true}}
}
$go.Add_Click({if($go.Tag){Start-Process -FilePath $go.Tag -WorkingDirectory ([IO.Path]::GetDirectoryName($go.Tag));$form.Close()}else{ApplyUpdate}})
$form.Add_FormClosing({param($s,$e)if($script:working){$e.Cancel=$true}})
if($env:SCENEFORGE_UPDATE_TEST -eq '1'){$path.Text=$env:SCENEFORGE_UPDATE_TARGET;ApplyUpdate;if($script:failed){exit 1};exit 0}else{[void]$form.ShowDialog()}

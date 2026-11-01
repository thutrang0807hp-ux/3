param([switch]$FunctionsOnly)
$ErrorActionPreference='Stop'
function Read-JsonFile([string]$path){
 if(Test-Path -LiteralPath $path){return Get-Content -LiteralPath $path -Raw -Encoding UTF8|ConvertFrom-Json}
 return $null
}
function Get-ReleaseInfo([string]$root,$expected){
 $build=Read-JsonFile (Join-Path $root 'app-build.json')
 $settings=Read-JsonFile (Join-Path $root 'install-settings.json')
 $files=@();$same=$true
 foreach($entry in $expected.PSObject.Properties){
  $path=Join-Path $root $entry.Name
  $actual=$null
  if(Test-Path -LiteralPath $path){$actual=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
  $match=$actual -eq $entry.Value
  if(!$match){$same=$false}
  $files+=@{file=$entry.Name;sha256=$actual;matches_original_v46_9=$match}
 }
 return @{release_directory=$root;installed_version=$build.version;installed_at=$build.installed_at;data_directory=$settings.data_directory;files=$files;all_files_match_original_v46_9=$same}
}
if($FunctionsOnly){return}
if([Environment]::OSVersion.Platform -ne 'Win32NT'){throw 'Run this diagnostic on Windows.'}
$base=$env:SF_CHECK_DIRECTORY
if(!$base){$base=$PSScriptRoot}
$expected=Read-JsonFile (Join-Path $base 'expected-v46.9.json')
if(!$expected){throw 'Missing expected-v46.9.json. Extract the complete ZIP first.'}
$roots=New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
$processes=@();$errors=@()
try{
 $apps=@(Get-CimInstance Win32_Process -Filter "Name='SceneForge.exe'")
 foreach($p in $apps){
  if($p.ExecutablePath){[void]$roots.Add([IO.Path]::GetDirectoryName($p.ExecutablePath))}
  $processes+=@{name=$p.Name;pid=$p.ProcessId;executable=$p.ExecutablePath;started_at=if($p.CreationDate){$p.CreationDate.ToUniversalTime().ToString('o')}else{$null}}
 }
 $python=@(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'")
 foreach($p in $python){
  # Parse only the known bootstrap path; never save arbitrary command lines.
  if($p.CommandLine -match '(?:"([^"]*windows_bootstrap\.py)"|(\S*windows_bootstrap\.py))'){
   $script=$Matches[1];if(!$script){$script=$Matches[2]}
   $appdir=[IO.Path]::GetDirectoryName($script)
   if($appdir){[void]$roots.Add([IO.Path]::GetDirectoryName($appdir))}
   $processes+=@{name=$p.Name;pid=$p.ProcessId;executable=$p.ExecutablePath;bootstrap_script=$script;started_at=if($p.CreationDate){$p.CreationDate.ToUniversalTime().ToString('o')}else{$null}}
  }
 }
}catch{$errors+='Cannot read process information: '+$_.Exception.Message}
# This is the release directory the user previously selected, not a disk scan.
$known='D:\4\releases\2026.10.28.2'
if(Test-Path -LiteralPath (Join-Path $known 'install-settings.json')){[void]$roots.Add($known)}
$releases=@()
foreach($root in $roots){
 try{
  $release=Get-ReleaseInfo $root $expected
  $release.running_processes=@($processes|Where-Object {
   $prefix=$root.TrimEnd('\')+'\'
   if($_.executable){if($_.executable.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){return $true}}
   if($_.bootstrap_script){if($_.bootstrap_script.StartsWith($prefix,[StringComparison]::OrdinalIgnoreCase)){return $true}}
   return $false
  })
  if($release.data_directory){
   $instance=Read-JsonFile (Join-Path $release.data_directory 'instance.json')
   if($instance){$release.instance=@{pid=$instance.pid;port=$instance.port}}
  }
  $releases+=$release
 }catch{$errors+='Cannot inspect '+$root+': '+$_.Exception.Message}
}
$report=@{tool='SceneForge installed upload check';tool_version=2;checked_at=[DateTime]::UtcNow.ToString('o');processes=$processes;releases=$releases;errors=$errors;notes=@('Read-only inspection: no app files, projects, credentials or caches were modified.','No cookies, passwords, tokens, environment dumps or arbitrary process command lines collected.','Disk hashes prove file contents, not Python modules already loaded in memory.','The same error message alone does not identify the running patch version.')}
$destination=Join-Path $base 'SceneForge-installed-check.json'
$report|ConvertTo-Json -Depth 10|Set-Content -LiteralPath $destination -Encoding UTF8
Write-Host ''
Write-Host 'DA TAO BAO CAO: SceneForge-installed-check.json'
Write-Host 'Gui file nay trong cuoc tro chuyen. Cong cu khong cai hay sua SceneForge.'
Start-Process explorer.exe -ArgumentList ('/select,"'+$destination+'"')

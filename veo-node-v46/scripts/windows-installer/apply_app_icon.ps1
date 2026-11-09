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

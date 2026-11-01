$ErrorActionPreference='Stop'
$tokens=$null;$errors=$null
$ast=[System.Management.Automation.Language.Parser]::ParseFile((Join-Path $PSScriptRoot 'apply_update.ps1'),[ref]$tokens,[ref]$errors)
if($errors.Count){throw ($errors|Out-String)}
$conversion=$ast.Find({param($node) $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and $node.Name -eq 'MinimumPatchVersion'},$true)
if(!$conversion){throw 'Missing minimum version conversion'}
Invoke-Expression $conversion.Extent.Text
$minimum=MinimumPatchVersion '2026.10.29.14'
foreach($text in @('2026.10.29.14','2026.11.01.46','2026.11.01.46.1','2026.11.01.46.2','2026.11.01.463')){
 if((MinimumPatchVersion $text) -lt $minimum){throw "Rejected supported installed version: $text"}
}
if((MinimumPatchVersion '2026.10.29.13') -ge $minimum){throw 'Accepted baseline older than v14'}
$rejected=$false
try{MinimumPatchVersion 'invalid'|Out-Null}catch{$rejected=$true}
if(!$rejected){throw 'Accepted malformed version'}
# All new releases must be directly accepted by System.Version.
$build=Get-Content -LiteralPath (Join-Path $PSScriptRoot 'build_patch.py') -Raw
if($build -notmatch "VERSION='([^']+)'"){throw 'Missing build version'}
$release=[version]$Matches[1]
if($release -le [version]'2026.11.01.46'){throw 'Release must be newer than v46'}
Write-Output 'PASS: updater parses; five supported versions including legacy five-part metadata accepted; pre-v14 and malformed metadata rejected; release version valid for System.Version.'

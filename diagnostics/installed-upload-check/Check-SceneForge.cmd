@echo off
set "SF_CHECK_DIRECTORY=%~dp0"
powershell.exe -NoLogo -NoProfile -Command "& ([ScriptBlock]::Create([IO.File]::ReadAllText((Join-Path $env:SF_CHECK_DIRECTORY 'Check-SceneForge.ps1'))))"
if errorlevel 1 echo Khong tao duoc bao cao. Gui anh loi trong cua so nay.
pause

$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Windows.Forms
try {
 [void][Windows.Forms.MessageBox]::Show('Đóng SceneForge và cửa sổ Flow do app mở trước khi chạy. Không cần đóng Chrome/Edge cá nhân. Công cụ chỉ kiểm tra phiên chạy nền, không tạo video hoặc dùng credit.','Thử phiên Flow chạy nền')
 $pick=New-Object Windows.Forms.OpenFileDialog
 $pick.Title='Chọn SceneForge.exe của bản đang cài'
 $pick.Filter='SceneForge.exe|SceneForge.exe'
 $pick.FileName='SceneForge.exe'
 if(Test-Path -LiteralPath 'D:\4\releases\2026.10.28.2'){$pick.InitialDirectory='D:\4\releases\2026.10.28.2'}
 if($pick.ShowDialog() -ne [Windows.Forms.DialogResult]::OK){exit 0}
 $root=Split-Path -Parent $pick.FileName
 $python=Join-Path $root 'runtime\python.exe'
 $app=Join-Path $root 'app'
 if(!(Test-Path -LiteralPath $python) -or !(Test-Path -LiteralPath (Join-Path $root 'install-settings.json'))){throw 'Chọn đúng thư mục bản cài có runtime và install-settings.json.'}
 $result=Join-Path $PSScriptRoot 'KET-QUA.json'
 & $python -E -s -X utf8 (Join-Path $PSScriptRoot 'probe.py') --app $app --out $result
 if($LASTEXITCODE -ne 0 -or !(Test-Path -LiteralPath $result)){throw 'Chưa chạy được công cụ. Chưa gửi tạo video.'}
 $data=Get-Content -LiteralPath $result -Raw -Encoding UTF8 | ConvertFrom-Json
 [void][Windows.Forms.MessageBox]::Show(($data.code+"`r`n`r`n"+$data.message+"`r`n`r`nKết quả không chứa cookie hoặc email. Gửi lại mã kết quả này để tiếp tục kiểm tra."),'Kết quả thử chạy nền')
 Start-Process -FilePath 'notepad.exe' -ArgumentList ('"'+$result+'"')
} catch {
 [void][Windows.Forms.MessageBox]::Show($_.Exception.Message,'Chưa kiểm tra được')
 exit 1
}

$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing
[System.Windows.Forms.Application]::EnableVisualStyles()
$version='2026.11.14.46129';$expectedHash='8178af48a4db6180eb0fb3ef042b04ea21617c7380ca2e106d8e967990eb0c35';$payloadSize=[long]'552974685';$expandedSize=[long]'1450000000'
$script:failure=$null;$script:stage='starting';$script:cancelled=$false;$script:working=$false;$script:child=$null;$archive=$null;$staging=$null;$work=$null
function LocalPath([string]$value) {
    if($value -notmatch '^[A-Za-z]:[\\/]'){throw 'Hãy chọn thư mục trên ổ đĩa cục bộ, ví dụ D:\SceneForge.'}
    $p=[IO.Path]::GetFullPath($value).TrimEnd('\')
    if($p.Length -le 3){throw 'Hãy chọn một thư mục, không chọn toàn bộ ổ đĩa.'}
    return $p
}
function Under([string]$child,[string]$parent){return $child.Equals($parent,[StringComparison]::OrdinalIgnoreCase) -or $child.StartsWith($parent.TrimEnd('\')+'\',[StringComparison]::OrdinalIgnoreCase)}
function Pump { [System.Windows.Forms.Application]::DoEvents();if($script:cancelled){throw 'Đã hủy cài đặt. Dữ liệu cũ được giữ nguyên.'} }
function Progress([string]$message,[int]$percent){$status.Text=$message;$bar.Value=[Math]::Min(100,[Math]::Max(0,$percent));Pump}
function Browse($box){$d=New-Object Windows.Forms.FolderBrowserDialog;$d.Description='Chọn thư mục';$d.SelectedPath=$box.Text;if($d.ShowDialog($form)-eq 'OK'){$box.Text=$d.SelectedPath};$d.Dispose()}
function Writable([string]$path){[void][IO.Directory]::CreateDirectory($path);$probe=Join-Path $path ('.sceneforge-write-'+[guid]::NewGuid().ToString('N'));try{[IO.File]::WriteAllText($probe,'probe')}finally{if([IO.File]::Exists($probe)){[IO.File]::Delete($probe)}}}
function RunPython($python,$argumentList,$cwd,$log){
    $si=New-Object Diagnostics.ProcessStartInfo;$si.FileName=$python;$si.Arguments=$argumentList;$si.WorkingDirectory=$cwd;$si.UseShellExecute=$false;$si.CreateNoWindow=$true;$si.RedirectStandardOutput=$true;$si.RedirectStandardError=$true;$si.StandardOutputEncoding=[Text.Encoding]::UTF8;$si.StandardErrorEncoding=[Text.Encoding]::UTF8
    $script:child=New-Object Diagnostics.Process;$script:child.StartInfo=$si;[void]$script:child.Start()
    $stdout=$script:child.StandardOutput.ReadToEndAsync();$stderr=$script:child.StandardError.ReadToEndAsync()
    while(!$script:child.WaitForExit(150)){Pump}
    $text=$stdout.Result+"`r`n"+$stderr.Result;[IO.File]::WriteAllText($log,$text,(New-Object Text.UTF8Encoding($false)))
    if($script:child.ExitCode -ne 0){throw "Chuẩn bị công cụ chưa hoàn tất. Nhật ký: $log`r`n$($text.Substring([Math]::Max(0,$text.Length-1500)))"}
    $script:child.Dispose();$script:child=$null
}
$form=New-Object Windows.Forms.Form;$form.Text='Cài đặt SceneForge';$form.Size=New-Object Drawing.Size(740,630);$form.StartPosition='CenterScreen';$form.Font=New-Object Drawing.Font('Segoe UI',10);$form.FormBorderStyle='FixedDialog';$form.MaximizeBox=$false
$title=New-Object Windows.Forms.Label;$title.Text='Chọn nơi cài và nơi lưu dữ liệu';$title.Font=New-Object Drawing.Font('Segoe UI',16,[Drawing.FontStyle]::Bold);$title.SetBounds(24,18,680,40);$form.Controls.Add($title)
$hint=New-Object Windows.Forms.Label;$hint.Text='Cần mạng để tải bộ chạy 553 MB. Mã mới nhất được cài sẵn, không cần bản vá.';$hint.SetBounds(26,65,680,28);$form.Controls.Add($hint)
$defaultRoot=Join-Path ([Environment]::GetFolderPath('LocalApplicationData')) 'SceneForge'
$oldData=if($env:SCENEFORGE_LOCAL_DATA){$env:SCENEFORGE_LOCAL_DATA}else{Join-Path ([Environment]::GetFolderPath('UserProfile')) '.sceneforge-local'}
function PathRow($caption,$top,$value){$l=New-Object Windows.Forms.Label;$l.Text=$caption;$l.SetBounds(26,$top,650,24);$form.Controls.Add($l);$b=New-Object Windows.Forms.TextBox;$b.Text=$value;$b.SetBounds(26,($top+27),565,28);$form.Controls.Add($b);$pick=New-Object Windows.Forms.Button;$pick.Text='Chọn…';$pick.SetBounds(600,($top+25),100,31);$pick.Tag=$b;$pick.Add_Click({Browse $this.Tag});$form.Controls.Add($pick);return $b}
$installBox=PathRow 'Thư mục phần mềm' 106 $defaultRoot
$existingSettings=$null
$installed=Get-ItemProperty 'HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\SceneForge-*' -ErrorAction SilentlyContinue|Sort-Object DisplayVersion -Descending|Select-Object -First 1
if($installed){$known=Join-Path (Join-Path (Join-Path $installed.InstallLocation 'releases') $installed.DisplayVersion) 'install-settings.json';if(Test-Path -LiteralPath $known){$existingSettings=Get-Content -LiteralPath $known -Raw|ConvertFrom-Json;$installBox.Text=$existingSettings.install_root}}
$dataDefault=if($existingSettings){$existingSettings.data_directory}elseif(Test-Path -LiteralPath $oldData){$oldData}else{Join-Path $defaultRoot 'Data'}
$dataBox=PathRow 'Thư mục dự án, tài khoản và model' 180 $dataDefault
$cacheBox=PathRow 'Thư mục cache và tệp tạm (có thể chọn ổ khác)' 254 (Join-Path $dataDefault 'Cache')
$script:autoData=if($existingSettings -or (Test-Path -LiteralPath $oldData)){$null}else{$dataBox.Text};$script:autoCache=$cacheBox.Text
if($existingSettings){$cacheBox.Text=$existingSettings.cache_directory;$script:autoCache=$null}
$installBox.Add_TextChanged({if($dataBox.Text -eq $script:autoData){$script:autoData=Join-Path $installBox.Text 'Data';$dataBox.Text=$script:autoData}})
$dataBox.Add_TextChanged({if($cacheBox.Text -eq $script:autoCache){$script:autoCache=Join-Path $dataBox.Text 'Cache';$cacheBox.Text=$script:autoCache}})
$note=New-Object Windows.Forms.Label;$note.SetBounds(26,328,674,48);$note.Text=if(Test-Path -LiteralPath $oldData){"Có dữ liệu cũ: $oldData. Chọn thư mục mới sẽ dùng thư viện riêng; không tự di chuyển hoặc xóa thư viện cũ."}else{'Dữ liệu được giữ khi gỡ phần mềm. Chọn thư mục còn đủ dung lượng.'};$form.Controls.Add($note)
$gemini=New-Object Windows.Forms.CheckBox;$gemini.Text='Chuẩn bị Gemini Chat (chỉ còn đăng nhập tài khoản)';$gemini.Checked=$true;$gemini.SetBounds(26,381,670,25);$form.Controls.Add($gemini)
$flow=New-Object Windows.Forms.CheckBox;$flow.Text='Chuẩn bị Flow để tạo ảnh / video';$flow.Checked=$true;$flow.SetBounds(26,410,670,25);$form.Controls.Add($flow)
$voice=New-Object Windows.Forms.CheckBox;$voice.Text='Giọng AI VieNeu — tùy chọn, cần mạng và tải thêm model';$voice.SetBounds(26,439,670,25);$form.Controls.Add($voice)
$bar=New-Object Windows.Forms.ProgressBar;$bar.SetBounds(26,479,674,18);$form.Controls.Add($bar)
$status=New-Object Windows.Forms.Label;$status.Text='Chưa giải nén. Chọn thư mục rồi bấm Cài đặt.';$status.SetBounds(26,503,674,35);$form.Controls.Add($status)
$start=New-Object Windows.Forms.Button;$start.Text='Cài đặt';$start.SetBounds(460,545,140,34);$form.Controls.Add($start)
$cancel=New-Object Windows.Forms.Button;$cancel.Text='Hủy';$cancel.SetBounds(610,545,90,34);$form.Controls.Add($cancel)
$cancel.Add_Click({if($script:working){$script:cancelled=$true;if($script:child -and !$script:child.HasExited){& taskkill /PID $script:child.Id /T /F | Out-Null}}else{$form.Close()}})
$form.Add_FormClosing({param($sender,$event)if($script:working){$script:cancelled=$true;$event.Cancel=$true}})

function DownloadBase([string]$file) {
    Progress 'Đang tải bộ chạy Windows 553 MB; cần kết nối mạng…' 2
    [Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12
    $client=New-Object Net.WebClient
    try {
        $task=$client.DownloadFileTaskAsync([uri]'https://github.com/thutrang0807hp-ux/3/releases/download/sceneforge-windows-full-20261028/SceneForge-Setup-Windows-x64-v2.exe',$file)
        while(!$task.IsCompleted){
            $mb=if(Test-Path -LiteralPath $file){[Math]::Round((Get-Item -LiteralPath $file).Length/1MB)}else{0}
            Progress ("Đang tải bộ chạy: $mb / 528 MiB…") 2
            Start-Sleep -Milliseconds 150
        }
        $task.GetAwaiter().GetResult()
    } finally {$client.CancelAsync();$client.Dispose()}
    if((Get-Item -LiteralPath $file).Length -ne 553209693 -or (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne '858fae3ee43bc08811e28339f4a84d0cd33ec645c206b1f62ff586d3f76eb6da'){throw 'Bộ chạy tải về bị thiếu hoặc sai checksum. Chưa cài mã ứng dụng.'}
}
function ApplyCurrentCode([string]$targetRoot) {
    $bundle=Get-Content -LiteralPath (Join-Path $env:SF_PATCH_ROOT 'fresh-manifest.json') -Encoding UTF8 -Raw|ConvertFrom-Json
    foreach($item in $bundle.files){
        $source=[IO.Path]::GetFullPath((Join-Path (Join-Path $env:SF_PATCH_ROOT 'files') $item.path))
        $target=[IO.Path]::GetFullPath((Join-Path $targetRoot $item.path))
        if(!(Under $source (Join-Path $env:SF_PATCH_ROOT 'files')) -or !(Under $target $targetRoot)){throw 'Đường dẫn mã ứng dụng không hợp lệ.'}
        if((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.sha256){throw ('Mã ứng dụng sai checksum: '+$item.path)}
    }
    foreach($item in $bundle.files){
        $target=Join-Path $targetRoot $item.path
        [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target))
        [IO.File]::Copy((Join-Path (Join-Path $env:SF_PATCH_ROOT 'files') $item.path),$target,$true)
    }
    @{version=$version;installed_at=[DateTime]::UtcNow.ToString('o');fresh_install=$true}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $targetRoot 'app-build.json') -Encoding UTF8
    [IO.File]::Copy((Join-Path $env:SF_PATCH_ROOT 'fresh-manifest.json'),(Join-Path $targetRoot 'fresh-code-manifest.json'),$true)
}

function Install {
    $script:failure=$null;$script:working=$true;$start.Enabled=$false
    try {
        $installRoot=LocalPath $installBox.Text;$dataRoot=LocalPath $dataBox.Text;$cacheRoot=LocalPath $cacheBox.Text
        $releases=Join-Path $installRoot 'releases'
        if((Under $dataRoot $releases)-or(Under $cacheRoot $releases)){throw 'Dữ liệu/cache phải nằm ngoài thư mục releases của phần mềm.'}
        $destination=Join-Path $releases $version
        if((Under $installRoot $dataRoot)-or(Under $installRoot $cacheRoot)){throw 'Thư mục phần mềm không được nằm trong dữ liệu/cache.'}
        if([Environment]::OSVersion.Version.Major -lt 10){throw 'Bản này hỗ trợ Windows 10/11 64-bit.'}
        $need=@{};foreach($item in @(@($installRoot,($expandedSize+$payloadSize+268435456)),@($dataRoot,536870912),@($cacheRoot,268435456))){$driveRoot=[IO.Path]::GetPathRoot($item[0]);if(!$need.ContainsKey($driveRoot)){$need[$driveRoot]=[long]0};$need[$driveRoot]+=[long]$item[1]}
        foreach($driveRoot in $need.Keys){$drive=New-Object IO.DriveInfo($driveRoot);if(!$drive.IsReady -or $drive.DriveType -eq 'Network'){throw 'Hãy dùng ổ đĩa cục bộ đang sẵn sàng.'};if($drive.AvailableFreeSpace -lt $need[$driveRoot]){throw "Ổ $driveRoot cần khoảng $([Math]::Ceiling($need[$driveRoot]/1MB)) MB trống để cài."}}
        $instance=Join-Path $dataRoot 'instance.json'
        if(Test-Path -LiteralPath $instance){$owner=Get-Content -LiteralPath $instance -Raw|ConvertFrom-Json;$active=Get-CimInstance Win32_Process -Filter ('ProcessId='+[int]$owner.pid) -ErrorAction SilentlyContinue;if($active -and $active.CommandLine -match 'windows_bootstrap|local_engine'){throw 'Hãy đóng SceneForge đang dùng thư viện này trước khi cài hoặc sửa công cụ.'}}
        $dataCreated=!(Test-Path -LiteralPath $dataRoot);$cacheCreated=!(Test-Path -LiteralPath $cacheRoot)
        foreach($path in @($installRoot,$dataRoot,$cacheRoot)){Writable $path}
        $tempRoot=Join-Path $cacheRoot 'Temp';Writable $tempRoot
        $work=Join-Path $installRoot ('.setup-'+[guid]::NewGuid().ToString('N'));[void][IO.Directory]::CreateDirectory($work)
        $archive=Join-Path $work 'payload.zip';$staging=Join-Path $work 'app'
        $marker=Join-Path $destination 'installation.json'
        if(Test-Path -LiteralPath $destination){$existingCode=Join-Path $destination 'fresh-code-manifest.json';if(!(Test-Path -LiteralPath $existingCode)){throw 'Thư mục bản .129 đã tồn tại từ một bộ cài khác. Chọn thư mục phần mềm mới; không ghi đè.'};$expectedCode=Get-Content -LiteralPath (Join-Path $env:SF_PATCH_ROOT 'fresh-manifest.json') -Raw|ConvertFrom-Json;$foundCode=Get-Content -LiteralPath $existingCode -Raw|ConvertFrom-Json;if($expectedCode.code_sha256 -ne $foundCode.code_sha256){throw 'Thư mục bản .129 có mã khác; chọn thư mục phần mềm mới.'}}
        if(Test-Path -LiteralPath $destination){
            if(!(Test-Path -LiteralPath $marker)-or((Get-Content -LiteralPath $marker -Raw|ConvertFrom-Json).payload_sha256 -ne $expectedHash)){throw 'Thư mục phiên bản đã tồn tại nhưng khác hoặc chưa hoàn chỉnh. Chọn thư mục phần mềm khác; không ghi đè.'}
            $existing=Get-Content (Join-Path $destination 'install-settings.json') -Raw|ConvertFrom-Json
            if($existing.data_directory -ne $dataRoot -or $existing.cache_directory -ne $cacheRoot){throw 'Phiên bản này đã gắn với nơi lưu dữ liệu khác. Chọn thư mục phần mềm mới; không tự đổi hoặc di chuyển thư viện cũ.'}
        }else{
            Progress 'Đang kiểm tra bộ cài…' 2
            $baseInstaller=Join-Path $work 'base-installer.exe';DownloadBase $baseInstaller
            $source=[IO.File]::OpenRead($baseInstaller);$output=[IO.File]::Create($archive)
            try{if($source.Length -le $payloadSize){throw 'File cài bị thiếu.'};[void]$source.Seek(-$payloadSize,[IO.SeekOrigin]::End);$buffer=New-Object byte[] 1048576;while(($n=$source.Read($buffer,0,$buffer.Length))-gt 0){$output.Write($buffer,0,$n);Pump}}finally{$output.Dispose();$source.Dispose()}
            if((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()-ne $expectedHash){throw 'File cài sai checksum. Hãy tải lại.'}
            Add-Type -AssemblyName System.IO.Compression.FileSystem
            $zip=[IO.Compression.ZipFile]::OpenRead($archive)
            try{$i=0;foreach($entry in $zip.Entries){
                $relative=$entry.FullName.Replace('/', '\');$target=[IO.Path]::GetFullPath((Join-Path $staging $relative));if(!(Under $target $staging)){throw 'Đường dẫn trong bộ cài không hợp lệ.'}
                if($entry.Name){[void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target));[IO.Compression.ZipFileExtensions]::ExtractToFile($entry,$target,$false)}else{[void][IO.Directory]::CreateDirectory($target)}
                $i++;if($i%30 -eq 0){Progress 'Đang giải nén vào thư mục đã chọn…' (5+[int](55*$i/$zip.Entries.Count))}
            }}finally{$zip.Dispose()}
            ApplyCurrentCode $staging
            foreach($required in @('SceneForge.exe','SceneForge-Uninstall.exe','SceneForge-Tools.exe','runtime\python.exe','tools\ffmpeg.exe','tools\ffprobe.exe','resources\whisper\model.bin')){if(!(Test-Path -LiteralPath (Join-Path $staging $required))){throw "Thiếu thành phần: $required"}}
            $settings=@{install_root=$installRoot;data_directory=$dataRoot;cache_directory=$cacheRoot;temp_directory=$tempRoot;version=$version;data_created=$dataCreated;cache_created=$cacheCreated}
            $settings|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $staging 'install-settings.json') -Encoding UTF8
            @{app_id='SceneForge';version=$version;install_root=$installRoot;payload_sha256=$expectedHash;installed_at=[DateTime]::UtcNow.ToString('o')}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $staging 'installation.json') -Encoding UTF8
            [void][IO.Directory]::CreateDirectory($releases);[IO.Directory]::Move($staging,$destination)
        }
        # The app is moved before creating SDK venvs, so their base Python path remains valid.
        Progress 'Đang chuẩn bị công cụ và kiểm tra model…' 64
        $components='core';if($gemini.Checked){$components+=',gemini'};if($flow.Checked){$components+=',flow'};if($voice.Checked){$components+=',voice'}
        $log=Join-Path $dataRoot 'installation-log.txt'
        RunPython (Join-Path $destination 'runtime\python.exe') ('-E -s -X utf8 "'+(Join-Path $destination 'app\provision.py')+'" --components '+$components) (Join-Path $destination 'app') $log
        Progress 'Đang kiểm tra WebView2 để mở cửa sổ ứng dụng…' 92
        $runtimeCheck=Start-Process -FilePath (Join-Path $destination 'SceneForge.exe') -ArgumentList '--check-runtime' -PassThru -Wait
        if($runtimeCheck.ExitCode -ne 0){
            $bootstrap=Join-Path $work 'MicrosoftEdgeWebview2Setup.exe'
            $client=New-Object Net.WebClient
            try{$task=$client.DownloadFileTaskAsync([uri]'https://go.microsoft.com/fwlink/p/?LinkId=2124703',$bootstrap);while(!$task.IsCompleted){Pump;Start-Sleep -Milliseconds 150};$task.GetAwaiter().GetResult()}finally{$client.CancelAsync();$client.Dispose()}
            $sig=Get-AuthenticodeSignature -LiteralPath $bootstrap
            if($sig.Status -ne 'Valid' -or $sig.SignerCertificate.Subject -notmatch 'O=Microsoft Corporation'){throw 'Bộ chuẩn bị WebView2 không có chữ ký Microsoft hợp lệ.'}
            [IO.File]::Copy($bootstrap,(Join-Path $destination 'MicrosoftEdgeWebview2Setup.exe'),$true)
            $runtimeInstall=Start-Process -FilePath $bootstrap -ArgumentList '/silent /install' -PassThru
            $runtimeTimer=[Diagnostics.Stopwatch]::StartNew()
            while(!$runtimeInstall.HasExited){Pump;if($runtimeTimer.Elapsed.TotalMinutes -gt 5){throw 'WebView2 đang cài lâu; kiểm tra mạng rồi mở lại bộ cài.'};Start-Sleep -Milliseconds 150}
            $runtimeCheck=Start-Process -FilePath (Join-Path $destination 'SceneForge.exe') -ArgumentList '--check-runtime' -PassThru -Wait
            if($runtimeCheck.ExitCode -ne 0){throw 'Chưa chuẩn bị được WebView2. Kiểm tra mạng rồi chạy lại bộ cài.'}
        }
        Progress 'Đang tạo shortcut và mục gỡ cài đặt…' 95
        $exe=Join-Path $destination 'SceneForge.exe';$uninstaller=Join-Path $destination 'SceneForge-Uninstall.exe';$tools=Join-Path $destination 'SceneForge-Tools.exe'
        $script:stage='Start Menu shortcuts'
        if(!('SceneForgeShortcut' -as [type])){Add-Type -TypeDefinition ([IO.File]::ReadAllText((Join-Path $destination 'app\ShellShortcut.cs')))}
        $menu=Join-Path ([Environment]::GetFolderPath('Programs')) 'SceneForge';[void][IO.Directory]::CreateDirectory($menu)
        foreach($item in @(@('SceneForge',$exe),@('Công cụ và kiểm tra',$tools),@('Gỡ SceneForge',$uninstaller))){[SceneForgeShortcut]::Write((Join-Path $menu ($item[0]+'.lnk')),[string]$item[1],$destination,[string]$item[0])}
        $script:stage='Desktop shortcut'
        $desktop=[Environment]::GetFolderPath('Desktop');if($desktop){[void][IO.Directory]::CreateDirectory($desktop);[SceneForgeShortcut]::Write((Join-Path $desktop 'SceneForge.lnk'),$exe,$destination,'SceneForge')}
        $script:stage='Windows Apps registration'
        $id=([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($installRoot.ToLowerInvariant())))).Replace('-','').Substring(0,12)
        $key='HKCU:\Software\Microsoft\Windows\CurrentVersion\Uninstall\SceneForge-'+$id;[void](New-Item -Path $key -Force)
        foreach($entry in @{DisplayName='SceneForge';DisplayVersion=$version;Publisher='SceneForge';InstallLocation=$installRoot;UninstallString=('"'+$uninstaller+'"');ModifyPath=('"'+$tools+'"');URLInfoAbout='https://thutrang0807hp-ux.github.io/3/download-code.html';NoModify=0;NoRepair=0}.GetEnumerator()){[void](New-ItemProperty -Path $key -Name $entry.Key -Value $entry.Value -PropertyType $(if($entry.Key -in @('NoModify','NoRepair')){'DWord'}else{'String'}) -Force)}
        @{registry_key=$key;menu_directory=$menu;desktop_link=(Join-Path $desktop 'SceneForge.lnk')}|ConvertTo-Json|Set-Content -LiteralPath (Join-Path $destination 'registration.json') -Encoding UTF8
        Progress 'Cài đặt và kiểm tra hoàn tất.' 100
        $script:working=$false;$start.Text='Mở SceneForge';$start.Enabled=$true;$cancel.Text='Đóng'
        if($env:SCENEFORGE_INSTALL_TEST -ne '1'){Start-Process -FilePath $exe -WorkingDirectory $destination}
        if($env:SCENEFORGE_INSTALL_TEST -eq '1'){$form.Close()}
        $start.Tag=$exe;$start.Add_Click({if($this.Tag){Start-Process -FilePath $this.Tag}})
    }catch{
        $script:failure=$_.Exception.Message
        $detail=@{stage=$script:stage;error=$_.Exception.ToString();script_line=$_.InvocationInfo.ScriptLineNumber;source_line=$_.InvocationInfo.Line;stack=$_.ScriptStackTrace}
        if($dataRoot -and(Test-Path -LiteralPath $dataRoot)){$detail|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $dataRoot 'installation-error.json') -Encoding UTF8}
        $script:working=$false;$status.Text=$_.Exception.Message;$start.Enabled=$true;$cancel.Text='Đóng';$script:cancelled=$false
        if($env:SCENEFORGE_INSTALL_TEST -eq '1'){$form.Close();return}
        [void][Windows.Forms.MessageBox]::Show($form,$_.Exception.Message,'Cài đặt chưa hoàn tất','OK','Error')
    }finally{if($archive -and(Test-Path -LiteralPath $archive)){Remove-Item -LiteralPath $archive -Force};if($work -and(Test-Path -LiteralPath $work)){Remove-Item -LiteralPath $work -Recurse -Force}}
}
$start.Add_Click({if(!$start.Tag){Install}})
if($env:SCENEFORGE_INSTALL_PLAN){
    $plan=Get-Content -LiteralPath $env:SCENEFORGE_INSTALL_PLAN -Raw|ConvertFrom-Json
    $installBox.Text=$plan.install_root;$dataBox.Text=$plan.data_directory;$cacheBox.Text=$plan.cache_directory
    if($null -ne $plan.gemini){$gemini.Checked=[bool]$plan.gemini};if($null -ne $plan.flow){$flow.Checked=[bool]$plan.flow};if($null -ne $plan.voice){$voice.Checked=[bool]$plan.voice}
    if($plan.cancel){$form.Show();[Windows.Forms.Application]::DoEvents();$form.Close();exit 0}
    try{Install;if($script:failure){exit 1};exit 0}catch{Write-Error $_;exit 1}
}else{[void]$form.ShowDialog();if($script:failure){exit 1}}

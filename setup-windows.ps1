$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$StateRoot = Join-Path $env:LOCALAPPDATA "ugc-video"
$Checkpoint = Join-Path $StateRoot "resume-windows-setup.json"
New-Item -ItemType Directory -Force -Path $StateRoot | Out-Null

$os = Get-CimInstance Win32_OperatingSystem
if ([int]$os.BuildNumber -lt 22000) {
    throw "Windows 11 is required. Contact the instructor for alternatives."
}
$memoryGB = [math]::Floor($os.TotalVisibleMemorySize / 1MB)
if ($memoryGB -lt 16) {
    Write-Warning "16 GB RAM is recommended; detected $memoryGB GB."
}
$driveName = (Split-Path -Qualifier $Root).TrimEnd(':')
$drive = Get-PSDrive -Name $driveName
if ($drive.Free -lt 15GB) {
    throw "At least 15 GB free storage is required for setup and video outputs."
}
$virtualization = Get-CimInstance Win32_Processor | Where-Object { $_.VirtualizationFirmwareEnabled }
if (-not $virtualization) {
    throw "Hardware virtualization must be enabled in firmware before installing WSL2."
}

$status = & wsl.exe --status 2>&1 | Out-String
if ($LASTEXITCODE -ne 0 -or $status -notmatch "Default Version: 2") {
    @{ stage = "wsl-install"; root = $Root } | ConvertTo-Json | Set-Content -Encoding UTF8 $Checkpoint
    & wsl.exe --install -d Ubuntu
    Write-Host "Restart Windows, then run START-HERE-WINDOWS.cmd again."
    exit 3010
}

$distros = & wsl.exe --list --quiet
if ($distros -notcontains "Ubuntu") {
    & wsl.exe --install -d Ubuntu
    Write-Host "Finish the Ubuntu account prompt, then run START-HERE-WINDOWS.cmd again."
    exit 3010
}

$wslRoot = (& wsl.exe -d Ubuntu -- wslpath -a $Root).Trim()
$wslHome = (& wsl.exe -d Ubuntu -- bash -lc 'printf %s "$HOME"').Trim()
$wslTarget = "$wslHome/ugc-video-student-kit"
& wsl.exe -d Ubuntu -- bash -lc "mkdir -p '$wslTarget' && cp -a '$wslRoot/.' '$wslTarget/' && cd '$wslTarget' && bash ./scripts/setup-linux.sh"
if ($LASTEXITCODE -ne 0) {
    throw "WSL2 setup failed with exit code $LASTEXITCODE"
}
Remove-Item -Force -ErrorAction SilentlyContinue $Checkpoint
Write-Host "Installation complete. Open Ubuntu and run: cd '$wslTarget' && uv run ugc-video setup"

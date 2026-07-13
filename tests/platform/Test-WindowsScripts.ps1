$ErrorActionPreference = "Stop"
$setup = Get-Content "$PSScriptRoot/../../setup-windows.ps1" -Raw
$linux = Get-Content "$PSScriptRoot/../../scripts/setup-linux.sh" -Raw

if ($setup -notmatch "WSL2" -or $setup -notmatch "wsl.exe --install") {
    throw "Windows setup must install and verify WSL2"
}
if ($setup -notmatch "resume-windows-setup.json") {
    throw "Windows setup must write a reboot checkpoint"
}
if ($linux -notmatch "uv sync --frozen" -or $linux -notmatch "ugc-video doctor --fast") {
    throw "Linux setup must sync the package and run doctor"
}
Write-Output "Windows bootstrap contracts passed"

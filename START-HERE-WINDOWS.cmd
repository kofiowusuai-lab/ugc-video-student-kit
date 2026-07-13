@echo off
setlocal
echo UGC Video Student Kit requires Windows 11 with WSL2 Ubuntu.
wsl --status
if errorlevel 1 (echo Enable WSL2, then rerun this launcher.& exit /b 1)
wsl bash -lc "cd /mnt/c/%~p0 && ./scripts/setup-linux.sh"

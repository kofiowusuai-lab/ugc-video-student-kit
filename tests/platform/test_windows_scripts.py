from pathlib import Path


def test_windows_setup_has_wsl_resume_checkpoint() -> None:
    setup = Path("setup-windows.ps1").read_text(encoding="utf-8")
    assert "WSL2" in setup
    assert "wsl.exe --install" in setup
    assert "resume-windows-setup.json" in setup


def test_wsl_setup_uses_locked_sync_and_doctor() -> None:
    linux = Path("scripts/setup-linux.sh").read_text(encoding="utf-8")
    assert "uv sync --frozen" in linux
    assert "ugc-video doctor --fast" in linux

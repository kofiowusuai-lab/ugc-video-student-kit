from pathlib import Path


def test_macos_setup_is_guarded_and_idempotent() -> None:
    script = Path("setup-macos.sh").read_text(encoding="utf-8")
    assert "set -Eeuo pipefail" in script
    assert '"$(uname -m)" != "arm64"' in script
    assert "command -v brew" in script
    assert "uv sync --frozen" in script
    assert "ugc-video doctor --fast" in script


def test_start_here_delegates_to_setup() -> None:
    launcher = Path("START-HERE-MAC.command").read_text(encoding="utf-8")
    assert 'exec "$ROOT/setup-macos.sh"' in launcher

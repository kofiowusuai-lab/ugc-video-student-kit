from pathlib import Path


def test_secret_and_output_patterns_are_ignored() -> None:
    ignored = Path(".gitignore").read_text(encoding="utf-8")
    for pattern in [".env", "secrets.env", "auth.json", "*.mp4", "models/"]:
        assert pattern in ignored


def test_secret_check_scans_git_history_and_worktree() -> None:
    script = Path("scripts/check-secrets.sh").read_text(encoding="utf-8")
    assert "gitleaks git" in script
    assert "gitleaks dir" in script

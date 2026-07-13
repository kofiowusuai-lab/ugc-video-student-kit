from pathlib import Path


def test_readme_has_supported_paths_and_start_commands() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    for text in ["Apple Silicon", "Windows 11 with WSL2", "16 GB RAM", "START-HERE-MAC.command", "START-HERE-WINDOWS.cmd", "contact the instructor", "ugc-video doctor --full", "ugc-video demo"]:
        assert text in readme


def test_subscriptions_are_dated_and_license_aware() -> None:
    subscriptions = Path("docs/SUBSCRIPTIONS.md").read_text(encoding="utf-8")
    for text in ["Last verified: July 13, 2026", "10,000 credits", "non-commercial use with attribution", "s2.1-pro-free", "end of July 2026", "SuperGrok", "xAI API billing", "ElevenLabs is not required"]:
        assert text in subscriptions

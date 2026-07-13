from pathlib import Path


def test_readme_has_supported_paths_and_start_commands() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    for text in ["Apple Silicon", "Windows 11 with WSL2", "16 GB RAM", "START-HERE-MAC.command", "START-HERE-WINDOWS.cmd", "contact the instructor", "ugc-video doctor --full", "ugc-video demo"]:
        assert text in readme


def test_subscriptions_are_dated_and_license_aware() -> None:
    subscriptions = Path("docs/SUBSCRIPTIONS.md").read_text(encoding="utf-8")
    for text in ["Last verified: July 13, 2026", "10,000 credits", "non-commercial use with attribution", "s2.1-pro-free", "end of July 2026", "SuperGrok", "xAI API billing", "ElevenLabs is not required"]:
        assert text in subscriptions


def test_readme_links_the_voice_provider_walkthrough() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "[Fish Audio and ElevenLabs setup](docs/VOICE-PROVIDER-SETUP.md)" in readme


def test_voice_provider_guide_is_complete_and_safe() -> None:
    guide = Path("docs/VOICE-PROVIDER-SETUP.md").read_text(encoding="utf-8")
    for text in [
        "Last verified: July 13, 2026",
        "https://fish.audio/app/api-keys/",
        "Bookmark",
        "Developers",
        "API Keys",
        "Text to Speech",
        "small credit limit",
        "uv run ugc-video setup",
        "Choose a voice number",
        "PASS Fish Audio",
        "SKIP ElevenLabs",
        "Library/Application Support/ugc-video/secrets.env",
        ".local/share/ugc-video/secrets.env",
        "Delete the exposed key",
        "create a replacement",
    ]:
        assert text in guide
    for unsafe_flag in ["--fish-key", "--elevenlabs-key", "--xai-key"]:
        assert unsafe_flag not in guide


def test_subscriptions_links_the_voice_provider_walkthrough() -> None:
    subscriptions = Path("docs/SUBSCRIPTIONS.md").read_text(encoding="utf-8")
    assert "[setup walkthrough](VOICE-PROVIDER-SETUP.md)" in subscriptions

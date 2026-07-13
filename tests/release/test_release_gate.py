from pathlib import Path


def test_release_checklist_requires_both_clean_machines_and_rollback() -> None:
    checklist = Path("docs/RELEASE-CHECKLIST.md").read_text(encoding="utf-8")
    for text in ["Apple Silicon clean-machine", "Windows 11/WSL2 clean-machine", "Fish Audio primary smoke test", "ElevenLabs fallback smoke test", "Git history secret scan", "Rollback tested", "User approved deployment"]:
        assert text in checklist


def test_acceptance_script_is_local_and_non_destructive() -> None:
    script = Path("scripts/acceptance.sh").read_text(encoding="utf-8")
    assert "pytest" in script
    assert "gitleaks" in script
    assert "ugc-video doctor --full" in script
    assert "rm -rf /" not in script


def test_release_checklist_covers_the_completed_voice_wizard() -> None:
    checklist = Path("docs/RELEASE-CHECKLIST.md").read_text(encoding="utf-8")
    for text in [
        "Voice setup wizard fake-provider tests",
        "hidden prompts and safe rerun",
        "lists bookmarked voice names",
        "lists available fallback voice names",
        "User approved deployment of v0.1.2",
    ]:
        assert text in checklist

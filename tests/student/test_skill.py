from pathlib import Path


def test_skill_preserves_required_gates_and_commands() -> None:
    skill = Path("codex-skills/ugc-video-producer/SKILL.md").read_text(encoding="utf-8")
    for text in ["ugc-video doctor --fast", "killer-script-system", "imagegen", "ugc-video run", "ugc-video resume", "Do not expose API keys", "Do not bypass"]:
        assert text in skill


def test_install_script_targets_user_codex_home() -> None:
    script = Path("scripts/install-codex-skill.sh").read_text(encoding="utf-8")
    assert '${CODEX_HOME:-$HOME/.codex}/skills/ugc-video-producer' in script
    assert "cp -R" in script

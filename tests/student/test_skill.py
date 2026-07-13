from pathlib import Path


def test_skill_preserves_required_gates_and_commands() -> None:
    skill = Path("codex-skills/ugc-video-producer/SKILL.md").read_text(encoding="utf-8")
    for text in ["ugc-video doctor --fast", "killer-script-system", "imagegen", "ugc-video run", "ugc-video resume", "Do not expose API keys", "Do not bypass"]:
        assert text in skill


def test_install_script_targets_user_codex_home() -> None:
    script = Path("scripts/install-codex-skill.sh").read_text(encoding="utf-8")
    assert '${CODEX_HOME:-$HOME/.codex}/skills' in script
    assert "ugc-video-producer" in script
    assert "killer-script-system" in script
    assert "cp -R" in script


def test_killer_script_skill_is_bundled_for_fresh_installs() -> None:
    skill_dir = Path("codex-skills/killer-script-system")
    skill = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    metadata = (skill_dir / "agents/openai.yaml").read_text(encoding="utf-8")

    assert "name: killer-script-system" in skill
    for text in [
        "natural spoken",
        "I had a feeling",
        "contractions",
        "read-aloud",
        "hook",
        "CTA",
    ]:
        assert text in skill
    assert "$killer-script-system" in metadata


def test_supported_installers_include_clis_and_remotion() -> None:
    for path in [Path("setup-macos.sh"), Path("scripts/setup-linux.sh")]:
        installer = path.read_text(encoding="utf-8")
        for text in [
            "@openai/codex",
            "https://x.ai/cli/install.sh",
            "remotion/package.json",
            "npm ci --prefix",
        ]:
            assert text in installer

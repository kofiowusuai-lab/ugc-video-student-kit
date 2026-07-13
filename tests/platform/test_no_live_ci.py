from pathlib import Path


def test_ci_never_runs_cloud_demo_or_reads_provider_keys() -> None:
    workflows = "\n".join(path.read_text(encoding="utf-8") for path in Path(".github/workflows").glob("*.yml"))
    assert "ugc-video demo\n" not in workflows
    assert "--offline-fixtures" in workflows
    for secret in ["FISH_AUDIO_API_KEY", "ELEVENLABS_API_KEY", "XAI_API_KEY"]:
        assert secret not in workflows

from pathlib import Path

from ugc_video.domain import RunManifest, StageStatus
from ugc_video.run_store import RunStore, hash_inputs


def test_completed_stage_is_reused_only_when_hash_and_outputs_match(tmp_path: Path) -> None:
    script = tmp_path / "script.txt"
    output = tmp_path / "voice.mp3"
    script.write_text("Exact line.", encoding="utf-8")
    output.write_bytes(b"audio")
    store = RunStore(tmp_path / "run.json")
    digest = hash_inputs([script], {"voice": "fish-a"})
    store.complete("voice", digest, [output], {"provider": "fish"})
    assert store.can_reuse("voice", digest) is True
    script.write_text("Changed line.", encoding="utf-8")
    assert store.can_reuse("voice", hash_inputs([script], {"voice": "fish-a"})) is False


def test_failed_stage_retains_error_and_attempt_count(tmp_path: Path) -> None:
    store = RunStore(tmp_path / "run.json")
    store.start("animation", "abc")
    store.fail("animation", "transient provider failure")
    manifest = RunManifest.model_validate_json((tmp_path / "run.json").read_text())
    assert manifest.stages["animation"].status == StageStatus.FAILED
    assert manifest.stages["animation"].attempts == 1
    assert "transient" in manifest.stages["animation"].detail

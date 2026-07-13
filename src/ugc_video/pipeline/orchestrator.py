from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ugc_video.pipeline.project import ProjectPaths
from ugc_video.progress import ProgressReporter
from ugc_video.run_store import RunStore, hash_inputs


@dataclass(frozen=True)
class PipelineServices:
    animate: Callable[[str, Path, Path], dict[str, Any]]
    voice: Callable[[str, Path], dict[str, Any]]
    verify: Callable[[Path, str], dict[str, Any]]
    finish: Callable[[Path, Path, Path], dict[str, Any]]


def _run_stage(
    store: RunStore,
    name: str,
    digest: str,
    outputs: list[Path],
    operation: Callable[[], dict[str, Any]],
    reporter: ProgressReporter | None = None,
) -> None:
    if store.can_reuse(name, digest):
        if reporter:
            reporter.complete(name, "reused verified checkpoint")
        return
    if reporter:
        reporter.start(name, "started")
    store.start(name, digest)
    try:
        metadata = operation()
        if not all(path.exists() and path.stat().st_size > 0 for path in outputs):
            raise RuntimeError(f"{name} produced no usable output")
        store.complete(name, digest, outputs, metadata)
        if reporter:
            reporter.complete(name, "passed")
    except Exception as exc:
        store.fail(name, str(exc))
        if reporter:
            reporter.update(name, f"failed: {exc}")
        raise


def run_pipeline(
    project: ProjectPaths,
    services: PipelineServices,
    reporter: ProgressReporter | None = None,
) -> Path:
    if not project.script.is_file() or not project.script.read_text(encoding="utf-8").strip():
        raise RuntimeError("script.txt is missing; run the bundled Codex skill")
    if not project.still.is_file() or project.still.stat().st_size == 0:
        raise RuntimeError("assets/still.png is missing; run the bundled Codex skill")
    script = project.script.read_text(encoding="utf-8").strip()
    store = RunStore(project.manifest)
    animation_hash = hash_inputs([project.script, project.still], {"stage": "animation"})
    voice_hash = hash_inputs([project.script], {"stage": "voice"})
    with ThreadPoolExecutor(max_workers=2) as executor:
        animation_future = executor.submit(
            _run_stage,
            store,
            "animation",
            animation_hash,
            [project.animation],
            lambda: services.animate(script, project.still, project.animation),
            reporter,
        )
        voice_future = executor.submit(
            _run_stage,
            store,
            "voice",
            voice_hash,
            [project.voice],
            lambda: services.voice(script, project.voice),
            reporter,
        )
        animation_future.result()
        voice_future.result()
    verify_animation_hash = hash_inputs(
        [project.animation, project.script], {"stage": "verify-animation"}
    )
    _run_stage(
        store,
        "verify-animation",
        verify_animation_hash,
        [project.animation],
        lambda: services.verify(project.animation, script),
        reporter,
    )
    final_hash = hash_inputs(
        [project.animation, project.voice, project.script], {"stage": "finish"}
    )
    _run_stage(
        store,
        "finish",
        final_hash,
        [project.final],
        lambda: services.finish(project.animation, project.voice, project.final),
        reporter,
    )
    verify_final_hash = hash_inputs([project.final, project.script], {"stage": "verify-final"})
    _run_stage(
        store,
        "verify-final",
        verify_final_hash,
        [project.final],
        lambda: services.verify(project.final, script),
        reporter,
    )
    return project.final

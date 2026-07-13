import os
from pathlib import Path
from typing import Optional

import typer

from ugc_video import __version__
from ugc_video.config import AppConfig, load_config, save_config
from ugc_video.demo import build_offline_services, prepare_demo
from ugc_video.doctor import run as doctor_run
from ugc_video.pipeline.orchestrator import run_pipeline
from ugc_video.pipeline.project import create_project, project_paths
from ugc_video.pipeline.services import build_services, provider_health
from ugc_video.paths import AppPaths
from ugc_video.progress import ProgressReporter
from ugc_video.run_store import RunStore
from ugc_video.secrets import read_secrets, write_secret

app = typer.Typer(help="Student-safe UGC video production", invoke_without_command=True)
whisper_app = typer.Typer(help="Install, inspect, and repair local Whisper fallbacks")
app.add_typer(whisper_app, name="whisper")
PROJECT_ROOT = Path(__file__).parents[2]


@app.callback()
def _root() -> None:
    """Student-safe UGC video production."""
    return None


@app.command()
def version() -> None:
    typer.echo(f"ugc-video {__version__}")


@app.command()
def setup(
    fish_key: str = typer.Option("", "--fish-key", prompt="Fish Audio API key", hide_input=True),
    elevenlabs_key: str = typer.Option(
        "", "--elevenlabs-key", prompt="ElevenLabs API key (fallback)", hide_input=True
    ),
    xai_key: str = typer.Option(
        "", "--xai-key", prompt="xAI API key (blank for guided Grok)", hide_input=True
    ),
) -> None:
    paths = AppPaths.from_environment(os.environ)
    for name, value in (
        ("FISH_AUDIO_API_KEY", fish_key),
        ("ELEVENLABS_API_KEY", elevenlabs_key),
        ("XAI_API_KEY", xai_key),
    ):
        if value:
            write_secret(paths.secrets, name, value)
    if not paths.config.exists():
        save_config(paths.config, AppConfig())
    typer.echo(f"Local configuration saved under: {paths.root}")


@app.command()
def doctor(
    full: bool = typer.Option(False, "--full/--fast"),
    json_output: bool = typer.Option(False, "--json"),
    provider: Optional[str] = None,
) -> None:
    if provider:
        paths = AppPaths.from_environment(os.environ)
        health = provider_health(read_secrets(paths.secrets), provider)
        typer.echo(f"{'PASS' if health.ok else 'FAIL'} {health.provider}: {health.detail}")
        if not health.ok:
            raise typer.Exit(2)
        return
    raise typer.Exit(doctor_run(full=full, as_json=json_output, provider=provider))


@app.command("new")
def new_project(
    name: str,
    product: str = typer.Option("", "--product", prompt=True),
    cta: str = typer.Option("", "--cta", prompt=True),
) -> None:
    paths = AppPaths.from_environment(os.environ)
    project = create_project(paths.projects / name, {"product": product, "cta": cta})
    typer.echo(f"Project created: {project.root}")


@app.command()
def status(project: Path) -> None:
    manifest = RunStore(project / "run.json").load()
    if not manifest.stages:
        typer.echo("No stages have run")
        return
    for name, record in manifest.stages.items():
        typer.echo(f"{record.status.value.upper()} {name}: {record.detail}")


@app.command("run")
def run_project(project: Path) -> None:
    paths = AppPaths.from_environment(os.environ)
    config = load_config(paths.config)
    secrets = read_secrets(paths.secrets)
    project_config = project_paths(project)
    reporter = ProgressReporter(secrets=list(secrets.values()))
    services = build_services(config, secrets, project_config, reporter=reporter)
    output = run_pipeline(project_config, services, reporter=reporter)
    typer.echo(f"Final video: {output}")


@app.command()
def resume(project: Path) -> None:
    run_project(project)


@app.command()
def demo(offline_fixtures: bool = typer.Option(False, "--offline-fixtures")) -> None:
    paths = AppPaths.from_environment(os.environ)
    project = prepare_demo(PROJECT_ROOT / "demo", paths.projects / "demo")
    if offline_fixtures:
        output = run_pipeline(project, build_offline_services())
        typer.echo(f"Offline demo complete: {output}")
        return
    run_project(project.root)


@whisper_app.command("install")
def whisper_install() -> None:
    from ugc_video.whisper.install import install_models

    paths = AppPaths.from_environment(os.environ)
    manifest = install_models(paths, PROJECT_ROOT / "config/models.json")
    typer.echo(f"Whisper model manifest: {manifest}")


@whisper_app.command("health")
def whisper_health(deep: bool = typer.Option(False, "--deep")) -> None:
    from ugc_video.whisper.health import inspect_whisper

    checks = inspect_whisper(deep=deep)
    for check in checks:
        typer.echo(f"{'PASS' if check.ok else 'FAIL'} {check.name}: {check.value or check.detail}")
    if not all(item.ok for item in checks):
        raise typer.Exit(2)


@whisper_app.command("repair")
def whisper_repair(backend: str) -> None:
    from ugc_video.whisper.install import repair_model

    paths = AppPaths.from_environment(os.environ)
    manifest = repair_model(paths, PROJECT_ROOT / "config/models.json", backend)
    typer.echo(f"Repaired {backend}; manifest: {manifest}")


if __name__ == "__main__":
    app()

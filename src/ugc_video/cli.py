import typer
import os
from pathlib import Path
from typing import Optional
from ugc_video import __version__
from ugc_video.doctor import run as doctor_run
from ugc_video.paths import AppPaths

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
def doctor(
    full: bool = typer.Option(False, "--full/--fast"),
    json_output: bool = typer.Option(False, "--json"),
    provider: Optional[str] = None,
) -> None:
    raise typer.Exit(doctor_run(full=full, as_json=json_output, provider=provider))

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

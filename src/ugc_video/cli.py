import typer
from typing import Optional
from ugc_video import __version__
from ugc_video.doctor import run as doctor_run

app = typer.Typer(help="Student-safe UGC video production", invoke_without_command=True)

@app.callback()
def _root() -> None:
    """Student-safe UGC video production."""
    return None

@app.command()
def version() -> None:
    typer.echo(f"ugc-video {__version__}")

@app.command()
def doctor(full: bool = False, json_output: bool = typer.Option(False, "--json"), provider: Optional[str] = None) -> None:
    raise typer.Exit(doctor_run(full=full, as_json=json_output, provider=provider))

if __name__ == "__main__":
    app()

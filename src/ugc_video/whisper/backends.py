import json
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, Optional, Union

from ugc_video.paths import AppPaths
from ugc_video.whisper.types import Transcript, Word

Runner = Callable[[list[str], int], str]


def default_runner(command: list[str], timeout: int) -> str:
    environment = os.environ.copy()
    environment.update({"HF_HUB_OFFLINE": "1", "TRANSFORMERS_OFFLINE": "1"})
    result = subprocess.run(
        command, check=True, capture_output=True, text=True, timeout=timeout, env=environment
    )
    return result.stdout


class JsonSubprocessBackend:
    def __init__(
        self, name: str, prefix: list[str], timeout: int, runner: Runner = default_runner
    ) -> None:
        self.name = name
        self.prefix = prefix
        self.timeout = timeout
        self.runner = runner

    def transcribe(self, media: Path, language: str) -> Transcript:
        payload = json.loads(self.runner([*self.prefix, str(media), language], self.timeout))
        words = [
            Word(str(item["text"]), float(item["start"]), float(item["end"]))
            for item in payload.get("words", [])
        ]
        return Transcript(text=str(payload.get("text", "")).strip(), words=words)


class WhisperCppBackend:
    name = "whispercpp-small-en"

    def __init__(self, model: Path, executable: str = "whisper-cli") -> None:
        self.model = model
        self.executable = executable

    def transcribe(self, media: Path, language: str) -> Transcript:
        with tempfile.TemporaryDirectory() as directory:
            prefix = Path(directory) / "result"
            subprocess.run(
                [
                    self.executable,
                    "-m",
                    str(self.model),
                    "-f",
                    str(media),
                    "-l",
                    language,
                    "-oj",
                    "-of",
                    str(prefix),
                ],
                check=True,
                capture_output=True,
                text=True,
                timeout=180,
            )
            payload = json.loads(prefix.with_suffix(".json").read_text(encoding="utf-8"))
        segments = payload.get("transcription", [])
        words = [
            Word(
                str(item.get("text", "")).strip(),
                float(item.get("offsets", {}).get("from", 0)) / 1000,
                float(item.get("offsets", {}).get("to", 0)) / 1000,
            )
            for item in segments
            if str(item.get("text", "")).strip()
        ]
        return Transcript(text=" ".join(item.text for item in words), words=words)


def load_backends(
    paths: Optional[AppPaths] = None,
) -> list[Union[JsonSubprocessBackend, WhisperCppBackend]]:
    paths = paths or AppPaths.from_environment(os.environ)
    cpp = WhisperCppBackend(paths.models / "whispercpp-small-en/ggml-small.en.bin")
    faster = JsonSubprocessBackend(
        "faster-small-en",
        [
            sys.executable,
            "-m",
            "ugc_video.whisper.worker_faster",
            str(paths.models / "faster-small-en"),
        ],
        240,
    )
    if platform.system() == "Darwin":
        third = JsonSubprocessBackend(
            "mlx-small",
            [sys.executable, "-m", "ugc_video.whisper.worker_mlx", str(paths.models / "mlx-small")],
            180,
        )
    else:
        third = JsonSubprocessBackend(
            "openai-small",
            [
                sys.executable,
                "-m",
                "ugc_video.whisper.worker_openai",
                str(paths.models / "openai-small"),
            ],
            300,
        )
    return [cpp, faster, third]

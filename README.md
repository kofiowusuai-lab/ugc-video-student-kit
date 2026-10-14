# UGC Video Student Kit

Build a vertical UGC spokesperson video with Codex, Grok, Fish Audio with ElevenLabs fallback, three local Whisper checks, and FFmpeg/Remotion finishing.

The supported installers add the Codex CLI, Grok CLI, the bundled `ugc-video-producer` and
`killer-script-system` Codex skills, and the pinned Remotion composition used to assemble the final
vertical video. Students sign in with their own accounts; no instructor API keys are included.

## Supported computers

- Apple Silicon M-series MacBook (M1 or later) on a current supported macOS release.
- Windows 11 with WSL2 and Ubuntu.
- 16 GB RAM recommended.
- 15 GB free storage recommended before model and video downloads.
- Stable internet for Codex, Grok, Fish Audio, ElevenLabs fallback, and initial model downloads.

Intel Macs, older Windows releases, native Windows without WSL2, and other Linux distributions are not supported by the first release. If your machine is outside this list, contact the instructor through the course contact channel for an alternative.

## Start here

### Mac

Double-click `START-HERE-MAC.command`, or run:

```bash
chmod +x START-HERE-MAC.command setup-macos.sh scripts/*.sh
./setup-macos.sh
```

### Windows

Double-click `START-HERE-WINDOWS.cmd`. Restart if WSL asks, then run the same file again.

## Configure your own accounts

Follow the [Fish Audio and ElevenLabs setup](docs/VOICE-PROVIDER-SETUP.md) walkthrough to create restricted keys, choose voices by name, and store everything safely.

```bash
codex login
grok
uv run ugc-video setup
uv run ugc-video doctor --full
```

Complete the Grok sign-in prompt, then exit back to the terminal. Your keys stay in a local ignored file. Never paste them into a prompt or commit them.

## Verify the complete workflow

```bash
uv run ugc-video demo --offline-fixtures
uv run ugc-video status ~/.local/share/ugc-video/projects/demo
```

Use `uv run ugc-video demo` for the live configured provider path.

## Start a project

```bash
uv run ugc-video new my-first-ad --product "My Product" --cta "Try it today"
codex
```

Inside Codex, ask: `Use the ugc-video-producer skill for my-first-ad.` If interrupted:

```bash
PROJECT_PATH="$HOME/.local/share/ugc-video/projects/my-first-ad"
uv run ugc-video status "$PROJECT_PATH"
uv run ugc-video resume "$PROJECT_PATH"
```

## More help

- [Accounts and subscriptions](docs/SUBSCRIPTIONS.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Alternative machines](docs/ALTERNATIVE-MACHINES.md)
- [Privacy, consent, and commercial use](docs/PRIVACY-CONSENT.md)
- Uninstall: `./scripts/uninstall.sh`
- [MIT License](LICENSE)

## How the workflow is implemented

This is the 0.1.2 student kit, with supported machine restrictions listed above. The Python package requires **Python 3.11 or 3.12**. Installers provision the platform tools; developer dependencies are recorded in `pyproject.toml` and `uv.lock`, and Remotion has a separate npm lockfile.

`new` creates a project and its `brief.json`. The bundled Codex skill supplies `script.txt` and `assets/still.png`; the CLI does not generate these inputs automatically. `run` then generates animation and voice in parallel, checks animation transcription, finishes the clip, and checks final transcription. The current CLI finishing service fits the voice and uses FFmpeg to produce 1080 × 1920 H.264/AAC video with loudness normalization. The bundled Remotion project is a separate composition asset, not invoked by that service. Fish Audio is preferred with configured ElevenLabs fallback. Grok can use guided or API mode; guided mode requires the user/agent interaction described by the skill.

```bash
uv run ugc-video run /absolute/path/to/project
uv run ugc-video whisper health
uv run ugc-video whisper health --deep
uv run ugc-video whisper install
uv run ugc-video whisper repair faster-small-en
```

Check available backend identifiers and repair guidance in [Troubleshooting](docs/TROUBLESHOOTING.md) before repairing a model. Installing models requires downloads; deep health checks perform local inference. The offline demo verifies fixture orchestration and does not establish live provider quality.

## Configuration and artifacts

`UGC_VIDEO_HOME` overrides the application's data root. Without it, `platformdirs` chooses the platform's user data directory: the `~/.local/share/ugc-video` examples above apply to Linux/WSL; macOS uses its platform-specific application data location. Use the path printed by `new` rather than assuming the Linux path on a Mac.

The data root contains `config.toml`, private `secrets.env`, `models/`, `state/`, `cache/`, and `projects/`. Setup stores only the supported secret names `FISH_AUDIO_API_KEY`, `ELEVENLABS_API_KEY`, and `XAI_API_KEY`. Nonsecret settings include `voice_provider`, `fish_model`, `fish_voice_id`, `elevenlabs_model`, `elevenlabs_voice_id`, `grok_mode`, `whisper_language`, and preferred/hard time-factor limits. Use the setup wizard and provider walkthrough to select real authorized voice IDs.

| Project path | Purpose |
|---|---|
| `brief.json` | Product and CTA inputs |
| `script.txt`, `assets/still.png` | Script and approved still supplied before running |
| `work/animation.mp4`, `work/voice.mp3` | Provider outputs |
| `work/voice-fitted.wav` | Fitted voice path used by finishing |
| `output/final.mp4` | Delivered video |
| `run.json` | Stage status, input hashes, output records, and failure details |

`status` reads the manifest; `resume` reruns the pipeline and reuses eligible checkpoints. Changed inputs can invalidate stages. Keep project artifacts together when moving a project.

## Developer checks and repository map

```bash
uv sync --extra dev
uv run pytest -q
uv run ruff check .
uv run mypy src
uv run ugc-video doctor --fast
```

These are the checks configured in the quality workflow; live provider calls do not belong in CI. Media checks still need the relevant local tools. `doctor --full`, live demos, and provider health checks may require accounts, network access, or installed models.

- `src/ugc_video/cli.py`: setup, doctor, project, resume, demo, and Whisper commands.
- `src/ugc_video/pipeline/`: input validation, providers, finishing orchestration, and checkpoints.
- `src/ugc_video/providers/`: Grok, Fish Audio, ElevenLabs, and retry adapters.
- `src/ugc_video/whisper/`: platform-specific model installation, routing, and health checks.
- `remotion/`: bundled pinned composition; the current Python CLI finishing service calls FFmpeg directly.
- `tests/`: platform, provider, pipeline, media, and student-workflow checks.

For missing script/still errors, complete the bundled skill step before `run`. For unsupported hardware, use the alternative-machine guide. For missing voices, provider quota errors, or transcription mismatches, consult the dedicated troubleshooting and voice-provider guides rather than repeatedly rerunning a billable generation.

# UGC Video Student Kit

Local-first UGC video workflow for Apple Silicon Mac and Windows 11/WSL2.

## Requirements

- Apple Silicon Mac (macOS 13+) or Windows 11 with WSL2 Ubuntu.
- 16 GB RAM recommended, 15 GB free storage, and a working FFmpeg install.
- Node.js 20+ for optional Remotion finishing.
- Codex access and Grok access (web or API, depending on the selected path).
- Fish Audio API access for the primary voice path. ElevenLabs is the fallback;
  its free tier is non-commercial and requires attribution. Commercial use or
  voice cloning requires the applicable paid ElevenLabs plan.

Run `START-HERE-MAC.command` or `START-HERE-WINDOWS.cmd` deliberately to begin
setup. Keys are entered locally and are never committed to Git. If your
machine is not compatible, contact the instructor for an alternative path.

## Local diagnostics

```bash
PYTHONPATH=src python3 -m ugc_video.cli doctor --full --json
```

The workflow is designed to keep Whisper fallback models local and to report
elapsed checkpoints rather than claiming progress that has not happened.

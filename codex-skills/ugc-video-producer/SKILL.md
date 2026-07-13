---
name: ugc-video-producer
description: Produce a realistic UGC spokesperson video from a brief with local QA and resumable cloud stages.
---

# UGC Video Producer

Read the repository `AGENTS.md` and project `brief.json`, then run `uv run ugc-video doctor --fast`.

1. Use `$killer-script-system` for natural spoken dialogue and save it to `script.txt`.
2. Use `imagegen` for a fictional adult, fully clothed, brand-safe 1080×1920 presenter still; inspect it and save it to `assets/still.png`.
3. Run `uv run ugc-video run "$PROJECT_PATH"`.
4. Complete a guided Grok handoff when requested, then run `uv run ugc-video resume "$PROJECT_PATH"`.
5. Review `run.json`, transcript checks, timing factor, provider metadata, and the final MP4.

Do not expose API keys. Do not bypass policy, consent, licensing, provenance, or timing gates. Fish Audio is primary; ElevenLabs is fallback only for configuration, quota, rate-limit, entitlement, or transient failures. Report the final path, providers, Whisper backend, timing factor, QA outcome, and commercial-license warning.

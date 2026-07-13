# Troubleshooting

| Message | Check | Next action |
|---|---|---|
| Unsupported platform | Read `ALTERNATIVE-MACHINES.md` | Contact the instructor |
| Missing executable | `uv run ugc-video doctor --fast` | Rerun the supported launcher |
| Whisper failure | `uv run ugc-video whisper health --deep` | Repair the named backend and repeat deep health |
| Fish authentication or quota | `uv run ugc-video doctor --provider fish` | Correct the local key or use configured fallback |
| ElevenLabs license warning | Read `SUBSCRIPTIONS.md` | Test non-commercially with attribution or obtain an eligible plan |
| Grok interruption | `uv run ugc-video status "$PROJECT_PATH"` | Run `uv run ugc-video resume "$PROJECT_PATH"` |
| Dialogue mismatch | Inspect `run.json` | Regenerate animation with the exact script |
| Unnatural time factor | Inspect `run.json` | Adjust Grok speaking pace; do not force audio |

Never paste API keys into support messages. Policy, consent, and licensing failures are not retryable through another provider.

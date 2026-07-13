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

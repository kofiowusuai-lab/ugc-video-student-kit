# Release checklist

## Automated evidence

- [ ] Full pytest, Ruff, mypy, Bash, PowerShell, and Gitleaks checks pass.
- [ ] Git history secret scan passes.
- [ ] Offline demo passes without cloud credentials.
- [ ] Voice setup wizard fake-provider tests pass without live cloud calls.

## Supported machines

- [ ] Apple Silicon clean-machine installation and safe rerun pass.
- [ ] Windows 11/WSL2 clean-machine installation, reboot resume, and safe rerun pass.
- [ ] Three Whisper backends pass deep health on both targets.
- [ ] Uninstall removes only kit-owned files on both targets.
- [ ] Voice setup wizard hidden prompts and safe rerun pass on Apple Silicon and Windows 11/WSL2.

## Credentialed smoke tests

- [ ] Fish Audio primary smoke test generates an approved short sentence.
- [ ] ElevenLabs fallback smoke test generates an approved short sentence.
- [ ] Grok guided/API modes record resumable artifacts.
- [ ] Final output passes dialogue checks.
- [ ] Fish Audio setup wizard lists bookmarked voice names and saves a selected voice.
- [ ] ElevenLabs setup wizard lists available fallback voice names and saves a selected voice.

## Documentation and rights

- [ ] Subscription claims rechecked against official pages.
- [x] Demo asset provenance and fictional identity recorded.
- [x] Commercial-license warnings visible.
- [x] Unsupported students directed to contact the instructor.

## Rollback and deployment

- [ ] Previous tag remains available.
- [ ] Rollback tested by installing the previous tag and restoring backed-up configuration.
- [ ] User approved deployment of v0.1.2.

Unchecked clean-machine and credentialed checks are release limitations, not implied successes.

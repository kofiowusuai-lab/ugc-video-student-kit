# UGC Video Student Kit Design

**Status:** Approved design

**Date:** 2026-07-13

**Target repository:** `kofiowusuai-lab/ugc-video-student-kit`

**Visibility:** Public

## 1. Purpose

Create a public, student-safe toolkit that installs and operates the end-to-end UGC video workflow used in the course. The kit must reproduce the workflow without distributing instructor API keys, private voice bookmarks, private assets, or machine-specific configuration.

The supported student paths are:

- Apple Silicon MacBooks running a supported current macOS release.
- Windows 11 machines using WSL2 with Ubuntu.

The README must state these requirements clearly. Students using Intel Macs, older Windows releases, Windows without WSL2, Linux distributions outside the supported WSL image, or incompatible hardware will be directed to contact the instructor for alternative options.

## 2. Goals

- Provide a deliberate one-command or double-click bootstrap experience.
- Install Codex CLI, Grok CLI, local media tooling, Remotion, and three local Whisper fallbacks.
- Guide students through account login and local secret configuration.
- Generate a short demo before students attempt a real project.
- Preserve checkpoints so slow cloud generation is never repeated unnecessarily.
- Report stage status and elapsed time so students know where time is being spent.
- Use Fish Audio as the primary voice provider and ElevenLabs as the fallback.
- Keep cloud-provider adapters replaceable as pricing, models, and access change.
- Verify transcription, voice timing, and final media before declaring success.
- Publish only after clean-machine installation and end-to-end acceptance tests pass.

## 3. Non-goals

- Running code automatically merely because a ZIP was downloaded or a repository was cloned.
- Supporting every Intel Mac, Windows release, native Windows Python stack, or Linux distribution in v1.
- Bundling API keys, account sessions, private Fish Audio bookmarks, paid voice IDs, or generated instructor assets.
- Redistributing vendor binaries or model files when the installer can fetch them from official sources.
- Guaranteeing permanent free access to any cloud provider.
- Circumventing provider moderation, watermarking, provenance, rate limits, or licensing terms.
- Promising frame-perfect lip re-animation from audio time fitting alone.

## 4. Chosen architecture

Use a guided, idempotent bootstrap rather than Docker or a monolithic opaque installer.

### 4.1 Platform entrypoints

- `START-HERE-MAC.command` launches `setup-macos.sh`.
- `START-HERE-WINDOWS.cmd` launches `setup-windows.ps1`.
- Windows setup verifies Windows 11, virtualization, WSL2, and Ubuntu, then invokes the shared Linux bootstrap inside WSL.
- Setup may require an explicit OS permission or reboot, but it must save a checkpoint and provide the exact resume action.
- Every setup phase logs what it changed and can be safely rerun.

### 4.2 Shared runtime

The student-facing `ugc-video` command orchestrates a Python application inside a project-owned virtual environment. FFmpeg, FFprobe, Rubber Band, Node.js, Remotion, Codex CLI, and Grok CLI are external tools discovered through a capability registry.

The runtime must not assume a fixed vendor model name indefinitely. It records installed CLI versions, queries available cloud capabilities when possible, and produces an actionable compatibility error when a required capability has changed.

### 4.3 Cloud and local boundary

Local:

- Whisper transcription and fallback selection.
- Audio inspection, silence handling, pitch-preserving time fitting, and muxing.
- FFmpeg and Remotion finishing.
- Checkpoints, manifests, prompts, logs, and final outputs.
- Dependency and model health checks.

Cloud:

- Codex orchestration and primary still generation when image generation is available.
- Grok image-to-video animation.
- Fish Audio text-to-speech.
- ElevenLabs fallback text-to-speech.

Cloud stages require internet access and the student's own account, entitlement, or API key.

## 5. Repository layout

```text
ugc-video-student-kit/
├── README.md
├── LICENSE
├── .env.example
├── .gitignore
├── START-HERE-MAC.command
├── START-HERE-WINDOWS.cmd
├── setup-macos.sh
├── setup-windows.ps1
├── scripts/
│   ├── setup-linux.sh
│   ├── download-models.sh
│   ├── doctor.sh
│   └── uninstall.sh
├── bin/
│   └── ugc-video
├── src/ugc_video/
│   ├── cli/
│   ├── pipeline/
│   ├── providers/
│   ├── audio/
│   ├── transcription/
│   ├── render/
│   └── security/
├── workflow/
│   ├── script/
│   ├── image/
│   ├── animation/
│   ├── voice/
│   ├── lipsync/
│   ├── qa/
│   └── render/
├── codex-skills/
│   └── ugc-video-producer/
├── config/
│   ├── defaults.example.json
│   └── voices.example.json
├── demo/
│   ├── brief.json
│   ├── script.txt
│   └── assets/
├── tests/
├── docs/
│   ├── SUBSCRIPTIONS.md
│   ├── TROUBLESHOOTING.md
│   ├── ALTERNATIVE-MACHINES.md
│   └── superpowers/
└── .github/workflows/
```

The final layout may consolidate folders during implementation when duplication is discovered, but the public commands and responsibilities must remain stable.

## 6. Student journey

1. Download or clone the public repository.
2. Open the README and run the platform's `START HERE` launcher.
3. Allow the installer to fetch supported local dependencies and Whisper models.
4. Sign in to Codex and Grok at their official login prompts.
5. Run `ugc-video setup` to add provider credentials to a local ignored environment file.
6. Run `ugc-video doctor --full` to verify the machine, accounts, APIs, model files, and output permissions.
7. Run `ugc-video demo` to create a short, low-cost test video.
8. Run `ugc-video new` to initialize a real project from a brief.
9. Use `ugc-video status`, `ugc-video run`, and `ugc-video resume` to operate the pipeline.

The README will provide both the launcher route and equivalent terminal commands so students can recover if double-click execution is blocked by Gatekeeper, execution policy, or antivirus software.

## 7. Pipeline design

### 7.1 Stages

1. **Brief and script** — Generate a natural UGC script using bundled killer-script and humanization guidance. Dialogue must use natural sentence openings, contractions, interruptions, and spoken phrasing instead of compressed AI-like fragments.
2. **Preflight** — Run fast local dependency, disk, provider, and Whisper checks.
3. **Still generation** — Create and inspect an identity-locked vertical still through Codex image generation. If that capability is unavailable, use the documented Grok still fallback.
4. **Parallel preparation** — Once the script is locked, voice generation and still preparation may run concurrently.
5. **Animation** — Animate the approved still with Grok using the exact dialogue and constrained natural movement.
6. **Animation transcript gate** — Transcribe the generated clip locally. Reject missing or substituted content words rather than silently continuing.
7. **Voice render** — Produce the approved script using Fish Audio, or ElevenLabs according to the provider policy below.
8. **Voice timing fit** — Detect the speech window, trim unnecessary silence, and use Rubber Band for pitch-preserving duration fitting.
9. **Audio replacement** — Replace the animation's generated voice while preserving intentional ambience when available and licensed.
10. **Post-swap transcript gate** — Verify the swapped result against the approved script.
11. **Visual QA** — Check identity consistency, framing, mouth behavior, hand artifacts, unexpected text, and continuity.
12. **Finish** — Apply captions, overlays, safe-zone layout, loudness normalization, and export through FFmpeg or Remotion.
13. **Report** — Write a human-readable QA summary and machine-readable manifest.

### 7.2 Timing policy

- First trim or pad non-speech silence before changing speech rate.
- Use pitch-preserving time fitting rather than naive resampling.
- Prefer a speech-duration factor between `0.94` and `1.06`.
- Permit up to `0.90` to `1.10` only when audio QA remains natural.
- Reject larger default changes and regenerate the Grok animation with adjusted speaking pace.
- Keep thresholds configurable for advanced students, but warn when they exceed the natural default range.

This is a duration-matching technique, not a claim of visual mouth re-animation. An optional external lip-sync adapter may be added later without changing the voice-provider interface.

### 7.3 Transcript policy

- Normalize case, punctuation, Unicode apostrophes, and benign whitespace.
- Require all content words to be present and in order.
- Allow configurable normalization for approved contractions.
- Report exact mismatches and timestamps.
- Use a secondary Whisper backend when the first result is uncertain or fails unexpectedly.

### 7.4 Progress and checkpoints

Each project contains a run manifest with:

- Stage status: pending, running, passed, failed, or skipped.
- Start, update, and completion timestamps.
- Input and output content hashes.
- Provider, model, voice identifier, and request identifier.
- Retry count and sanitized failure category.
- Local output paths and QA results.
- Provider-reported usage or cost metadata when available.

The console reports the current stage and elapsed time. It must not invent completion percentages or fake countdowns. Long cloud requests emit bounded status updates and persist request IDs so polling can resume.

## 8. Grok modes

### 8.1 Guided mode

Guided mode uses the installed official Grok CLI and the student's Grok account. When a Grok Imagine action cannot be invoked reliably through the CLI, the workflow produces a precise guided handoff and resumes from the downloaded result.

### 8.2 Automatic API mode

Automatic mode uses `XAI_API_KEY` with the official asynchronous Imagine video API. It submits an image-to-video request, stores the request ID, polls with bounded backoff, and downloads completed media immediately because result URLs may be temporary.

Grok consumer subscriptions and xAI API billing are documented separately. A SuperGrok subscription is not represented as an API credit balance.

Official references:

- [Grok Build CLI](https://x.ai/cli)
- [xAI video generation](https://docs.x.ai/developers/model-capabilities/video/generation)
- [xAI Imagine pricing](https://docs.x.ai/developers/pricing)

## 9. Voice-provider design

All TTS providers implement one internal contract:

- `health()`
- `list_or_validate_voice()`
- `synthesize(script, voice, settings)`
- `usage()` when the provider exposes it
- normalized audio metadata and error categories

### 9.1 Provider selection

`voice.provider` accepts `auto`, `fish`, or `elevenlabs`.

In `auto` mode:

1. Use Fish Audio as primary.
2. Retry a transient Fish failure at most twice with bounded backoff.
3. Fall back to ElevenLabs for provider outage, exhausted quota, unavailable model, or invalid primary entitlement.
4. Do not fall back to evade a safety, consent, policy, or licensing rejection.
5. If both providers are unavailable, stop at the preserved checkpoint with a clear remediation message.

The workflow never assumes that a Fish voice ID maps to an ElevenLabs voice. Students configure a separate approved voice for each provider.

### 9.2 Fish Audio

- Require the student's own `FISH_AUDIO_API_KEY`.
- Default to the supported free S2.1 Pro model while that program remains available and appropriate.
- Query or display available usage information when supported.
- Date-stamp free-tier documentation and link to live provider terms.
- Do not include instructor bookmarks or private voice identifiers.

As verified on 2026-07-13, Fish Audio states that `s2.1-pro-free` is available under fair use through the end of July 2026, without SLA or latency guarantees. This must not be presented as permanent.

Official references:

- [Fish Audio free S2.1 Pro announcement](https://fish.audio/blog/s2-1-pro-free-api/)
- [Fish Audio pricing and rate limits](https://docs.fish.audio/developer-guide/models-pricing/pricing-and-rate-limits)

### 9.3 ElevenLabs fallback

- Accept an optional `ELEVENLABS_API_KEY` during setup.
- Allow students to add or replace the key later without rerunning the installer.
- Validate `ELEVENLABS_VOICE_ID` before generation.
- Read subscription/usage metadata when available and warn before an expected quota failure.
- Install the official supported SDK, while keeping the adapter isolated from the pipeline.

As verified on 2026-07-13:

- ElevenLabs Free includes 10,000 credits monthly.
- The API is available on the free plan.
- Free-plan output is for non-commercial use with attribution.
- Commercial licensing and Instant Voice Cloning require an eligible paid plan.
- Voice and model choices can consume credits at different rates.

Official references:

- [ElevenLabs pricing](https://elevenlabs.io/pricing)
- [ElevenLabs API plan guidance](https://help.elevenlabs.io/hc/en-us/articles/28184926326033-How-much-does-it-cost-to-use-the-API)
- [ElevenLabs billing and licensing](https://elevenlabs.io/docs/overview/administration/billing)
- [ElevenLabs API authentication](https://elevenlabs.io/docs/api-reference/authentication)

## 10. Local Whisper redundancy

The installer provides three local transcription backends per supported platform.

Apple Silicon:

1. whisper.cpp Small English
2. Faster-Whisper Small English
3. MLX Whisper Small

Windows 11 through WSL2:

1. whisper.cpp Small English
2. Faster-Whisper Small English
3. OpenAI Whisper Small through the pinned Python environment

Model downloads use a manifest with source, expected size, revision, and checksum where the distributor publishes a stable checksum. `ugc-video doctor` performs a fast model-load test and a known-audio transcription test. A full health command exercises all three backends.

Backend isolation must avoid importing incompatible native audio/video runtimes into the same process when separate subprocesses are safer.

## 11. Installer behavior

### 11.1 macOS

- Verify Apple Silicon architecture and supported macOS version.
- Install or locate Homebrew using an explicit student-approved system step.
- Install pinned compatible Python, Node.js, FFmpeg, FFprobe, Rubber Band, Git, and supporting packages.
- Install Codex CLI using the official OpenAI package.
- Install Grok CLI using xAI's official installer.
- Create a project-owned Python virtual environment and install pinned packages.
- Install Remotion dependencies in the project workspace.
- Download and verify local Whisper models.
- Run the fast doctor.

### 11.2 Windows 11

- Verify Windows 11, administrative capability, virtualization support, and available disk space.
- Enable or install WSL2 and Ubuntu through supported Microsoft commands.
- Record a resume checkpoint before any required reboot.
- Invoke `scripts/setup-linux.sh` inside Ubuntu.
- Keep project files inside the WSL filesystem for predictable performance and permissions.
- Install Windows launch shortcuts that call the WSL-hosted `ugc-video` command.
- Run the fast doctor inside WSL.

### 11.3 Idempotency and uninstall

- Detect existing compatible tools before installing.
- Never replace an unrelated user-managed installation without a clear reason and log entry.
- Pin project libraries; record vendor CLI versions installed from current official channels.
- `uninstall.sh` removes only kit-owned virtual environments, models, caches, launchers, and configuration after confirmation.
- Shared system tools such as Homebrew, WSL2, Node.js, Python, and FFmpeg are retained unless an explicit advanced removal option is chosen.

## 12. Commands

```text
ugc-video setup
ugc-video doctor [--fast|--full|--provider NAME]
ugc-video demo
ugc-video new [PROJECT]
ugc-video run [PROJECT]
ugc-video resume [PROJECT]
ugc-video status [PROJECT]
ugc-video config get|set|validate
ugc-video clean [PROJECT]
ugc-video version
```

Commands default to safe, non-destructive behavior and print the next concrete action on failure.

## 13. Security and privacy

- `.env`, provider sessions, generated projects, raw media, and logs with user content are ignored by Git.
- Secrets are collected through hidden interactive input, not command-line arguments.
- Local secret files use restrictive permissions on macOS and WSL.
- Authorization headers, tokens, and known secret patterns are redacted from logs and exception output.
- `.env.example` contains placeholders only.
- Gitleaks and repository tests scan commits and fixtures.
- Provider API keys should use the narrowest permissions and optional quota limits supported by the vendor.
- Students are told which assets leave the machine during Codex, Grok, Fish Audio, and ElevenLabs stages.
- If a key is accidentally committed, instructions require immediate revocation rather than merely deleting the file.

## 14. Rights, consent, and provenance

- Students must use voices, likenesses, music, product media, and scripts they own or are authorized to use.
- The kit will not clone or imitate a real person's voice without documented authorization.
- Commercial UGC must use provider plans and assets that permit commercial use.
- The kit preserves required Grok watermarks and provenance signals.
- The kit will not retry through another provider to bypass a moderation decision.
- Generated manifests record the provider and model used for each media artifact.

## 15. README requirements

The README must lead with:

- What the kit makes.
- Supported and unsupported machines.
- Minimum and recommended hardware, including at least 16 GB RAM recommended and sufficient free storage for models and video outputs.
- The deliberate `START HERE` action.
- A dated account/subscription table using `Required`, `Free but limited`, `Recommended`, and `Optional` labels.
- A warning that prices and free programs change, with links to official live pages.
- The demo command and expected output.
- How to see status and resume a run.
- How to get help and contact the instructor for incompatible computers.
- Commercial licensing, consent, privacy, and watermark expectations.

Codex is currently included in eligible ChatGPT plans including Free, with plan-dependent limits. Paid Codex usage is recommended for sustained course work but must not be described as mandatory when the free plan is sufficient for a test.

Official reference:

- [Using Codex with a ChatGPT plan](https://help.openai.com/en/articles/11369540-using-codex-with-chatgpt)

## 16. Error handling

- Classify failures as configuration, authentication, quota, rate limit, transient provider, policy, invalid media, local dependency, model corruption, or QA rejection.
- Retry only transient and rate-limit failures.
- Retry the same action no more than twice without changing approach.
- Use provider-suggested retry delays when available; otherwise use bounded backoff.
- Persist request IDs and checkpoints before waiting on cloud work.
- Stop clearly on policy, consent, invalid credential, unsupported machine, or corrupted model failures.
- Never mask a hard failure with a placeholder output.

## 17. Testing strategy

### 17.1 Automated tests

- Unit tests for configuration, redaction, provider selection, retry bounds, manifests, transcript normalization, timing calculations, and command behavior.
- Contract tests for Fish Audio and ElevenLabs adapters using recorded sanitized fixtures, not live keys.
- CLI dry-run tests for macOS, PowerShell, and WSL bootstrap decisions.
- Model-manifest and checksum tests.
- Media fixture tests for FFmpeg, time fitting, muxing, loudness, and transcript comparison.
- Resume tests that interrupt each stage and verify no passed stage is repeated.
- Secret scanning for the repository and test artifacts.

### 17.2 Local credentialed smoke tests

- Provider health calls that avoid billable generation when possible.
- One very short Fish Audio sentence.
- One very short ElevenLabs fallback sentence.
- One low-cost Grok image-to-video request for release candidates.
- Complete demo render with transcript and visual QA.

### 17.3 Clean-machine acceptance

- Fresh supported Apple Silicon Mac installation.
- Fresh Windows 11 and WSL2 installation, including a reboot/resume scenario.
- Safe installer rerun after partial and complete installation.
- All three Whisper backends pass known-audio health tests.
- Demo completes from brief to exported vertical video.
- No credentials appear in files, logs, Git history, or fixtures.
- Offline/local stages remain usable when cloud providers are unavailable.
- Uninstall removes only kit-owned files.

## 18. CI and release

GitHub Actions must run non-billable validation only:

- Shell and PowerShell linting.
- Python formatting, typing, unit tests, and package build.
- Cross-platform CLI tests.
- Secret scanning and dependency review.
- Installer dry runs with mocked system discovery.
- Demo fixture media tests that do not call cloud providers.

Release requires:

- Acceptance criteria passing or an explicit documented waiver.
- A tagged semantic version and release notes.
- Checksums for downloadable release artifacts.
- Tested installation and rollback instructions.
- A public GitHub release only after the deployment gate is approved.

## 19. Rollback

- Keep the previous tagged release available.
- Provide an installer option to select a supported release version.
- Back up kit-owned configuration before migration.
- Restore the previous configuration schema when a migration fails.
- Never attempt an automatic OS-level rollback of Homebrew, WSL2, Node.js, Python, or vendor CLIs.

## 20. Implementation orchestration

After the implementation plan is approved, use the minimum useful three-lane structure:

1. **Installer/build lane** — platform bootstrap, dependency pinning, model downloads, and CLI packaging.
2. **Workflow integration lane** — pipeline state machine, provider adapters, audio timing, transcription, and rendering.
3. **Independent QA lane** — security review, test fixtures, clean-machine scenarios, documentation validation, and release readiness.

The primary integration lane owns shared interfaces, merges only after dependency checks, and presents one combined update at each merge gate.

## 21. Acceptance criteria

The project is complete when a supported student can:

1. Start from a clean Apple Silicon Mac or Windows 11 machine.
2. Run one deliberate `START HERE` action.
3. Finish installation or resume cleanly after a required reboot.
4. Configure personal Codex, Grok, Fish Audio, and optional ElevenLabs access without exposing secrets.
5. Pass `ugc-video doctor --full` with three healthy local Whisper backends.
6. Run the included demo and receive a vertical video, manifest, and QA report.
7. Create a new project, see stage timing, survive a provider interruption, and resume without repeating completed expensive work.
8. Use ElevenLabs when Fish Audio is unavailable, with licensing warnings appropriate to the student's plan.
9. Uninstall kit-owned components without damaging unrelated development tools.

The remote repository is not published and no release is deployed until these criteria and the deployment gate are satisfied.

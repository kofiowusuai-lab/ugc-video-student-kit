# Voice Provider Onboarding Design

**Date:** July 13, 2026
**Status:** Approved approach
**Target release:** v0.1.2

## Goal

Give a first-time student one safe command that stores personal Fish Audio and optional ElevenLabs
credentials, displays available voices by name, saves the selected provider-specific voice IDs, and
confirms whether each provider is ready.

The companion guide must be simple enough to follow without technical knowledge while still
treating students as adults who can create ordinary website accounts themselves.

## Non-goals

- Do not automate account registration, email verification, subscription purchase, or website login.
- Do not collect, bundle, print, or transmit instructor credentials.
- Do not ask students to edit `secrets.env` or `config.toml` manually.
- Do not use browser automation against Fish Audio or ElevenLabs.
- Do not clone, select, or authorize a voice on the student's behalf.
- Do not make live provider calls in automated tests or CI.

## Student experience

The README links prominently to a new `docs/VOICE-PROVIDER-SETUP.md` guide. The guide uses short
sentences, one action per numbered step, exact button or command names, and a **What you should see**
checkpoint after every important action.

### Before running the command

The guide tells the student to:

1. Visit Fish Audio, create or sign into an account, and open the official API Keys page.
2. Create a descriptively named key, such as `ugc-video-student-kit`.
3. Copy the key once and keep that browser tab open until setup succeeds.
4. Choose at least one approved Fish Audio voice and bookmark it.
5. Visit ElevenLabs, create or sign into an account, then open **Developers → API Keys**.
6. Create a key restricted to Text to Speech and set a small credit limit.
7. Copy the key once. ElevenLabs may not show the full key again.

The guide explains that Fish Audio is the primary provider and ElevenLabs is an optional fallback.
Students may skip ElevenLabs, but the guide describes the licensing limits that apply before
commercial publication.

### One-command setup

From the repository root on macOS, or from the repository directory inside WSL2 Ubuntu, the student
runs:

```bash
uv run ugc-video setup
```

The wizard performs this flow:

1. Prompt for the Fish Audio API key with hidden input.
2. Prompt for the optional ElevenLabs API key with hidden input.
3. Prompt for the optional xAI API key with hidden input; blank keeps guided Grok mode.
4. Save only non-empty values to the app's private secret file outside the Git repository.
5. Load the student's bookmarked Fish Audio voices and display names as a numbered list.
6. Ask the student to choose a Fish Audio voice number.
7. If ElevenLabs is configured, load available ElevenLabs voices and display names as a numbered
   list.
8. Ask the student to choose an ElevenLabs voice number.
9. Save the two selected IDs to the non-secret application configuration.
10. Check the configured providers and print a short readiness summary.

The wizard never prints an API key or asks the student to put one on a command line. The guide does
not document the `--fish-key`, `--elevenlabs-key`, or `--xai-key` flags because command-line values
can be retained in shell history.

### Expected terminal summary

The final output uses plain status words rather than relying on color:

```text
PASS Fish Audio: key accepted; voice selected
PASS ElevenLabs: key accepted; fallback voice selected
SKIP xAI API: guided Grok mode will be used
READY Voice setup is complete
```

When ElevenLabs is intentionally omitted:

```text
PASS Fish Audio: key accepted; voice selected
SKIP ElevenLabs: optional fallback was not configured
SKIP xAI API: guided Grok mode will be used
READY Voice setup is complete
```

## Components and changes

### `docs/VOICE-PROVIDER-SETUP.md`

Create the child-simple walkthrough with these sections:

- **What you are setting up**
- **Part 1: Make a Fish Audio key**
- **Part 2: Bookmark a Fish Audio voice**
- **Part 3: Make a safer ElevenLabs key**
- **Part 4: Run one setup command**
- **Part 5: Pick voices by number**
- **Part 6: Check that it worked**
- **If you see FAIL**
- **Keep your keys safe**

Use direct links to official provider documentation. Include a verification date because provider
navigation, plans, and limits can change.

### README and subscription guidance

- Link the new guide immediately below **Configure your own accounts**.
- Keep the README's setup path short; do not duplicate the full walkthrough.
- Cross-link `docs/SUBSCRIPTIONS.md` to the guide.
- Keep plan and commercial-use claims in `SUBSCRIPTIONS.md`, not in the onboarding steps.

### Setup command

Reuse the existing boundaries instead of adding a second setup system:

- `AppPaths` determines the user-scoped storage location.
- `write_secret` performs atomic secret writes and mode `0600` protection on macOS and WSL2.
- `build_voice_providers` creates Fish Audio and ElevenLabs adapters from saved credentials.
- `configure_voice_ids` lists voices and returns a configuration containing the selected IDs.
- `save_config` atomically persists non-secret provider choices.
- `provider_health` produces the final readiness status.

Wire these existing pieces into `ugc-video setup` after credential storage. Preserve existing saved
keys when a student presses Enter on a rerun. Preserve an existing voice choice unless the student
successfully selects a replacement.

## Security rules

- API-key prompts remain hidden.
- Keys are written only to the user-scoped `secrets.env`, never to the repository.
- The secret file remains mode `0600` on supported Unix environments.
- Keys, full voice IDs, and secret-file contents never appear in normal output, errors, logs, tests,
  screenshots, or documentation examples.
- The ElevenLabs walkthrough recommends a Text-to-Speech-only key and a small credit limit.
- If a key is pasted into chat, committed, shown in a screenshot, or otherwise exposed, the guide
  tells the student to delete it, create a replacement, and rerun setup.
- Rerunning setup is safe and does not erase a stored key when the matching prompt is left blank.

## Error handling

Failures use provider names and one next action:

| Condition | Student-facing result | Next action |
|---|---|---|
| Fish key rejected | `FAIL Fish Audio: key was not accepted` | Create a replacement key and rerun setup |
| No Fish bookmarks | `FAIL Fish Audio: no bookmarked voices found` | Bookmark a voice, then rerun setup |
| Fish network outage | `FAIL Fish Audio: service could not be reached` | Wait and rerun setup |
| ElevenLabs key rejected | `FAIL ElevenLabs: key was not accepted` | Replace or skip the optional fallback |
| No ElevenLabs voices | `FAIL ElevenLabs: no available voices found` | Add a voice or skip the fallback |
| Invalid menu choice | `Enter one of the displayed voice numbers` | Retry, up to the existing bounded limit |
| Existing valid setup rerun | Show current provider choices and allow replacement | Keep existing choices when no replacement succeeds |

Fish Audio readiness is required for the live primary voice path. ElevenLabs failure is clearly
marked as an optional-fallback problem and must not silently report full fallback readiness.

The command exits `0` only when Fish Audio is ready and every provider the student elected to
configure passes its check. It exits `2` after printing the relevant recovery action when required
setup remains incomplete.

## Testing strategy

Use a red-green-refactor cycle. Automated tests use fake provider adapters and temporary application
homes; they never use real keys, accounts, credits, or network calls.

Add or extend tests that prove:

1. The README links to the new guide.
2. The guide contains both official key-management paths, the single setup command, voice selection,
   safe-storage rules, leak rotation, and simple failure recovery.
3. Interactive setup saves keys only in a temporary user-scoped secret file.
4. Secret files have mode `0600` on supported Unix environments.
5. Setup never prints keys or full voice IDs.
6. Fish and ElevenLabs voice names appear as numbered choices.
7. Selected provider-specific voice IDs are persisted to `config.toml`.
8. Leaving ElevenLabs blank produces an explicit optional-fallback `SKIP` state.
9. Invalid credentials, zero Fish bookmarks, and network failures produce the specified message and
   exit status without destroying an existing valid configuration.
10. A second setup run is idempotent and preserves values for blank prompts.

The full repository gate remains: pytest, Ruff, mypy, Remotion typecheck, shell syntax checks,
Gitleaks history/worktree scans, offline demo, package build, and GitHub CI.

## Official references

- [Fish Audio API introduction and API-key page](https://docs.fish.audio/api-reference/introduction)
- [Fish Audio quick start and key-safety guidance](https://docs.fish.audio/developer-guide/getting-started/quickstart)
- [ElevenLabs API-key administration](https://elevenlabs.io/docs/overview/administration/workspaces/api-keys)
- [ElevenLabs API-key creation help](https://help.elevenlabs.io/hc/en-us/articles/14599447207697-How-do-I-authorize-myself-using-an-API-key)
- [ElevenLabs voice management](https://elevenlabs.io/docs/product/voices/overview)

## Acceptance criteria

- A student never needs to find or type a provider voice ID manually.
- A student pastes each key only into a hidden terminal prompt.
- Fish Audio and optional ElevenLabs readiness are reported separately and truthfully.
- The student gets one concrete recovery action for every expected setup failure.
- Existing valid credentials and voice choices survive safe reruns.
- No secrets enter source control, logs, documentation, screenshots, fixtures, or CI.
- The complete local and GitHub verification gates pass before v0.1.2 is published.

## Rollback

If the new interactive flow blocks setup, revert the onboarding commit and retain the existing
credential-only setup command while the defect is repaired. Because secret and configuration writes
remain atomic and backward-compatible, existing student credentials and project data do not require
migration or deletion.

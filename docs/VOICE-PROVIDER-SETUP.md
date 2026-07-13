# Set up Fish Audio and ElevenLabs voices

Last verified: July 13, 2026. Provider screens can change. Use the official links on this page if a button has moved.

## What you are setting up

Fish Audio makes the voice for your video. It is the primary voice service.

ElevenLabs is an optional backup. You may skip it.

You will make your own API keys on the provider websites. Then one command will store them safely, show your voice names, and let you choose by number. You will never need to find or type a voice ID.

Use only voices you own or have permission to use. Do not clone or imitate a real person without documented permission.

## Part 1: Make a Fish Audio key

1. Open [Fish Audio](https://fish.audio/).
2. Create an account or sign in.
3. Open the official [Fish Audio API Keys page](https://fish.audio/app/api-keys/).
4. Choose **Create API Key**.
5. Name the key **ugc-video-student-kit**.
6. Create the key.
7. Copy the key.
8. Keep this browser tab open until the terminal says **READY**.

**What you should see:** Fish Audio shows a new key that you can copy.

Do not paste the key into chat, a document, your code, or a screenshot.

## Part 2: Bookmark a Fish Audio voice

1. Open the Fish Audio voice library.
2. Choose a voice you are allowed to use.
3. Open that voice.
4. Choose **Bookmark**, or choose the bookmark or heart icon shown by Fish Audio.
5. Bookmark at least one voice.

**What you should see:** the voice is marked as saved or bookmarked in your Fish Audio account.

The setup command only shows your bookmarked Fish Audio voices. If you bookmark none, there is nothing to choose.

## Part 3: Make a safer ElevenLabs key

ElevenLabs is optional. Skip this part if you only want Fish Audio.

1. Open [ElevenLabs](https://elevenlabs.io/).
2. Create an account or sign in.
3. Open **Developers**.
4. Open **API Keys**.
5. Choose **Create API Key**.
6. Name the key **ugc-video-student-kit**.
7. Restrict the key to **Text to Speech**.
8. Set a small credit limit.
9. Create the key.
10. Copy the key now. ElevenLabs may show the full key only once.
11. Keep this browser tab open until the terminal says **READY**.

**What you should see:** ElevenLabs shows a new restricted key that you can copy.

See the official [ElevenLabs API-key guide](https://elevenlabs.io/docs/overview/administration/workspaces/api-keys) if the menu has moved.

## Part 4: Run one setup command

Open the repository folder in Terminal on a Mac, or open the repository folder inside WSL2 Ubuntu on Windows.

Run:

```bash
uv run ugc-video setup
```

The command asks for three keys:

1. Paste the Fish Audio key, then press **Enter**.
2. Paste the ElevenLabs key, then press **Enter**. Press **Enter** without typing anything if you are skipping ElevenLabs.
3. Paste an xAI API key, then press **Enter**. Press **Enter** without typing anything to use guided Grok.

Your typing is hidden. The screen may look blank while you paste a key. That is normal.

**What you should see:** the command starts loading voice names. It never prints any key back to you.

## Part 5: Pick voices by number

The command prints names like this:

```text
Fish Audio bookmarked voices:
1. Warm Narrator
2. Friendly Guide
Choose a voice number:
```

Type the number beside the voice you want. Then press **Enter**.

If ElevenLabs is configured, choose its fallback voice the same way.

On a later setup run, press **Enter** at a voice question to keep the saved choice. The command shows the saved voice name, never its private ID.

**What you should see:** your chosen names remain visible and no long voice IDs appear.

## Part 6: Check that it worked

A Fish-only setup ends like this:

```text
PASS Fish Audio: key accepted; voice selected
SKIP ElevenLabs: optional fallback was not configured
SKIP xAI API: guided Grok mode will be used
READY Voice setup is complete
```

A setup with the fallback ends like this:

```text
PASS Fish Audio: key accepted; voice selected
PASS ElevenLabs: key accepted; fallback voice selected
SKIP xAI API: guided Grok mode will be used
READY Voice setup is complete
```

Then run:

```bash
uv run ugc-video doctor --full
```

## If you see FAIL

Read the one action printed after **FAIL**.

- **Fish Audio key was not accepted:** create a replacement key and run setup again.
- **No bookmarked Fish Audio voices:** bookmark a voice and run setup again.
- **Fish Audio could not be reached:** wait a few minutes and run setup again.
- **ElevenLabs key was not accepted:** create a replacement key and run setup again.
- **No ElevenLabs voices:** add a voice and run setup again.
- **Wrong voice number:** enter one of the numbers shown. The command stops after three wrong tries.

A failed rerun does not erase a saved key or saved voice choice.

## Keep your keys safe

The command stores keys outside this Git repository:

- macOS: **~/Library/Application Support/ugc-video/secrets.env**
- WSL2 Ubuntu: **~/.local/share/ugc-video/secrets.env**

Voice choices go in **config.toml** in the same private application folder. Do not edit either file by hand.

Never put a key in:

- a Codex or Grok prompt;
- Git or GitHub;
- a screenshot or screen recording;
- course chat, email, or shared documents;
- source code or project files.

If a key is exposed:

1. Delete the exposed key on the provider website.
2. Choose **Create API Key** and create a replacement.
3. Run **uv run ugc-video setup** again.
4. Paste the replacement into the hidden prompt.

Fish Audio also documents [API-key safety in its quick start](https://docs.fish.audio/developer-guide/getting-started/quickstart). Read [Accounts, subscriptions, and usage](SUBSCRIPTIONS.md) before publishing commercial work.

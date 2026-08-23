# vivid-clean

![vivid-clean: local-first document cleaning](./gh-cover2.png)

[![CI](https://github.com/vnsavitri/vivid-clean/actions/workflows/ci.yml/badge.svg)](https://github.com/vnsavitri/vivid-clean/actions/workflows/ci.yml)
[![Latest release](https://img.shields.io/github/v/release/vnsavitri/vivid-clean?style=flat-square)](https://github.com/vnsavitri/vivid-clean/releases/latest)
[![Licence: MIT](https://img.shields.io/badge/licence-MIT-00B67A?style=flat-square)](./LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](./pyproject.toml)
[![Local metadata cleaning](https://img.shields.io/badge/metadata%20cleaning-local-5B6CFF?style=flat-square)](#privacy-in-plain-english)

`vivid-clean` removes deterministic provenance marks it can identify, helps you revise AI-assisted writing without flattening your voice, then checks the result and tells you what actually happened. It works by mark type, so it isn't tied to Claude, Codex, Gemini or any other vendor.

I built it for people who use AI as an accessibility aid, a writing aid, or simply part of how they get work done. A marker can't tell the difference between outsourcing your thinking and getting help with spelling, structure, fatigue, or a disability. That distinction matters.

## What you get

You get a command-line tool and an assistant skill. Together, they handle the fiddly bits:

- A pinned, local metadata-cleaning engine.
- A restricted working copy for the humanising pass.
- Format-preserving DOCX and PPTX text editing.
- Post-edit DOCX scrubbing.
- A verification gate that fails when checks can't finish.
- A channel-based report that keeps the cleaning engine's evidence.

The report says what was checked, what came out, what remains, and which checks weren't available. It won't call a file universally “clean”. No honest tool knows what every outside detector will decide.

## Install

vivid-clean supports macOS and Linux. You'll need Git and Python 3.11 or newer. It doesn't need Pandoc, MarkItDown or Docker.

```bash
git clone https://github.com/vnsavitri/vivid-clean.git
cd vivid-clean
chmod +x install.sh
./install.sh
```

The installer creates `.venv` inside the repo, checks out audited dependency commits, and installs the skill for compatible agents at:

| Assistant | Skill location |
| --- | --- |
| Agent Skills-compatible tools | `~/.agents/skills/vivid-clean/` |
| Cursor | `~/.cursor/skills/vivid-clean/` |
| Claude Code | `~/.claude/skills/vivid-clean/` |
| Codex | `~/.codex/skills/vivid-clean/` |

If Codex uses a custom `CODEX_HOME`, the installer uses that location. Existing skill copies are moved out of the assistant's skill folder and backed up under `$XDG_STATE_HOME/vivid-clean/skill-backups/`, or `~/.local/state/vivid-clean/skill-backups/` when `XDG_STATE_HOME` isn't set. That means an old copy can't appear as a duplicate skill. Run `./install.sh --skills-only` when the CLI is already set up and you only want to refresh the assistant instructions.

If you've already got Node 22 and pnpm, the installer builds anthropies as a fallback. If you haven't, no drama. The core installation still works.

Add `~/.local/bin` to your `PATH` if it isn't there already, then check the setup:

```bash
vivid-clean doctor
```

## Use it with an assistant

Give your assistant the file path and say what you want:

> Use the vivid-clean skill on `/full/path/to/Draft.docx`. Keep my meaning and formatting as close as possible, and use a neutral `_reviewed` suffix.

The skill runs two commands around the writing pass:

```bash
vivid-clean prepare "/full/path/to/Draft.docx"
# The assistant revises the protected text blocks in draft.md.
vivid-clean finish "/private/session/path" --suffix "_reviewed"
```

`prepare` starts the pinned local cleaner with a one-use token, sends the file over loopback, then stops it. You don't need to run a server yourself.

For Word and PowerPoint, `draft.md` is only an editing sidecar. `finish` puts the revised text back into the cleaned OOXML package. It doesn't convert the document to Markdown and rebuild it. Paragraphs, runs, styles, tables, hyperlinks, slide geometry and speaker-note structures stay in place. Numbers, URLs and email addresses are protected, and changed block markers make the run fail.

The default suffix is `_vivid` for backwards compatibility. That filename can reveal which tool you used, so choose a neutral suffix when that matters.

You can also compare any two files yourself:

```bash
vivid-clean verify Draft.docx Draft_reviewed.docx
```

Exit status `0` means the applicable checks finished without medium or high residual findings. Status `1` means findings remain. Status `2` means verification couldn't finish.

The overall report says `checks_passed`, `findings`, or `incomplete`. It also separates deterministic text, file provenance, statistical, proprietary, protected-value and package-structure results. `checks_passed` only covers the checks named in that report.

If you abandon a session, clear expired plaintext working copies with:

```bash
vivid-clean cleanup
# Preview first, or clear every valid session now:
vivid-clean cleanup --dry-run
vivid-clean cleanup --older-than 0
```

## What works today

| Input | Current behaviour | Main limitation |
| --- | --- | --- |
| `.docx` | Local cleaning, package-aware text editing, property scrub, structural check and verification | A close human check is still needed for fields, tracked changes and heavily styled text |
| `.pptx` | Local cleaning, package-aware slide and speaker-note editing, structural check and verification | Rewording can still change line wrapping inside an unchanged text box |
| `.pdf` | Local deterministic cleaning and verification; output stays PDF | Humanising needs the editable source because vivid-clean won't fake a safe PDF reconstruction |
| `.txt`, `.md` | Local deterministic cleaning, editable text pass, verification | Statistical detectors remain outside the default checks |
| `.png`, `.jpg`, `.jpeg`, `.webp` | Local deterministic cleaning and verification | Pixel-level watermarks need optional upstream backends |

Start with an editable source when you have one. Keep the original and check the result. Tables, fields, tracked changes, legal wording and dense slide layouts deserve an extra look.

## Privacy in plain English

Here's the honest version. Metadata cleaning, sidecar extraction, package editing and verification run on your computer. Humanising happens wherever your chosen assistant runs. If it's hosted, your text may go to that provider under its privacy and retention terms.

Advanced users can point the CLI at a persistent loopback service with `WATERMARKS_SERVICE_URL`. Remote addresses are rejected so a configuration mistake can't upload the file. If the service uses `WATERMARKS_SERVER_API_KEY`, export the same value for the CLI. Don't put the token in a command argument, document, or report. A separately started service's commit can't be independently verified, so its self-reported version is recorded instead of the audited local SHA.

Want the whole workflow to stay local? Use a local model such as Ollama to edit the prepared `draft.md`, then run `vivid-clean finish`. That keeps the text on your computer. It still can't guarantee that every watermark is gone or predict what a detector will say.

## Limits and responsible use

- vivid-clean removes deterministic marks its available checks can find. It can't promise a result against keyed statistical watermarks or private third-party detectors.
- Rewriting can change nuance. You're responsible for checking meaning, attribution, legal intent, and formatting.
- Many schools and workplaces have rules about AI assistance or detector avoidance. Those rules still apply.
- Removing C2PA, EXIF, or copyright-related provenance from somebody else's work may be unlawful and can harm the creator. Only clean files you're entitled to edit.
- A report records test results, not proof of human authorship.

The detailed assumptions and failure cases are in the [threat model](./docs/threat-model.md). Dependency pins and licences are recorded in [DEPENDENCIES.md](./DEPENDENCIES.md).

## Releases and updates

Meaningful updates get a dated [changelog](./CHANGELOG.md), a matching Git tag, and a [GitHub Release](https://github.com/vnsavitri/vivid-clean/releases). Small copy fixes may sit under `Unreleased` until the next version. If a change affects how your file is handled, installed, or checked, it belongs in the release notes.

The latest release is [v0.2.0](https://github.com/vnsavitri/vivid-clean/releases/tag/v0.2.0). It adds format-preserving Word and PowerPoint editing, clearer check reports, safer session cleanup, and skill updates that don't leave duplicate copies behind.

## Why this exists

I built vivid-clean because AI can make writing possible, or simply less exhausting, for people with dyslexia, ADHD, autism, learning disabilities, injury, fatigue, or a packed day. Treating every assisted sentence as deception erases why people use these tools in the first place.

I wrote the longer argument here: [AI watermarking is the new scarlet letter](https://www.linkedin.com/pulse/ai-watermarking-new-scarlet-letter-vivid-n-savitri-npzpc).

## Project notes

- Changes are recorded in [CHANGELOG.md](./CHANGELOG.md).
- Security reports belong in the process described in [SECURITY.md](./SECURITY.md).
- Contributions are welcome. Start with [CONTRIBUTING.md](./CONTRIBUTING.md).
- Work that's still ahead is tracked in [ROADMAP.md](./ROADMAP.md).

Built by [Vivid Savitri](https://github.com/vnsavitri) under the [MIT Licence](./LICENSE).

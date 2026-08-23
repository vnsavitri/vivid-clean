# vivid-clean

![vivid-clean: local-first document cleaning](./gh-cover2.png)

[![CI](https://github.com/vnsavitri/vivid-clean/actions/workflows/ci.yml/badge.svg)](https://github.com/vnsavitri/vivid-clean/actions/workflows/ci.yml)
[![Licence: MIT](https://img.shields.io/badge/licence-MIT-00B67A?style=flat-square)](./LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-3776AB?style=flat-square&logo=python&logoColor=white)](./pyproject.toml)
[![Local metadata cleaning](https://img.shields.io/badge/metadata%20cleaning-local-5B6CFF?style=flat-square)](#privacy-in-plain-english)

`vivid-clean` removes deterministic provenance marks it can identify, helps you revise AI-assisted writing in your own voice, then checks the exported file and tells you what actually happened.

I built it for people who use AI as an accessibility aid, a writing aid, or simply part of how they get work done. A marker can't tell the difference between outsourcing your thinking and getting help with spelling, structure, fatigue, or a disability. That distinction matters.

## What you get

You get a command-line tool and an assistant skill. Together, they handle the fiddly bits:

- A pinned, local metadata-cleaning engine.
- A private working copy for the humanising pass.
- Post-export DOCX scrubbing.
- A verification gate that fails when checks can't finish.
- A readable report beside every finished file.

The report says what was checked, what came out, what remains, and which checks weren't available. It won't call a file universally “clean”. No honest tool knows what every outside detector will decide.

## Install

vivid-clean supports macOS and Linux. You'll need Git and Python 3.11 or newer. You'll also need Pandoc to rebuild Word, PowerPoint, or PDF-derived documents.

```bash
git clone https://github.com/vnsavitri/vivid-clean.git
cd vivid-clean
chmod +x install.sh
./install.sh
```

The installer creates `.venv` inside the repo, installs the Word, PowerPoint, and PDF document helpers there, and checks out audited dependency commits. It also installs the skill for compatible agents at:

| Assistant | Skill location |
| --- | --- |
| Agent Skills-compatible tools | `~/.agents/skills/vivid-clean/` |
| Cursor | `~/.cursor/skills/vivid-clean/` |
| Claude Code | `~/.claude/skills/vivid-clean/` |
| Codex | `~/.codex/skills/vivid-clean/` |

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
# The assistant revises the session's draft.md.
vivid-clean finish "/private/session/path" --suffix "_reviewed"
```

`prepare` starts the pinned local cleaner with a one-use token, sends the file over loopback, then stops it. You don't need to run a server yourself.

The default suffix is `_vivid` for backwards compatibility. That filename can reveal which tool you used, so choose a neutral suffix when that matters.

You can also compare any two files yourself:

```bash
vivid-clean verify Draft.docx Draft_reviewed.docx
```

Exit status `0` means the applicable checks finished without medium or high residual findings. Status `1` means findings remain. Status `2` means verification couldn't finish.

## What works today

| Input | Current behaviour | Main limitation |
| --- | --- | --- |
| `.docx` | Local metadata cleaning, text extraction, sandboxed rebuild, DOCX property scrub, verification | Markdown round-tripping can flatten complex formatting or omit linked remote images |
| `.pptx` | Local cleaning, text extraction, sandboxed best-effort rebuild, verification | Slide layout, notes, and linked remote images need a close human check |
| `.pdf` | Local cleaning and text extraction, then DOCX output | It doesn't reproduce the original PDF layout |
| `.txt`, `.md` | Local deterministic cleaning, editable text pass, verification | Statistical detectors remain outside the default checks |
| `.png`, `.jpg`, `.jpeg`, `.webp` | Local deterministic cleaning and verification | Pixel-level watermarks need optional upstream backends |

Start with an editable source when you have one. Keep the original and check the result. Tables, footnotes, slide layouts, legal wording, names, dates, and numbers deserve an extra look.

## Privacy in plain English

Here's the honest version. Metadata cleaning, extraction, rebuilding, and verification run on your computer. Humanising happens wherever your chosen assistant runs. If it's hosted, your text may go to that provider under its privacy and retention terms.

Advanced users can point the CLI at a persistent loopback service with `WATERMARKS_SERVICE_URL`. Remote addresses are rejected so a configuration mistake can't upload the file. If the service uses `WATERMARKS_SERVER_API_KEY`, export the same value for the CLI. Don't put the token in a command argument, document, or report. A separately started service's commit can't be independently verified, so its self-reported version is recorded instead of the audited local SHA.

Want the whole workflow to stay local? Use a local model such as Ollama to edit the prepared `draft.md`, then run `vivid-clean finish`. That keeps the text on your computer. It still can't guarantee that every watermark is gone or predict what a detector will say.

## Limits and responsible use

- vivid-clean removes deterministic marks its available checks can find. It can't promise a result against keyed statistical watermarks or private third-party detectors.
- Rewriting can change nuance. You're responsible for checking meaning, attribution, legal intent, and formatting.
- Many schools and workplaces have rules about AI assistance or detector avoidance. Those rules still apply.
- Removing C2PA, EXIF, or copyright-related provenance from somebody else's work may be unlawful and can harm the creator. Only clean files you're entitled to edit.
- A report records test results, not proof of human authorship.

The detailed assumptions and failure cases are in the [threat model](./docs/threat-model.md). Dependency pins and licences are recorded in [DEPENDENCIES.md](./DEPENDENCIES.md).

## Why this exists

I built vivid-clean because AI can make writing possible, or simply less exhausting, for people with dyslexia, ADHD, autism, learning disabilities, injury, fatigue, or a packed day. Treating every assisted sentence as deception erases why people use these tools in the first place.

I wrote the longer argument here: [AI watermarking is the new scarlet letter](https://www.linkedin.com/pulse/ai-watermarking-new-scarlet-letter-vivid-n-savitri-npzpc).

## Project notes

- Changes are recorded in [CHANGELOG.md](./CHANGELOG.md).
- Security reports belong in the process described in [SECURITY.md](./SECURITY.md).
- Contributions are welcome. Start with [CONTRIBUTING.md](./CONTRIBUTING.md).
- Formatting-preserving document editing is tracked in [ROADMAP.md](./ROADMAP.md).

Built by [Vivid Savitri](https://github.com/vnsavitri) under the [MIT Licence](./LICENSE).

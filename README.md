# vivid-clean

A document- and media-cleaning pipeline for people who use AI to help them write.

`vivid-clean` takes a file drafted with an AI assistant and removes both the deterministic marks (invisible Unicode, C2PA/EXIF/XMP metadata, document properties) and the statistical tells that make text sound machine-generated.

It is not a cheating tool. It is an accessibility tool. If you are dyslexic, neurodivergent, have a learning disability, or rely on voice dictation and AI editing to communicate clearly, the current push for AI watermarking treats assistive technology as a confession. This tool pushes back.

## What it does

1. **Deterministic clean** — strips invisible Unicode, file metadata, and vendor-bound provenance marks.
2. **Extract** — converts the cleaned file to Markdown.
3. **Humanise** — rewrites the text to sound like a person, breaking statistical watermark patterns and AI-tell vocabulary.
4. **Re-export** — converts the result back to the original format.

## Supported formats

| Format | Notes |
|--------|-------|
| **DOCX** | Microsoft Word; most common use case |
| **PPTX** | PowerPoint slides and notes |
| **PDF** | Text extraction; output is DOCX by default |
| **TXT** | Plain text |
| **MD** | Markdown |
| **Images** | PNG, JPEG, WebP, AVIF, HEIC, BMP, GIF, TIFF, SVG — metadata/C2PA strip only |

## How it works

The pipeline wraps two open-source projects and adds a humanising rewrite pass:

- **[watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover)** by Guillaume Meyer — the primary cleaner for deterministic marks.
- **[anthropies](https://github.com/CharlesHoskinson/anthropies)** — a fallback cleaner for Anthropic/Claude-specific marks.
- **`/human` rewrite rules** — degrades statistical text watermarks by changing vocabulary, rhythm, and sentence structure.

For strongest mitigation against keyed statistical watermarks, route the final draft through a local, non-watermarked open model such as Kimi, DeepSeek, GLM, Qwen, Llama, or Mistral with watermarking disabled.

## Quick start

### 1. Install dependencies

You need Python 3.10+, plus `pandoc` and `markitdown`:

```bash
# macOS
brew install pandoc
pip install markitdown

# Debian/Ubuntu
sudo apt-get install pandoc
pip install markitdown
```

### 2. Start the watermarks-remover service

```bash
git clone --depth 1 https://github.com/guillaumemeyer/watermarks-remover.git ./vendor/watermarks-remover
cd ./vendor/watermarks-remover
python3 service/scripts/server.py --host 127.0.0.1 --port 8765
```

### 3. Install vivid-clean

Copy `SKILL.md` (or the full repo contents) into your agent skills directory, for example:

```bash
mkdir -p ~/.agents/skills/vivid-clean
cp ./SKILL.md ~/.agents/skills/vivid-clean/SKILL.md
```

### 4. Run it

The skill accepts file paths or directories. For a single file:

```bash
# Trigger the skill from your agent, or run the underlying pipeline:
./vivid-clean "Draft.docx"
```

The output is saved next to the source with a `_vivid` suffix:

```
Draft.docx → Draft_vivid.docx
```

## Important constraints

- **Do not change substantive meaning or legal intent.** This is a style and watermark-mitigation pass, not a content edit.
- **Do not remove required institutional voice.** Keep formal documents appropriate while removing AI tells.
- **Preserve originals.** The source file is never overwritten.
- **This tool does not prove a text is human-written, nor does it guarantee an official detector will fail.** It raises the cost of detection and protects ordinary people who use assistive technology.

## Limitations

- `watermarks-remover` Layer A removes invisible Unicode and file metadata deterministically. It does **not** remove a keyed statistical text watermark.
- `anthropies clean` removes metadata and vendor-bound marks. It does **not** remove Anthropic's keyed text watermark.
- The `/human` rewrite pass degrades statistical watermarks by changing word choices, but because it is run by an AI assistant, it does not give a cryptographic guarantee.
- For maximum assurance, run the final draft through a local open model with watermarking off, or edit it heavily yourself.

## Why this exists

AI labs like Anthropic, OpenAI, and Google are pushing watermarking as "transparency." In practice, watermarking punishes the people who already face the most friction when they write: people with dyslexia, ADHD, autism, learning disabilities, and anyone who dictates or uses AI as an accessibility aid.

There is no moral difference between running Grammarly over an email and asking ChatGPT or Claude to tidy up the same sentences. Both are assistive. Both help people express themselves. One gets a friendly green tick. The other is about to get a watermark that says "this person needed help."

This tool is for the second group.

## Credits and license

- Deterministic cleaning by [watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover) (Guillaume Meyer).
- Fallback Anthropic/Claude cleaning by [anthropies](https://github.com/CharlesHoskinson/anthropies).
- Humanising rewrite rules derived from the `/human` skill.

Released under the MIT License.

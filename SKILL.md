---
name: vivid-clean
description: Remove deterministic AI marks and AI-writing tells from documents and media. Use when the user gives you files and asks to "remove the watermark", "humanise", "strip AI marks", "make it less like AI", or wants a _vivid version of a document.
---

# vivid-clean

**Install name:** `vivid-clean`
**Source repo:** https://github.com/vnsavitri/vivid-clean

A document- and media-oriented wrapper around the `/human` skill. Use it when you need to take an existing file drafted with an AI assistant and remove both:

1. **Deterministic marks** — invisible Unicode, C2PA/EXIF/XMP metadata, doc properties, and other hard-bound provenance.
2. **AI writing tells / statistical watermarks** — the `/human` skill rewrites the text to sound like a person and to degrade token-sampling watermark patterns.

This skill combines two tools into one pipeline:
- **[watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover)** — Layer A Unicode scrub + file/metadata cleaner for many formats.
- **anthropies** (legacy fallback) — focused on Anthropic/Claude-specific deterministic marks.

## Triggers

- `/vivid-clean`
- "remove watermark"
- "remove watermark from this docx"
- "humanise this document"
- "vivid clean these files"
- "make this docx less like AI"
- "de-watermark"
- "clean up AI tells"
- "strip AI marks"
- "remove AI provenance"

## When to use

- The user gives you one or more files and asks you to "remove the watermark", "humanise", "strip AI marks", or "make it less like AI".
- The user wants a `_vivid` version of a DOCX, PPTX, PDF, TXT, MD, or image file.
- The user is finalising external-facing documents (applications, letters, reports, emails) drafted with AI and wants them to sound like a person wrote them.

## Supported formats

| Format | Notes |
|--------|-------|
| **DOCX** | Microsoft Word; most common use case |
| **PPTX** | PowerPoint slides and notes |
| **PDF** | Text extraction; output is DOCX by default |
| **TXT** | Plain text |
| **MD** | Markdown |
| **Images** | PNG, JPEG, WebP, AVIF, HEIC, BMP, GIF, TIFF, SVG — metadata/C2PA strip only; pixel watermark removal is optional and heavy |

## Workflow

1. **Collect inputs.** Accept file paths or directories from the user. If a directory is given, recurse into it and process all supported files.
2. **Deterministic clean (preferred: watermarks-remover).** If the watermarks-remover HTTP service is running, send the file to `POST /clean`.
   ```bash
   WATERMARKS_SERVICE_URL="${WATERMARKS_SERVICE_URL:-http://127.0.0.1:8765}"
   
   python3 - << 'PY'
   import base64, json, os, requests, sys
   service = os.environ.get("WATERMARKS_SERVICE_URL", "http://127.0.0.1:8765")
   path = sys.argv[1]
   out = sys.argv[2]
   with open(path, "rb") as f:
       b64 = base64.b64encode(f.read()).decode()
   r = requests.post(f"{service}/clean", json={"file": b64, "name": os.path.basename(path)})
   r.raise_for_status()
   data = r.json()
   with open(out, "wb") as f:
       f.write(base64.b64decode(data["cleaned"]))
   print(json.dumps(data.get("report", {}), indent=2))
   PY
   ```
   Use the cleaned file if the call succeeds and the output is non-empty; otherwise fall back to the original.
3. **Deterministic clean (fallback: anthropies).** If watermarks-remover is not available, try `anthropies clean` on the input file. This removes C2PA metadata from images, `Co-Authored-By` trailers from text, and other hard-bound vendor marks. It does **not** remove Anthropic's keyed text watermark.
   ```bash
   ANTHROPIES_CLI="./vendor/anthropies/dist/cli.js"
   if [ -f "$ANTHROPIES_CLI" ]; then
     node "$ANTHROPIES_CLI" clean "input.docx" -o ".tmp/vivid-clean/input.clean.docx" || true
   elif command -v anthropies >/dev/null 2>&1; then
     anthropies clean "input.docx" -o ".tmp/vivid-clean/input.clean.docx" || true
   fi
   ```
   `anthropies clean` exits with code 1 when it finds a mark, but it still writes the cleaned file. Use the cleaned file if it exists; otherwise fall back to the original.
4. **Inspect / detect (optional).** If the user only wants to know whether a file carries marks, use `POST /inspect` or `POST /detect` from watermarks-remover instead of `/clean`, and stop here. For images, this can also surface an optional SynthID pixel score if the heavy backend is configured.
5. **Extract.** Convert the cleaned file (or the original, if no cleaner was available) to Markdown using `markitdown`.
   ```bash
   if [ -f ".tmp/vivid-clean/input.clean.docx" ]; then
     markitdown ".tmp/vivid-clean/input.clean.docx" -o ".tmp/vivid-clean/input.md"
   else
     markitdown "input.docx" -o ".tmp/vivid-clean/input.md"
   fi
   ```
6. **Humanise.** Rewrite the Markdown by applying the `/human` skill rules in full:
   - Write like a person talking to one person.
   - Australian English spelling (`colour`, `organise`, `behaviour`, `centred`, `modelling`).
   - **No em dashes.** Use comma, colon, full stop, or parentheses.
   - Avoid AI vocabulary: `delve`, `boasts`, `bolstered`, `crucial`, `emphasizing`, `enduring`, `garner`, `intricate`, `interplay`, `landscape`, `meticulous`, `pivotal`, `underscore`, `tapestry`, `testament`, `vibrant`, `align with`, `enhance`, `fostering`, `highlighting`, `showcasing`, `realm`, `multifaceted`, `commendable`, `paramount`, `commence`, `leverage`, `facilitate`, `utilise`, `foster`, `nestled`, `breathtaking`.
   - Avoid negative parallelism, rule-of-three padding, superficial "-ing" tails, "Despite X, Y faces challenges", and compulsive summarising.
   - Vary sentence length deliberately.
   - Sentence case for headings.
   - Preserve all names, dates, numbers, legal disclaimers, commitments, bullet lists, tables, and section headings.
7. **Re-export.** Convert the rewritten Markdown back to the original format using `pandoc`.
   ```bash
   pandoc ".tmp/vivid-clean/input_vivid.md" -o "input_vivid.docx"
   ```
8. **Name the output.** Insert `_vivid` before the file extension:
   - `Draft.docx` → `Draft_vivid.docx`
   - `Slides.pptx` → `Slides_vivid.pptx`
   - `Paper.pdf` → `Paper_vivid.docx` (PDFs are re-exported as DOCX by default)
9. **Preserve originals.** Never overwrite the source file. Place the new file in the same directory as the source.
10. **Clean up.** Delete the temporary Markdown files and the `.tmp/vivid-clean` working directory.
11. **Report.** List the created files and give a short summary of what was changed.

## Important constraints

- **Do not change substantive meaning or legal intent.** This is a style and watermark-mitigation pass, not a content edit.
- **Do not remove required institutional voice.** For formal applications and letters, keep the register appropriate while removing AI tells.
- **If the user specifies a different suffix**, use it instead of `_vivid`.
- **If pandoc or markitdown is missing**, install or alert the user rather than failing silently.

## Setting up watermarks-remover

The skill prefers a local watermarks-remover HTTP service. You only need to set this up once.

### Quick start (Python, no Docker)

```bash
git clone --depth 1 https://github.com/guillaumemeyer/watermarks-remover.git \
  ./vendor/watermarks-remover
cd ./vendor/watermarks-remover
python3 service/scripts/server.py --host 127.0.0.1 --port 8765
```

The core service needs only Python 3.10+ stdlib. Optional heavy backends (CtrlRegen pixel removal, SynthID scoring, MarkLLM verification) require separate setup and are not required for the document pipeline.

### Docker

```bash
git clone --depth 1 https://github.com/guillaumemeyer/watermarks-remover.git \
  ./vendor/watermarks-remover
cd ./vendor/watermarks-remover
make docker-core-build
docker run --rm -p 127.0.0.1:8765:8765 --read-only --tmpfs /tmp watermarks-remover
```

### Tell the skill where the service is

Set `WATERMARKS_SERVICE_URL` if the service is not on the default `http://127.0.0.1:8765`.

## anthropies setup and maintenance (fallback)

This skill can use a working build of [anthropies](https://github.com/CharlesHoskinson/anthropies) at:

`./vendor/anthropies/`

If watermarks-remover is unavailable, the skill falls back to `anthropies clean`.

To update the vendored copy:

```bash
git clone --depth 1 https://github.com/CharlesHoskinson/anthropies.git /tmp/anthropies
cd /tmp/anthropies
pnpm install
pnpm build
rm -rf ./vendor/anthropies
mv /tmp/anthropies ./vendor/anthropies
```

## Integration with /human

This skill is a document pipeline for `/human`. Whenever `/human` receives a document file as input, route it here instead of trying to rewrite inline text.

## Limitations

- **watermarks-remover Layer A** removes invisible Unicode and file metadata deterministically. It does **not** remove a keyed statistical text watermark.
- **watermarks-remover Layer B** is a best-effort rewrite for statistical marks; it is not enabled by default in this pipeline because the `/human` pass already rewrites the text.
- **anthropies clean** removes metadata and visible/vendor-bound marks. It does **not** remove Anthropic's keyed text watermark.
- The `/human` rewrite pass degrades the statistical watermark by changing word choices, but because it is run by an AI assistant, it does not give a cryptographic guarantee.
- For maximum assurance against keyed text detection, run the final draft through a local, non-watermarked model (Llama, Qwen, Mistral, DeepSeek with watermarking off), or edit the draft heavily yourself.
- This skill does not prove a text is human-written, nor does it guarantee an official detector will fail.

## Future extensions

- Optional flags: `--suffix custom`, `--in-place`, `--output-dir <dir>`, `--check-only`.
- PDF-to-PDF re-export using a reference doc or template.
- Batch reports showing AI-tell density and detected marks before and after.
- Optional local-model rewrite pass for users who want stronger keyed-watermark mitigation.

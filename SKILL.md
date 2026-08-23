---
name: vivid-clean
description: Prepare, humanise, preserve and check documents or media with the vivid-clean CLI. Use when a user asks to remove deterministic AI marks, strip provenance metadata, humanise a file, or make a checked copy.
---

# vivid-clean

Run the installed CLI. Don't rebuild the pipeline with bits of inline shell or Python. The CLI talks to the local cleaner, looks after the restricted session, edits Word and PowerPoint packages without rebuilding them, checks the result, and saves a report.

## Before starting

1. Confirm the user owns the file or is allowed to edit it.
2. Run `vivid-clean doctor` if the setup hasn't been checked in this environment.
3. Never overwrite the source.
4. Ask for a suffix only when the user hasn't expressed a preference and the filename matters. `_vivid` is the compatibility default, but it advertises the tool. A neutral suffix such as `_reviewed` is often better.

## Workflow

### 1. Prepare the file

```bash
vivid-clean prepare "/absolute/path/to/Draft.docx"
```

The command starts the pinned local cleaner with a one-use token and prints a restricted session directory. It fails if neither watermarks-remover nor the installed anthropies fallback can produce an output. Don't bypass that failure by copying the original into the session.

For PDF and images, the session has no `draft.md`. Skip the writing pass and finish the session. Ask for the editable source when the user wants a PDF humanised.

### 2. Humanise `draft.md`

Open the `draft.md` path printed by the CLI. First establish what the user wants:

- Use a `voice-preserving` pass for ordinary editing. This can be light, and it doesn't claim to reduce a keyed statistical watermark.
- Use `statistical-risk-reduction` only when the user asks for it and accepts a more substantial rewrite. Don't perform this pass with Claude, Gemini, the model that produced the source, or another known watermarked provider. That can add a fresh mark. Use a human editor or a local model whose watermarking is switched off. If you can't establish the backend, stop and offer the voice-preserving pass instead.

You're helping one person say what they already mean, so write like it:

- Edit only inside the labelled blocks. Don't alter, move, add, or remove their HTML comment markers.
- Preserve names, dates, numbers, quotations, citations, commitments, disclaimers, headings, tables, and list structure.
- Establish the audience, purpose, register and regional spelling first. Ask when an unclear choice would materially change the edit.
- Use a voice sample only when the user owns it or is authorised to use it. Don't imitate another identifiable person.
- Keep the author's register and vocabulary. Preserve deliberate repetition, directness, dialect, dictation patterns and unusual phrasing unless the user asks for a change or the meaning is genuinely unclear.
- Prefer plain wording and natural contractions where they fit.
- Vary sentence length and structure. Remove repeated model-like patterns rather than applying mechanical substitutions.
- Treat punctuation as voice, not a detection checklist. Keep or replace dashes according to the author's style and readability instead of banning one mark everywhere.
- Avoid stock AI phrasing, padded conclusions, forced groups of three, vague attribution, and repetitive summary paragraphs.
- Don't claim the rewrite proves human authorship or defeats a detector.

For statistical-risk reduction, change sentence boundaries, clause order and connecting words instead of swapping synonyms inside the same sentence skeleton. Aim to leave fewer than half of the original five-word sequences, while keeping the protected facts and the author's voice. This is a rewrite-depth target, not a watermark detector. Short passages won't contain enough words for the CLI to calculate it.

If the user's chosen assistant is hosted, tell them the text may be sent to that provider and may receive that provider's marks. For a local-only pass, have a local model edit `draft.md`, then continue with the same finish command. Don't describe a local model as a guarantee.

### 3. Finish and verify

```bash
vivid-clean finish "/private/session/path" --suffix "_reviewed" \
  --writing-backend "manual edit" --writing-backend-kind human \
  --rewrite-purpose voice-preserving
```

Name the backend honestly. Use `local-unwatermarked` only when a local backend's watermarking is known to be off. A hosted backend is `hosted`, even when the vendor says it doesn't watermark. For statistical-risk reduction, change the final flag and use only `human` or `local-unwatermarked`:

```bash
vivid-clean finish "/private/session/path" --suffix "_reviewed" \
  --writing-backend "ollama:qwen3" --writing-backend-kind local-unwatermarked \
  --rewrite-purpose statistical-risk-reduction
```

Use `--output "/absolute/path/to/result.docx"` when the user gave an exact destination. Add `--report-json "/path/to/report.json"` only when they need machine-readable results.

The finish command:

1. Puts revised DOCX and PPTX text back into the existing package structure.
2. Refuses changed block markers, numbers, URLs, email addresses, or package structure.
3. Removes residual DOCX properties and package references.
4. Compares the source with the output.
5. Saves `<output>.vivid-clean-report.md` with separate check channels and engine evidence.
6. Records the declared writing backend and a best-effort five-word-sequence overlap measure.
7. Deletes the restricted session after an output reaches verification, whether checks pass or fail. A correctable pre-output rejection keeps the session so you can fix the draft or run `vivid-clean cleanup`.

Exit status `0` means the checks that ran found no medium or high residual marks. Status `1` means findings remain. Status `2` means a check couldn't finish. Don't present status `1` or `2` as done.

If statistical-risk reduction rejects a long passage for excessive overlap, revise the existing draft and run `finish` again. Don't alter exact quotations or fixed legal and factual wording just to chase the overlap target. If protected material dominates the document, use the voice-preserving mode and report the statistical limitation instead.

### 4. Report to the user

Give them the output and report paths. Use the report's exact scope:

- Say “the configured checks passed without medium or high residual findings” when the result is `checks_passed`.
- Name any checks that weren't available.
- Say who or what performed the writing pass and whether the rewrite-depth measure was computed or insufficient.
- Never say “there's no watermark” or “this will pass AI detection”.
- Remind them to inspect formatting and meaning before sending the file.

## Supported workflow

| Format | Behaviour |
| --- | --- |
| DOCX | Package-aware writing, scrub, structure check and verification; no Markdown rebuild |
| PPTX | Package-aware slide and speaker-note writing with structure checks; no Markdown rebuild |
| PDF | Deterministic cleaning only; output stays PDF and humanising needs the editable source |
| TXT, MD | Direct writing and verification |
| PNG, JPEG, WebP | Deterministic cleaning and verification; no writing pass |

Don't batch directories in this release. Work through one file at a time so each one gets its own result and report.

Run `vivid-clean cleanup --dry-run` to inspect expired sessions, or `vivid-clean cleanup` to remove validated sessions older than 24 hours.

## Keep the skill current

After updating the vivid-clean repo, refresh the assistant instructions with:

```bash
./install.sh --skills-only
```

The installer updates Agent Skills-compatible tools, Cursor, Claude Code and Codex, including a custom `CODEX_HOME`. It keeps replaced copies under `$XDG_STATE_HOME/vivid-clean/skill-backups/`, or `~/.local/state/vivid-clean/skill-backups/` when `XDG_STATE_HOME` isn't set. That sits outside the folders assistants scan for skills. The installer also moves older `vivid-clean.backup.*` folders out of those scan paths, so only the current skill is discovered.

Don't copy `SKILL.md` by hand unless the installer can't run. A partial update can leave the instructions out of step with the CLI.

## Persistent service override

Most people don't need this. `prepare` starts and stops the pinned service itself. For repeated work, an advanced user may run it persistently:

```bash
.venv/bin/python vendor/watermarks-remover/service/scripts/server.py \
  --host 127.0.0.1 --port 8765
```

Set `WATERMARKS_SERVICE_URL` to opt into that persistent service. If `WATERMARKS_SERVER_API_KEY` protects it, export the same value for the CLI. Never print it or put it in a report. The report records a self-reported version for external services because vivid-clean can't prove which checkout launched them.

The installer pins both engines. Don't run `git pull` inside `vendor/` or replace a pin during an ordinary cleaning task.

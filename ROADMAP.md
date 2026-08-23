# Roadmap

## Document fidelity

DOCX and PPTX writing now happens inside the cleaned OOXML package. The editor preserves package members, paragraph and run structures, styles, tables, hyperlinks, slide shapes and speaker-note structures. It doesn't rebuild the document through Markdown.

The next fidelity fixtures should cover fields, tracked changes, comments, footnotes, endnotes, charts, embedded workbooks, animations and right-to-left documents. When a structure can't be edited safely, the run should stop and explain why.

PDF stays PDF for deterministic cleaning. Humanising still needs an editable source because a reliable general-purpose PDF text editor is outside this project's scope.

## Distribution

- Publish tagged releases with checksums.
- Add `pipx` and `uv tool` installation paths.
- Add Windows CI and installation guidance.
- Add explicit skill install and uninstall commands.

## Workflow

- Add safe directory and batch processing after single-file reports are stable.
- Add a machine-readable session listing command.
- Add optional local-model adapters without silently sending text to a hosted service.
- Keep cleaning engines behind one capability interface so vendor-specific fallbacks can't pretend to be equivalent.

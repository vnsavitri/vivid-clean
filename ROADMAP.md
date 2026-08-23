# Roadmap

This file defines the planned scope. Concrete work links to a public issue, and the [vivid-clean backlog](https://github.com/users/vnsavitri/projects/1) shows whether it's in Backlog, Doing or Done. Early research stays as a project-only draft until there's a realistic job to finish. Finished work is recorded in the [changelog](./CHANGELOG.md).

## Document fidelity

DOCX and PPTX writing now happens inside the cleaned OOXML package. The editor preserves package members, paragraph and run structures, styles, tables, hyperlinks, slide shapes and speaker-note structures. It doesn't rebuild the document through Markdown.

The next fidelity fixtures should cover fields, tracked changes, comments, footnotes, endnotes, charts, embedded workbooks, animations and right-to-left documents. When a structure can't be edited safely, the run should stop and explain why. Follow the work in [issue #11](https://github.com/vnsavitri/vivid-clean/issues/11).

PDF stays PDF for deterministic cleaning. Humanising still needs an editable source because a reliable general-purpose PDF text editor is outside this project's scope.

## Distribution

- [Publish checksums with tagged releases](https://github.com/vnsavitri/vivid-clean/issues/8).
- [Add a `uv tool` installation path](https://github.com/vnsavitri/vivid-clean/issues/7).
- [Add Windows CI and installation guidance](https://github.com/vnsavitri/vivid-clean/issues/12).
- [Add explicit skill install and uninstall commands](https://github.com/vnsavitri/vivid-clean/issues/13).

## Workflow

- [Add safe directory and batch processing](https://github.com/vnsavitri/vivid-clean/issues/10) after single-file reports are stable.
- [Add a machine-readable session listing command](https://github.com/vnsavitri/vivid-clean/issues/6).
- [Add optional local-model adapters](https://github.com/vnsavitri/vivid-clean/issues/9) without silently sending text to a hosted service.
- Add an opt-in official watermark detector when a stable provider API, privacy terms and test fixture are available.
- [Keep cleaning engines behind one capability interface](https://github.com/vnsavitri/vivid-clean/issues/5) so vendor-specific fallbacks can't pretend to be equivalent.

## Opt-in pixel restoration research

Pixel-level watermark removal isn't a current vivid-clean feature. Research it as a separate, opt-in restoration step rather than quietly adding a model to the metadata-cleaning path.

It can't ship until the implementation:

- Names the exact detector and restoration backend instead of calling it generic AI.
- Says whether each step runs locally or sends the image to a hosted service.
- Keeps the original file untouched and writes a separate result.
- Distinguishes visible logos from imperceptible patterns embedded in pixels.
- Records what was detected, changed, verified and left `not_checked`.
- Tests supported formats with before-and-after fidelity fixtures.
- Warns that generated or reconstructed pixels can alter detail and meaning.
- Includes responsible-use guidance for copyright, provenance and files the user isn't entitled to edit.

Don't advertise image, logo, SynthID or pixel-watermark removal until a named implementation passes those tests.

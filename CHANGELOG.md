# Changelog

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses semantic versioning.

## Unreleased

### Changed

- Updated the workflow diagram to cover images, editable-file drafts and both writing modes, with the image limits stated plainly.
- Put the beginner installation prompt in a one-click copy box on GitHub.
- Added plain-English answers for common AI watermark, document-format, image and privacy questions.
- Expanded the package and repository search terms around text watermarks, document metadata and local-first cleaning without claiming pixel-level removal.
- Added release gates for any future opt-in pixel-restoration work.
- Linked the public project board from the README so planned, active and finished work is easy to follow.
- Synced the roadmap with the public backlog, linked earlier merged pull requests to their finished work, and sorted Backlog and Done with the newest cards first.
- Turned nine concrete roadmap cards into public issues with finish criteria, while keeping three speculative ideas as project-only drafts.
- Added a roadmap issue form and pull request guidance so new, linked and merged work updates the project board through GitHub's enabled workflows.

## 0.3.0 - 2026-08-23

### Added

- Writing-pass provenance in Markdown and JSON reports, including the declared backend, its kind, the rewrite purpose, and a best-effort five-word-sequence overlap measure.
- A separate statistical-risk-reduction mode for people who knowingly choose a more substantial rewrite.
- A tested Python wheel, a `vivid-clean setup` command for packaged installs, and a Trusted Publishing workflow for PyPI.
- CodeQL and OpenSSF Scorecard workflows, plus badges that link to their results.
- A lightweight 1280×640 social-preview image for shared repository links.

### Changed

- Added a plain-English workflow diagram and its editable Excalidraw source to the README.
- Statistical-risk reduction now requires a human or declared local unwatermarked backend. Long passages must clear the rewrite-depth target, while short passages are reported as insufficient to measure.
- The assistant skill now warns that an origin or known watermarked model can add a fresh mark during rewriting.
- GitHub Actions now use pinned Node 24 releases instead of deprecated Node 20 releases.
- The repository now carries searchable topics for accessibility, privacy, document cleaning and AI watermarking.

### Fixed

- Prevented hosted or unknown writing backends from being presented as statistical-risk mitigation.
- Backend labels can no longer inject control characters or Markdown into a verification report.
- Correctable pre-output failures now keep the restricted session, so the draft can be fixed without preparing the source again.

## 0.2.0 - 2026-08-23

### Added

- A Python CLI for preparing, finishing, checking, and diagnosing the workflow.
- Independent verification, DOCX property scrubbing, scoped sidecar reports, and macOS/Linux CI.
- Skill installation for Agent Skills-compatible tools, Cursor, Claude Code, and Codex.
- Security, contribution, dependency, threat-model, and roadmap documentation.
- Format-preserving DOCX and PPTX text editing with protected block markers, values, package-structure checks, and speaker-note support.
- Scoped check channels, retained upstream evidence, multi-vendor producer hints, and cleanup for abandoned sessions.

### Changed

- Dependencies are checked out at reviewed commits instead of floating branches.
- Python packages install inside the repo's virtual environment.
- Privacy and result claims now describe the hosted-assistant boundary and unavailable checks.
- Humanising guidance preserves the author's punctuation patterns instead of applying a uniform substitution rule.
- PDF cleaning now keeps PDF output and requires an editable source for humanising.
- The overall success label is now `checks_passed` instead of the broader `verified`.
- Skill installation honours custom `CODEX_HOME` locations and backs up existing copies before replacement.
- Pandoc and MarkItDown are no longer core dependencies.

### Fixed

- Skill upgrades now keep backups outside assistant skill folders, so an older copy can't be discovered as a second `vivid-clean` skill.

## 0.0.1 - 2026-08-22

- Published the first setup guide, assistant skill, accessibility framing, and background reading.

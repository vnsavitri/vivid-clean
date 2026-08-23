# Changelog

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses semantic versioning.

## Unreleased

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

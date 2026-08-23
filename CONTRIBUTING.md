# Contributing

Thanks for pitching in. Keep changes small enough to review, and add a fixture that proves the behaviour. It saves everyone a guessing game later.

## Set up

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[dev]'
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/ruff check src tests tools
.venv/bin/ruff format --check src tests tools
```

Run `shellcheck install.sh` when you change the installer.

## Pull requests

- Explain which threat or user problem the change handles.
- Add a regression test for scanners, file rewriting, service responses, or installer logic.
- Never weaken a check just to make a fixture pass.
- Use synthetic documents. Don't commit a real person's application, report, image metadata, or model API response.
- Keep privacy and result claims consistent across the README, setup prompt, skill, report wording, and threat model.
- Update `DEPENDENCIES.md` when changing an upstream pin, after reviewing its source, licence, and interface.

For DOCX or PPTX changes, preserve the existing package structure and add a fixture for the exact feature you touched. Fields, tracked changes, comments, charts and right-to-left documents still need more coverage. See [ROADMAP.md](./ROADMAP.md).

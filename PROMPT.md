# Copy-paste setup prompt

Don't fancy doing the setup by hand? Paste this into a coding assistant that can run terminal commands:

```text
Please install vivid-clean from https://github.com/vnsavitri/vivid-clean.

1. Clone it into ~/vivid-clean if it isn't already installed.
2. Read install.sh, then run it from the repo.
3. Don't install Pandoc or change my shell profile without asking me first. If Pandoc is missing, show me the right command for my system.
4. Run vivid-clean doctor and explain anything that's unavailable. The cleaner should start privately when a file is prepared, so don't leave a background service running.
5. Confirm that the vivid-clean skill was copied into the skill directory used by this assistant.

Metadata cleaning and verification run locally. Tell me clearly if the writing pass will send text through a hosted assistant, and offer a local-model route if I want the text to stay on my computer.

Once setup is working, ask which file I want to prepare first.
```

To use it later:

```text
Use the vivid-clean skill on "/full/path/to/my/file.docx". Preserve my meaning, ask before making a substantive edit, and use the suffix "_reviewed".
```

You'll get a separate output and a Markdown verification record. The record covers the checks that ran. It can't promise anything about every watermark or AI detector in existence.

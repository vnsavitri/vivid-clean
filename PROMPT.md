# Copy-paste setup prompt

Don't fancy doing the setup by hand? Paste this into a coding assistant that can run terminal commands:

```text
Please install vivid-clean from https://github.com/vnsavitri/vivid-clean.

1. Clone it into ~/vivid-clean if it isn't already installed.
2. Read install.sh, then run it from the repo.
3. Don't change my shell profile without asking me first.
4. Run vivid-clean doctor and explain anything that's unavailable. The cleaner should start on loopback with a one-use token when a file is prepared, so don't leave a background service running.
5. Confirm that the vivid-clean skill was copied into the skill directory used by this assistant, including a custom CODEX_HOME when present.

Metadata cleaning and verification run locally. Tell me clearly if the writing pass will send text through a hosted assistant or may add that provider's own marks. Offer a human or local unwatermarked route if I ask for statistical-risk reduction.

Once setup is working, ask which file I want to prepare first.
```

To use it later:

```text
Use the vivid-clean skill on "/full/path/to/my/file.docx". Preserve its existing document structure and formatting, preserve my meaning, ask before making a substantive edit, and use the suffix "_reviewed".
```

You'll get a separate output and a Markdown verification record. The record covers the checks that ran. It can't promise anything about every watermark or AI detector in existence.

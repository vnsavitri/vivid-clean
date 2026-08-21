# Copy-paste prompt for your AI assistant

If you would rather not type commands yourself, copy and paste the block below into Claude Code, Codex, ChatGPT, or any AI assistant that can run commands. It will install vivid-clean and run it for you.

## One-time setup prompt

```text
Please install the vivid-clean tool from https://github.com/vnsavitri/vivid-clean so I can remove AI watermarks and AI-writing tells from my documents.

Do this step by step, and tell me what you are doing at each step:

1. Clone the repo to ~/vivid-clean.
2. Run ./install.sh inside that folder.
3. Check whether pandoc is installed. If it is missing, ask me before installing it, and suggest the right command for my system (for example, "brew install pandoc" on a Mac with Homebrew, or "sudo apt-get install pandoc" on Ubuntu/Debian).
4. Start the watermarks-remover service in the background on 127.0.0.1:8765, or tell me how to keep it running.
5. Install the skill so I can trigger it with /vivid-clean.

Once setup is done, ask me which file I would like to clean first.
```

## Cleaning a file

After setup, whenever you want to clean a document, paste this:

```text
Please run /vivid-clean on "[full path to your file]".
```

For example:

```text
Please run /vivid-clean on "/Users/vnsavitri/Documents/Cover_Letter.docx".
```

Your assistant will create a cleaned file next to the original with `_vivid` in the name, such as `Cover_Letter_vivid.docx`.

## Optional: stronger cleaning

If the file was drafted with ChatGPT or Claude and you want the strongest result, ask your assistant to first route the text through a non-watermarked open model like Kimi, DeepSeek, GLM, or Qwen, then run vivid-clean.

```text
This file was edited with ChatGPT. Please first rewrite it through a non-watermarked open model to break any statistical watermark pattern, then run /vivid-clean on the result.
```

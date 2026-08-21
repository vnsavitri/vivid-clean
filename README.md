# vivid-clean

Clean AI watermarks and AI-writing tells out of your documents.

If you use AI to help you write because of dyslexia, ADHD, autism, a learning disability, or voice dictation, companies like Anthropic, OpenAI, and Google want to put a watermark on text that AI helped produce. That watermark cannot tell the difference between someone who pasted a whole prompt and someone who just asked AI to fix their grammar. It marks both people as suspect.

**vivid-clean** is a small tool that helps. It strips hidden markers from your files and rewrites the text so it sounds like a person wrote it.

---

## Is this for me?

Use this if:

- You use ChatGPT, Claude, or another AI assistant to help draft emails, cover letters, essays, reports, or applications.
- You want the final document to sound like you, not a chatbot.
- You want to remove hidden file metadata and watermark markers.

Do not use this to hide that you generated an entire assignment or application dishonestly. This tool is for accessibility, not cheating.

---

## What you need

You do not need to be a programmer, but you need to be comfortable copying and pasting a few commands into the Terminal app on your Mac or Linux computer. Windows users: this tool works best on macOS and Linux for now.

Before you start, check that you have:

1. **Python 3.10 or newer.** Open Terminal and type:
   ```bash
   python3 --version
   ```
   If you see `3.10`, `3.11`, `3.12`, or higher, you are good. If not, install Python from [python.org](https://python.org).

2. **pandoc.** This converts files between formats. To check, type:
   ```bash
   pandoc --version
   ```
   If it is not installed, the install script will tell you how to get it.

---

## Installation

Open Terminal and run these commands one at a time.

### 1. Download the tool

```bash
cd ~
git clone https://github.com/vnsavitri/vivid-clean.git
cd vivid-clean
```

What this does: it copies the tool from GitHub onto your computer into a folder called `vivid-clean` in your home directory.

### 2. Run the installer

```bash
./install.sh
```

This will:
- check that Python is new enough;
- install `markitdown` (a small helper for reading documents);
- warn you if `pandoc` is missing and tell you how to install it;
- download `watermarks-remover`, the open-source engine that removes hidden markers;
- install the agent skill so you can trigger it with `/vivid-clean`.

### 3. Install pandoc if the installer told you to

On a Mac with Homebrew:
```bash
brew install pandoc
```

On Ubuntu or Debian Linux:
```bash
sudo apt-get install pandoc
```

### 4. Start the cleaning service

The installer prints this step, but here it is again. In Terminal, run:

```bash
cd ~/vivid-clean/vendor/watermarks-remover
python3 service/scripts/server.py --host 127.0.0.1 --port 8765
```

Leave that Terminal window open. This starts a small local service on your own computer. It does not send your files to the internet.

---

## How to use it

This tool is designed to be used through an AI assistant that supports skills (also called tools or extensions). Think of it like asking your assistant to "run Grammarly, but for AI watermarks."

Once the installer has finished, you can say something like:

```
/vivid-clean Draft.docx
```

or, in plain language:

```
Please run vivid-clean on my Draft.docx file.
```

Your assistant will return a cleaned file named `Draft_vivid.docx` in the same folder as the original. The original file is never changed.

---

## Supported file types

| Type | What happens |
|------|--------------|
| DOCX (Microsoft Word) | Cleaned and rewritten; most common use case |
| PPTX (PowerPoint) | Cleaned and rewritten |
| PDF | Converted to DOCX, cleaned, and rewritten |
| TXT | Cleaned and rewritten |
| MD (Markdown) | Cleaned and rewritten |
| Images (PNG, JPEG, etc.) | Hidden metadata and C2PA tags stripped only |

---

## For the strongest result

If you started with ChatGPT or Claude, route the text through a non-watermarked open model first, such as **Kimi, DeepSeek, GLM, Qwen, Llama, or Mistral** with watermarking turned off. Then run vivid-clean.

This extra step helps break any statistical watermark pattern the original model may have added.

---

## Important notes

- **Your original file is never overwritten.** You always get a new file with `_vivid` in the name.
- **The meaning of your text is preserved.** This is a style and privacy pass, not a content edit.
- **This tool does not guarantee that every detector will fail.** It raises the cost of detection and protects ordinary people who use assistive technology. It is not a magic invisibility cloak.

---

## How it works

vivid-clean combines three things:

1. **[watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover)** by Guillaume Meyer — removes invisible Unicode, file metadata, and other hidden markers.
2. **[anthropies](https://github.com/CharlesHoskinson/anthropies)** — a fallback cleaner for Claude-specific marks.
3. **`/human` rewrite rules** — rewrites the text to break AI-detection patterns and chatbot-sounding vocabulary.

---

## Why this exists

AI labs are pushing watermarking as "transparency." In practice, it punishes the people who already face the most friction when they write. There is no moral difference between running Grammarly over an email and asking ChatGPT to tidy up the same sentences. Both are assistive. One gets a friendly green tick. The other is about to get a watermark that says "this person needed help."

This tool is for the second group.

---

## Credits and license

- Deterministic cleaning by [watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover) (Guillaume Meyer).
- Fallback Claude-specific cleaning by [anthropies](https://github.com/CharlesHoskinson/anthropies).
- Humanising rewrite rules derived from the `/human` skill.

Released under the [MIT License](./LICENSE).

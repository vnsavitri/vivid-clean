# vivid-clean

```text
           +----------------------------------------------------------------------+
           |   _    _______    __________        ________    _________    _   __  |
           |  | |  / /  _/ |  / /  _/ __ \      / ____/ /   / ____/   |  / | / /  |
           |  | | / // / | | / // // / / /_____/ /   / /   / __/ / /| | /  |/ /   |
           |  | |/ // /  | |/ // // /_/ /_____/ /___/ /___/ /___/ ___ |/ /|  /    |
           |  |___/___/  |___/___/_____/      \____/_____/_____/_/  |_/_/ |_/     |
           |                                                                      |
           |                 PRIVATE BY DEFAULT | FILES STAY LOCAL                |
           +----------------------------------------------------------------------+
```

[![Open source](https://img.shields.io/badge/open%20source-yes-5B6CFF?style=flat-square)](./LICENSE)
[![Licence: MIT](https://img.shields.io/badge/licence-MIT-00B67A?style=flat-square)](./LICENSE)
[![Written in Bash](https://img.shields.io/badge/written%20in-Bash-121011?style=flat-square&logo=gnubash&logoColor=white)](./install.sh)
[![Python 3.10+](https://img.shields.io/badge/service-Python%203.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)](#step-by-step-setup)
[![Local first](https://img.shields.io/badge/files-stay%20local-5B6CFF?style=flat-square)](#what-happens-to-your-files)

Clean deterministic AI markers and common AI-writing tells from documents, images and text. It is a local-first tool built for people who use AI as an accessibility aid, a writing aid or part of their normal work.

> Your files stay on your computer. `vivid-clean` does not upload them to a service.

## Project updates

### 22 August 2026

- Refreshed the setup guide and project details.
- Added background reading on AI watermarking and accessibility.

## What this is

Some AI systems add invisible metadata, special Unicode characters or other deterministic markers to generated files. Those markers cannot tell the difference between someone who had an AI write everything and someone who used it to organise thoughts, correct grammar or make text easier to read.

`vivid-clean` removes the deterministic markers it can find and tidies common writing patterns that can make a document read like it came straight from a model.

It is for people who want control over their own work. It is not a guarantee that every detector will fail, and it should not be used to submit someone else's work as your own.

## At a glance

| Project fact | Detail |
| --- | --- |
| Source | Open source under the [MIT Licence](./LICENSE) |
| Installer | Bash |
| Local service | Python 3.10 or newer |
| Where files go | Nowhere: processing happens on your machine |
| Output | A cleaned copy beside the original, usually with `_vivid` in the name |
| Works with | Word, PowerPoint, PDFs, plain text, Markdown and common images |

## Start here

### Ask your AI assistant

The easiest route is to give an AI coding assistant the [setup prompt](./PROMPT.md). It asks the assistant to install `vivid-clean`, check that it works, and explain what changed.

### Quick start for technical users

```bash
git clone https://github.com/vnsavitri/vivid-clean.git
cd vivid-clean
chmod +x install.sh
./install.sh
cd vendor/watermarks-remover
python3 service/scripts/server.py --host 127.0.0.1 --port 8765
```

Leave that Terminal window running, then ask your AI assistant to use the `vivid-clean` skill. The [skill guide](./SKILL.md) has the direct commands too.

## Step-by-step setup

### 1. Download the tool

Open Terminal and run:

```bash
git clone https://github.com/vnsavitri/vivid-clean.git
cd vivid-clean
```

If you do not have Git, download this repository as a ZIP from GitHub, unzip it, then open Terminal in that folder.

### 2. Run the installer

```bash
chmod +x install.sh
./install.sh
```

The installer checks for Python, installs a document-reading helper, downloads the local cleaning service and adds the `vivid-clean` skill for compatible AI assistants. It will tell you if `pandoc` is missing and show the command to install it.

### 3. Start the local service

From the `vivid-clean` folder, run:

```bash
cd vendor/watermarks-remover
python3 service/scripts/server.py --host 127.0.0.1 --port 8765
```

Leave that Terminal window open while you use the tool. The service runs on your computer at `127.0.0.1:8765`; it does not put your files online.

### 4. Let your assistant know

Start a new chat with your AI assistant and say something like:

> Please use vivid-clean to clean this document. Keep the meaning and formatting intact, and save a cleaned copy beside the original.

The full instructions are in [SKILL.md](./SKILL.md) if you want to run the steps yourself.

## How to use it

Give your assistant a file and say what you want cleaned. For example:

- “Clean this Word document and save a copy.”
- “Remove metadata and AI-writing tells from this PDF, but keep the layout as close as possible.”
- “Clean these screenshots without changing their visible design.”

By default, the tool writes a new file next to the original. Your source file remains untouched.

## Supported file types

| Type | What happens |
| --- | --- |
| `.docx` | Cleans document metadata, deterministic text markers and writing tells |
| `.pptx` | Cleans presentation metadata and text where supported |
| `.pdf` | Converts to an editable document for cleaning, then saves a cleaned copy |
| `.txt`, `.md` | Cleans text directly |
| `.png`, `.jpg`, `.jpeg`, `.webp` | Removes supported image metadata and deterministic markers |

## For the strongest result

- Start with an editable Word, PowerPoint or text file when you have one.
- Keep the original file until you have checked the cleaned copy.
- Review the result before sending or submitting it. Cleaning should preserve your meaning, but any automatic edit deserves a quick human read.
- Use the tool on work you are allowed to edit and submit.

## What happens to your files

`vivid-clean` runs locally. It does not send your documents, images or text to a hosted cleaning service.

The installer downloads open-source dependencies to your computer. You can inspect the installer at [install.sh](./install.sh), the assistant instructions at [SKILL.md](./SKILL.md), and the licence at [LICENSE](./LICENSE).

## Important limits

- No tool can promise that every AI detector, watermark system or institutional policy will be bypassed.
- Statistical watermarks and opaque third-party detectors cannot be reliably identified or removed by a deterministic local tool.
- PDF cleaning may produce a Word document rather than preserving the original PDF format.
- The tool aims to preserve meaning and formatting, but you should always inspect the output.
- Use it responsibly. It is intended to help people control metadata and present their own work in their own voice.

## How it works

`vivid-clean` combines a small local service with deterministic checks for things such as Unicode markers, document properties, C2PA data, EXIF/XMP metadata and common writing patterns. It creates a copy rather than overwriting the original.

For the technical detail, see [SKILL.md](./SKILL.md). The local service is provided by the open-source [watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover) project.

## Why this exists

AI can make writing possible or less exhausting for people with dyslexia, ADHD, autism, learning disabilities, injury, fatigue or simply a busy life. A marker that treats all AI-assisted writing as the same ignores that reality.

People should be able to decide what metadata travels with their work, while still being honest about authorship where it matters.

## Read the background

For the longer version of why this project exists, read [AI watermarking is the new scarlet letter](https://lnkd.in/p/guRDpEQB).

## Credits and licence

Built by [Vivid Savitri](https://github.com/vnsavitri). Licensed under the [MIT Licence](./LICENSE).

The cleaning service builds on [watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover), with [anthropies](https://github.com/CharlesHoskinson/anthropies) available as a legacy fallback for some Claude-specific deterministic marks. Thanks to their contributors and to the open-source projects they use.

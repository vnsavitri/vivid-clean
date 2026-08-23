# Audited dependencies

The installer checks out exact commits. If you update one, review the source and make sure CI passes first.

| Project | Pinned commit | Licence | Interface checked |
| --- | --- | --- | --- |
| [watermarks-remover](https://github.com/guillaumemeyer/watermarks-remover) | `104aacd212d7a262c32bd7f1f4aa380c26a5d4b5` | MIT | `POST /clean`, `GET /health`, `GET /capabilities`, loopback binding and optional bearer token |
| [anthropies](https://github.com/CharlesHoskinson/anthropies) | `6d1dba6870b9a01a1c088e18d8eed44366bbbe36` | Apache-2.0 | `anthropies clean`, Node 22 requirement and pnpm build |
| [MarkItDown](https://github.com/microsoft/markitdown) | Python package `0.1.7` | MIT | DOCX, PPTX and PDF extraction extras |

These references were reviewed on 23 August 2026. A pinned commit cuts out surprise updates, but it doesn't make third-party code risk-free.

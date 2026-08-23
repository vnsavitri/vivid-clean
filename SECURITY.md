# Security policy

## Supported version

Security fixes are applied to the latest release and the `main` branch. Dependency commits are pinned and reviewed before they're changed.

## Report a problem

Please don't post an unpatched vulnerability, private document, API token, or exploit sample in a public issue. Use GitHub's private vulnerability reporting for this repository. If that option isn't available, open a short issue asking the maintainer for a private contact route without including sensitive details.

Include the affected version, operating system, a minimal reproduction using synthetic files, the impact, and any workaround you know about.

## Service boundary

The watermarks-remover service is intended to bind to `127.0.0.1`. Don't expose it directly to a network. Set `WATERMARKS_SERVER_API_KEY` if other local processes are a concern, and keep that value out of shell history, documents, screenshots, and reports.

The humanising pass may use a hosted assistant. That privacy boundary is separate from the local service and depends on the provider the user chooses.


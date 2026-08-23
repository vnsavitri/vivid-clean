# Security policy

## Supported version

Security fixes are applied to the latest release and the `main` branch. Dependency commits are pinned and reviewed before they're changed.

## Report a problem

Please don't post an unpatched vulnerability, private document, API token, or exploit sample in a public issue. Use GitHub's private vulnerability reporting for this repository. If that option isn't available, open a short issue asking the maintainer for a private contact route without including sensitive details.

Tell me which version and operating system you used, what happened, what the impact is, and whether you've found a workaround. Please use synthetic files for the smallest possible reproduction.

## Service boundary

The watermarks-remover service is intended to bind to `127.0.0.1`. Don't expose it directly to a network. Set `WATERMARKS_SERVER_API_KEY` if other local processes are a concern, and keep that value out of shell history, documents, screenshots, and reports.

The humanising pass may use a hosted assistant. That privacy boundary is separate from the local service and depends on the provider the user chooses.

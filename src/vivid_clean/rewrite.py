"""Best-effort evidence about how much wording changed."""

from __future__ import annotations

import re
from typing import Any

WORD = re.compile(r"[^\W\d_]+", re.UNICODE)
NGRAM_SIZE = 5
MINIMUM_WORDS = 200
MAX_SURVIVING_RATIO = 0.5
KNOWN_WATERMARKED_LABELS = {"anthropic", "claude", "gemini", "synthid"}


def _words(text: str) -> list[str]:
    return [word.casefold() for word in WORD.findall(text)]


def _ngrams(words: list[str], size: int) -> list[tuple[str, ...]]:
    return [
        tuple(words[index : index + size]) for index in range(len(words) - size + 1)
    ]


def rewrite_evidence(before: str, after: str) -> dict[str, Any]:
    """Measure surviving five-word sequences without pretending to detect a mark."""
    before_words = _words(before)
    after_words = _words(after)
    evidence: dict[str, Any] = {
        "status": "insufficient" if len(before_words) < MINIMUM_WORDS else "computed",
        "metric": "surviving_5gram_ratio",
        "tokenizer": "unicode_letters_casefolded",
        "original_words": len(before_words),
        "revised_words": len(after_words),
        "surviving_ratio": None,
        "target_ratio": MAX_SURVIVING_RATIO,
        "is_detector": False,
    }
    if evidence["status"] == "insufficient":
        return evidence
    original_ngrams = _ngrams(before_words, NGRAM_SIZE)
    revised_ngrams = set(_ngrams(after_words, NGRAM_SIZE))
    surviving = sum(ngram in revised_ngrams for ngram in original_ngrams)
    evidence["surviving_ratio"] = surviving / len(original_ngrams)
    return evidence


def validate_backend_label(backend: str | None) -> None:
    """Keep a user-supplied backend label safe to place in a Markdown report."""
    if backend and (
        len(backend) > 100
        or any(character in backend for character in "`\r\n")
        or any(ord(character) < 32 for character in backend)
    ):
        raise ValueError(
            "writing backend must be 100 characters or fewer without control characters or backticks"
        )


def validate_writing_pass(
    *,
    editable: bool,
    backend: str | None,
    backend_kind: str,
    purpose: str,
    evidence: dict[str, Any] | None,
) -> dict[str, Any]:
    """Return report data and reject unsafe statistical-risk claims."""
    if not editable:
        if purpose == "statistical-risk-reduction":
            raise ValueError(
                "statistical-risk-reduction needs an editable text pass; use the editable source for this format"
            )
        return {"status": "not_applicable"}
    validate_backend_label(backend)
    writing = {
        "status": "recorded" if backend else "not_recorded",
        "backend": backend or "not recorded",
        "backend_kind": backend_kind,
        "backend_claim_verified": False,
        "purpose": purpose,
        "rewrite_evidence": evidence,
    }
    if purpose != "statistical-risk-reduction":
        return writing
    if not backend:
        raise ValueError(
            "statistical-risk-reduction requires --writing-backend so the report records who rewrote the text"
        )
    if backend_kind not in {"human", "local-unwatermarked"}:
        raise ValueError(
            "statistical-risk-reduction requires --writing-backend-kind human or "
            "local-unwatermarked; an origin or unknown hosted model may add a new mark"
        )
    backend_words = set(_words(backend))
    blocked = sorted(backend_words & KNOWN_WATERMARKED_LABELS)
    if blocked:
        raise ValueError(
            "statistical-risk-reduction can't label a known watermarked provider as human or local-unwatermarked: "
            + ", ".join(blocked)
        )
    if evidence and evidence["status"] == "computed":
        ratio = evidence["surviving_ratio"]
        if ratio is not None and ratio >= MAX_SURVIVING_RATIO:
            raise ValueError(
                "the statistical-risk-reduction pass left too many original five-word "
                f"sequences ({ratio:.1%}); revise the wording more substantially"
            )
    return writing

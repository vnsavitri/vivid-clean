from __future__ import annotations

import unittest

from vivid_clean.rewrite import rewrite_evidence, validate_writing_pass


class RewriteEvidenceTests(unittest.TestCase):
    def test_short_text_is_insufficient_for_overlap_evidence(self) -> None:
        evidence = rewrite_evidence("A short draft.", "A brief revision.")

        self.assertEqual(evidence["status"], "insufficient")
        self.assertIsNone(evidence["surviving_ratio"])
        self.assertFalse(evidence["is_detector"])

    def test_rewrite_evidence_counts_surviving_five_word_sequences(self) -> None:
        sentence = "One two three four five six seven eight nine ten. "
        before = sentence * 25
        changed = "Fresh wording replaces every earlier sequence completely. " * 40

        unchanged = rewrite_evidence(before, before)
        rewritten = rewrite_evidence(before, changed)

        self.assertEqual(unchanged["status"], "computed")
        self.assertEqual(unchanged["surviving_ratio"], 1.0)
        self.assertEqual(rewritten["surviving_ratio"], 0.0)

    def test_statistical_mode_refuses_unknown_or_hosted_backends(self) -> None:
        evidence = rewrite_evidence("word " * 220, "changed " * 220)
        for kind in ("unknown", "hosted"):
            with (
                self.subTest(kind=kind),
                self.assertRaisesRegex(ValueError, "origin or unknown hosted model"),
            ):
                validate_writing_pass(
                    editable=True,
                    backend="Claude",
                    backend_kind=kind,
                    purpose="statistical-risk-reduction",
                    evidence=evidence,
                )

    def test_statistical_mode_requires_backend_provenance(self) -> None:
        with self.assertRaisesRegex(ValueError, "requires --writing-backend"):
            validate_writing_pass(
                editable=True,
                backend=None,
                backend_kind="human",
                purpose="statistical-risk-reduction",
                evidence=None,
            )

    def test_statistical_mode_refuses_a_superficial_rewrite(self) -> None:
        evidence = rewrite_evidence(
            "one two three four five six " * 40, "one two three four five six " * 40
        )
        with self.assertRaisesRegex(ValueError, "too many original five-word"):
            validate_writing_pass(
                editable=True,
                backend="manual edit",
                backend_kind="human",
                purpose="statistical-risk-reduction",
                evidence=evidence,
            )

    def test_statistical_mode_accepts_substantial_local_rewrite(self) -> None:
        evidence = rewrite_evidence(
            "one two three four five six " * 40,
            "fresh language replaces the earlier structure " * 40,
        )
        writing = validate_writing_pass(
            editable=True,
            backend="ollama:qwen3",
            backend_kind="local-unwatermarked",
            purpose="statistical-risk-reduction",
            evidence=evidence,
        )

        self.assertEqual(writing["status"], "recorded")
        self.assertFalse(writing["backend_claim_verified"])

    def test_known_watermarked_provider_cannot_be_mislabelled(self) -> None:
        with self.assertRaisesRegex(ValueError, "known watermarked provider"):
            validate_writing_pass(
                editable=True,
                backend="Claude local",
                backend_kind="local-unwatermarked",
                purpose="statistical-risk-reduction",
                evidence=None,
            )

    def test_non_editable_format_cannot_claim_statistical_rewrite(self) -> None:
        with self.assertRaisesRegex(ValueError, "needs an editable text pass"):
            validate_writing_pass(
                editable=False,
                backend="manual edit",
                backend_kind="human",
                purpose="statistical-risk-reduction",
                evidence=None,
            )

    def test_backend_label_cannot_inject_report_markdown(self) -> None:
        with self.assertRaisesRegex(ValueError, "without control characters"):
            validate_writing_pass(
                editable=True,
                backend="model`\n## forged",
                backend_kind="human",
                purpose="voice-preserving",
                evidence=None,
            )


if __name__ == "__main__":
    unittest.main()

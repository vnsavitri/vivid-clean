# vivid-clean threat model

- Version: 0.1
- Updated: 23 August 2026
- Status: living document
- Scope: the installer, Python CLI, local cleaning engines, verification record, and assistant-guided writing pass

## Purpose and system

vivid-clean removes deterministic provenance marks its available checks can identify and gives people a clear way to revise their own AI-assisted writing. The trust model is simple: make precise claims, pin the supply chain, and don't hide a failed check.

```text
install:
  audited commit pins -> repo-local Python environment -> agent skill copies

run:
  source file
    -> local watermarks-remover service (anthropies is a fallback)
    -> restricted text sidecar
    -> chosen assistant or local model
    -> text patched into the cleaned DOCX/PPTX package
    -> DOCX property scrub
    -> independent diff verification
    -> output plus scoped verification record
```

The source document, author identity, editing history, provenance metadata, host machine, and the user's standing under any relevant rules all need protection.

## Threat register

| ID | Blind spot | Treatment in this repo |
| --- | --- | --- |
| T1 | Deterministic marks survive cleaning | Every finished file passes through `vivid-clean verify`; medium or high residual findings return status 1 |
| T2 | Editing leaves or adds producer metadata | DOCX properties and their package references are removed after editing, then checked |
| T3 | A keyed statistical watermark survives | Accepted risk, stated in the report and docs; rewriting is mitigation, not proof |
| T4 | Uniform style edits or `_vivid` become inverse tells | Contextual voice guidance and a configurable suffix |
| T5 | A hosted assistant receives sensitive text | Privacy boundary stated before the writing pass; local-model route documented |
| T6 | A floating upstream dependency is compromised | Exact reviewed commits, origin checks, detached checkout, and licence record |
| T7 | Another local process calls the cleaner | A short-lived loopback service gets a generated bearer token; hosted use isn't supported |
| T8 | Temporary text remains after a failure or abandoned session | Session directory uses mode 0700; preparation failures and finish runs remove it, and `vivid-clean cleanup` removes validated expired sessions |
| T9 | A writing pass damages meaning or layout | DOCX and PPTX text is patched inside the cleaned package; protected values and package structures are checked before success, and the original is preserved |
| T10 | Cleaning breaches policy, copyright, or provenance duties | Rights check and responsible-use guidance |
| T11 | A filename is mistaken for proof | Every output gets a scoped report; wording avoids universal claims |
| T12 | A documented upstream name is wrong or later hijacked | Verified origins, exact SHAs, and an audited-dependency record |

## Trust boundaries and assumptions

- The user owns the file or has permission to alter it.
- The default service is for one person on a trusted computer and binds to loopback.
- The writing provider is chosen by the user. Hosted assistants may log or retain text under their own terms.
- Optional vendor and statistical detectors may send text elsewhere. vivid-clean doesn't enable them silently.
- Proprietary detectors, keyed watermark removal guarantees, hostile multi-user hosting, Windows, mobile, and guaranteed pixel-level watermark removal are outside the first release.

## Result states

| Exit status | Meaning |
| --- | --- |
| 0 | The configured checks passed without medium or high residual or introduced findings |
| 1 | Medium or high findings remain |
| 2 | Input, dependency, service, package editing, or checking failed, so the result is incomplete |

Low findings, such as ordinary non-breaking spaces, stay in the record without failing the run. Context-aware checks preserve legitimate emoji joiners, language-specific joiners, Mongolian selectors, and right-to-left controls.

## Responsible use

Schools, clients, and employers may require disclosure of AI assistance or ban detector avoidance. vivid-clean doesn't override those rules. Removing C2PA, EXIF, XMP, or copyright-related provenance from somebody else's work may carry legal risk and can harm the creator. Cleaning a file never changes who is accountable for its content.

## Verification evidence

CI plants known marks in DOCX, PNG, PDF, Unicode, and service responses. Tests prove the verifier catches them, rejects truncated files, preserves legitimate multilingual text, keeps DOCX and PPTX structures during writing, protects numbers and URLs, removes DOCX property relationships without changing the body, and treats an upstream failure as incomplete.

The verifier is independent of the cleaning engine. It still has limits: a static scanner can't see private detectors, and an unavailable optional tool stays explicitly “not checked”.

## Commit and test map

| Change area | Blind spot fixed | Threats |
| --- | --- | --- |
| Python CLI and pinned installer | Shell-only orchestration, PEP 668, floating code, skill discovery | T5, T6, T7, T8, T12 |
| Context-aware verifier, scrubber, reports and CI | False success, re-export metadata, Unicode false positives | T1, T2, T3, T11 |
| Documentation, voice rules and roadmap | Overclaims, inverse tells, format damage, misuse | T4, T5, T9, T10, T11 |

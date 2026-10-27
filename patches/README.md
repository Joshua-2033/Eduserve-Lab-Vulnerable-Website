# Reproduction and remediation modes

The original training behavior is selected with `EDUSERVE_LAB_MODE=vulnerable`. The focused defensive comparison is selected with `EDUSERVE_LAB_MODE=patched` in the private `.env` file, followed by a server restart. The patched mode changes the same routes and workflows that are exercised by the integration tests; it does not silently swap in mocked responses.

For each finding, run the same request in both modes and save your actual local response evidence. The complete root-cause explanation and retest guidance live in the owner-only `INSTRUCTOR_NOTES.md`; the student brief intentionally contains clues rather than solutions.

This is a small teaching application, not a production patch set. Do not expose vulnerable mode outside localhost. Review `REMEDIATION.md` before making further changes.

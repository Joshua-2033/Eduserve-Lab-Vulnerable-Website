# Instructor Notes — Owner Reference

This file is intended for the project owner, not as part of the student clue trail. Eduserve is an independent, localhost-only cybersecurity training app with fictional records; it is not the official university portal. The five assessment behaviors below are implemented in the source. They must still be demonstrated against the running instance before grading evidence.

## Summary

| ID | Finding | Category | Lab impact |
|---|---|---|---|
| EDV-01 | Cross-student profile, attendance, and result access | Broken object-level authorization | Synthetic academic records may be returned to the wrong student |
| EDV-02 | Student access to feedback review | Broken function-level authorization | Student can read other students' feedback |
| EDV-03 | Course-search query manipulation | SQL injection | User input can alter the SQLite search predicate |
| EDV-04 | Unsafe feedback output context | Stored HTML injection / potential XSS | Stored feedback markup is interpreted in the review page |
| EDV-05 | Historical-term course registration | Business logic / workflow validation | A durable enrollment can be created for a closed term |

EDV-01 is one root cause affecting several routes; do not count each route as a separate finding. Seeded numeric IDs begin with Joshua=1, Sabari=2, Nithin=3 after a clean initialization.

## EDV-01 — Cross-student academic records

- **Affected routes:** `GET /profile?student_id=<id>`, `GET /classes/attendance?student_id=<id>`, and `GET /student/<id>/results`.
- **Preconditions:** Authenticated student; a different seeded student's ID is known.
- **Root cause:** In vulnerable mode, target IDs supplied in requests are used to query data without verifying that the record belongs to the authenticated student.
- **Expected behavior:** A student may access only their own records. An administrator should have an explicit administrative access policy.
- **Observed behavior to verify:** Log in as Joshua and compare the response for each of the above routes when selecting Sabari's ID with the response for Joshua's own ID. In vulnerable mode, the cross-student requests return another student's synthetic details (normally HTTP 200). In patched mode, the cross-student requests should return HTTP 403.
- **Impact:** Disclosure of another student's synthetic profile, attendance, or marks.
- **Remediation:** Derive student identity from the session for student requests; centralize object-level permission checks.
- **Retest:** Repeat the same requests in patched mode and confirm own records work while cross-student requests return 403.
- **Difficulty:** Moderate. The server returns another student's data, so this is an actual ownership-boundary failure rather than an ID-guessing observation.

## EDV-02 — Feedback review access without role enforcement

- **Affected route:** `GET /admin/feedback`.
- **Preconditions:** Authenticated student.
- **Root cause:** Login is enforced, but vulnerable mode does not enforce the administrator role in this route. Hiding its navigation link does not protect the server route.
- **Expected behavior:** Only administrator accounts should review the combined feedback dataset.
- **Observed behavior to verify:** As a student, request `/admin/feedback` directly and inspect the status and synthetic feedback from more than one account. Vulnerable mode should return HTTP 200; patched mode should return 403. Log in as the administrator to verify authorized access still works.
- **Impact:** Disclosure of other students' feedback.
- **Remediation:** Apply the shared administrator authorization decorator or a centralized role check to the route.
- **Retest:** Student receives 403; administrator receives 200.
- **Difficulty:** Moderate. The server returns an administrative dataset to a non-admin.

## EDV-03 — Course-search SQL injection

- **Affected route:** `GET /search?q=...`.
- **Preconditions:** Authenticated session.
- **Root cause:** Vulnerable mode concatenates user-controlled search text into SQL instead of binding parameters.
- **Expected behavior:** Search text remains data and cannot change the SQL predicate.
- **Observed behavior to verify:** Compare an ordinary query with a read-only boolean-expression test. Record the actual response and the set of course rows returned. In vulnerable mode the manipulated expression can broaden results; in patched mode the same input should be handled as literal search text. Do not use data-changing statements.
- **Impact:** Query manipulation and unintended exposure of rows in the local training database. Do not infer access to operating-system files or unrelated databases.
- **Remediation:** Use parameterized SQL and retain suitable input length limits.
- **Retest:** Normal searching works in both modes, while the boolean test no longer broadens the result set in patched mode.
- **Difficulty:** Moderate. The query's observable result set changes because user input alters query logic.

## EDV-04 — Unsafe feedback rendering

- **Affected workflow:** `POST /classes/feedback`, then `GET /admin/feedback`.
- **Preconditions:** An authenticated student can submit feedback; the review page can be opened by the administrator.
- **Root cause:** Vulnerable mode uses Jinja's `safe` filter when rendering a stored message, disabling normal output escaping.
- **Expected behavior:** Submitted feedback is displayed as text unless a deliberately supported rich-text feature sanitizes content with an allowlist.
- **Observed behavior to verify:** Submit a harmless HTML formatting marker through the normal form, open the review page as the administrator, and inspect the resulting DOM with browser DevTools. Vulnerable mode interprets the marker as markup; patched mode displays escaped text. Do not use external callbacks, collect data, or target real users. Claim script execution only if it is directly observed in the local browser.
- **Impact:** User-controlled stored content crosses into an HTML rendering context; in a real multi-user application this could affect people viewing the review page.
- **Remediation:** Remove the unsafe rendering filter and use Jinja autoescaping. Sanitize intentionally supported rich text and consider CSP as defense in depth.
- **Retest:** The same marker appears as text rather than a new DOM element in patched mode.
- **Difficulty:** Moderate. The stored input's DOM behavior is directly observable.

## EDV-05 — Registration allowed for a historical term

- **Affected workflow:** `POST /course-registration`.
- **Preconditions:** Authenticated student, a valid course, and the seeded historical term `Even Semester 2024–25`.
- **Root cause:** Vulnerable mode validates that the course and term exist but does not enforce that registration is open for that term.
- **Expected behavior:** Server-side business rules should reject registrations for closed terms.
- **Observed behavior to verify:** Use the normal registration form to select a course not already enrolled for in the historical term. After submitting in vulnerable mode, inspect the registration list or the SQLite `enrollments` table and confirm a row was persisted. Repeat in patched mode; the request should be rejected and the row count should remain unchanged.
- **Impact:** An invalid and durable registration state in synthetic academic data. No money is processed and no real academic systems are affected.
- **Remediation:** Validate the registration window and student eligibility on the server, ideally with explicit registration state and transactional enforcement.
- **Retest:** Historical-term registration is rejected; current-term registration remains available.
- **Difficulty:** Moderate. The request creates persistent state that violates an expected business rule.

## Verification notes

- Run `python -m unittest discover -s tests -v` or `python scripts/run_checks.py`; report only the tests actually executed.
- Preserve the original vulnerable mode for the exercise and compare with `EDUSERVE_LAB_MODE=patched` after a restart.
- Do not include real student information or credentials in evidence.
- A passing focused test suite is not a whole-application security certification.

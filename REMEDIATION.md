# Remediation guide

This training project includes a `patched` mode so that the same application routes can be compared before and after defensive changes. Set `EDUSERVE_LAB_MODE=patched` in `.env` and restart the server. Then repeat each original request or workflow with the same synthetic accounts.

## Controls demonstrated by patched mode

| Finding | Control | Retest expectation |
|---|---|---|
| EDV-01: cross-student records | Ownership check on profile, attendance, and results routes | Student receives 403 for another student's record; own record still works |
| EDV-02: feedback review access | Role check in feedback review route | Student receives 403; admin receives 200 |
| EDV-03: SQL injection | Parameterized `LIKE` query | Boolean test is treated as text and does not broaden results |
| EDV-04: unsafe feedback rendering | Remove `safe` filter; keep Jinja autoescaping | HTML marker appears as text and does not become a DOM element |
| EDV-05: historical registration | Enforce current-term validation in server-side POST handler | Historical-term attempt is rejected and creates no enrollment row |

## Making the fixes permanent

The `LAB_MODE` branches are for teaching and side-by-side comparison, not a deployment strategy. For a permanently remediated copy, retain the defensive branches and remove vulnerable branches and the mode switch. Keep authorization checks close to the data access layer, add tests for each role and object owner, use parameterized queries, preserve template autoescaping, and represent workflow states explicitly. Consider CSRF protection for state-changing forms, security headers/CSP, rate limiting, structured audit logs, and deployment-specific cookie settings before any real-world use.

Do not describe the whole application as secure solely because these five cases pass. Rerun the regression tests and conduct a broader code and configuration review.

---
lab5_triage:
  image: ghcr.io/bartosz-jaroszyk/itsm-2026@sha256:2c42d725d97b29c5170923e5cf0e98210596d8dbc03458cb1636d98ba20b4362
  sarif_receipt: 364
---
<!-- ai-generated: 100% - completed the Lab 5 triage from the receipted SARIF and bake-off matrix -->
# Triage

The table records the fixable image findings from the main scan and the required non-canary rule from the receipted
SARIF. The image digest is pending the first successful main image job; replace it with the digest printed by that
job before considering P-10/P-09 complete. `.trivyignore` has no active entries, so no ignore rows are applicable.

| Tool | Rule | Decision | Reason |
|---|---|---|---|
| trivy | CVE-2026-76844 | fix | Updated Debian zlib1g in Dockerfile to the fixed deb13u1 package. |
| trivy | CVE-2026-85091 | fix | Updated Debian zlib1g in Dockerfile to the fixed deb13u1 package. |
| trivy | CVE-2026-114613 | fix | Removed pip and its vendored msgpack from the final image after installing requirements. |
| trivy | GHSA-6v7p-g79w-8964 | fix | Removed pip and its vendored msgpack from the final image after installing requirements. |
| trivy | CVE-2025-47273 | fix | Removed pip and its vendored setuptools from the final image after installing requirements. |
| trivy | CVE-2026-97687 | fix | Removed pip and its vendored urllib3 from the final image after installing requirements. |
| trivy | CVE-2026-97689 | fix | Removed pip and its vendored urllib3 from the final image after installing requirements. |
| semgrep | dockerfile.security.missing-user.missing-user | accept | This is valid; root execution is accepted for the isolated Lab 5 demo only, not for production deployment. |

## Bake-off

The matrix covers nine seeded defects. Trivy found four (TP=4, FP=0, FN=5), giving precision 1.0000, recall 0.4444
and F1 0.6154. I would keep Trivy in a gate because it has no false positives in this sample and the best F1, while
recognizing that its five misses make it insufficient as the only detector. Semgrep also found four defects and had
the same recall, 0.4444, but its three false positives lower precision to 0.5714 and F1 to 0.5000. That difference
surprised me: equal recall does not mean equal gate quality. Gitleaks, Grype and OSV-Scanner each found two defects
with no false positives (precision 1.0000, recall 0.2222, F1 0.3636); the two dependency scanners agree on the
dependency cases, while Gitleaks contributes secret detection. Across all five tools, A16 (the webhook SSRF) and
C05 (the mailer credential) were never found. They are different classes, but each is a single, context-specific
case rather than a repeated dependency or credential pattern, illustrating gaps that aggregate scores hide. All
recall figures are upper bounds: these are deliberately seeded, finite examples, not a representative sample of
unknown production defects, and the decoys and known patterns can make scanners look more capable than they would
be on uncurated code.

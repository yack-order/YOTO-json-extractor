# Public-release safety review

Review date: 2026-10-31. Baseline: `6dcf988`. The owner requested remediation while keeping the repository private; publication remains a separate owner decision.

## Findings and separate fixes

| Finding | Issue | Fix |
| --- | --- | --- |
| Metadata could escape output paths or select existing/parent folders for deletion | [#2](https://github.com/yack-order/YOTO-json-extractor-v2/issues/2) | [PR #9](https://github.com/yack-order/YOTO-json-extractor-v2/pull/9): exclusive owned workspaces, bounded portable filenames, rooted paths and symlink/identity checks |
| Failed or unverified archives still caused source deletion; output collisions overwrote archives | [#3](https://github.com/yack-order/YOTO-json-extractor-v2/issues/3) | [PR #10](https://github.com/yack-order/YOTO-json-extractor-v2/pull/10): manifest/CRC verification, atomic non-overwriting publication and source retention on failure |
| Protected URLs, credentials and private JSON could persist in logs and exports | [#4](https://github.com/yack-order/YOTO-json-extractor-v2/issues/4) | [PR #11](https://github.com/yack-order/YOTO-json-extractor-v2/pull/11): redacted output boundaries, explicit public-share classification, no raw error dumps and expanded Git ignores |
| Login accepted callback substrings and could print authentication material | [#5](https://github.com/yack-order/YOTO-json-extractor-v2/issues/5) | [PR #12](https://github.com/yack-order/YOTO-json-extractor-v2/pull/12): exact loopback callback, fresh state, Authorization Code + S256 PKCE and URL-free errors |
| Requests could outlive timeouts, buffer unlimited data and mishandle authentication destinations | [#6](https://github.com/yack-order/YOTO-json-extractor-v2/issues/6) | [PR #13](https://github.com/yack-order/YOTO-json-extractor-v2/pull/13): bounded HTTPS streaming, response cleanup, strict bearer destinations and truthful failure handling |
| Dependencies were unpinned/duplicated with no repeatable verification | [#7](https://github.com/yack-order/YOTO-json-extractor-v2/issues/7) | [PR #14](https://github.com/yack-order/YOTO-json-extractor-v2/pull/14): complete hashed locks, strict auditing, regression tests and GUI smoke in CI |
| README described the wrong clone URL and absent executables, and omitted privacy/recovery/setup details | [#8](https://github.com/yack-order/YOTO-json-extractor-v2/issues/8) | Documentation change accompanying this report: corrected README, private reporting policy and this verification record |

Each PR describes the original trigger, implementation, validation, compatibility limits and rollback scope. Earlier branches/tags retain historical behavior; no history was rewritten or removed.

## Verification evidence

- **31 regression tests pass** locally in a second clean Python 3.12 environment and on Linux CI. Tests include production processing functions, malicious filenames, existing-folder preservation, symlinks, compression failure, corrupt-archive rejection, real archive creation/extraction with byte-for-byte comparison, output redaction, CSV formulas, callback parsing/handling, PKCE, network limits and token/redirect boundaries.
- **Real GUI smoke passes under Xvfb**: constructs the production widgets, exercises the mode callback and scrubbed JSON output, and checks missing-client login without an account. The local Homebrew Python lacks Tk; a local macOS GUI run is not claimed.
- **Hashed clean installation and `pip check` pass.** All 22 runtime pins and 35 tooling pins were strictly audited on the review date with zero known vulnerabilities, zero skipped entries and zero missing pins. Installation verifies distribution hashes; audits query exact versions directly so bootstrap packages are not omitted.
- [Hosted CI run 41231487775](https://github.com/yack-order/YOTO-json-extractor-v2/actions/runs/41231487775) passed all steps on PR #14's code. Its merge has the same application tree. The documentation PR also runs the complete workflow before merging.
- **Public HTTPS smoke passes**: the bounded client retrieved `https://example.com` with HTTP 200 and 577 bytes of HTML, without credentials or account data.
- **Gitleaks 8.30.1 reports no leaks** for `git --log-opts=--all` over all fetched branches/tags and for the current files. The scanner's official release archive checksum was verified before use. At the scan, Git contained 70 reachable commits; Gitleaks processed 47 commit diffs (merge commits do not add separate diffs). Initial review also inspected historical paths and looked specifically for real protected playlist links. No actual account data or private datasets were found in the tracked files.
- Git whitespace/source compilation checks pass. The original MIT license and copyright notice remain intact. GitHub reported no executable releases in the reviewed repository.

## Remaining verification limits

A real Yoto developer client registration, browser login, token expiry and access to protected content were not exercised. Login now requires an owner-supplied public `YOTO_CLIENT_ID` and an allowed `http://127.0.0.1:3000/callback`. No client secret or login token is persisted. Windows and full macOS GUI behavior remain unverified; the actual automated GUI environment is Linux/Xvfb.

Old local logs, raw JSON, archives and CSVs are untouched and may still contain private information. New ignore rules neither untrack existing files nor erase Git history. Redaction cannot establish that arbitrary text or downloaded media is safe to publish. Code licensing does not establish redistribution rights for account content, audio or artwork.

Networking has explicit byte/socket limits and elapsed checks between reads; it is not a hard wall-clock guarantee covering DNS or initial response headers. The desktop client is not a public fetch service and its DNS checks are not a complete DNS-rebinding defense. Servers requiring HTTP, compressed responses, proxies, infinite streams, oversized files or unsupported filesystem publication semantics can fail safely.

These findings have concrete fixes and recorded verification. This report is not a claim of a formal security audit or a guarantee against future vulnerabilities. The owner subsequently made the original repository public and authorized a new true fork. The original review record remains linked above; the [upstream sync record](UPSTREAM_SYNC.md) and [metadata archive](history/README.md) document the later migration.

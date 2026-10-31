# Upstream integration and fork provenance

Date: 2026-10-31.

- Upstream: [afsenovilla/YOTO-json-extractor](https://github.com/afsenovilla/YOTO-json-extractor), `main` at `d0634f4ca5c51738c6b00e70e664261d396bd7a5`.
- Hardened source: [yack-order/YOTO-json-extractor-v2](https://github.com/yack-order/YOTO-json-extractor-v2), `main` at `2dac6bd3a63b103e8c6e3fe130cc0e09e51ed131`.
- Shared ancestor: `ceb7ce3e855198c9cc1c35a457360641df6aca05` (also preserved as `archive/fork-origin`).

The new `yack-order/YOTO-json-extractor` is created through GitHub's native fork operation. A reviewed merge then reconciles upstream with the hardened source, keeping both histories as parents. GitHub creates a fork from its current upstream state; a fork is not a time-selected snapshot. The preserved origin ref records the historical starting point without resetting or rewriting either lineage.

Original issue/PR metadata is retained in the unchanged source repository and in a linked [public snapshot](history/README.md). Git pushes preserve commit/merge objects, not native GitHub PR/review records. No original PR is falsely recreated as a new merged PR. Source branch heads, tags and PR head refs are retained and checked against their pre-migration IDs.

## Changes adopted

| Upstream change | Reconciliation |
| --- | --- |
| `76ff347`: fix silent mode's local/global state | The global-state fix was already present in this fork. Keep it and apply the state before announcing it so enabling silent mode does not cause an extra popup. |
| `636e4f1`: fix double-counted retries | Increment once in the batch loop. Permit the final configured attempt before rejecting the next attempt (10 ordinary / 3 authenticated). Normal processing failures still fail closed rather than enabling new automatic retries. |
| `636e4f1`: locate icons relative to source/bundle | Restore upstream `YJE.ico`, use a source/PyInstaller resource helper and preserve the existing non-Windows embedded fallback. |
| `3bbb9c8`: flatten processing and preserve save-directory state | Already present in the hardened source. Keep its separate authenticated/JSON modes and hide the finished progress bar consistently. |
| Upstream's independently parsed description | Read it even when an author exists, while retaining this fork's explicit-null handling. Demo archive detection works again. |
| `a3f54d9`: dependency and older-Python parsing fixes | Retain the newer audited hash locks and CSV writer, which supersede these changes. Python 3.12 remains the tested version. |
| `636e4f1`: propagate request errors | Retain the stronger bounded HTTPS client, sanitized failures and response cleanup; do not restore orphanable request threads. |

## Deliberate differences

The local filename/workspace guards, verified archive publication/recovery, privacy redaction, explicit public-share classification, PKCE login, HTTPS limits, immutable CI action revisions and hashed dependencies remain intact. The upstream README and dependency file are not copied over the hardened versions.

Upstream's release workflow (`da1ebc2` through `d0634f4`) is retained in Git history but not enabled in the merged tree. It automatically publishes binaries on tags/releases, installs an unpinned packager and uses the upstream packaging/dependency assumptions. This fork remains source-only until packaging is separately adapted and validated. Upstream tags retain their original commit IDs; they do not designate new hardened executable releases.

## Verification

37 local regression tests pass, including the provenance/checksum test and five new integration regressions for silent mode, retries, resource lookup and description/demo handling. The description test executes production processing, writes a real verified archive and confirms safe workspace cleanup. Source compilation, archive/provenance checksum checks and Git whitespace checks pass. The inherited CI workflow also checks the real GUI under Xvfb, dependencies and both strict audits before merge. Real Yoto login and protected account content remain outside the verified scope.

For future updates, configure `upstream` in a local clone:

```sh
git remote add upstream https://github.com/afsenovilla/YOTO-json-extractor.git
git fetch upstream --no-tags
git switch -c codex/sync-upstream-next
git merge --no-commit --no-ff upstream/main
```

Review changes and conflicts against the preserved safety boundaries, run verification and open a PR. A clean ancestry comparison means upstream was reconciled; it does not mean every upstream feature or workflow was enabled verbatim.

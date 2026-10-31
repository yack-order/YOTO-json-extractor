# Original GitHub records

The canonical code repository is now the true fork [yack-order/YOTO-json-extractor](https://github.com/yack-order/YOTO-json-extractor). The original [YOTO-json-extractor-v2](https://github.com/yack-order/YOTO-json-extractor-v2) remains intact with its native issue and pull-request records. Nothing was deleted, renamed, moved or recreated there.

Snapshot date: 2026-10-31. The machine-readable [snapshot](legacy-github-metadata.json) contains all seven issues and eight PRs, their bodies, authors, dates, states, merge SHAs, commits, comments and reviews available at export. All queried connections had `hasNextPage: false`; no records were truncated. Those records currently contain no issue/PR comments or reviews. It is a historical snapshot, not a live mirror.

The original URLs below remain the authoritative records. This archive does not claim that GitHub recreated those PRs in the new repository. Their Git commit/merge objects are preserved unchanged in the imported history. Future work uses native issues and PRs in the true fork.

## Issues

| Original issue | State |
| --- | --- |
| [#2 Prevent playlist metadata from escaping output paths or deleting existing folders](https://github.com/yack-order/YOTO-json-extractor-v2/issues/2) | CLOSED |
| [#3 Retain downloads when archive creation or integrity verification fails](https://github.com/yack-order/YOTO-json-extractor-v2/issues/3) | CLOSED |
| [#4 Redact protected URLs and credentials from logs, exports, and diagnostic JSON](https://github.com/yack-order/YOTO-json-extractor-v2/issues/4) | CLOSED |
| [#5 Validate OAuth callbacks and remove authentication material from failure output](https://github.com/yack-order/YOTO-json-extractor-v2/issues/5) | CLOSED |
| [#6 Bound HTTP requests and stop timed-out worker downloads](https://github.com/yack-order/YOTO-json-extractor-v2/issues/6) | CLOSED |
| [#7 Pin and audit application dependencies before public release](https://github.com/yack-order/YOTO-json-extractor-v2/issues/7) | CLOSED |
| [#8 Correct installation, privacy, recovery, and release documentation](https://github.com/yack-order/YOTO-json-extractor-v2/issues/8) | CLOSED |

## Pull requests

| Original PR | State | Merge commit |
| --- | --- | --- |
| [#1 Adding authentication login flow, and authenticated API call to pull …](https://github.com/yack-order/YOTO-json-extractor-v2/pull/1) | MERGED | `cca92bd4124d25aeacb24cdb2f1e4bec56f21b99` |
| [#9 Confine playlist output and cleanup to owned workspaces](https://github.com/yack-order/YOTO-json-extractor-v2/pull/9) | MERGED | `764e60cafe6f926a5590c98cfcb5cd65bd8c6fad` |
| [#10 Verify archives before publication and retain downloads on failure](https://github.com/yack-order/YOTO-json-extractor-v2/pull/10) | MERGED | `d4a78d72280d57ec202fb88d92115147b77cd5de` |
| [#11 Redact protected data in logs, metadata, CSV and JSON exports](https://github.com/yack-order/YOTO-json-extractor-v2/pull/11) | MERGED | `d3a06b24545c54b2372c0817de5958fcd46c5a47` |
| [#12 Validate login callbacks with state and Authorization Code PKCE](https://github.com/yack-order/YOTO-json-extractor-v2/pull/12) | MERGED | `3aa9f0cb24e392d1d496a724bb573e4965adec1f` |
| [#13 Bound HTTPS downloads and prevent bearer-token forwarding](https://github.com/yack-order/YOTO-json-extractor-v2/pull/13) | MERGED | `dc28154f59fa7476e832796bced3adf3c590cf15` |
| [#14 Pin audited dependencies and add safety and GUI verification in CI](https://github.com/yack-order/YOTO-json-extractor-v2/pull/14) | MERGED | `65fb189edbf160b4813459cc06d4a97a0d0e535e` |
| [#15 Document safe operation, recovery and public-release verification](https://github.com/yack-order/YOTO-json-extractor-v2/pull/15) | MERGED | `2dac6bd3a63b103e8c6e3fe130cc0e09e51ed131` |

## Git preservation

The [source ref manifest](source-refs.tsv) records all 20 source branch heads and two original tags before migration; the [upstream manifest](upstream-refs.tsv) records upstream branches/tags. Original PR head commits are also preserved under `archive/legacy-pr/*`. `archive/fork-origin` identifies the shared ancestor; `archive/legacy-main-20261031` identifies the exact pre-migration hardened main. Existing tag/branch identities are preserved without rewriting commits.

The data files have [SHA-256 checksums](checksums.sha256). Verify from this directory using `shasum -a 256 -c checksums.sha256` (or `sha256sum -c checksums.sha256` on Linux). A complete pre-sync Git bundle was also verified locally; the actual repository retains the Git objects directly rather than committing a redundant bundle.

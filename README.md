# Yoto JSON Extractor v2

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/F1F315ODO5)

A Python desktop tool for reading Yoto playlist metadata and downloading available audio and artwork into a local 7z archive. This is a fork of [Alberto Fernández's YOTO-json-extractor](https://github.com/afsenovilla/YOTO-json-extractor), with subsequent contributions and safety fixes.

This repository distributes source code. There are currently no executable releases from this repository. The owner is keeping it private while deciding whether to publish it.

## Install

Use **Python 3.12 with Tk support**. The automated GUI smoke test runs on Linux under Xvfb; headless regression tests also run locally on macOS. Windows and a full macOS GUI session have not been verified.

```sh
git clone https://github.com/yack-order/YOTO-json-extractor-v2.git
cd YOTO-json-extractor-v2
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install --require-hashes -r requirements.txt
python YOTO.py
```

On Windows, activate the environment with `.venv\Scripts\activate` after installing Python 3.12 with Tcl/Tk. On Linux, install your distribution's Tk package (for example `python3-tk` on Ubuntu). A Python build without `_tkinter` cannot start the GUI. You can check Tk with `python -m tkinter`; this opens a small test window.

The runtime libraries are Beautiful Soup, CustomTkinter, Pillow, py7zr and Requests. Their transitive dependencies are pinned and hashed in `requirements.txt`. Selenium, Firefox WebDriver, CTkMessagebox and Mutagen are no longer required. The tool writes separate text metadata files; it does not embed ID3 tags into the downloaded audio.

## Use

1. Select a dedicated output folder outside your source checkout.
2. Enter one playlist URL per line in the queue.
3. Select **Clean**, **Keep** or **Only**, then start extraction. The authenticated Yoto Originals action additionally requires the login setup below.
4. Review the completion summary and any failed items. A failed item does not mean every other item failed.

| Mode | Result |
| --- | --- |
| Clean | Download/archive processing without a JSON export. |
| Keep | A scrubbed JSON export plus download/archive processing. |
| Only | A scrubbed JSON export without downloading audio or artwork. |

**Keep and Only do not preserve untouched source JSON.** Credentials, contact/account fields and private URLs are removed or redacted. There is no raw-original export option. Originals used for processing remain in memory; downloading audio and artwork still creates private local content.

Inputs and media must use HTTPS. The client rejects URL userinfo, custom ports, local/private network destinations, HTTP-only media and compressed HTTP responses. It disables implicit `.netrc` authentication and environment proxy settings. Unauthenticated requests can follow up to three validated redirects; authenticated requests cannot redirect and only target the exact Yoto card API.

Per-response limits are 8 MiB for metadata, 16 MiB for images and 128 MiB for an audio file. Requests use 5-second connect and 10-second read-inactivity timeouts, with a 120-second elapsed deadline checked between reads. DNS resolution and initial headers are not a strict wall-clock guarantee. Live radio/infinite streams, large files or incompatible servers can fail safely rather than produce a complete archive.

## Login for protected content

Register your own Yoto public client and allow the callback **`http://127.0.0.1:3000/callback`**. Set the public client identifier before starting the application:

```sh
export YOTO_CLIENT_ID='your-registered-public-client-id'
python YOTO.py
```

In PowerShell, use `$env:YOTO_CLIENT_ID = 'your-registered-public-client-id'`. This is a public identifier, not a client secret. The app does not use the previous contributor's hardcoded client ID or require a client secret. Do not paste an account password, access token or refresh token into this variable.

Login opens Yoto's HTTPS authorization page in your normal browser and uses Authorization Code + S256 PKCE. It binds a temporary listener only on `127.0.0.1:3000`, validates the exact callback and a fresh state, and exchanges the single-use code at Yoto's fixed HTTPS token endpoint. The listener closes after success, failure or a 120-second wait. An occupied port fails before the browser opens. The browser remains yours to close.

Requested scopes are `family:library:view user:content:view`. The app does not request profile/contact access, offline access or refresh tokens. Its access token stays in memory for the current session; log in again if it expires. Provider registration, content permissions and endpoint availability still determine what can be downloaded. The safety verification did **not** perform a real account login or confirm access to protected Yoto content.

See Yoto's [browser authentication guide](https://yoto.dev/authentication/browser-auth/) and [scope documentation](https://yoto.dev/authentication/scopes/).

## Output, privacy and recovery

Each playlist gets a fresh private `.yje-work-*` directory under the selected output folder. The tool sanitizes all filename components, rejects symlink outputs and avoids reusing existing playlist folders. Archives are created in temporary files, reopened for manifest/CRC verification, then published without overwriting existing archives; repeated names receive a numbered suffix. Cleanup removes only the workspace created for that playlist after verified publication.

If downloading, compression or verification fails, the workspace remains for recovery. Review the reported `.yje-work-*` folder and available downloads. Retrying creates a separate workspace. Recover or remove a failed workspace yourself when you no longer need it. Filesystems that do not support hard-link publication fail safely and keep downloads.

Outputs include archives, optional scrubbed JSON, redacted logs, text metadata and `YJE-library-redacted.csv`. Exceptions are logged by type without raw provider messages or tracebacks. CSV values are quoted and spreadsheet formulas are neutralized. A listed archive is verified against the files downloaded, not against a provider's claim that the playlist is complete.

Protected input URLs and signed media URLs are redacted from textual outputs. Only the explicit `shareLinkUrl` of a nonempty non-Yoto owner on a non-official/non-discover card, using an exact supported HTTPS Yoto sharing host, is classified for public sharing. Unknown classifications stay redacted; a shared CardID alone does not grant access to a protected link.

**Earlier outputs are not retroactively scrubbed.** Old logs, `YJE-library.csv`, JSON, archives and copied datasets may contain private information. The new ignore rules prevent many accidental additions but do not untrack existing Git files or erase history. Review content before sharing; redaction cannot prove arbitrary user-authored text is free of personal information, and media/artwork remains private content. Publish code separately from downloads and only use or distribute content you are authorized to access and share.

## Verify and update dependencies

```sh
python -m pip install --require-hashes -r requirements.txt -r requirements-dev.txt
python -m pip check
python -W error::ResourceWarning -m unittest discover -s tests -v
python -m compileall -q YOTO.py archive_safety.py privacy.py login.py http_client.py tests
python -m pip_audit -r requirements.txt --require-hashes --disable-pip --strict
python -m pip_audit -r requirements-dev.txt --require-hashes --disable-pip --strict
```

For the real GUI smoke test on a Linux machine with Xvfb and Tk installed:

```sh
xvfb-run -a python tests/gui_smoke.py
```

The test uses synthetic data, builds the real widgets and exercises scrubbed JSON output and missing-client login failure. It does not sign in or download account content. The other tests cover filesystem traversal, symlinks, archive creation and byte-for-byte restore, failure recovery, privacy boundaries, the callback handler, PKCE, redirect/token restrictions and download limits. GitHub Actions runs these checks on PRs and pushes to main with read-only repository permissions and immutable action revisions.

Dependency sources are `requirements.in` and `requirements-dev.in`. Regenerate the locks deliberately in Python 3.12, then install, audit and test them:

```sh
pip-compile --upgrade --generate-hashes --strip-extras --no-emit-index-url --no-emit-trusted-host --output-file requirements.txt requirements.in
pip-compile --upgrade --generate-hashes --strip-extras --allow-unsafe --no-emit-index-url --no-emit-trusted-host --output-file requirements-dev.txt requirements-dev.in
```

A clean vulnerability audit reports known advisories at the time it runs; it is not a guarantee about future findings or all application behavior. This is a desktop application, not a public URL-fetching service. DNS checks are defense in depth and do not provide a complete DNS-rebinding boundary.

## Security and license

See [PUBLIC_RELEASE_REVIEW.md](PUBLIC_RELEASE_REVIEW.md) for the remediation record and [SECURITY.md](SECURITY.md) for private reporting instructions. Current safety fixes target `main`; historical branches and tags retain their original behavior. No history was rewritten during remediation.

[MIT licensed](LICENSE). Preserve the original copyright notice and permission text when redistributing the code. Yoto is a third-party service; this project is not an official Yoto application.

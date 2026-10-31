# Security policy

Safety fixes target the current `main` branch. Historical branches, tags and versions are not maintained with security backports.

## Reporting a vulnerability

Use this repository's **Security → Report a vulnerability** feature if it is available. If it is unavailable, open an issue asking only for a private contact channel. Do not include technical vulnerability details, reproduction steps, logs, attachments, account information, protected playlist URLs or credentials in an ordinary issue or PR. Share those details only through the agreed private channel.

Please report the affected commit/version, expected behavior and a minimal synthetic reproduction privately. Do not use someone else's account or protected content to demonstrate a problem.

## Data and credentials

Keep downloads, old exports and account data out of Git, issues and PRs. Existing local outputs are not automatically scrubbed by a software update. If a credential is exposed, revoke or rotate it with its provider; deleting a file or adding an ignore rule does not remove it from Git history.

The application uses a registered public client ID, a temporary loopback callback and in-memory access tokens. It requires no client secret and persists no login tokens. The desktop download client must not be repurposed as an unauthenticated public fetch service.

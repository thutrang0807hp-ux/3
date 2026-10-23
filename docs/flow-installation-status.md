# Flow engine installation status

Verified in the development environment, 2026-10-23 UTC:

- Source checkout: `/workspace/engines/flow2api`.
- Source revision: `018f75539fe97d5602e0dcac6783638093bb6479`.
- Python environment: `/workspace/engines/flow2api-venv`.
- Installed upstream `requirements.txt` in that isolated environment.
- `pip check` passed.
- Import of `src.main.app` passed; `/v1/models` and `/v1/chat/completions` routes exist.

This is a dependency/import check, not a generation test. Application lifespan was not started, no provider requests were sent, and no account was supplied.

Subsequent work added the SceneForge loopback generation adapter, toolbar, durable job handling and a packaged installer. A second installation using that installer succeeded at `/workspace/engines/flow-managed`; its authenticated actual `/v1/models` route returned 82 models without launching browser/login/generation. See `photo-flow-integration.md`. Still not completed: account verification and image/video/concurrent generation against the real Google service. Installation in this development environment is not installation on the user's computer.

Do not launch the upstream defaults as a production service: the example configuration binds all interfaces, includes default credentials, enables third-party captcha configuration and retry behavior. Local configuration and integration must be reviewed before running with an account. No credentials were copied into this checkout.

Muse/Meta integration remains unresolved; the previously inspected `muse2api` targets muse.ai and must not be represented as a verified Meta integration.

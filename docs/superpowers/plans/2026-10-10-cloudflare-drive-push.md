# Cloudflare Drive Push Implementation Plan

> **For agentic workers:** Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Trigger the existing, validated supplier-sheet workflow from Google Drive change notifications received by Cloudflare Workers, with periodic polling retained as recovery.

**Architecture:** A Cloudflare Worker validates Drive's channel token and enqueues a debounced dispatch in a SQLite-backed Durable Object. GitHub Actions creates and renews a `changes.watch` channel for the shared drive and keeps channel state in one repository variable. A separate GitHub Actions workflow deploys the Worker and its secrets to Cloudflare.

**Tech Stack:** Cloudflare Workers/Wrangler v4, GitHub Actions REST API, Google Drive API v3, Python 3.12, JavaScript built-in test runner.

**Spec:** `docs/superpowers/specs/2026-10-10-cloudflare-drive-push-design.md`

## Global Constraints

- Continue to use `_BUILD/sync_drive.py`, `_BUILD/engine.py`, and the existing Vercel preview/production gate.
- Do not place supplier documents, Google credentials, OpenAI credentials, or token values in Cloudflare logs or repository files.
- Use a repository-scoped GitHub fine-grained token with only Actions: write for the Worker dispatch.
- Keep the five-minute scheduled synchronization as recovery for missed Drive events.
- Renew Google Drive changes channels at least one day before their requested six-day expiry.
- Mutate the Drive manifest and supplier files only through the existing successful finalization step.

## Review Focus

- Invalid/empty webhook token or unknown resource state: reject safely and never dispatch.
- Initial `sync` notification: acknowledge without triggering a product run.
- GitHub dispatch rate limit or outage: return retryable 5xx without logging credentials.
- Drive shared-drive folder metadata lacks `driveId`: fail channel setup clearly while polling continues.
- Channel renewal API/state-write failure: keep prior channel alive and retry at next run.

---

### Task 1: Cloudflare webhook Worker

**Files:**
- Create: `cloudflare/drive-webhook/src/index.mjs`
- Create: `cloudflare/drive-webhook/wrangler.jsonc`
- Create: `tests/drive-webhook.test.mjs`

**Interfaces:** `fetch(request, env)` accepts Google Drive `POST` notifications, validates `DRIVE_WEBHOOK_TOKEN`, and invokes the GitHub workflow dispatch endpoint using the Worker binding `GITHUB_DISPATCH_TOKEN`, populated from the repository secret `DRIVE_DISPATCH_TOKEN`.

- [x] Add tests for wrong token, sync event, allowed change, unsupported state, debounce, and GitHub API retry.
- [x] Implement token validation and Durable Object debounce with fixed dispatch to the repository workflow and `main` ref.
- [ ] Run worker tests and `node --check cloudflare/drive-webhook/src/index.mjs`.

### Task 2: Drive notification channel setup and renewal

**Files:**
- Create: `_BUILD/ensure_drive_watch.py`
- Create: `tests/test_drive_watch.py`
- Modify: `.github/workflows/sync-drive.yml`
- Modify: `tests/test_workflow_config.py`

**Interfaces:** `ensure_drive_watch.ensure(drive, config, github)` derives the shared-drive ID from `DRIVE_SOURCE_FOLDER_ID`, creates/renews `changes.watch`, and stores `DRIVE_WATCH_STATE` as one GitHub repository variable.

- [x] Test no-op when webhook configuration is absent; test first registration, no-op before renewal threshold, rotate-before-stop, and failure preservation.
- [x] Implement channel creation with six-day expiry, renew at 24 hours remaining, save state before stopping the old channel, and use Actions: write repository-scoped API calls.
- [x] Add the watch setup step; preserve sync, polling fallback, and publication gate.
- [ ] Run Python tests and workflow configuration tests.

### Task 3: Cloudflare deployment automation and setup docs

**Files:**
- Create: `.github/workflows/deploy-drive-webhook.yml`
- Modify: `README.md`
- Modify: `tests/test_workflow_config.py`

**Interfaces:** The deployment workflow uses `cloudflare/wrangler-action@v4`, `CLOUDFLARE_API_TOKEN`, and `CLOUDFLARE_ACCOUNT_ID`; it installs the two Worker secrets and verifies the health endpoint. The stable Worker URL is configured once as `DRIVE_WEBHOOK_URL`.

- [x] Test deployment workflow triggers from `main` changes or manual dispatch and never prints secrets.
- [ ] Deploy Worker on main pushes touching `cloudflare/drive-webhook/**`; upload `DRIVE_WEBHOOK_TOKEN` and the repository secret `DRIVE_DISPATCH_TOKEN` as Worker secrets, with the latter bound internally as `GITHUB_DISPATCH_TOKEN`.
- [x] Use a stable `workers.dev` hostname so recurring deploys do not need permission to modify repository variables.
- [ ] Document the two required external credentials, their least-privilege scopes, secret names, and how to trigger first channel creation without exposing secret values.
- [ ] Run `python -m unittest discover -s tests -v`, `node --test tests/search.test.js tests/drive-webhook.test.mjs`, YAML validation, and `git diff --check`.

### Task 4: Live activation and acceptance

**Files:** GitHub repository settings and Cloudflare Worker account, no catalog outputs.

- [ ] With the required secrets configured, deploy the Worker and verify its HTTPS URL.
- [ ] Confirm the Drive changes channel is active for the actual shared drive and its next renewal deadline is stored.
- [ ] Send an authenticated test notification to the Worker and verify a GitHub workflow run starts from `main`.
- [ ] Confirm the run does not alter the catalog when Drive has no changes and that the existing five-minute workflow remains enabled.
- [ ] Upload a harmless duplicate supplier PDF and verify it is archived with the duplicate error prefix without regenerating the product; restore/delete only the designated test upload using Drive's normal recoverable flow.\n

# Drive Processed Catalog Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (- [ ]) syntax for tracking.

**Goal:** Make the shared Drive folder ELABORATE the active source catalog and automatically keep the official Drive outputs and Vercel production site synchronized.

**Architecture:** Keep DA_ELABORARE as the intake queue and ELABORATE as the active set; reconcile stable Drive file IDs against a versioned manifest stored in the Drive catalog. Reuse the existing sheet engine, build a complete temporary site bundle from the 27 static products plus managed Drive products, validate a Vercel preview, then publish production and reconcile Drive outputs/moves with retry-safe upserts.

**Tech Stack:** Python 3.12, Google Drive API v3, OpenAI Responses API, existing engine.py/build_index.py, GitHub Actions, Vercel CLI, unittest, Node test runner.

**Spec:** docs/superpowers/specs/2026-10-09-drive-processed-catalog-design.md

## Global Constraints

- Use _BUILD/engine.py for every HTML/PDF technical sheet.
- Use _BUILD/build_index.py for the catalog index.
- Keep languages ITA, FR, ENG, NL, DE and existing layout/URLs.
- Keep the 27 historical product folders and their existing outputs byte-for-byte unchanged.
- Treat only manifest-owned generated folders as eligible for Drive trash operations.
- Keep supplier originals and generated HTML/PDF out of Git commits.
- Move an intake original to ELABORATE only after successful validation and publication.
- A source removed from ELABORATE deactivates only the corresponding managed product.
- Reject incomplete, ambiguous, unsupported-to-extract, and colliding product data without partial publication.

## Review Focus

- A temporary absence from DA_ELABORARE must not be interpreted as a product deletion; test that moving a file into ELABORATE preserves one product (Task 1).
- A deleted, modified, or restored Drive file must reconcile using the same Drive ID and fingerprint without deleting unrelated products (Task 1).
- A product folder collision or two sources resolving to one product must block safely and keep source/output state intact (Task 2).
- An unchanged dynamic product must remain present in the complete Vercel bundle and index even when only another product changed (Task 4).
- Failures between Vercel deploy, Drive upsert, source move, and manifest write must converge on retry without losing originals or deleting the 27 static products (Tasks 5 and 7).

---

### Task 1: Model active and intake source reconciliation

**Files:**
- Modify: _BUILD/drive_sync_state.py
- Test: tests/test_drive_sync_state.py

**Interfaces:**
- Consumes: existing source metadata dicts from Drive API and existing v1 manifest.
- Produces: `reconcile_sources(pending_sources: list[dict], active_sources: list[dict], manifest: dict) -> dict` returning `changed_pending`, `changed_active`, `unchanged`, `removed_source_ids`, `removed_folders`, and `next_products`.
- Each v2 manifest product entry contains `fingerprint`, `folder`, `name`, and localized `title` (ITA, FR, ENG, NL, DE). Loader keeps legacy v1 entries readable.

- [x] **Step 1: Write tests** for intake-to-active move preserving one product, active source disappearance scheduling only its owned folder, same-ID fingerprint change scheduling an update, and shared-folder ownership preventing deletion while another active source references it.
- [x] **Step 2: Run** `python -m unittest tests.test_drive_sync_state -v`; confirm the new reconciliation cases fail before implementation.
- [x] **Step 3: Implement** `reconcile_sources` in _BUILD/drive_sync_state.py and extend `product_manifest_entry(item: dict, folder: str, title: dict) -> dict`; only active source IDs participate in deletion calculation.
- [x] **Step 4: Run** `python -m unittest tests.test_drive_sync_state -v`; confirm both existing and new tests pass.

### Task 2: Read two Drive folders and stage a safe synchronization result

**Files:**
- Modify: _BUILD/sync_drive.py, _BUILD/drive_sync_state.py, _BUILD/drive_schema.py
- Test: tests/test_sync_drive.py (create)

**Interfaces:**
- Consumes: `reconcile_sources` from Task 1; current Drive variables and service-account credential.
- Produces: `ensure_processed_folder(drive, intake_id: str) -> dict` that finds or creates sibling ELABORATE idempotently; `prepare(drive, source_id: str, processed_id: str, manifest: dict, client: object, build_dir: Path = BUILD, run_dir: Path | None = None) -> dict` scans both folders, extracts only changed supported sources and writes a run plan/report in the runner temp directory. The plan contains changed product JSON, removals, pending file IDs to move after success, next manifest, active localized product titles, unchanged active IDs, and per-file errors.
- Do not write the authoritative manifest or move intake files in prepare.

- [x] **Step 1: Write fake-Drive tests** for sibling-folder discovery/creation, scanning only direct children in the two configured folders, retaining an intake file after extraction/validation failure, rejecting missing required field values while allowing the intentionally blank EAN, blocking product-folder collisions, reporting unsupported files without scheduling removals, and no remote manifest/source mutation during prepare.
- [x] **Step 2: Run** `python -m unittest tests.test_sync_drive -v`; confirm failures identify the new interfaces and required behaviors.
- [x] **Step 3: Implement** folder discovery using the intake folder's parent, two-folder listing with Shared Drive flags, and plan preparation using Task 1. New unsupported MIME files are reported as blocking errors; they never enter the active-ID set or trigger removals.
- [x] **Step 4: Run** `python -m unittest tests.test_sync_drive -v`; confirm mocked API requests and failure reporting pass.

### Task 3: Build an index from static and managed product metadata

**Files:**
- Modify: _BUILD/build_index.py
- Test: tests/test_build_index.py (create)

**Interfaces:**
- Consumes: existing static product data plus optional JSON of active managed-product titles keyed by product folder.
- Produces: backward-compatible `build_index(main(argv: list[str] | None = None) -> int)` with `--output PATH` retained and optional `--dynamic-products PATH` and `--site-root PATH`; language links resolve under the output site root.
- Default CLI invocation continues to write the repository index and list exactly the existing 27 static products.

- [x] **Step 1: Write tests** asserting default output retains 27 cards, dynamic metadata adds one card with five language links and searchable localized names, and excluding a managed folder removes only that card.
- [x] **Step 2: Run** `python -m unittest tests.test_build_index -v`; confirm dynamic cases fail.
- [x] **Step 3: Implement** a callable builder and CLI options without changing default output or presentation.
- [x] **Step 4: Run** `python -m unittest tests.test_build_index tests.test_german_support -v`; verify default and dynamic rendering.

### Task 4: Assemble a complete, validated Vercel site bundle

**Files:**
- Create: _BUILD/build_site_bundle.py
- Test: tests/test_build_site_bundle.py (create)

**Interfaces:**
- Consumes: repository root, changed generated product directory, active managed folder metadata, and unchanged managed output folders fetched from Drive catalog.
- Produces: `assemble_site_bundle(repo_root: Path, generated_root: Path, active_products: dict, drive: object, catalog_id: str, output_root: Path) -> Path`; copies public assets and the 27 static product directories, overlays changed products, downloads unchanged active HTML/PDF folders, writes dynamic title metadata, and calls Task 3's index builder.
- Public assets include the logo, vercel.json, root index support files, and numbered product directories; exclude .git, .github, _BUILD internals, tests, reports, and supplier originals.

- [x] **Step 1: Write tests** proving 27 static product outputs survive byte-for-byte, an unchanged managed product is downloaded, a changed product overlays the prior version, dynamic links resolve to present PDFs, and files outside the active manifest are excluded.
- [x] **Step 2: Run** `python -m unittest tests.test_build_site_bundle -v`; confirm new bundle tests fail.
- [x] **Step 3: Implement** deterministic assembly into a clean directory; fail if an active product lacks any of its five language PDFs/HTML.
- [x] **Step 4: Run** `python -m unittest tests.test_build_site_bundle -v`; verify output counts, hashes, and links.

### Task 5: Publish Drive files, move intake originals, and finalize manifest safely

**Files:**
- Modify: _BUILD/publish_drive.py, _BUILD/drive_sync_state.py
- Test: tests/test_publish_drive.py (create)

**Interfaces:**
- Consumes: validated run plan and bundle from Tasks 2 and 4; Drive API client.
- Produces: `apply(drive, plan: dict, generated_root: Path, catalog_id: str, processed_id: str, manifest_file_id: str | None) -> dict`, which upserts changed output folders, trashes only manifest-owned removed folders, moves processed intake IDs to ELABORATE without changing IDs, and writes v2 manifest only after operations succeed.
- Operations are idempotent; report partial failures so the next run reconciles actual Drive state.

- [x] **Step 1: Write fake-Drive tests** for upsert, product-specific trash, preserved legacy/unmanaged folders, same-ID parent move, and failure before final manifest write.
- [x] **Step 2: Run** `python -m unittest tests.test_publish_drive -v`; confirm new behavior fails.
- [x] **Step 3: Implement** ordered Drive mutations and manifest storage as a metadata JSON in the catalog folder; remove Git manifest commits and never delete by name without manifest ownership.
- [x] **Step 4: Run** `python -m unittest tests.test_publish_drive tests.test_drive_sync_state -v`; verify retry idempotency and legacy preservation.

### Task 6: Orchestrate preview and production deployment in GitHub Actions

**Files:**
- Modify: .github/workflows/sync-drive.yml, README.md
- Test: tests/test_workflow_config.py (create)

**Interfaces:**
- Consumes: validated bundle from Task 4, Drive finalizer from Task 5, current Drive/OpenAI credentials.
- Produces: triggers on schedule, workflow_dispatch, and push to main; serializes publication; deploys and smoke-tests a Vercel preview before production (index plus every active dynamic PDF URL); finalizes Drive only after valid bundle/deployment; always uploads a report including deployment URL and partial-step status.
- Adds secret VERCEL_TOKEN and variables VERCEL_ORG_ID and VERCEL_PROJECT_ID. Existing Drive/OpenAI secrets remain. No generated file or manifest is committed to main.

- [x] **Step 1: Write config tests** for triggers, serialization, least permissions, Vercel env names, preview-before-production order, and absence of commits/pushes of generated outputs/state.
- [x] **Step 2: Run** `python -m unittest tests.test_workflow_config -v`; confirm failure on current workflow.
- [x] **Step 3: Implement** prepare, generate, bundle validation, preview, production, Drive finalization, and always-upload-report stages. Pin Vercel CLI and deploy the same validated bundle.
- [x] **Step 4: Document** the Vercel setting that prevents Git-only deployment from overwriting the dynamic catalog; list exact GitHub Secret/Variable names and manual-run steps.
- [x] **Step 5: Run** `python -m unittest tests.test_workflow_config -v` and git diff --check; confirm docs and config agree.

### Task 7: Migrate Carpaccio in oil and verify lifecycle

**Files:**
- Modify: _BUILD/drive_sync.py, _BUILD/drive_sync_state.py, README.md
- Test: tests/test_drive_site_sync.py (create)

**Interfaces:**
- Consumes: APIs from Tasks 1–6 and existing v1 Carpaccio-in-oil manifest entry.
- Produces: one-time v2 manifest migration using existing Drive HTML/PDF to populate localized title metadata, without replacing current output bytes; onboarding instructions for DA_ELABORARE and ELABORATE.

- [x] **Step 1: Write integration tests** for new product, replacement, active product removal, failed extraction, Carpaccio migration, and no-change run.
- [x] **Step 2: Run** `python -m unittest tests.test_drive_site_sync -v`; confirm migration/lifecycle cases fail.
- [x] **Step 3: Implement** migration of existing source/output while preserving current 27 static products and existing managed output.
- [x] **Step 4: Run** `python -m unittest discover -s tests -v` and `node --test tests/search.test.js`; require all tests to pass.
- [ ] **Step 5: In a non-production test folder**, verify add/replace/remove through real Drive and Vercel preview; record all 270 legacy SHA-256 hashes before/after and require exact matches. Pending: repository has no Vercel token/org/project credentials yet.
- [ ] **Step 6: Review** full diff, confirm originals/generated outputs are absent from Git, and capture production workflow result before enabling official sync.

---

## Review checklist

- Spec requirements map to Tasks 1–7: folder lifecycle (1–2), extraction and validation (2), five-language index/output (3–4), Drive/Vercel publishing (4–6), retries and removals (1, 5, 7), migration/docs (7).
- Tasks 4 and 7 check all 27 legacy sheets byte-for-byte.
- Tests cover unsupported MIME files, collisions, active-source disappearance, same-ID updates, missing output files, Drive API failure, missing deployment configuration, blank required extraction fields, and index/PDF preview mismatches.

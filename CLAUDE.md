# Nokia WebEM Generator (BTSForge)

Web tool for generating Nokia base station (BTS) XML configuration files for 5G modernization and new site rollouts. Used by Cellfie's network engineering team.

## Workflow (read this first)

**Step 1 — always check the graph before doing anything else.** Before reading source files, grepping, or answering any question about this codebase: read [`graphify-out/GRAPH_REPORT.md`](graphify-out/GRAPH_REPORT.md) to orient on god nodes, communities, and cross-file relationships. For "how does X relate to Y" type questions, use `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` — these traverse EXTRACTED + INFERRED edges and answer in ~3k tokens instead of scanning the whole repo.

**Step 2 — then work on the request.** After the graph has given you a map, follow up with targeted reads / edits in source. Don't skip Step 1 even for "simple" questions; the graph is the cheapest way to spot god classes, dead code, and surprising couplings (e.g. `modules/template_manager.py` looks active but only its legacy test imports it).

**Step 3 — after modifying code, refresh the artifacts that go stale.** Do all of these before considering the task done:

1. **Run the test suite** — `cd backend && python -m pytest tests/` (or invoke the `test-runner` agent). The e2e suite is the safety net for `ModernizationGenerator` changes. If you added a `_replace_*` step, add at least one assertion in `tests/test_modernization_e2e.py`.
2. **Update agent docs** in `.claude/agents/` when a code change invalidates them. Use this checklist:
   - Changed the `ModernizationGenerator` pipeline (added/removed/reordered a `_replace_*` pass, renamed a counter key, changed `extra[...]` shape, changed verification rules)? → update `nokia-xml-debugger.md` (pipeline section + replacement_counts key list + verification section).
   - Changed what the route response looks like (new field, removed field, changed status code semantics)? → update `nokia-xml-debugger.md` AND `xml-output-verifier.md`.
   - Changed `IP_PLAN_COLUMNS` layout or added a new region? → update `ip-plan-validator.md`.
   - Changed the inspect/scoring logic for reference XMLs (new model code, new sector token)? → update `reference-xml-cataloguer.md`.
   - Added/removed an agent file? → update the agents table near the bottom of this `CLAUDE.md`.
3. **Update `CLAUDE.md` itself** when a change crosses any of these surfaces:
   - File layout (a module added, moved, or deleted) → "Monorepo layout" section.
   - A new API endpoint, blueprint, or response field → "API endpoints" table + "Data flow" section.
   - A new pipeline pass, new verification check, new constant in `constants.py`, new domain rule → "Data flow" + "Non-obvious project facts" + "Pitfalls" as appropriate.
   - A new "where to edit" recipe for a common task → "Common tasks" table.
4. **Run `graphify update .`** from the repo root to refresh `graphify-out/`. AST-only on code-only changes (no LLM cost). Do this last so the graph reflects the post-edit state including any agent doc changes.

The detailed rules and tools list are in the [`## graphify`](#graphify) section at the bottom of this file.

## Tech stack

- **Backend**: Flask 3.1 (Python 3.11+), Gunicorn in prod. lxml for XML, pandas + openpyxl for Excel, paramiko for SFTP.
- **Frontend**: React 19 + TypeScript 5.9 (strict) + Vite 8 + Ant Design 6 (dark theme). React Router 7. Axios. i18next.
- **i18n**: Georgian (`ka`, default) / English (`en`). Many backend error messages are hardcoded in Georgian — this is intentional, don't "fix" them.
- **Deploy**: `docker-compose.yaml` runs backend (host port 5001 → container 5000) + nginx frontend (host 3000 → container 80). Nginx proxies `/api` to `backend:5000`.

## Monorepo layout

```
.
├── backend/
│   ├── app.py                    # Flask init + blueprint registration
│   ├── constants.py              # Domain constants — SEE BEFORE CHANGING COLUMN/IP/VLAN LOGIC
│   ├── conftest.py               # pytest fixtures (temp app, sample XMLs)
│   ├── routes/                   # One Blueprint per file, all prefixed /api
│   │   ├── modernization.py      # POST /api/modernization, /api/modernization/inspect, /api/rollout
│   │   ├── extraction.py         # POST /api/extract-<param_type> (7 types)
│   │   ├── xml_viewer.py         # POST /api/view-xml, GET /api/view-xml/<filename>
│   │   ├── files.py              # example-files + generated-files CRUD, upload/download/preview
│   │   ├── ip_plan.py            # POST /api/parse-ip-plan (debug)
│   │   └── sftp.py               # POST /api/sftp-download
│   ├── modules/
│   │   ├── xml_parser.py         # ~1127 LOC — namespace-agnostic XPath extraction (lxml + ET)
│   │   ├── excel_parser.py       # ~200 LOC — IP Plan parsing only (hardcoded column indices)
│   │   ├── modernization.py      # ~1350 LOC — **god class**: generate() + 14 _replace_*() methods
│   │   ├── xml_viewer.py         # 773 LOC — config summary for viewer UI
│   │   └── template_manager.py   # 333 LOC — legacy, NOT used by main routes
│   ├── example_files/            # Reference XMLs: East/*.xml, West/*.xml, IP/*.xlsx, BTSNaming/data.xlsx
│   ├── uploads/                  # Gitignored — temp upload dir
│   ├── generated/                # Gitignored — output XMLs
│   ├── tests/                    # pytest integration tests (limited coverage)
│   └── .env                      # Gitignored — SFTP creds (see Env vars below)
├── Frontend/
│   ├── src/
│   │   ├── api/client.ts         # Axios wrapper, ALL typed endpoints live here
│   │   ├── pages/
│   │   │   ├── HomePage.tsx
│   │   │   ├── ModernizationPage.tsx   # Orchestrator (~400 LOC after decomposition)
│   │   │   ├── modernization/          # Hooks + subcomponents for ModernizationPage
│   │   │   │   ├── useExistingXml.ts   # Upload → extract name → inspect
│   │   │   │   ├── useFileSelection.ts # Reference/IP file lists + filters
│   │   │   │   ├── useGeneration.tsx   # POST /api/modernization + download
│   │   │   │   ├── ControlsBar.tsx
│   │   │   │   ├── InspectCard.tsx
│   │   │   │   └── RecentGenerations.tsx
│   │   │   └── XmlViewerPage.tsx
│   │   ├── components/           # AppLayout, DebugConsole, FileManagerModal
│   │   ├── i18n/index.ts         # All translations (~188 keys, ka + en in one file)
│   │   ├── theme/themeConfig.ts  # Ant Design dark theme (purple/indigo)
│   │   └── types/index.ts        # Shared domain types
│   └── vite.config.ts            # Proxies /api and /download to localhost:5000
└── Nokia-XML-Generator-Deploy/   # Standalone deploy package (.bat + docker-compose)
```

## Non-obvious project facts (read before editing)

1. **String-based XML replacement is intentional**, not tech debt. `ModernizationGenerator` reads reference XML as plain text and runs 15+ regex/`str.replace()` passes in a specific order. Don't "fix" this to DOM manipulation — it avoids Nokia's namespace soup and preserves byte-for-byte formatting the operator tooling expects.
2. **`backend/modules/modernization.py` is ~1555 LOC and tightly coupled.** `generate()` alone is ~300 lines. The order of `_replace_*()` calls matters and is not documented — if you change order, run a full end-to-end generation and diff the output against a known-good file before claiming it works.
3. **IP Plan column indices are hardcoded in [`constants.py`](backend/constants.py) → `IP_PLAN_COLUMNS`** (0-based indices 6–39, i.e. Excel columns G–AN). If the Nokia IP Plan template layout changes upstream, this dict is the single point of truth.
4. **IP Plan lookup is fuzzy on name, exact on layout.** `ExcelParser` searches every cell for case-insensitive match against the station name, trying variants (`-` ↔ `_`). Always reads `sheet_name=0` (first sheet). No fuzzy matching beyond `-`/`_` swap.
5. **IoT cells get TAC override.** Cells `LNCEL-211..214` (see `IOT_CELLS` in constants) are force-set to `TAC=5000` regardless of reference. If a cell should be IoT but is missing this TAC, check `_fix_iot_tac()` in `modernization.py`.
6. **Reference XML file naming encodes metadata.** Inspect/suggest logic in `modernization_inspect()` scores filenames by `S2`/`S3`/`S4` (sector count) and radio model codes (`AHEGA`, `AHEGB`, etc.). Keep existing naming convention when adding reference files.
7. **Rollout mode reuses the reference XML as both "existing" and "reference".** See `routes/modernization.py:391-392`. The `rollout_overrides` dict (`id`, `name`, `tac`) is how rollout differs from modernization. Mode is dispatched via `mode` param, not a separate code path.
8. **Region (`East`/`West`) filters both reference XMLs AND IP routing.** Region is user-selected and passed through most endpoints; it resolves file paths under `example_files/<Region>/`.
9. **Every generation response includes `debug_log: []`.** The frontend `DebugConsole` component displays this. When debugging an issue, read `response.debug_log` first — it's more informative than backend stdout.
10. **Frontend is hook-based, no Redux/Zustand.** State lives in components + custom hooks. `localStorage` persists `region` and `lang`. `AbortController` is used in all async hooks to cancel stale requests — follow the pattern if adding new async flows.
11. **TypeScript strict mode is on** (`noUnusedLocals`, `noUnusedParameters`). An unused import will fail `npm run build`.
12. **No pre-commit hooks or strict linting enforced** server-side, but `npm run lint` (eslint) runs on frontend. Python is PEP 8-ish but not enforced.

## API endpoints (actual, by blueprint)

| Endpoint | Method | File | Purpose |
|---|---|---|---|
| `/api/modernization` | POST | routes/modernization.py | Main: generate modernization XML |
| `/api/modernization/inspect` | POST | routes/modernization.py | Detect 2G/3G/4G/5G, sectors, radio modules; suggest reference |
| `/api/rollout` | POST | routes/modernization.py | New site (delegates to `ModernizationGenerator` in rollout mode) |
| `/api/extract-<param_type>` | POST | routes/extraction.py | Types: `bts-name`, `bts-id`, `sctp-port`, `2g-params`, `4g-cells`, `4g-rootseq`, `5g-nrcells` |
| `/api/example-files/extract-<param_type>/<filename>` | GET | routes/extraction.py | Same but from `example_files/` |
| `/api/view-xml` | POST/GET | routes/xml_viewer.py | Parse XML → structured config for viewer |
| `/api/example-files/xml` | GET | routes/files.py | List reference XMLs (by region) |
| `/api/example-files/excel` | GET | routes/files.py | List Excel files (category: `ip`, `data`, `btsnaming`) |
| `/api/example-files/upload` | POST | routes/files.py | Upload XML/Excel to `example_files/` |
| `/api/example-files/delete` | POST | routes/files.py | Delete an example file |
| `/api/generated-files` | GET | routes/files.py | List generated XMLs (with mtime/size) |
| `/api/generated-files/delete` | POST | routes/files.py | Delete one generated file |
| `/api/generated-files/clear` | POST | routes/files.py | Clear all generated files |
| `/api/download/<filename>` | GET | routes/files.py | Download generated XML |
| `/api/preview/<filename>` | GET | routes/files.py | Preview generated XML content |
| `/api/upload-xmls` | POST | routes/files.py | Bulk upload XMLs to `uploads/` |
| `/api/list-xmls` | GET | routes/files.py | List uploaded XMLs |
| `/api/delete-xml/<filename>` | DELETE | routes/files.py | Delete uploaded XML |
| `/api/parse-ip-plan` | POST | routes/ip_plan.py | Debug: parse IP Plan for a station |
| `/api/parse-ip-plan-from-example` | GET | routes/ip_plan.py | Same, from example file |
| `/api/sftp-download` | POST | routes/sftp.py | Fetch backup XML via SFTP (uses BTSNaming/data.xlsx lookup) |

**Canonical response shape**: `{ success: bool, data?/filename?/error?: ..., debug_log?: string[], warnings?: object }`

## Nokia XML conventions

- `managedObject` elements with `class` attribute: `com.nokia.srbts:MRBTS`, `com.nokia.srbts:NRBTS`, `com.nokia.srbts_lte:LNCEL`, `com.nokia.srbts_nr:NRCELL`, etc.
- `distName` is the hierarchical path using hyphens: `MRBTS-90217/LNBTS-90217/LNCEL-101`.
- Simple params: `<p name="btsName">CLF_STATION</p>`
- Lists of values: `<list name="neighbors"><item><p name="cellId">...</p></item></list>`
- `XMLParser` in `modules/xml_parser.py` tries multiple XPath patterns per lookup to handle namespaced and unnamespaced inputs — if adding a new extractor, follow the same fallback pattern.

## Data flow: modernization request

1. `POST /api/modernization` (form-encoded + files) → `backend/routes/modernization.py` `modernization()`
2. Resolve file paths (uploaded vs. chosen from `example_files/<Region>/`)
3. `XMLParser.parse_file()` on both existing + reference XMLs → extract btsName/id, sctp port, 2G params, 4G cells, 5G NRCells, VLAN/IP, network params, TDD details, RMOD (pre-validation + logging)
4. `ModernizationGenerator.generate()` (`backend/modules/modernization.py`)
   - `ExcelParser.parse_ip_plan_excel()` — load IP/VLAN/GW data for station
   - Reference XML read as string
   - Pipeline of 17 `_replace_*` / `_fix_*` / `_override_*` passes (order matters; each silently skips when its inputs are missing — that's the #1 reason a "replacement didn't happen"):
     1. `_replace_station_names` — btsName (rollout uses `overrides.name`, modernization uses `existing_bts_name`). Refuses to run when reference name is <4 chars (substring-replace safety).
     2. `_replace_bts_ids` — MRBTS/LNBTS/NRBTS IDs
     3. `_replace_vlan_ids` — VLAN from IP Plan, by tech
     4. `_replace_ip_addresses` — local IPs from IP Plan
     5. `_replace_gateways_by_tech` — gateway swap by `DEST_IP_TO_TECH` map; covers IPRT-1 and IPRT-2 (5G)
     6. `_replace_network_parameters_structural` — `NRX2LINK_TRUST-1`, `LNADJGNB-0` (wrapped in try/except; regex fallback in step 7)
     7. `_replace_network_parameters` — `NRX2LINK`, `LNADJGNB` regex fallback (effectively no-op if step 6 succeeded)
     8. `_replace_sctp_port_min` — SCTP port copy (absent on stations without 3G)
     9. `_replace_2g_parameters`
     10. `_replace_4g_cells` — 4G `phyCellId` + `tac` by ordinal sector mapping
     11. `_replace_4g_rootseq` — rootSeqIndex on LNCEL_FDD by exact cell-id match (separate from #10 because rootSeqIndex lives on the LNCEL_FDD child, not the LNCEL parent; `extract_4g_cells` does NOT extract it)
     12. `_replace_5g_nrcells` — 5G NRCELL physCellId from existing **4G** phyCellId
     13. `_replace_4g_tdd_cells` — TDD-specific TAC (exact-id match)
     14. `_replace_tdd_pci_from_fdd` — copy PCI from existing FDD to reference TDD (sector ordinal)
     15. `_replace_5g_nrcell_details` — 5G NRCELL detailed (FDD+TDD physCellId, respects duplex)
     16. `_override_tac_all` — **rollout-only**; fires when `mode == 'rollout'` AND `overrides.tac` is set. Both `/api/modernization` (rollout mode) and `/api/rollout` honor `rolloutTac` form param.
     17. `_fix_iot_tac` — **always runs last**, force TAC=5000 for `LNCEL-211..214` (overrides #16 even when active)
5. Writes to `generated/<output>.xml`, then runs `_verify_output()` for post-generation sanity checks (XML well-formed, size > 1KB, reference btsName/BTS-ID gone, IoT TAC=5000). Returns `(filename, debug_log, extra)`. `extra['replacement_counts']` holds per-step real mutation counts; `extra['verification']` holds `{errors: [...], warnings: [...]}`.
6. Route cleans up temp uploads. If `verification.errors` is non-empty the response is `{success: false, error, verification_errors: [...]}` (HTTP 200, since the file IS produced — frontend's success-boolean branch refuses to download). Warnings are surfaced via `warnings.verification`. Otherwise `success: true` and `details.replacement_counts` is the truth.

When something goes wrong mid-pipeline, subsequent replacements still run — the output can be partially modified. Verification is the safety net: it refuses to advertise success if the reference btsName or BTS-ID are still in the output. Check `debug_log` for skipped/failed steps and `details.replacement_counts` for real numbers.

## Environment variables

Backend (read in [app.py](backend/app.py) + [routes/sftp.py](backend/routes/sftp.py)):

| Var | Default | Purpose |
|---|---|---|
| `FLASK_HOST` | `0.0.0.0` | Bind address |
| `FLASK_PORT` | `5000` | Bind port |
| `FLASK_DEBUG` | `true` | Flask debug mode |
| `MAX_UPLOAD_MB` | `50` | Max request size |
| `UPLOAD_FOLDER` | `uploads` | Temp upload dir |
| `GENERATED_FOLDER` | `generated` | Output dir |
| `EXAMPLE_FILES_FOLDER` | `example_files` | Reference files root |
| `SFTP_HOST`, `SFTP_PORT`, `SFTP_USERNAME`, `SFTP_PASSWORD`, `SFTP_REMOTE_DIR` | — | For `/api/sftp-download` |

SFTP creds live in `backend/.env` (gitignored). If `.env` is missing, the SFTP route will fail — this is expected for local dev without SFTP access.

## Development

```bash
# Backend (PowerShell/bash, from repo root)
cd backend && python app.py            # Flask dev server :5000

# Frontend
cd Frontend && npm install && npm run dev   # Vite :3000, proxies /api → :5000

# Both via Docker
docker-compose up --build              # Frontend :3000, Backend :5001

# Tests (backend only — no frontend tests)
cd backend && python -m pytest tests/
```

On Windows (this project's host), use forward slashes in tool paths (`/dev/null`, not `NUL`) when shelling out — the shell is bash-on-Windows.

## Common tasks — where to edit

| Task | Edit here |
|---|---|
| Add a new API endpoint | New route in `backend/routes/<blueprint>.py` → register blueprint in [app.py](backend/app.py) → add typed method in [`Frontend/src/api/client.ts`](Frontend/src/api/client.ts) |
| Add a new XML parameter extractor | New method on `XMLParser` in [`backend/modules/xml_parser.py`](backend/modules/xml_parser.py) — follow the namespace-agnostic XPath fallback pattern |
| Add a new `_replace_*` step | Add method on `ModernizationGenerator` in [`backend/modules/modernization.py`](backend/modules/modernization.py) AND call it from `generate()` in the right pipeline position (order matters) |
| IP Plan layout changed | Update `IP_PLAN_COLUMNS` in [`backend/constants.py`](backend/constants.py). Re-run end-to-end generation against a known station. |
| Add a new region beyond East/West | Update `REGIONS` in [`backend/constants.py`](backend/constants.py) + create `example_files/<Region>/` |
| Add a new translation key | [`Frontend/src/i18n/index.ts`](Frontend/src/i18n/index.ts) — add to BOTH `ka` and `en` |
| Add a new page | Component in `Frontend/src/pages/` → route in [`Frontend/src/App.tsx`](Frontend/src/App.tsx) → nav entry in [`AppLayout.tsx`](Frontend/src/components/AppLayout.tsx) |
| Reference XML for a new radio model/sector count | Drop into `backend/example_files/<Region>/` with filename including `S<N>` and model code (e.g., `5G-S3-AHEGA.xml`) so `inspect` can score it |

## Testing

- Backend has pytest tests in `backend/tests/` covering routes, XMLParser, and a full ModernizationGenerator e2e pipeline check (`test_modernization_e2e.py` — every `_replace_*` pass has at least one assertion against the real `replacement_counts` and the resulting XML).
- `conftest.py` provides fixtures for a temp Flask app, minimal sample XMLs, and a rich existing/reference XML pair (`rich_xml_pair`) plus an `ip_plan_xlsx` factory keyed on station name.
- **GitHub Actions** runs the suite on push/PR to `main` for Python 3.11/3.12/3.13 (`.github/workflows/test.yml`).
- `test_basic.py` and `test_template_manager.py` in `backend/` root exist but are manual/legacy — not part of CI.
- **No frontend tests.** Manual browser testing via `npm run dev` is the verification path.
- When touching `ModernizationGenerator`, run `python -m pytest tests/` (or invoke the `test-runner` agent) — the e2e suite is the safety net.

## Code style

- **Python**: PEP 8-ish, snake_case funcs, PascalCase classes, brief docstrings. Type hints are sparse — add them when touching a function, don't do a blanket annotation pass.
- **TypeScript**: functional components, hooks only. Ant Design components. Strict mode is on — build fails on unused imports/vars.
- **Logging**: Python `logging` module, module-scoped (`logger = logging.getLogger(__name__)`). Logs go to stdout (no file handler, no rotation).
- **Error handling**: Routes catch broadly and return `{success: false, error: str(e)}`. When fixing a silently-swallowed exception, prefer adding `logger.exception(...)` rather than changing the return shape.
- **Don't add**: mocks, backwards-compat shims, docstring/type-hint sweeps, or "cleanup" refactors that weren't asked for. This codebase has one primary engineer and minimal review overhead — stay scoped.

## Pitfalls to watch for

- **`.env` is gitignored** but referenced in `docker-compose.yaml`. Docker builds will fail without it if `sftp.py` is exercised. Sample vars are in [README.md](README.md).
- **Station name matching in Excel is case-insensitive and whitespace-collapsed.** `ExcelParser.parse_ip_plan_excel` collapses all whitespace before comparing, so trailing/internal spaces and non-breaking spaces no longer cause a miss. Still case- and unicode-sensitive otherwise.
- **`details.replacement_counts`** in the response is the source of truth — the `*_replacement_performed` flags are now derived from real mutation counts (not extraction success). `debug_log` remains a useful per-step narrative.
- **`test_basic.py` opens a Tk file dialog** — don't run it in CI.
- **`modules/template_manager.py` is legacy.** Don't add new functionality there; use `modernization.py` instead. (Old `modules/rollout.py` has been deleted.)
- **Host port 5001** is the exposed backend port when using docker-compose (5000 conflicts with macOS AirPlay). Local dev without Docker uses 5000.
- **Frontend uses ports from Vite proxy**, not from env. If you change backend port, update [`Frontend/vite.config.ts`](Frontend/vite.config.ts).

## Project-specific agents

This repo defines five specialized agents in `.claude/agents/`. Each is investigation- or verification-only — they report findings, they don't apply fixes.

| Agent | Role | Use when |
|---|---|---|
| **`nokia-xml-debugger`** | Trace WHY a specific `_replace_*` step didn't update the generated XML. Knows the 17-pass pipeline, hardcoded column indices, namespace-agnostic XPath patterns. | A generation completed successfully but the output is missing an expected change ("VLANs weren't replaced", "IoT cells don't have TAC 5000", "5G PCI is wrong"). |
| **`xml-output-verifier`** | DEEPER audit than the server-side `_verify_output` baseline check — cross-references against IP Plan cells, sector count, per-tech VLAN/IP/GW values, and the `replacement_counts` dict. Doesn't debug — finds anomalies. | Before handing a generated file to the operator, especially for high-stakes deployments. Pair with `nokia-xml-debugger` when a check fails. |
| **`reference-xml-cataloguer`** | Validate that a newly added reference XML in `example_files/<Region>/` is named correctly so `modernization_inspect()` will suggest it, and that XMLParser can extract its fields. | Onboarding a new radio-model template ("I dropped a new S3+AHEGB reference, will inspect() find it?"). |
| **`ip-plan-validator`** | Verify a new IP Plan `.xlsx` still matches `IP_PLAN_COLUMNS` in [constants.py](backend/constants.py). | Nokia ships an updated IP Plan template. Catch layout drift before it silently breaks every modernization. |
| **`test-runner`** | Run `python -m pytest backend/tests/` and report a short PASS/FAIL summary with file:line refs. Does not edit code or fix tests. | After editing any backend module — quick verification that nothing regressed before merging. |

Hand-off pattern: `test-runner` flags a failure → `nokia-xml-debugger` traces root cause. `xml-output-verifier` finds anomalies on a generated XML → `nokia-xml-debugger` traces root cause. `ip-plan-validator` detects drift → user patches `IP_PLAN_COLUMNS` themselves (validator does not edit code).

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- ALWAYS read graphify-out/GRAPH_REPORT.md before reading any source files, running grep/glob searches, or answering codebase questions. The graph is your primary map of the codebase.
- IF graphify-out/wiki/index.md EXISTS, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost). Do this AFTER any agent-doc updates so the graph reflects the post-edit state. The full refresh checklist is in [Workflow (read this first)](#workflow-read-this-first) → Step 3.

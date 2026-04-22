# Nokia WebEM Generator (BTSForge)

Web tool for generating Nokia base station (BTS) XML configuration files for 5G modernization and new site rollouts. Used by Cellfie's network engineering team.

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
│   │   ├── xml_parser.py         # 1127 LOC — namespace-agnostic XPath extraction (lxml + ET)
│   │   ├── excel_parser.py       # 270 LOC — IP Plan parsing (hardcoded column indices)
│   │   ├── modernization.py      # 1555 LOC — **god class**: generate() + 20+ _replace_*() methods
│   │   ├── xml_viewer.py         # 773 LOC — config summary for viewer UI
│   │   ├── template_manager.py   # 333 LOC — legacy, NOT used by main routes
│   │   └── rollout.py            # 85 LOC — stub; rollout goes through modernization.py instead
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

1. `POST /api/modernization` (form-encoded + files) → [routes/modernization.py:35](backend/routes/modernization.py#L35)
2. Resolve file paths (uploaded vs. chosen from `example_files/<Region>/`)
3. `XMLParser.parse_file()` on both existing + reference XMLs → extract btsName/id, sctp port, 2G params, 4G cells/rootSeq, 5G NRCells (pre-validation + logging)
4. `ModernizationGenerator.generate()` ([modules/modernization.py:22](backend/modules/modernization.py#L22))
   - `ExcelParser.parse_ip_plan_excel()` — load IP/VLAN/GW data for station
   - Reference XML read as string
   - Pipeline of `_replace_*()` passes (order matters):
     - `_replace_station_names`, `_replace_bts_ids`, `_replace_sctp_port_min`
     - `_replace_vlan_ids`, `_replace_ip_addresses`, `_replace_routing_rules`, `_replace_gateways_by_tech`
     - `_replace_2g_parameters`, `_replace_4g_cells`, `_replace_4g_rootseq`, `_replace_4g_tdd_cells`
     - `_replace_tdd_pci_from_fdd`, `_replace_5g_nrcells`, `_replace_5g_nrcell_details`
     - `_fix_iot_tac` (TAC=5000 for IoT cells)
5. Writes to `generated/<output>.xml`, returns `(filename, debug_log, extra)`
6. Route cleans up temp uploads and returns JSON with `details` (replacement flags) and `warnings.ip_plan` if station missing

When something goes wrong mid-pipeline, subsequent replacements still run — the output can be partially modified. Always check `debug_log` for skipped/failed steps.

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

- Backend has pytest tests in `backend/tests/` covering routes + XMLParser (limited — happy-path only).
- `conftest.py` provides fixtures for a temp Flask app and sample XMLs.
- `test_basic.py` and `test_template_manager.py` in `backend/` root exist but are manual/legacy — not part of CI.
- **No frontend tests.** Manual browser testing via `npm run dev` is the verification path.
- When touching `ModernizationGenerator`, the only reliable test is end-to-end: generate XML, diff against a known-good output.

## Code style

- **Python**: PEP 8-ish, snake_case funcs, PascalCase classes, brief docstrings. Type hints are sparse — add them when touching a function, don't do a blanket annotation pass.
- **TypeScript**: functional components, hooks only. Ant Design components. Strict mode is on — build fails on unused imports/vars.
- **Logging**: Python `logging` module, module-scoped (`logger = logging.getLogger(__name__)`). Logs go to stdout (no file handler, no rotation).
- **Error handling**: Routes catch broadly and return `{success: false, error: str(e)}`. When fixing a silently-swallowed exception, prefer adding `logger.exception(...)` rather than changing the return shape.
- **Don't add**: mocks, backwards-compat shims, docstring/type-hint sweeps, or "cleanup" refactors that weren't asked for. This codebase has one primary engineer and minimal review overhead — stay scoped.

## Pitfalls to watch for

- **`.env` is gitignored** but referenced in `docker-compose.yaml`. Docker builds will fail without it if `sftp.py` is exercised. Sample vars are in [README.md](README.md).
- **Station name matching in Excel is case-insensitive but whitespace-sensitive.** If a station is "in the file" but not found, check for trailing spaces or non-ASCII characters.
- **The generator's `replacement_performed` flags in the response can be `True` even when a specific replacement silently no-op'd.** Flags are set from extraction success, not replacement success. `debug_log` is the source of truth.
- **`test_basic.py` opens a Tk file dialog** — don't run it in CI.
- **`modules/template_manager.py` and `modules/rollout.py` are largely dead code.** Don't add new functionality there; use `modernization.py` instead.
- **Host port 5001** is the exposed backend port when using docker-compose (5000 conflicts with macOS AirPlay). Local dev without Docker uses 5000.
- **Frontend uses ports from Vite proxy**, not from env. If you change backend port, update [`Frontend/vite.config.ts`](Frontend/vite.config.ts).

## Project-specific agents

This repo defines one specialized agent in `.claude/agents/`:

- **`nokia-xml-debugger`** — for tracing why a specific `_replace_*` step didn't update the generated XML. Knows the pipeline order, the hardcoded column indices, and the namespace-agnostic XPath patterns. Use it when a generation completes successfully but the output XML is missing an expected change.

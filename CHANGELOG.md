# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Post-generation `_verify_output` in `ModernizationGenerator` — 5 sanity checks (well-formed XML, size > 1KB, reference btsName not leaked, reference BTS-ID not leaked from `MRBTS-/LNBTS-/NRBTS-` tokens, IoT TAC = 5000). Hard errors set `success: false` + `verification_errors`; soft warnings surface in `warnings.verification`.
- `details.replacement_counts` in the route response — real per-step mutation counts (`station_names`, `bts_ids`, `vlan_ids`, `ip_addresses`, `gateways`, `network_params_structural`, `network_params_legacy`, `sctp_port_min`, `params_2g`, `cells_4g`, `rootseq_4g`, `nrcells_5g_pci`, `tdd_cells_4g`, `tdd_pci_from_fdd`, `nrcell_5g_details`, `tac_override`, `iot_tac_fix`).
- End-to-end pytest suite (`backend/tests/test_modernization_e2e.py`) — 19 tests calling `ModernizationGenerator.generate()` directly against rich fixtures and asserting both `replacement_counts` and resulting XML. Total backend tests: 58 → 81.
- Rich `EXISTING_STATION_XML` / `REFERENCE_TEMPLATE_XML` fixtures and an `ip_plan_xlsx` factory in `conftest.py`.
- 4 namespaced-extractor regression tests (`TestExtractorsOnNamespacedXml` in `test_xml_parser.py`) locking in the xml_parser silent-failure fix.
- `test-runner` Claude agent — runs the pytest suite from chat and reports a short PASS/FAIL summary.
- GitHub Actions CI (`.github/workflows/test.yml`) — pytest on push/PR to `main`, Python 3.11/3.12/3.13 matrix, pip-cached, path-filtered to `backend/**`.
- `MIN_NAME_TOKEN_LEN` substring-replacement safety guard in `_replace_station_names` (refuses to operate on reference btsNames < 4 chars).
- Workflow checklist in `CLAUDE.md` Step 3 — codifies "after changing code: run tests → update agent docs → update CLAUDE.md → run `graphify update .`" with per-trigger mapping.
- Rollout TAC override now honored by the `/api/rollout` endpoint (previously dropped silently).

### Changed
- `_replace_4g_cells` no longer pretends to handle `rootSeqIndex` — that branch was dead because `extract_4g_cells` doesn't extract rootSeqIndex. `_replace_4g_rootseq` is the single source of LNCEL_FDD rootSeqIndex writes.
- `*_replacement_performed` flags in the response are now derived from real mutation counts, not from extraction success (they used to be `True` even when a replacement silently no-op'd).
- `ExcelParser.parse_ip_plan_excel` station-name lookup now collapses all whitespace before comparing, so trailing/internal/non-breaking-space variants no longer cause a miss.
- `xml-output-verifier` Claude agent rescoped to deeper checks (IP Plan cross-reference, sector count, per-tech VLAN/IP/GW, replacement_counts plausibility) since `_verify_output` now handles the baseline server-side.
- `nokia-xml-debugger` Claude agent updated for the 17-pass pipeline and the new `_verify_output` step.

### Fixed
- IPRT-2 NR routing key mismatch — `ExcelParser` wrote `'IPRT-2_NR'` (underscore) but `ModernizationGenerator` read `'IPRT-2 NR'` (space). Aligned to space.
- Four `XMLParser` extractors (`extract_vlan_parameters`, `extract_ip_parameters`, `extract_network_parameters`, `extract_routing_parameters`) used `obj.find(".//*[local-name()='p'][@name='X']")` which lxml's ElementPath rejects with "invalid predicate" on namespaced trees. The functions silently returned `{}` for every real-world Nokia XML. Switched all 11 occurrences to the existing `_find_param` helper (xpath-based, namespace-aware).
- `ngrok` service in `docker-compose.yaml` behind a `share` profile for one-command public-URL sharing.
- `backend/.env.example` documenting required environment variables.
- Vite dev server now allows `*.ngrok-free.app`, `*.ngrok.app`, `*.ngrok.io` hosts.

### Removed
- `backend/modules/rollout.py` (`RolloutGenerator`) — orphaned legacy, no callers.
- `ExcelParser.parse_transmission_excel` / `parse_radio_excel` — only consumers were `RolloutGenerator` and a dead "load for potential future use" path in `generate()`.
- `ModernizationGenerator._replace_routing_rules` — overlapped with `_replace_gateways_by_tech`; IPRT-1 prefixes only matched 4G by accident, IPRT-2 was unreachable due to the key mismatch above.
- `ModernizationGenerator._update_element_with_station_data` / `_update_network_configuration` — tree-based helpers never wired into `generate()`.

## [1.2.0] - 2026-04

### Added
- `nokia-xml-debugger` Claude agent definition for tracing missed `_replace_*` steps.
- `CLAUDE.md` expanded with non-obvious project facts, full API table, env vars, and pitfalls.

### Changed
- Gunicorn runs with 2 workers × 4 threads per worker for the production container.
- BTS ID replacement broadened to cover stray `traceId` and unrelated references that mirror the BTS ID.
- East reference XML templates refreshed.

### Fixed
- `traceId` value mirroring BTS ID in `nrRanTraceReference` is now updated alongside the rest of the ID rewrites.

## [1.1.0] - 2026-02

### Added
- TypeScript-strict React 19 + Vite 8 + Ant Design 6 frontend (separate `Frontend/` directory).
- `Frontend/src/api/client.ts` — typed Axios wrapper for all endpoints.
- Custom hooks (`useExistingXml`, `useFileSelection`, `useGeneration`) and decomposed `ModernizationPage` subcomponents.
- Region selector (East / West Georgia) wired through the file pickers and IP routing.
- Georgian (default) + English i18n.
- `DebugConsole` UI component that surfaces backend `debug_log` per request.

### Changed
- Backend split into Flask blueprints under `backend/routes/` (`modernization`, `extraction`, `xml_viewer`, `files`, `ip_plan`, `sftp`).
- Standardized API response shape: `{ success, data?/filename?/error?, debug_log?, warnings? }`.
- Hardcoded values extracted into `backend/constants.py` (IP plan column indices, regions, IoT cells, defaults).
- Pinned backend Python dependencies in `requirements.txt`.

### Removed
- Legacy Jinja2 templates and the monolithic `app.py` HTML rendering paths.

### Fixed
- Silent exception swallowing in several backend routes — now logged via `logger.exception`.
- Modernization TDD PCI mapping from FDD references.

## [1.0.0] - 2026-01

### Added
- Initial public release of the BTS Forge / Nokia WebEM Generator.
- Modernization pipeline: 15+ ordered `_replace_*` passes over a reference XML.
- Rollout mode (reuses reference XML as both "existing" and "reference").
- Excel-based IP Plan parsing with fixed column indices (G–AN).
- XML Viewer page (cells, VLANs, routing, IPs).
- Reference file management (upload / preview / delete).
- SFTP backup fetch (`/api/sftp-download`).
- Docker Compose deployment (backend on host port 5001, frontend on 3000).

[Unreleased]: https://github.com/gkochievi/Nokia_XML_Generator/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/gkochievi/Nokia_XML_Generator/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/gkochievi/Nokia_XML_Generator/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/gkochievi/Nokia_XML_Generator/releases/tag/v1.0.0

# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- `ngrok` service in `docker-compose.yaml` behind a `share` profile for one-command public-URL sharing.
- `backend/.env.example` documenting required environment variables.
- Vite dev server now allows `*.ngrok-free.app`, `*.ngrok.app`, `*.ngrok.io` hosts.

### Changed
- README rewritten to match the current backend/Frontend split, real ports (3000/5001), real API routes, and the ngrok workflow.
- `CONTRIBUTING.md` aligned with the actual project layout (no more `templates/` references).

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

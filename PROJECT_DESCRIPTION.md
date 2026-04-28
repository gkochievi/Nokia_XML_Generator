# Project Description

## Overview

**BTS Forge** (Nokia WebEM Generator) is an internal web tool for Cellfie's network engineering team that automates the generation of Nokia base station (BTS) XML configuration files. It plays a similar role to Huawei's iMasterMAE for Nokia kit — taking station data scattered across reference XMLs and operations Excel files (IP plans, BTS naming sheets) and producing a single configuration file ready to be loaded onto the WebEM/NetAct.

## Problem it solves

Hand-editing Nokia BTS XMLs is slow and error-prone:
- Files contain dozens of `managedObject` blocks with namespaced attributes, hierarchical `distName` paths, and multiple cell/neighbor lists.
- Per-station IP, VLAN, and gateway data lives in a different team's Excel file with a fixed column layout (G–AN).
- Modernization (adding 5G to an existing site) requires merging an existing config with a regional reference while preserving operator-specific formatting.
- Rollouts (new sites) need every value swapped consistently across the file.

BTS Forge automates this by running an ordered pipeline of string-based replacements over a vetted reference XML, parameterized by the target station's data pulled from the IP Plan Excel.

## Two main flows

### 1. 5G Modernization (existing BTS upgrade)
- **Inputs:** existing station XML + a regional 5G-enabled reference XML + the team's IP Plan Excel.
- **Output:** a new XML carrying the existing station's identity but with 5G blocks, IP routing, and VLAN mappings injected from the reference and IP Plan.

### 2. New Site Rollout
- **Inputs:** a similar-class reference XML + IP Plan Excel.
- **Output:** a single XML for the new site (the reference is reused as both "existing" and "reference"; differences are encoded as overrides — `id`, `name`, `tac`).

### 3. XML Configuration Viewer
A read-only structured view of any uploaded BTS XML — cells (2G/3G/4G/5G), VLANs, IP routing, gateways, neighbor lists — so engineers can verify a generated file or inspect a backup before importing it.

## Architecture

| Layer | Stack |
|---|---|
| Backend | Flask 3.1 (Python 3.11+), lxml, pandas + openpyxl, paramiko, Gunicorn (prod) |
| Frontend | React 19 + TypeScript 5.9 (strict), Vite 8, Ant Design 6 (dark theme), React Router 7, i18next, Axios |
| Deploy | Docker Compose: backend on host port 5001, frontend (nginx-served static build) on 3000 |

Backend routes are split into Flask Blueprints under `backend/routes/`. The core generation logic lives in `backend/modules/modernization.py` — a 1500-LOC pipeline that intentionally uses string-based regex replacement over the reference XML rather than DOM manipulation, to preserve byte-for-byte formatting that downstream Nokia tooling expects.

## Data inputs

### IP Plan Excel
Layout is **fixed by column index**, not header name. `ExcelParser` reads from columns G–AN (0-based indices 6–39), with the mapping defined in `backend/constants.py` → `IP_PLAN_COLUMNS`. Station-name lookup is case-insensitive and tries `-`/`_` swaps, but is otherwise exact.

### Reference XMLs
Stored in `backend/example_files/<Region>/`, where region is `East` or `West`. Filenames encode metadata (sector count, radio model code) so the modernization-inspect endpoint can score and suggest the best match for an uploaded existing config.

### SFTP backup fetch (optional)
A station's latest backup XML can be pulled directly from the OSS server via `/api/sftp-download` — credentials live in `backend/.env`.

## Internationalization

UI is bilingual: **Georgian (default)** and **English**. Many backend error messages are hardcoded in Georgian — this is intentional, not a bug, since the operators using the tool prefer Georgian-language errors.

## Further reading

- [`README.md`](README.md) — setup, commands, environment variables.
- [`CLAUDE.md`](CLAUDE.md) — full architectural notes, non-obvious facts, pitfalls.
- [`CONTRIBUTING.md`](CONTRIBUTING.md) — code style and PR flow.

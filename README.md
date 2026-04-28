# BTS Forge — Nokia WebEM Generator

Web tool for generating Nokia base station (BTS) XML configuration files for **5G modernization** and **new site rollouts**. Used by Cellfie's network engineering team.

## Features

- **Modernization** — add 5G to an existing BTS by merging an uploaded XML with a regional reference and IP Plan
- **Rollout** — generate a complete configuration for a brand-new site
- **XML Viewer** — structured, color-coded view of any Nokia BTS XML (cells, VLANs, routing, IPs, neighbors)
- **IP Plan integration** — Excel parsing with a fixed column layout (G–AN); fuzzy station-name match
- **Region-aware** — separate reference XMLs and IP routing for `East` / `West` Georgia
- **i18n** — Georgian (default) and English UI
- **SFTP backup fetch** — pull a station's latest backup XML directly from the OSS server
- **Bulk file management** — upload/preview/delete reference and generated files from the UI

## Tech stack

| Layer | Stack |
|---|---|
| Backend | Flask 3.1, Python 3.11+, lxml, pandas + openpyxl, paramiko, Gunicorn (prod) |
| Frontend | React 19 + TypeScript 5.9 (strict), Vite 8, Ant Design 6 (dark), React Router 7, i18next, Axios |
| Deploy | Docker Compose — backend (port 5001) + nginx-served frontend (port 3000) |

## Quick start (Docker — recommended)

```bash
# Clone and start everything
docker-compose up --build

# Frontend → http://localhost:3000
# Backend  → http://localhost:5001
```

The nginx in the frontend container proxies `/api/` to the backend, so the frontend port (3000) is the only one you actually need to open.

### Sharing a running instance via ngrok

A separate `ngrok` service is wired into `docker-compose.yaml` behind the `share` profile, so it doesn't start by default.

1. Get a free authtoken at https://dashboard.ngrok.com/get-started/your-authtoken
2. Add it to `backend/.env`:
   ```
   NGROK_AUTHTOKEN=your_token_here
   ```
3. Start the stack with sharing enabled:
   ```bash
   docker-compose --profile share up -d
   ```
4. Open the ngrok inspector at http://localhost:4040 and copy the public `https://<random>.ngrok-free.app` URL — share that with whoever needs access.

To stop sharing without taking the app down: `docker stop nokia-webem-ngrok`.

## Local development (without Docker)

### Backend

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
source venv/bin/activate
pip install -r requirements.txt

# SFTP creds in backend/.env (see "Environment variables" below)
python app.py
# Flask dev server → http://localhost:5000
```

### Frontend

```bash
cd Frontend
npm install
npm run dev
# Vite dev server → http://localhost:3000 (proxies /api → :5000)
```

## Project structure

```
.
├── backend/
│   ├── app.py                    # Flask init + blueprint registration
│   ├── constants.py              # IP plan column indices, regions, IoT cells, etc.
│   ├── routes/                   # One Blueprint per file, all under /api
│   │   ├── modernization.py      # /api/modernization, /inspect, /rollout
│   │   ├── extraction.py         # /api/extract-<param_type> (7 types)
│   │   ├── xml_viewer.py         # /api/view-xml
│   │   ├── files.py              # example-files / generated-files CRUD
│   │   ├── ip_plan.py            # /api/parse-ip-plan (debug)
│   │   └── sftp.py               # /api/sftp-download
│   ├── modules/
│   │   ├── xml_parser.py         # Namespace-agnostic XPath extraction
│   │   ├── excel_parser.py       # IP Plan parsing
│   │   ├── modernization.py      # Generate pipeline (15+ regex/replace passes)
│   │   └── xml_viewer.py         # Config summary for viewer UI
│   ├── example_files/            # Reference XMLs (East/, West/), IP Plans, BTS naming
│   ├── tests/                    # pytest integration tests
│   ├── requirements.txt
│   └── Dockerfile
├── Frontend/
│   ├── src/
│   │   ├── api/client.ts         # All typed API endpoints
│   │   ├── pages/                # HomePage, ModernizationPage, XmlViewerPage
│   │   ├── components/           # AppLayout, DebugConsole, FileManagerModal
│   │   ├── i18n/index.ts         # ka + en translations
│   │   └── theme/themeConfig.ts  # AntD dark theme (purple/indigo)
│   ├── nginx.conf                # Prod proxy config (/api → web:5000)
│   └── Dockerfile                # Multi-stage: Vite build → nginx
├── docker-compose.yaml           # web + frontend + ngrok (share profile)
└── Nokia-XML-Generator-Deploy/   # Standalone deploy package
```

## API endpoints (selected)

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/modernization` | POST | Generate modernization XML |
| `/api/modernization/inspect` | POST | Detect tech (2G/3G/4G/5G), sectors, radio modules; suggest reference |
| `/api/rollout` | POST | New site (delegates to modernization in rollout mode) |
| `/api/extract-<param_type>` | POST | Types: `bts-name`, `bts-id`, `sctp-port`, `2g-params`, `4g-cells`, `4g-rootseq`, `5g-nrcells` |
| `/api/view-xml` | POST/GET | Parse XML → structured config for viewer |
| `/api/example-files/xml` | GET | List reference XMLs (filter by region) |
| `/api/example-files/excel` | GET | List Excel files (`ip`, `data`, `btsnaming`) |
| `/api/generated-files` | GET | List generated XMLs |
| `/api/download/<filename>` | GET | Download generated XML |
| `/api/preview/<filename>` | GET | Preview generated XML content |
| `/api/parse-ip-plan` | POST | Debug: parse IP Plan for a station |
| `/api/sftp-download` | POST | Fetch backup XML via SFTP |

Canonical response shape: `{ success, data?, filename?, error?, debug_log?, warnings? }`.

The frontend `DebugConsole` displays `debug_log` from each generation — it's the source of truth when something goes silently wrong in the pipeline.

## Environment variables

Backend reads these from `backend/.env` (gitignored). Defaults shown for non-secret values:

| Var | Default | Purpose |
|---|---|---|
| `FLASK_HOST` | `0.0.0.0` | Bind address |
| `FLASK_PORT` | `5000` | Bind port |
| `FLASK_DEBUG` | `true` | Flask debug mode |
| `MAX_UPLOAD_MB` | `50` | Max request body size |
| `UPLOAD_FOLDER` | `uploads` | Temp upload dir |
| `GENERATED_FOLDER` | `generated` | Output dir |
| `EXAMPLE_FILES_FOLDER` | `example_files` | Reference files root |
| `SFTP_HOST`, `SFTP_PORT`, `SFTP_USERNAME`, `SFTP_PASSWORD`, `SFTP_REMOTE_DIR` | — | For `/api/sftp-download` |
| `NGROK_AUTHTOKEN` | — | Required when running the `share` compose profile |

## IP Plan format

The IP Plan Excel layout is **fixed** — `ExcelParser` reads by column index, not by header name. Column indices (0-based, Excel columns G–AN) are defined in `IP_PLAN_COLUMNS` in [`backend/constants.py`](backend/constants.py).

Station-name lookup is **case-insensitive** and tries `-` ↔ `_` swaps, but is otherwise exact (whitespace-sensitive). If your station "exists in the file" but isn't found, check for trailing spaces or non-ASCII characters.

## Testing

```bash
cd backend && python -m pytest tests/
```

Backend tests cover routes and the XML parser (happy-path only). There are no frontend tests — manual browser testing via `npm run dev` is the verification path. The most reliable check after changing the modernization pipeline is end-to-end: generate XML and diff it against a known-good output.

## Development notes

- **String-based XML replacement is intentional**, not tech debt — it preserves byte-for-byte formatting that operator tooling expects.
- **`backend/modules/modernization.py`** is the core. The order of `_replace_*()` calls matters; don't reorder without an end-to-end diff check.
- **TypeScript strict mode is on** (`noUnusedLocals`, `noUnusedParameters`) — unused imports break `npm run build`.
- See [CLAUDE.md](CLAUDE.md) for the full architectural notes and pitfalls.

## License

[MIT](LICENSE)

# Nokia WebEM Generator (BTSForge)

Web tool for generating Nokia base station (BTS) XML configuration files for 5G modernization and new site rollouts.

## Architecture

- **Backend**: Flask 3.0+ (Python 3.11+), served by Gunicorn on port 5000
- **Frontend**: React 19 + TypeScript + Vite + Ant Design 6, dev server on port 3000
- **i18n**: Georgian (ka) / English (en) via i18next, persisted to localStorage

### Monorepo Layout

```
.
├── backend/                 # Flask backend
│   ├── app.py               # Flask init + blueprint registration
│   ├── routes/              # API blueprints
│   │   ├── modernization.py # /api/modernization, /api/modernization/inspect, /api/rollout
│   │   ├── extraction.py    # /api/extract-<type> (generic, handles 7 param types)
│   │   ├── xml_viewer.py    # /api/view-xml
│   │   ├── files.py         # example-files CRUD, generated-files CRUD, uploads, download
│   │   ├── ip_plan.py       # /api/parse-ip-plan endpoints
│   │   └── sftp.py          # /api/sftp-download
│   ├── modules/
│   │   ├── xml_parser.py    # Nokia XML parsing with namespace-agnostic XPath
│   │   ├── excel_parser.py  # IP Plan / transmission / radio Excel parsing
│   │   ├── modernization.py # Core generation engine (modernization + rollout modes)
│   │   ├── xml_viewer.py    # Extract config data for viewer UI
│   │   ├── rollout.py       # Legacy rollout (mostly unused, delegated to modernization.py)
│   │   └── template_manager.py  # BTS info extraction helpers
│   ├── example_files/       # Reference XMLs (East/, West/), IP Plans (IP/), naming data
│   ├── uploads/             # Temporary uploaded files (gitignored)
│   ├── generated/           # Output XML files (gitignored)
│   ├── Dockerfile           # Python + Gunicorn
│   └── requirements.txt
├── Frontend/                # React SPA
│   ├── src/
│   │   ├── api/client.ts    # Axios API client with typed endpoints
│   │   ├── pages/           # HomePage, ModernizationPage, XmlViewerPage
│   │   ├── components/      # AppLayout, DebugConsole, FileManagerModal
│   │   ├── i18n/            # i18next config
│   │   └── theme/           # Ant Design theme
│   ├── Dockerfile           # Multi-stage: Node build -> Nginx serve
│   └── nginx.conf           # SPA + /api proxy to backend:5000
├── Nokia-XML-Generator-Deploy/  # Standalone deploy package (bat + docker-compose)
└── docker-compose.yaml
```

## Key Design Decisions

1. **String-based template replacement** - Reference XML is read as text, tokens replaced via string operations (not DOM manipulation). This avoids Nokia XML namespace complexity.
2. **Single generate() method** handles both modernization and rollout via `mode` parameter and `rollout_overrides` dict.
3. **IP Plan Excel column indices are hardcoded** (0-based) in `backend/modules/excel_parser.py`. Assumes specific Nokia IP Plan format.
4. **Multiple XPath fallback patterns** in `backend/modules/xml_parser.py` for namespace-agnostic element matching.
5. **Region-based file organization** - Reference XMLs split into East/ and West/ subdirectories.

## API Endpoints

Endpoints are split across `backend/routes/` blueprints. Key ones:

| Endpoint | Method | Purpose |
|---|---|---|
| `/api/modernization` | POST | Generate modernization/rollout XML |
| `/api/modernization/inspect` | POST | Inspect XML to suggest reference template |
| `/api/view-xml` | POST | Parse XML and extract config for viewer |
| `/api/extract-bts-name` | POST | Extract btsName from uploaded XML |
| `/api/example-files/xml` | GET | List reference XMLs by region |
| `/api/example-files/excel` | GET | List IP Plan Excel files |
| `/api/generated-files` | GET | List generated output files |
| `/api/download/<filename>` | GET | Download generated XML |

**Response format**: `{ success: bool, data/filename/error: ..., debug_log?: [], warnings?: [] }`

## Nokia XML Conventions

- `managedObject` elements with `class` attribute: `com.nokia.srbts:MRBTS`, `com.nokia.srbts:NRBTS`, etc.
- `distName` attribute: path format with hyphens (`MRBTS-90217/NRBTS-123`)
- Parameters: `<p name="btsName">value</p>`
- Lists: `<list name="..."><item>...</item></list>`

## Development

```bash
# Backend
cd backend && python app.py      # Flask dev server on :5000

# Frontend
cd Frontend && npm run dev       # Vite dev server on :3000, proxies /api to :5000

# Docker (both services)
docker-compose up --build        # Frontend :3000, Backend :5001
```

## Testing

```bash
cd backend && python -m pytest test_basic.py test_template_manager.py
```

Limited test coverage. Manual testing is primary.

## Build & Deploy

- Docker Compose runs two services: `web` (Flask+Gunicorn) and `frontend` (Nginx+React)
- `Nokia-XML-Generator-Deploy/` contains a self-contained deploy package that clones from GitHub
- Host port 5001 is used for backend (5000 conflicts with macOS AirPlay)

## Code Style

- Python: PEP 8 (not strict), snake_case functions, PascalCase classes, brief docstrings
- TypeScript: functional components, hooks, Ant Design components
- No strict linting enforced
- Logging via Python `logging` module throughout backend

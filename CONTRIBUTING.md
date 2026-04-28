# Contributing to BTS Forge

Thanks for your interest in BTS Forge (Nokia WebEM Generator). This document covers how the codebase is organized and what's expected from a contribution.

## Project layout (high-level)

```
backend/           # Flask 3.1 API — Python 3.11+, lxml, pandas, paramiko
  routes/          # One Blueprint per file, all mounted under /api
  modules/         # Core logic: xml_parser, excel_parser, modernization, xml_viewer
  example_files/   # Reference XMLs (East/, West/), IP plans, BTS naming
  tests/           # pytest integration tests

Frontend/          # React 19 + TypeScript 5.9 (strict) + Vite 8 + Ant Design 6
  src/api/         # Typed Axios endpoints — add new methods here
  src/pages/       # Top-level routes
  src/components/  # Shared UI
  src/i18n/        # ka + en translations
```

The full architectural notes — including non-obvious facts about the modernization pipeline, hardcoded IP-plan column indices, region conventions, and the IoT TAC override — live in [`CLAUDE.md`](CLAUDE.md). **Read it before touching `backend/modules/modernization.py` or `backend/modules/xml_parser.py`.**

## Getting set up

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env              # then fill in real values (file is gitignored)
python app.py                     # http://localhost:5000

# Frontend
cd Frontend
npm install
npm run dev                       # http://localhost:3000 (proxies /api → :5000)
```

Or run the whole stack with Docker Compose:

```bash
docker-compose up --build         # frontend → :3000, backend → :5001
```

## Code style

### Python (backend)
- PEP 8-ish, snake_case functions, PascalCase classes.
- Brief docstrings — one line is fine if the function name carries the intent.
- Type hints are sparse; add them when you touch a function, don't do a blanket annotation pass.
- Logging: module-scoped `logger = logging.getLogger(__name__)`, `logger.info/exception(...)`. No print statements.
- Prefer `logger.exception(...)` when adding error handling — don't silently swallow.

### TypeScript (frontend)
- Functional components and hooks only. No class components.
- Strict mode is **on** — unused imports/vars break `npm run build`. Fix at write time.
- Ant Design first; only reach for raw HTML elements when AntD doesn't fit.
- State lives in components and custom hooks (no Redux/Zustand). Persist user prefs (`region`, `lang`) via `localStorage`.
- Use `AbortController` to cancel stale async calls in custom hooks — follow the existing pattern in `pages/modernization/`.

### General
- Don't add features, refactors, or "cleanup" passes that weren't asked for. Stay scoped.
- Don't mock the database / file system in tests — the project's tests are integration-style for a reason.
- Don't add backward-compat shims when changing internal APIs — there's one primary engineer; just update the call sites.

## Testing

```bash
cd backend && python -m pytest tests/
```

- Backend tests cover the Blueprints and `XMLParser` (happy-path).
- There are no frontend tests. Manual browser verification is the path.
- When changing `ModernizationGenerator`, the only reliable check is end-to-end: generate XML against a known-good reference and `diff` the output. Order of `_replace_*()` calls matters.

## Commit messages

Match the existing style (see `git log`):
- Sentence-case, present tense, descriptive.
- One-line summary under ~70 characters; body wrapped at ~72 if needed.
- Examples: `Run gunicorn with 2 workers and 4 threads per worker`, `Fix modernization TDD PCI mapping and polish UI`.

## Pull request flow

1. Branch from `main`.
2. Make focused changes — one logical concern per PR.
3. Update [CHANGELOG.md](CHANGELOG.md) under `## [Unreleased]` if the change is user-visible.
4. Ensure `cd backend && python -m pytest tests/` and `cd Frontend && npm run build` both pass.
5. Open a PR with a description that explains *why*, not just *what*.

## Adding common things — where to edit

| Task | Edit here |
|---|---|
| New API endpoint | `backend/routes/<blueprint>.py` → register in `backend/app.py` → typed method in `Frontend/src/api/client.ts` |
| New XML parameter extractor | `XMLParser` in `backend/modules/xml_parser.py` (follow the namespace-agnostic XPath fallback pattern) |
| New `_replace_*` step | Add method on `ModernizationGenerator` AND call it from `generate()` in the right pipeline position |
| IP Plan column layout change | `IP_PLAN_COLUMNS` in `backend/constants.py` — re-run end-to-end against a known station |
| New region beyond East/West | `REGIONS` in `backend/constants.py` + create `backend/example_files/<Region>/` |
| New translation key | `Frontend/src/i18n/index.ts` — add to **both** `ka` and `en` |
| New page | Component under `Frontend/src/pages/` → route in `Frontend/src/App.tsx` → nav entry in `Frontend/src/components/AppLayout.tsx` |
| New reference XML for a radio model | Drop into `backend/example_files/<Region>/` with filename containing `S<N>` and the model code (e.g. `5G-S3-AHEGA.xml`) so `inspect` can score it |

## Reporting issues

- Include steps to reproduce.
- Attach the relevant `debug_log` from the response if it's a generation issue (visible in the `DebugConsole` UI panel).
- Include OS, Python, and Node versions for environment-specific bugs.

## Questions

Open an issue on the GitHub or GitLab tracker, or reach out to the maintainer.

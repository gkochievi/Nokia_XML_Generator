# Nokia WebEM Generator — Deploy from GitHub

## Requirements

- Docker Desktop installed and running

## First Time Setup

1. Copy this folder to your computer
2. Edit `.env` to set SFTP credentials (if needed)
3. Double-click `Nokia-XML-Generator-Deploy.bat`
4. Wait for build to complete (first time takes 2-3 minutes)
5. Browser opens automatically at http://localhost

## Update to Latest Version

Double-click `Nokia-XML-Generator-Deploy.bat` again.

- The image is **rebuilt** from the **latest GitHub** code (each run uses a fresh shallow `git clone` inside the build).
- Docker **replaces the app container** when the new image is ready. You do **not** lose uploaded or generated XML: those live in Docker **volumes** (`uploads`, `generated`), which are kept across updates.
- The script no longer force-removes the container first; `docker compose up -d --build` updates in place. Builds are **faster** than before because only layers after the git clone are rebuilt when the cache bust changes (no full `--no-cache` on every run).

## Access

| URL | Description |
|-----|-------------|
| http://localhost:3000 | New React UI (Modernization, XML Viewer) |
| http://localhost:5000 | Original UI (all features) |

## Configuration

Edit `.env` to change SFTP connection settings:

```
SFTP_HOST=172.30.179.128
SFTP_PORT=22
SFTP_USERNAME=root
SFTP_PASSWORD=changeme
SFTP_REMOTE_DIR=/d/oss/global/var/sct/backup_sites/mrbts
```

## Troubleshooting

- **Docker not found**: Install Docker Desktop from https://docker.com
- **Build fails**: Make sure you have internet access (needs to download from GitHub)
- **Port 80 in use**: Change `80:80` to `8080:80` in `docker-compose.yaml`, then access http://localhost:8080

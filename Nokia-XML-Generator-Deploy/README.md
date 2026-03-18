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

Just double-click `Nokia-XML-Generator-Deploy.bat` again.
It always pulls the latest code from GitHub and rebuilds.

## Access

| URL | Description |
|-----|-------------|
| http://localhost | New React UI (Modernization, XML Viewer) |
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

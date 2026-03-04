# Nokia WebEM Generator — Deploy from Git

## Quick Start

1. Make sure Docker and Docker Compose are installed.
2. Run:

```bash
docker-compose up --build -d
```

3. Open http://localhost:5000

## Update to Latest Version

```bash
docker-compose up --build -d
```

This re-clones the latest code from GitHub and rebuilds.

## Configuration

Edit `.env` to change SFTP connection settings.

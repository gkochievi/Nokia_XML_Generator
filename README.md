# Nokia WebEM Generator

A web-based tool for generating Nokia WebEM configuration files for 5G network modernization and new site rollouts.

## Features

- **5G Modernization**: Add 5G configuration to existing base stations
- **New Site Rollout**: Generate complete configuration for new base stations
- **XML Viewer**: User-friendly XML configuration file viewer
- **Excel Integration**: Parse transmission and radio parameter Excel files
- **File Management**: Upload, view, and manage XML configuration files

## Prerequisites

- Python 3.11+
- Docker (optional)

## Installation & Usage

### Using Docker (Recommended)

```bash
# Build and run with Docker Compose
docker-compose up --build

# Or build and run manually
docker build -t nokia-webem-generator .
docker run -p 5000:5000 nokia-webem-generator
```

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create .env with SFTP settings (or edit existing)
echo "SFTP_HOST=172.30.179.127" >> .env
echo "SFTP_PORT=22" >> .env
echo "SFTP_USERNAME=root" >> .env
echo "SFTP_PASSWORD=changeme" >> .env
echo "SFTP_REMOTE_DIR=/d/oss/global/var/sct/backup_sites/mrbts" >> .env

# Run the application
python app.py
```

### Using the provided script

```bash
# Make script executable (Linux/Mac)
chmod +x run.sh

# Run the application
./run.sh
```

The application will be available at http://localhost:5000

## Project Structure

```
nokia_webem_generator/
├── app.py                 # Main Flask application
├── modules/               # Core modules
│   ├── excel_parser.py    # Excel file parsing
│   ├── modernization.py   # 5G modernization logic
│   ├── rollout.py         # New site rollout logic
│   ├── xml_parser.py      # XML parsing utilities
│   └── xml_viewer.py      # XML viewing interface
├── templates/             # HTML templates
├── uploads/               # Uploaded files storage
├── generated/             # Generated XML files
├── example_files/         # Example configuration files
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yaml   # Docker Compose configuration
├── sftp_downloader.py    # CLI tool to download backups from SFTP
└── run.sh                # Quick start script
```

## API Endpoints

- `GET /` - Main application page
- `POST /api/view-xml` - Parse and view XML configuration
- `POST /api/modernization` - Generate 5G modernization configuration
- `POST /api/rollout` - Generate new site rollout configuration
- `GET /download/<filename>` - Download generated XML files
- `GET /api/list-xmls` - List uploaded XML files
- `DELETE /api/delete-xml/<filename>` - Delete uploaded XML file

## Configuration File Formats

### Transmission Excel File
Should contain columns:
- Station_Name
- OM_IP, 2G_IP, 3G_IP, 4G_IP, 5G_IP
- Gateway, VLAN, Subnet_Mask

### Radio Parameters Excel File
Should contain columns:
- Station_Name
- Sector_ID, Antenna_Count, Radio_Module
- Frequency, Carrier_ID

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please create an issue in the GitHub repository.


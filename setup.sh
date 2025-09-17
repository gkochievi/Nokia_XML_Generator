#!/bin/bash

# Nokia WebEM Generator Setup Script
# This script sets up the development environment

set -e

echo "Setting up Nokia WebEM Generator..."

# Check if Python 3.11+ is installed
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python 3.11 or higher is required. Found: $python_version"
    exit 1
fi

echo "Python version check passed: $python_version"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create necessary directories
echo "Creating necessary directories..."
mkdir -p uploads
mkdir -p generated
mkdir -p logs

# Set up .gitkeep files
touch uploads/.gitkeep
touch generated/.gitkeep

echo "Setup completed successfully!"
echo ""
echo "Create a .env file based on .env.example to configure SFTP access."
echo "If .env does not exist, you can create it now with default values:"
if [ ! -f .env ]; then
  cat > .env << 'EOF'
SFTP_HOST=172.30.179.127
SFTP_PORT=22
SFTP_USERNAME=root
SFTP_PASSWORD=vmR00t-
SFTP_REMOTE_DIR=/d/oss/global/var/sct/backup_sites/mrbts
EOF
  echo ".env file created with placeholder credentials. Please edit it."
fi

echo "To run the application:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "Or use the provided script:"
echo "  ./run.sh"

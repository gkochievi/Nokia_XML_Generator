# Project Description

## Overview

This project creates a web-based tool for Nokia WebEM configuration file generation, similar to Huawei's iMasterMAE system. The tool handles configuration changes for RAN (Radio Access Network) systems through XML file imports.

## Main Functionality

The web application allows users to upload Excel files from switch teams containing:
- Base station names
- IP addresses for all technologies (2G, 3G, 4G, 5G)
- VLAN configurations
- Radio parameters (antennas, radio modules, sectors, carriers, frequencies)

Users can input station names, and the system will search for corresponding information in the uploaded files to generate prepared XML configuration files.

## Two Main Configuration Types

### 1. 5G Modernization (Existing Base Station Upgrade)

**Input Files:**
- Existing station XML script
- Transmission team Excel file (containing multiple stations with OM, 2G, 3G, 4G, 5G IP addresses, gateways, VLANs, etc.)
- Reference 5G-enabled base station XML script

**Output:**
- New XML file containing existing station configuration + 5G configuration based on the reference
- Updated IP routes and ports

### 2. New Site Rollout

**Input Files:**
- Similar station XML configuration script file
- Radio parameters Excel file
- Transmission team Excel file

**Output:**
- Single XML file integrating the new base station

### 3. XML Configuration Viewer

Additional functionality for user-friendly viewing of XML file information and configurations.

## Technical Stack

- **Backend**: Python Flask
- **Frontend**: HTML/CSS/JavaScript
- **File Processing**: XML parsing, Excel file processing
- **Deployment**: Docker support

## File Structure Requirements

### Transmission Excel File
Columns should include:
- Station_Name
- OM_IP, 2G_IP, 3G_IP, 4G_IP, 5G_IP
- Gateway, VLAN, Subnet_Mask

### Radio Parameters Excel File
Columns should include:
- Station_Name
- Sector_ID, Antenna_Count, Radio_Module
- Frequency, Carrier_ID

## Development Approach

1. **Frontend First**: Design schema and web interface before file processing
2. **Backend Integration**: Implement file processing logic after frontend completion
3. **Modular Design**: Separate modules for different functionality types 
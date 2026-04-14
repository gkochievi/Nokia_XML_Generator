"""Shared domain constants for Nokia BTSForge backend.

Centralizes hardcoded values that were previously scattered across modules.
"""

# ---------------------------------------------------------------------------
# File organization
# ---------------------------------------------------------------------------
REGIONS = ('East', 'West')
EXAMPLE_SUBDIRS = {'ip': 'IP', 'data': 'Data', 'btsnaming': 'BTSNaming'}
ALLOWED_EXTENSIONS = {'xml', 'xlsx', 'xls'}
XML_EXTENSIONS = {'.xml'}
EXCEL_EXTENSIONS = {'.xlsx', '.xls'}

# ---------------------------------------------------------------------------
# App defaults (overridable via environment variables)
# ---------------------------------------------------------------------------
DEFAULT_MAX_UPLOAD_MB = 50
DEFAULT_SERVER_HOST = '0.0.0.0'
DEFAULT_SERVER_PORT = 5000

# ---------------------------------------------------------------------------
# VLAN constraints
# ---------------------------------------------------------------------------
VLAN_MIN = 1
VLAN_MAX = 4094

# ---------------------------------------------------------------------------
# IoT cell identifiers
# ---------------------------------------------------------------------------
IOT_CELLS = frozenset({'LNCEL-211', 'LNCEL-212', 'LNCEL-213', 'LNCEL-214'})
IOT_TAC = '5000'

# ---------------------------------------------------------------------------
# Technology normalization — canonical labels used across modules
# ---------------------------------------------------------------------------
TECH_ALIASES = {
    'OAM': 'OAM', 'OM': 'OAM', 'OMU': 'OAM', 'MGMT': 'OAM',
    'MGT': 'OAM', 'MANAGEMENT': 'OAM',
    '2G': '2G', 'GSM': '2G', 'GERAN': '2G',
    '3G': '3G', 'WCDMA': '3G', 'UMTS': '3G',
    '4G': '4G', 'LTE': '4G',
    '5G': '5G', 'NR': '5G',
}

# Ordered tokens for substring matching (longest/most specific first)
TECH_TOKENS = [
    ('GERAN', '2G'), ('WCDMA', '3G'), ('UMTS', '3G'),
    ('MGMT', 'OAM'), ('MGT', 'OAM'),
    ('OAM', 'OAM'), ('OM', 'OAM'),
    ('GSM', '2G'), ('2G', '2G'),
    ('3G', '3G'),
    ('LTE', '4G'), ('4G', '4G'),
    ('NR', '5G'), ('5G', '5G'),
]

# ---------------------------------------------------------------------------
# IP Plan Excel column indices (0-based) — Nokia IP Plan format
# ---------------------------------------------------------------------------
IP_PLAN_COLUMNS = {
    # VLANs
    'MGT_VLAN_ID': 6,    # G
    'GSM_VLAN_ID': 10,   # K
    'WCDMA_VLAN_ID': 17, # R
    'LTE_VLAN': 26,      # AA
    '5G_VLAN': 36,       # AK
    # IPs
    'MGT_IP': 7,         # H
    'GSM_IP': 11,        # L
    'WCDMA_IP': 18,      # S
    'LTE_IP': 27,        # AB
    '5G_IP': 37,         # AL
    # Subnet masks / prefix lengths
    'MGT_MASK': 8,       # I
    'GSM_MASK': 12,      # M
    'WCDMA_MASK': 19,    # T
    'LTE_MASK': 28,      # AC
    '5G_MASK': 38,       # AM
    # Gateways
    'MGT_GW': 9,         # J
    'GSM_GW': 13,        # N
    'WCDMA_GW': 20,      # U
    'LTE_GW': 29,        # AD
    '5G_GW': 39,         # AN
}

# ---------------------------------------------------------------------------
# IP routing — gateway prefix → technology (IPRT-1 / IPRT-2)
# ---------------------------------------------------------------------------
IPRT1_PREFIX_TO_TECH = {
    '10.110': 'OAM',
    '10.171': '2G',
    '10.141': '3G',
    '10.111': '4G',
}

IPRT2_PREFIX_TO_TECH = {
    '10.112': '5G',
}

# ---------------------------------------------------------------------------
# Destination IP → technology mapping for gateway replacement in IPRT objects
# ---------------------------------------------------------------------------
DEST_IP_TO_TECH = {
    '0.0.0.0': 'OAM',
    # 3G / WCDMA
    '10.0.0.192': '3G',
    '10.0.1.192': '3G',
    '10.0.2.192': '3G',
    '10.0.3.192': '3G',
    # 2G / GSM
    '10.0.7.112': '2G',
    '10.0.7.144': '2G',
    '10.0.7.96': '2G',
    '10.0.8.112': '2G',
    '10.0.8.144': '2G',
    '10.0.8.96': '2G',
    # 4G / LTE
    '10.111.0.0': '4G',
    '10.121.0.0': '4G',
    '10.131.0.0': '4G',
    '172.28.16.64': '4G',
    '172.28.37.80': '4G',
    '172.28.37.96': '4G',
    '172.28.44.64': '4G',
    '172.28.44.80': '4G',
    '172.29.16.64': '4G',
    '172.29.37.16': '4G',
    '172.29.37.32': '4G',
    '172.30.157.240': '4G',
    '172.30.160.32': '4G',
    '10.112.0.0': '4G',
    '10.122.0.0': '4G',
}

# ---------------------------------------------------------------------------
# BTS naming data Excel lookup paths (relative to example_files dir)
# ---------------------------------------------------------------------------
BTS_NAMING_EXCEL_PATHS = ('BTSNaming/data.xlsx', 'data.xlsx')

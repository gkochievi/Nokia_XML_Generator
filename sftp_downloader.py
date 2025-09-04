import os
import re
import pandas as pd
import paramiko
from dotenv import load_dotenv

# ----------------------------
# Function to download a file from SFTP
# ----------------------------
def download_from_sftp(backup_name, local_base_filename=None):
    # Load env once (safe to call multiple times)
    load_dotenv()
    host = os.getenv("SFTP_HOST", "127.0.0.1")
    port = int(os.getenv("SFTP_PORT", "22"))
    username = os.getenv("SFTP_USERNAME", "")
    password = os.getenv("SFTP_PASSWORD", "")
    remote_dir = os.getenv("SFTP_REMOTE_DIR", "/")
    local_dir = "downloads"

    # Connect to SFTP
    transport = paramiko.Transport((host, port))
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)

    # Ensure local folder exists
    os.makedirs(local_dir, exist_ok=True)

    # Determine local filename (keep original extension)
    file_extension = os.path.splitext(backup_name)[1]
    if local_base_filename:
        safe_base = "".join("_" if c in '<>:"/\\|?*' else c for c in str(local_base_filename))
        local_filename = f"{safe_base}{file_extension}"
    else:
        local_filename = backup_name

    remote_path = f"{remote_dir}/{backup_name}"
    local_path = os.path.join(local_dir, local_filename)

    try:
        sftp.get(remote_path, local_path)
        print(f"✅ Downloaded: {local_path}")
    except FileNotFoundError:
        print(f"❌ File {backup_name} not found on SFTP.")

    # Close connection
    sftp.close()
    transport.close()


# ----------------------------
# Main program
# ----------------------------
if __name__ == "__main__":
    # Prefer example_files/data.xlsx; fallback to local data.xlsx
    excel_path = os.path.join("example_files", "data.xlsx")
    if not os.path.exists(excel_path):
        excel_path = "data.xlsx"

    # Load Excel file
    df = pd.read_excel(excel_path, engine="openpyxl")  # Make sure openpyxl is installed

    # Normalization helper: treat '_' and '-' as the same
    def normalize_name(value):
        text = str(value).strip().lower()
        text = text.replace("_", "-")
        text = re.sub(r"-+", "-", text)
        return text

    # Add normalized name column for robust matching
    df["_name_norm"] = df["Name"].apply(normalize_name)

    while True:
        # Ask user for input
        choice = input("Enter ID or Name (q to quit): ").strip()

        # Exit conditions
        if choice == "" or choice.lower() in ("q", "quit", "exit"):
            print("Exiting.")
            break

        # Match by ID if numeric
        if choice.isdigit():
            row = df[df["ID"] == int(choice)]
        else:
            # Match by Name: case-insensitive, '-' and '_' treated equivalently
            choice_norm = normalize_name(choice)
            row = df[df["_name_norm"] == choice_norm]

        if row.empty:
            print("❌ No match found in Excel.")
            continue

        backup_name = row.iloc[0]["Backup_Name"]
        base_name = str(row.iloc[0]["Name"])  # from Excel
        base_id = str(row.iloc[0]["ID"])      # from Excel
        desired_local_base = f"Config-{base_name}-{base_id}"
        print(f"Found Backup File: {backup_name} -> saving as {desired_local_base}")
        download_from_sftp(backup_name, desired_local_base)

#!/opt/homebrew/bin/python3
"""
Google Sheets OAuth Setup for Metamonitor
Autoriseer gspread eenmalig, dan kan het automatisch data toevoegen.
"""

import os
import sys
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from oauth2client.client import OAuth2WebServerFlow, OAuth2Credentials
from oauth2client.tools import run_local_server
from pathlib import Path

CREDS_PATH = Path.home() / "recruitin" / "google_oauth_creds.json"
ENV_PATH = Path.home() / "recruitin" / ".env"

def setup_oauth():
    """Setup Google Sheets OAuth via browser"""
    print("🔐 Setting up Google Sheets OAuth...\n")

    # You need to create an OAuth app first
    print("""
    ⚠️  First, create a Google Cloud project:
    1. Go to https://console.cloud.google.com/
    2. Create a new project: "Metamonitor"
    3. Enable Google Sheets API
    4. Go to Credentials → Create OAuth 2.0 Client ID
    5. Download as JSON
    6. Save as: ~/recruitin/google_oauth_creds_template.json

    After doing this, run this script again.
    """)

def create_sheet():
    """Create a new Google Sheet for Metamonitor"""
    print("📊 Creating Metamonitor Google Sheet...\n")

    # For now, provide manual instructions
    print("""
    Manual Setup (Fastest):

    1. Go to Google Drive: https://drive.google.com/
    2. Create new Sheet: "Metamonitor Dashboard"
    3. Share it with your Google account (or keep it private)
    4. Copy the Sheet ID from the URL:
       https://docs.google.com/spreadsheets/d/[SHEET_ID]/edit
    5. Add these columns (Row 1):
       - Date
       - Campaign Name
       - Spend
       - Leads
       - CPL
       - Status
       - Instagram (Followers)

    6. Then run:
       python3 << 'EOF'
       sheet_id = "your_sheet_id_here"
       with open(os.path.expanduser("~/recruitin/.env"), "a") as f:
           f.write(f"GOOGLE_SHEETS_ID={sheet_id}\\n")
       EOF
    """)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "manual":
        create_sheet()
    else:
        print("🔧 Metamonitor → Google Sheets Setup\n")
        print("Choose an option:\n")
        print("1. Setup OAuth (Recommended if you have credentials)")
        print("2. Manual Setup (Fastest - just create a Google Sheet)\n")

        choice = input("Enter 1 or 2: ").strip()
        if choice == "1":
            setup_oauth()
        elif choice == "2":
            create_sheet()
        else:
            print("Invalid choice")

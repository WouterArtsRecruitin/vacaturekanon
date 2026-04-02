#!/opt/homebrew/bin/python3
"""
Authorize gspread with your Google account (one-time setup)
Opens browser for Google permission
"""

import sys
from pathlib import Path

print("🔐 Authorizing gspread...\n")

try:
    import gspread
    from google.auth.transport.requests import Request
    from google.oauth2.service_account import Credentials

    # Try to use gspread.oauth which handles browser auth
    print("📱 Opening browser for Google authorization...")
    print("   (A browser tab will open asking for permission)\n")

    # This will open a browser and save credentials locally
    gc = gspread.oauth(
        scopes=['https://www.googleapis.com/auth/spreadsheets']
    )

    print("✅ Successfully authorized!")
    print("   Credentials saved locally for future use.\n")
    print("🎉 You can now run: bash ~/recruitin/scripts/metamonitor_run.sh")

except ImportError as e:
    print(f"⚠️  Missing dependencies: {e}")
    print("\nInstalling required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "google-auth-oauthlib"])
    print("✅ Dependencies installed. Try again!")

except Exception as e:
    print(f"❌ Authorization failed: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure you have gspread and google-auth-oauthlib installed")
    print("2. Your browser should open automatically")
    print("3. If not, check terminal for a URL to open manually")
    sys.exit(1)

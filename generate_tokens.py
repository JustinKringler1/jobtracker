"""
Generate OAuth 2.0 Tokens for Gmail and Google Drive APIs.

This script must be run **locally** to generate authentication tokens required 
for accessing Gmail and Google Drive via Google APIs. It performs the following:
1. Authenticates with Google OAuth 2.0.
2. Generates `token.json` for Gmail API access.
3. Generates `drive_token.json` for Google Drive API access.
4. Saves the tokens locally for use in GitHub Actions.

After running this script:
- Upload `token.json` and `drive_token.json` to GitHub Secrets.
- GitHub Actions can then use these tokens without requiring manual authentication.

---

Usage:
Run the script locally using:
    python generate_tokens.py

Do not commit `token.json` or `drive_token.json` to GitHub. 
These files contain sensitive credentials.

"""

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Define OAuth scopes for Gmail and Google Drive APIs
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def generate_gmail_token():
    """
    Authenticate with Google OAuth 2.0 and generate `token.json` for Gmail API access.
    
    This function:
    - Uses OAuth 2.0 to authenticate the user.
    - Requests `readonly` access to Gmail messages.
    - Stores the generated token in `token.json`.

    If a token already exists and is valid, it is reused.
    """
    creds = None
    credentials_file = "credentials.json"

    # Check if a valid token already exists
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json")

    # If no valid credentials exist, authenticate the user
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the generated credentials to a token file
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    print("Gmail token successfully generated and saved as `token.json`.")


def generate_drive_token():
    """
    Authenticate with Google OAuth 2.0 and generate `drive_token.json` for Google Drive API access.
    
    This function:
    - Uses OAuth 2.0 to authenticate the user.
    - Requests access to read and write files in Google Drive.
    - Stores the generated token in `drive_token.json`.

    If a token already exists and is valid, it is reused.
    """
    creds = None
    credentials_file = "credentials.json"

    # Check if a valid token already exists
    if os.path.exists("drive_token.json"):
        creds = Credentials.from_authorized_user_file("drive_token.json")

    # If no valid credentials exist, authenticate the user
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_file, DRIVE_SCOPES)
            creds = flow.run_local_server(port=0)

        # Save the generated credentials to a token file
        with open("drive_token.json", "w") as token:
            token.write(creds.to_json())

    print("Google Drive token successfully generated and saved as `drive_token.json`.")


if __name__ == "__main__":
    """
    Entry point for token generation.

    - Runs both `generate_gmail_token()` and `generate_drive_token()`.
    - Ensures both authentication tokens are generated and saved locally.
    """
    print("Starting Google OAuth token generation process...")
    
    generate_gmail_token()
    generate_drive_token()
    
    print("\nToken generation complete.")
    print("Next Steps:")
    print("- Upload `token.json` and `drive_token.json` to GitHub Secrets.")
    print("- GitHub Actions can now use these tokens without manual authentication.")

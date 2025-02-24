# Job Tracker: Automated Email Classification & Storage

This script automates tracking job applications by:
- Fetching recent job-related emails from Gmail.
- Classifying emails using OpenAI's API (e.g., `Application Submitted`, `Interview Received`).
- Storing results in a Google Drive CSV file.
- Ensuring no duplicate processing.

The script runs daily via **GitHub Actions**, making job application tracking automated and effortless.

---

## Setup Guide

To set up and run this script, follow the steps below.

### 1. Google Cloud Setup

You'll need to enable **Gmail API** and **Google Drive API** in Google Cloud.

#### Step 1: Create a Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Click **"Select a project"** → **"New Project"** → Enter a name → Click **"Create"**.

#### Step 2: Enable Required APIs
Enable the following APIs for your project:
- [Enable Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com)
- [Enable Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com)

#### Step 3: Create OAuth Credentials
1. Go to **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**.
2. Under **Application Type**, select **Desktop App**.
3. Click **Create**, then **Download JSON file** (Save it as `credentials.json`).

---

### 2. Local Authentication & Token Generation

This script must be **run locally** to generate OAuth tokens before using GitHub Actions.

#### Step 1: Install Required Dependencies
Run the following command to install necessary Python packages:
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client openai
```

#### Step 2: Generate Tokens Locally
Run this script to authenticate and generate `token.json` and `drive_token.json`:
```bash
python generate_tokens.py
```
- A **browser will open**, asking for Google login and permissions.
- Click **"Allow"** to grant API access.
- The script will generate:
  - `token.json` → Authentication for Gmail API.
  - `drive_token.json` → Authentication for Google Drive API.

#### Step 3: Store Tokens in GitHub Secrets
Since GitHub Actions **cannot do interactive authentication**, store the generated tokens in **GitHub Secrets**:

1. Open `token.json` and `drive_token.json` in a text editor.
2. Copy their contents.
3. Go to **GitHub → Your Repository → Settings → Secrets**.
4. Add the following **GitHub Secrets**:

| Secret Name                 | Value (Paste from Local File) |
|-----------------------------|------------------------------|
| `OPENAI_API_KEY`            | Your OpenAI API Key         |
| `GMAIL_OAUTH_CREDENTIALS`   | `credentials.json` contents |
| `GMAIL_REFRESH_TOKEN`       | `token.json` contents       |
| `GOOGLE_DRIVE_REFRESH_TOKEN`| `drive_token.json` contents |
| `GOOGLE_DRIVE_FOLDER_ID`    | Google Drive folder ID      |

---

### 3. Running the Script

#### Run Locally
To run the script manually:
```bash
python track_jobs.py
```
- This fetches **job-related emails** from Gmail.
- It **classifies them** using OpenAI.
- The data is **stored in Google Drive**.

#### Run via GitHub Actions
The script is scheduled to **run daily** using GitHub Actions.  
You can also trigger it manually in **GitHub → Actions → "Run workflow"**.


---

## How the Script Works

### 1. Email Fetching
- The script retrieves **the last 24 hours** of emails.
- Extracts **Date, Sender, Subject, Snippet**.

### 2. OpenAI Email Classification
- Uses **GPT-4o** to classify emails into:
  - `Application Submitted`
  - `Interview Received`
  - `Rejection Notice`
  - `Follow-up Needed`
  - `Irrelevant`
  
### 3. Updating the CSV File in Google Drive
- The script checks for duplicates before adding new emails.
- Updates **Google Drive CSV file** with classified emails.

---

## File Structure
```
/jobtracker
│── track_jobs.py            # Main script to fetch, classify, and store job applications
│── generate_tokens.py       # Script to generate OAuth tokens for Gmail & Drive
│── .github/workflows        # GitHub Actions workflow configuration
│── README.md                # Documentation for the project
│── credentials.json         # OAuth credentials (DO NOT COMMIT)
│── token.json               # Gmail authentication token (store in GitHub Secrets)
│── drive_token.json         # Google Drive authentication token (store in GitHub Secrets)
```

---

## Troubleshooting

### Error: `GMAIL_REFRESH_TOKEN not set in GitHub Secrets`
**Solution:**
- Make sure `GMAIL_REFRESH_TOKEN` is correctly stored in GitHub Secrets.

### Error: `403: Access Denied` for Google Drive API
**Solution:**
- Ensure the **Google Drive API is enabled**.
- Make sure the **OAuth client has read & write permissions**.

---

## Future Improvements
- Add a **dashboard** to visualize job application trends.
- Allow **manual reclassification** of emails.
- Integrate **LinkedIn & Indeed tracking**.

---

## Contributing
If you want to improve this project, feel free to submit a **pull request**.  
For major changes, please open an **issue first**.

---

## License
This project is licensed under the **MIT License**.

---


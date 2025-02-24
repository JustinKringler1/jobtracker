# Job Tracker: Automated Email Classification & Storage

This script automates tracking job applications by:  
**Fetching recent job-related emails from Gmail**  
**Classifying emails using OpenAI's API** (e.g., `Application Submitted`, `Interview Received`)  
**Storing results in a Google Drive CSV file**  
**Ensuring no duplicate processing**  

The script runs **daily** via **GitHub Actions**, making job application tracking **automated and effortless**.  

---

## 🛠️ Setup Guide
To set up and run this script, follow the steps below:

### 1️⃣ Google Cloud Setup
You'll need to enable **Gmail API** and **Google Drive API** in Google Cloud.

#### Step 1: Create a Google Cloud Project
1. **Go to Google Cloud Console**:  
   👉 [Google Cloud Console](https://console.cloud.google.com/)  
2. Click **"Select a project"** → **"New Project"** → Enter a name → Click **"Create"**.

#### Step 2: Enable Required APIs
Enable the following APIs for your project:  
1. **Gmail API**  
   - 👉 [Enable Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com)  
2. **Google Drive API**  
   - 👉 [Enable Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com)  

#### Step 3: Create OAuth Credentials
1. Go to **APIs & Services** → **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**.
2. Under **Application Type**, select **Desktop App**.
3. Click **Create**, then **Download JSON file** (Save it as `credentials.json`).

---

### 2️⃣ Local Authentication & Token Generation
To run the script, you need to generate **OAuth tokens** for Gmail and Google Drive.

#### Step 1: Install Required Dependencies
Run the following command to install necessary Python packages:
```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client openai
```

#### Step 2: Generate Tokens
Run this script **once locally** to authenticate and generate `token.json` and `drive_token.json`:
```bash
python generate_tokens.py
```
- A **browser will open** → Log in and **grant permissions** for Gmail and Drive.
- It will generate **`token.json`** and **`drive_token.json`**, which store access tokens.
- NOTE these json files might need to be cleaned up due to how they are generated, you can use an llm to clean it but make sure it does not save your input.

#### Step 3: Store Tokens in GitHub Secrets
Since GitHub Actions **cannot perform interactive authentication**, store the tokens in **GitHub Secrets**:

1. Open `token.json` and `drive_token.json` and **copy the contents**.
2. Go to **GitHub → Your Repository → Settings → Secrets**.
3. Add the following **GitHub Secrets**:
   - **`GMAIL_REFRESH_TOKEN`** → Paste the contents of `token.json`.
   - **`GOOGLE_DRIVE_REFRESH_TOKEN`** → Paste the contents of `drive_token.json`.
   - **`GOOGLE_DRIVE_FOLDER_ID`** → **Google Drive folder ID** where the CSV file will be stored.
   - **`OPENAI_API_KEY`** → Your **OpenAI API key** from 👉 [OpenAI API Keys](https://platform.openai.com/account/api-keys).

---

### 3️⃣ Running the Script
#### Run Locally
To run the script manually:
```bash
python track_jobs.py
```
- This fetches **job-related emails** from Gmail.
- It **classifies them** using OpenAI.
- The data is **stored in Google Drive**.

#### Run via GitHub Actions
This script is scheduled to **run daily** using GitHub Actions.  
You can also trigger it manually in **GitHub → Actions → "Run workflow"**.

---

## ⚙️ How the Script Works
### 1️⃣ Email Fetching
- The script **retrieves the last 24 hours** of emails.
- Extracts **Date, Sender, Subject, Snippet**.

### 2️⃣ OpenAI Email Classification
- Uses **GPT-4o** to classify emails into:
  - `Application Submitted`
  - `Interview Received`
  - `Rejection Notice`
  - `Follow-up Needed`
  - `Irrelevant`
  
### 3️⃣ Updating the CSV File in Google Drive
- The script **checks for duplicates** before adding new emails.
- Updates **Google Drive CSV file** with classified emails.

---

## 📝 File Structure
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

## 🛠️ Troubleshooting
### Error: `GMAIL_REFRESH_TOKEN not set in GitHub Secrets`
Solution:
- Make sure **`GMAIL_REFRESH_TOKEN`** is correctly stored in GitHub Secrets.

### Error: `403: Access Denied` for Google Drive API
Solution:
- Ensure your **Google Drive API is enabled**.
- Make sure the **OAuth client has read & write permissions**.

---

## Future Improvements
- Add a **dashboard** to visualize job application trends.
- Allow **manual reclassification** of emails.
- Integrate **LinkedIn & Indeed tracking**.

---

## 💡 Contributing
Want to improve this project? **Feel free to submit a PR!**  
For major changes, please open an **issue first**.

---

## 📜 License
This project is licensed under **MIT License**.

---

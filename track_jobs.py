"""
Job Tracker Script
------------------
This script automates tracking job applications by:
1. Fetching recent emails from Gmail.
2. Classifying job-related emails using OpenAI's API.
3. Storing the results in a Google Drive CSV file.

It runs daily via GitHub Actions and ensures no duplicate processing.
"""

import os
import csv
import datetime
import json
import openai
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from io import BytesIO

def get_gmail_service():
    """Authenticate and return a Gmail API service instance."""
    creds = None
    token_json = os.getenv("GMAIL_REFRESH_TOKEN")
    
    if token_json:
        creds = Credentials.from_authorized_user_info(json.loads(token_json))
    else:
        raise ValueError("GMAIL_REFRESH_TOKEN not set in GitHub Secrets.")
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    return build('gmail', 'v1', credentials=creds)

def get_drive_service():
    """Authenticate and return a Google Drive API service instance."""
    creds = None
    token_json = os.getenv("GOOGLE_DRIVE_REFRESH_TOKEN")
    
    if token_json:
        creds = Credentials.from_authorized_user_info(json.loads(token_json))
    else:
        raise ValueError("GOOGLE_DRIVE_REFRESH_TOKEN not set in GitHub Secrets.")
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    return build('drive', 'v3', credentials=creds)

from datetime import datetime, timedelta

def fetch_recent_emails():
    """
    Retrieves emails from Gmail for the last 24 hours and extracts relevant details.
    Includes logging to verify email retrieval.
    """
    service = get_gmail_service()
    
    # Calculate the timestamp for 24 hours ago
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y/%m/%d")
    query = f"after:{yesterday}"  # Fetches emails after yesterday
    
    print(f"Fetching emails using query: {query}")

    try:
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])

        if not messages:
            print("No emails found in the last 24 hours.")
            return []

        email_data = []
        for msg in messages:
            msg_details = service.users().messages().get(userId='me', id=msg['id']).execute()
            headers = msg_details.get('payload', {}).get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
            sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown Sender")
            date_received = next((h['value'] for h in headers if h['name'] == 'Date'), "Unknown Date")
            snippet = msg_details.get('snippet', "")

            email_data.append((date_received, sender, subject, snippet))

        print(f"Retrieved {len(email_data)} emails from Gmail.")
        for i, email in enumerate(email_data[:5]):  # Print first 5 emails for verification
            print(f"Email {i+1}: From: {email[1]} | Subject: {email[2]}")
        
        return email_data

    except Exception as e:
        print(f"Error fetching emails from Gmail: {str(e)}")
        return []


def classify_email(content, sender, subject):
    """
    Classifies an email's content into predefined categories using OpenAI.
    Ensures only the correct classification label is returned.

    :param content: The email content (subject + snippet).
    :param sender: The email sender.
    :param subject: The email subject.
    :return: (category, sender, subject, snippet)
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")

    # Auto-classify as "Irrelevant" if the sender is missing
    if not sender or sender.strip() == "":
        return "Irrelevant", sender, subject, content[:100]

    # Auto-classify as "Irrelevant" for GitHub and automated emails
    if "github.com" in sender.lower():
        return "Irrelevant", sender, subject, content[:100]

    # Define system instructions for OpenAI
    system_prompt = (
    "You are an AI assistant designed to track job application statuses from email communications. "
    "Your task is to analyze emails and classify them strictly based on their relevance to job applications. "
    "Ignore any emails that are unrelated to job searches, applications, interviews, or rejections.\n\n"
    
    "Classify emails into one of the following categories:\n"
    "- Application Submitted: The email confirms that a job application has been successfully submitted.\n"
    "- Interview Received: The email contains an invitation to interview for a job.\n"
    "- Rejection Notice: The email states that an application has been rejected.\n"
    "- Follow-up Needed: The email requests additional information, assessments, or action related to a job application.\n"
    "- Irrelevant: The email does not pertain to job applications or status updates.\n\n"
    
    "Rules:\n"
    "1. Return only the category name, with no extra words or formatting.\n"
    "2. If an email contains a mix of relevant and irrelevant information, classify it based only on job-related content.\n"
    "3. If unsure, return 'Irrelevant'.\n"
)


    user_prompt = f"Email Subject: {subject}\n\nEmail Content: {content}\n\nWhat is the correct category?"

    # Call OpenAI (Using GPT-4o for cost efficiency)
    response = openai.chat.completions.create(
        model="gpt-4o",  # Switched to GPT-4o to reduce costs
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    # Extract response and ensure only the category name is returned
    classification = response.choices[0].message.content.strip()

    # Ensure only valid categories are returned
    valid_categories = [
        "Application Submitted", "Interview Received", 
        "Rejection Notice", "Follow-up Needed", "Irrelevant"
    ]

    if classification not in valid_categories:
        return "Irrelevant", sender, subject, content[:100]

    return classification, sender, subject, content[:100]


import csv
import os
from io import BytesIO
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload

def update_csv(email_data):
    """
    Updates the job applications CSV file stored in Google Drive.
    Ensures no duplicate entries and properly processes new emails.

    :param email_data: List of tuples (date_received, sender, subject, snippet).
    """
    drive_service = get_drive_service()
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    filename = "job_applications.csv"
    file_id = None
    existing_data = set()
    csv_has_data = False  # Track whether the CSV has actual email data

    # Check if CSV file exists in Google Drive
    response = drive_service.files().list(q=f"name='{filename}' and '{folder_id}' in parents", fields='files(id)').execute()
    files = response.get('files', [])

    # If a file exists, read its contents
    if files:
        file_id = files[0]['id']
        request = drive_service.files().get_media(fileId=file_id)
        file_stream = BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        file_stream.seek(0)

        # Read existing CSV and store unique email records
        csv_reader = csv.reader(file_stream.read().decode('utf-8').splitlines())
        headers = next(csv_reader, None)  # Read header row
        for row in csv_reader:
            if len(row) >= 5:  # Ensure it's a valid row with content
                existing_data.add(tuple(row))
                csv_has_data = True  # Marks that there is real email data

    new_entries = []
    
    for date_received, sender, subject, snippet in email_data:
        # Ensure classification is based on sender & subject
        category, classified_sender, classified_subject, classified_snippet = classify_email(snippet, sender, subject)
        new_entry_key = (date_received, category, classified_sender, classified_subject, classified_snippet)

        # If the CSV only had headers (no data), process all emails
        if not csv_has_data:
            new_entries.append(new_entry_key)  # Add full data row
            existing_data.add(new_entry_key)  # Prevent future duplicates

        # Otherwise, add only unique and relevant emails
        elif category != "Irrelevant" and new_entry_key not in existing_data:
            new_entries.append(new_entry_key)
            existing_data.add(new_entry_key)  # Prevent future duplicates

    # If the CSV exists but only had headers, process all emails
    if not csv_has_data and new_entries:
        print("CSV only contained headers. Processing all emails.")

    # If no new entries, return
    if not new_entries:
        print("No new unique emails to classify.")
        return

    # Correct header order
    column_headers = ["Date", "Category", "Sender", "Subject", "Snippet"]

    # Write CSV file (Ensures single header row)
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(column_headers)
        for entry in existing_data.union(new_entries):  # Combine old + new emails
            writer.writerow(entry)  # Ensure the correct data structure

    # Upload updated CSV to Google Drive
    media = MediaFileUpload(filename, mimetype='text/csv', resumable=True)
    if file_id:
        drive_service.files().update(fileId=file_id, media_body=media).execute()
    else:
        file_metadata = {'name': filename, 'parents': [folder_id]}
        drive_service.files().create(body=file_metadata, media_body=media).execute()

    print("CSV file updated successfully.")

def main():
    """Main function to fetch, classify, and store job application emails."""
    emails = fetch_recent_emails()
    if emails:
        update_csv(emails)
    print("Job application tracking updated in Google Drive.")

if __name__ == "__main__":
    main()

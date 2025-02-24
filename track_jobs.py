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
    creds = None
    token_json = os.getenv("GOOGLE_DRIVE_REFRESH_TOKEN")
    
    if token_json:
        creds = Credentials.from_authorized_user_info(json.loads(token_json))
    else:
        raise ValueError("GOOGLE_DRIVE_REFRESH_TOKEN not set in GitHub Secrets.")
    
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    
    return build('drive', 'v3', credentials=creds)

def fetch_recent_emails():
    service = get_gmail_service()
    query = "newer_than:1d"  # Emails from last 24 hours
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    
    email_data = []
    for msg in messages:
        msg_details = service.users().messages().get(userId='me', id=msg['id']).execute()
        headers = msg_details['payload']['headers']
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "No Subject")
        sender = next((h['value'] for h in headers if h['name'] == 'From'), "Unknown Sender")
        date_received = next((h['value'] for h in headers if h['name'] == 'Date'), "Unknown Date")
        snippet = msg_details.get('snippet', "")
        email_data.append((date_received, sender, subject, snippet))
    
    return email_data

def classify_email(content):
    openai.api_key = os.getenv("OPENAI_API_KEY")
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful email classifier. Always output in the format: Category|Sender|Subject|Snippet."},
            {"role": "user", "content": f"""Classify the following email into one of these categories: 
            - Application Submitted 
            - Interview Received 
            - Rejection Notice 
            - Follow-up Needed 
            - Irrelevant 
            
            Format your response as: Category|Sender|Subject|Snippet 
            
            Email: {content}"""}
        ]
    )
    
    classification = response["choices"][0]["message"]["content"].strip()
    parts = classification.split('|')
    
    if len(parts) == 4:
        return parts[0], parts[1], parts[2], parts[3]
    else:
        return "Irrelevant", "Unknown", "Invalid Response", content[:50]

def update_csv(email_data):
    drive_service = get_drive_service()
    folder_id = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
    filename = "job_applications.csv"
    file_id = None
    existing_data = set()
    
    response = drive_service.files().list(q=f"name='{filename}' and '{folder_id}' in parents", fields='files(id)').execute()
    files = response.get('files', [])
    
    if files:
        file_id = files[0]['id']
        request = drive_service.files().get_media(fileId=file_id)
        file_stream = BytesIO()
        downloader = MediaIoBaseDownload(file_stream, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        file_stream.seek(0)
        csv_reader = csv.reader(file_stream.read().decode('utf-8').splitlines())
        next(csv_reader)  # Skip header
        for row in csv_reader:
            existing_data.add(tuple(row))
    
    with open(filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Date", "Category", "Sender", "Subject", "Snippet"])
        for date_received, sender, subject, snippet in email_data:
            category, classified_sender, classified_subject, classified_snippet = classify_email(f"{subject}\n{snippet}")
            new_entry = (date_received, category, classified_sender, classified_subject, classified_snippet)
            if new_entry not in existing_data:
                writer.writerow(new_entry)
    
    media = MediaFileUpload(filename, mimetype='text/csv', resumable=True)
    if file_id:
        drive_service.files().update(fileId=file_id, media_body=media).execute()
    else:
        file_metadata = {'name': filename, 'parents': [folder_id]}
        drive_service.files().create(body=file_metadata, media_body=media).execute()

def main():
    emails = fetch_recent_emails()
    if emails:
        update_csv(emails)
    print("Job application tracking updated in Google Drive.")

if __name__ == "__main__":
    main()


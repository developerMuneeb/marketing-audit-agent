import os
import time
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError
import io

# Import necessary config variables
from config import (
    LOG_FOLDER_NAME, LOG_SHEET_NAME, LOG_HEADERS
)

SCOPES = ['https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/spreadsheets']
CLIENT_SECRET_FILE = 'client_secret.json'
TOKEN_FILE = 'token.json'

class GoogleClients:
    def __init__(self):
        self.creds = None
        self.drive_service = None
        self.sheets_service = None
        self._authenticate_google()

    def _authenticate_google(self):
        """Handles OAuth 2.0 authentication."""
        if os.path.exists(TOKEN_FILE):
            self.creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
                self.creds = flow.run_local_server(port=0)
            with open(TOKEN_FILE, 'w') as token:
                token.write(self.creds.to_json())
        
        try:
            self.drive_service = build('drive', 'v3', credentials=self.creds)
            self.sheets_service = build('sheets', 'v4', credentials=self.creds)
        except Exception as e:
            print(f"Failed to build Google services: {e}")
            self.drive_service = None
            self.sheets_service = None

    def find_or_create_folder(self, parent_folder_id: str, folder_name: str) -> str or None:
        """Finds a folder by name inside a parent, or creates it if it doesn't exist."""
        print(f"  [Drive] Searching for folder '{folder_name}'...")
        query = (f"name='{folder_name}' and '{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false")
        
        try:
            results = self.drive_service.files().list(
                q=query, 
                spaces='drive', 
                fields='nextPageToken, files(id, name)'
            ).execute()
            
            items = results.get('files', [])
            if items:
                return items[0]['id']
            else:
                print(f"  [Drive] Folder '{folder_name}' not found. Creating...")
                file_metadata = {
                    'name': folder_name,
                    'mimeType': 'application/vnd.google-apps.folder',
                    'parents': [parent_folder_id]
                }
                folder = self.drive_service.files().create(body=file_metadata, fields='id').execute()
                return folder.get('id')
        except HttpError as error:
            print(f"  [Drive Error] Failed to find or create folder: {error}")
            return None

    def upload_file_to_drive(self, docx_path, doc_title, parent_folder_id):
        """
        Uploads a local DOCX file and CONVERTS it to a Google Doc.
        Used for the Marketing Audit Report.
        """
        try:
            media = MediaFileUpload(docx_path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document', resumable=True)
            file_metadata = {
                'name': doc_title, 
                'parents': [parent_folder_id], 
                'mimeType': 'application/vnd.google-apps.document' # Convert to Google Doc
            }
            
            print(f"    [Drive] Uploading and converting '{doc_title}'...")
            file = self.drive_service.files().create(
                body=file_metadata, 
                media_body=media, 
                fields='id, webViewLink'
            ).execute()
            
            print(f"    ✅ Successfully created Google Doc '{doc_title}'.")
            return file.get('webViewLink') if file else None
            
        except HttpError as error:
            print(f"    [Drive Error] {error}")
            return None
        except FileNotFoundError:
             print(f"    ❌ [Local Error] File not found: {docx_path}")
             return None

    def upload_audio_asset(self, parent_folder_id, file_path, file_name):
        """
        Uploads an MP3 audio file as-is (binary).
        Used for Voiceovers.
        """
        try:
            if not os.path.exists(file_path):
                print(f"    ❌ [Local Error] Audio file not found: {file_path}")
                return None

            media = MediaFileUpload(file_path, mimetype='audio/mpeg', resumable=True)
            file_metadata = {'name': file_name, 'parents': [parent_folder_id]}
            
            print(f"    [Drive] Uploading audio '{file_name}'...")
            file = self.drive_service.files().create(
                body=file_metadata, 
                media_body=media, 
                fields='id, webViewLink'
            ).execute()
            
            print(f"    ✅ Successfully uploaded audio: {file_name}")
            return file.get('webViewLink')
        except Exception as e:
            print(f"    ❌ Audio Upload Failed: {e}")
            return None

    def upload_video_asset(self, parent_folder_id, file_path, file_name):
        """
        Uploads an MP4 video file as-is (binary).
        Used for the final Video Ad.
        """
        try:
            if not os.path.exists(file_path):
                print(f"    ❌ [Local Error] Video file not found: {file_path}")
                return None

            media = MediaFileUpload(file_path, mimetype='video/mp4', resumable=True)
            file_metadata = {'name': file_name, 'parents': [parent_folder_id]}
            
            print(f"    [Drive] Uploading video '{file_name}'...")
            file = self.drive_service.files().create(
                body=file_metadata, 
                media_body=media, 
                fields='id, webViewLink'
            ).execute()
            
            print(f"    ✅ Successfully uploaded video: {file_name}")
            return file.get('webViewLink')
        except Exception as e:
            print(f"    ❌ Video Upload Failed: {e}")
            return None

    def log_to_google_sheet(self, log_sheet_id, target_log_tab_name, log_row_data):
        # ... existing log logic if needed ...
        pass
from googleapiclient.discovery import build
from google.oauth2 import service_account
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
import os
import toml

SCOPES = ['https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'api\service_account.json'
PARENT_FOLDER_ID = '1dAvTsTgVnrQxZohqHuHgZ9IgJ9xCal1n'

def authenticate():
    # Load the secrets from secrets.toml
    secrets = toml.load('.streamlit/secrets.toml')
    google_service_account = secrets['google_service_account']
    
    # Convert the TOML dictionary to the format expected by from_service_account_info
    creds = service_account.Credentials.from_service_account_info(google_service_account, scopes=SCOPES)
    return creds

# Functions to create and delete folders
def create_folder(name):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [PARENT_FOLDER_ID]
    }
    file = service.files().create(body=file_metadata, fields='id').execute()
    return file.get('id')

def delete_folder(folder_id):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    service.files().delete(fileId=folder_id).execute()

def create_folder_in_folder(parent_folder_id, name):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    file_metadata = {
        'name': name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    file = service.files().create(body=file_metadata, fields='id').execute()
    return file.get('id')

# upload a file to a folder given the folder id, file path, and file name
def upload_file_to_folder(folder_id, file_path, file_name):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    
    file_metadata = {
        'name': file_name,
        'parents': [folder_id]
    }
    
    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    
    return file.get('id')

# download a file from a folder
def download_file_from_folder(folder_id, file_id, file_path):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    request = service.files().get_media(fileId=file_id)
    fh = open(file_path, 'wb')
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    fh.close()

# delete a file from a folder
def delete_file_from_folder(file_id):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    service.files().delete(fileId=file_id).execute()

# list all files in a folder, include file id, name, date created, date modified, size, and type
def list_files_in_folder(folder_id):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    results = service.files().list(q=f"'{folder_id}' in parents", fields="files(id, name, createdTime, modifiedTime, size, mimeType)").execute()
    items = results.get('files', [])
    return items

# Filter based on given text input on name
def filter_files_in_folder(folder_id, name):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    results = service.files().list(q=f"'{folder_id}' in parents and name contains '{name}'", fields="files(id, name, createdTime, modifiedTime, size, mimeType)").execute()
    items = results.get('files', [])
    return items

# Get the parent of a given folder, returns the parent folder id
def get_parent_folder(folder_id):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    file = service.files().get(fileId=folder_id, fields='parents').execute()
    return file.get('parents')[0]

# Get folder name given the folder id
def get_folder_name(folder_id):
    creds = authenticate()
    service = build('drive', 'v3', credentials=creds)
    file = service.files().get(fileId=folder_id, fields='name').execute()
    return file.get('name')

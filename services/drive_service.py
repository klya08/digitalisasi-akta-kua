import os
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/drive.readonly']
SERVICE_ACCOUNT_FILE = 'credentials.json'

def get_drive_service():
    """Membuka koneksi ke Google Drive API."""
    try:
        creds = Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('drive', 'v3', credentials=creds)
        return service
    except Exception as e:
        print(f"Error saat autentikasi: {e}")
        return None

def get_folder_id_by_name(service, folder_name):
    """
    JURUS BARU: Mencari ID Folder secara otomatis hanya dengan bermodalkan nama foldernya.
    """
    try:
        # Mencari file yang tipenya adalah 'folder' dan namanya sesuai dengan inputan
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = service.files().list(
            q=query,
            fields="files(id, name)",
            supportsAllDrives=True,
            includeItemsFromAllDrives=True
        ).execute()
        
        folders = results.get('files', [])
        if folders:
            # Mengembalikan ID dari folder pertama yang namanya cocok
            return folders[0]['id']
            
    except Exception as e:
        print(f"Error mencari folder {folder_name}: {e}")
        
    return None

def get_pdfs_by_folder(service, folder_id):
    """Mengambil file PDF HANYA dari dalam Folder ID target."""
    pdf_list = []
    page_token = None
    folder_id = str(folder_id).strip()
    
    try:
        while True:
            query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
            results = service.files().list(
                q=query,
                fields="nextPageToken, files(id, name)",
                pageSize=1000,
                pageToken=page_token,
                includeItemsFromAllDrives=True,
                supportsAllDrives=True
            ).execute()
            
            items = results.get('files', [])
            for item in items:
                pdf_list.append({
                    'id': item['id'],
                    'name': item['name'],
                    'link': f"https://drive.google.com/file/d/{item['id']}/view"
                })
                
            page_token = results.get('nextPageToken')
            if not page_token:
                break
    except Exception as e:
        print(f"Error saat membaca Drive: {e}")
        
    return pdf_list
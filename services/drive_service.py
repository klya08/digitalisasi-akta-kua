import os
import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build

def get_drive_service():
    """Menghubungkan ke Google Drive (Bisa untuk Lokal maupun Internet)"""
    SCOPES = ['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/drive.metadata.readonly']
    
    try:
        # 1. JIKA BERJALAN DI INTERNET (Membaca brankas rahasia Streamlit Secrets)
        if "google_credentials" in st.secrets:
            creds_dict = json.loads(st.secrets["google_credentials"])
            creds = service_account.Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            
        # 2. JIKA BERJALAN DI LAPTOP (Membaca file credentials.json)
        else:
            creds = service_account.Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
            
        service = build('drive', 'v3', credentials=creds)
        return service
        
    except Exception as e:
        print(f"Gagal menghubungkan ke Google Drive: {e}")
        return None

# (Biarkan fungsi get_folder_id_by_name dan get_pdfs_by_folder yang ada di bawahnya tetap seperti semula. Jika kamu tadi menghapus semuanya, pastikan fungsi tersebut juga ikut di-paste kembali. Untuk amannya, ini kode lengkapnya:)

def get_folder_id_by_name(service, folder_name):
    query = f"mimeType='application/vnd.google-apps.folder' and name='{folder_name}' and trashed=false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])
    if not items:
        return None
    return items[0]['id']

def get_pdfs_by_folder(service, folder_id):
    query = f"'{folder_id}' in parents and mimeType='application/pdf' and trashed=false"
    pdf_list = []
    page_token = None
    while True:
        results = service.files().list(
            q=query, 
            fields="nextPageToken, files(id, name)",
            pageToken=page_token,
            pageSize=1000
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
    return pdf_list

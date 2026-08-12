import re

def normalize_text(text):
    """
    Berfungsi untuk menormalisasi teks (nama suami, istri, dll):
    - Mengubah ke huruf kecil (lowercase)
    - Menghapus gelar/karakter khusus yang sering mengganggu
    - Mengganti pemisah seperti garis bawah, strip, dan spasi berlebih menjadi spasi biasa
    """
    if not text or pd_isna(text):
        return ""
    
    # Ubah ke string dan jadikan huruf kecil semua
    text = str(text).lower()
    
    # Menghapus karakter khusus selain huruf, angka, dan spasi/pemisah dasar
    # Mengganti tanda hubung (-), garis bawah (_), dan titik (.) dengan spasi
    text = text.replace('_', ' ').replace('-', ' ').replace('.', ' ')
    
    # Menghapus spasi berlebih (ganda)
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def pd_isna(val):
    """Fungsi pembantu untuk mengecek data kosong."""
    import pandas as pd
    return pd.isna(val)

def normalize_date(date_val):
    """
    Menyeragamkan format tanggal agar mudah dicocokkan.
    Mendukung format dari Excel (datetime) maupun string teks.
    """
    if not date_val or pd_isna(date_val):
        return ""
    
    try:
        # Jika formatnya sudah datetime dari pandas
        import pandas as pd
        if isinstance(date_val, (pd.Timestamp, datetime_type())):
            return date_val.strftime('%Y-%m-%d')
        
        # Jika berupa string, ubah ke bentuk standar YYYY-MM-DD
        # Bisa dikembangkan lebih lanjut sesuai format tanggal di Excel kamu
        parsed_date = pd.to_datetime(date_val, errors='coerce')
        if not pd.isna(parsed_date):
            return parsed_date.strftime('%Y-%m-%d')
            
    except Exception:
        pass
        
    return str(date_val).strip()

def datetime_type():
    import datetime
    return datetime.datetime
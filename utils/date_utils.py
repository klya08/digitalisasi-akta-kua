import pandas as pd

def parse_excel_date(date_val):
    """Memastikan tanggal dari Excel terbaca konsisten berformat YYYY-MM-DD."""
    if pd.isna(date_val):
        return ""
    try:
        dt = pd.to_datetime(date_val, errors='coerce')
        if pd.isna(dt):
            return str(date_val).strip()
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return str(date_val).strip()
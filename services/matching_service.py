import os
import sys
import pandas as pd
import re
from thefuzz import fuzz

# Menambahkan root folder ke path agar modul utils bisa dibaca
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.date_utils import parse_excel_date

def clean_for_match(text):
    """JURUS SAPU JAGAT: Ekstrak HANYA huruf dan angka, ubah ke huruf kecil semua."""
    if pd.isna(text) or text is None:
        return ""
    return re.sub(r'[^a-z0-9]', '', str(text).lower().strip())

def match_data_row(row, pdf_list):
    """Mencocokkan data murni berdasarkan nama, ditambah BONUS POIN jika tanggal cocok."""
    
    # 1. Bersihkan nama dari Excel
    suami_clean = clean_for_match(row.get('SUAMI_NAMA', ''))
    istri_clean = clean_for_match(row.get('ISTRI_NAMA', ''))
    
    # 2. Ambil dan bersihkan tanggal (contoh output parse: 2018-08-27 -> 20180827)
    tanggal_raw = parse_excel_date(row.get('TGLNIKAHMASEHI', ''))
    tanggal_clean = clean_for_match(tanggal_raw)
    
    # Antisipasi jika di PDF petugas KUA menulisnya dengan format DDMMYYYY (27082018)
    tanggal_balik = ""
    if len(tanggal_clean) == 8:
        tanggal_balik = tanggal_clean[6:8] + tanggal_clean[4:6] + tanggal_clean[0:4]
    
    candidates = []

    # Kita cek ke semua PDF di dalam folder tahun tersebut
    for pdf in pdf_list:
        pdf_clean = clean_for_match(pdf['name'])
        
        score = 0
        match_reasons = []

        # 3. Cek Kecocokan Suami (Nilai Maksimal 40)
        if suami_clean and len(suami_clean) > 2:
            if suami_clean in pdf_clean:
                score += 40
                match_reasons.append("Suami Cocok")
            else:
                suami_score = fuzz.partial_ratio(suami_clean, pdf_clean)
                if suami_score >= 85:
                    score += 40
                    match_reasons.append(f"Suami Mirip ({suami_score}%)")

        # 4. Cek Kecocokan Istri (Nilai Maksimal 40)
        if istri_clean and len(istri_clean) > 2:
            if istri_clean in pdf_clean:
                score += 40
                match_reasons.append("Istri Cocok")
            else:
                istri_score = fuzz.partial_ratio(istri_clean, pdf_clean)
                if istri_score >= 85:
                    score += 40
                    match_reasons.append(f"Istri Mirip ({istri_score}%)")

        # 5. Cek Kecocokan Tanggal sebagai BONUS POIN (Nilai Maksimal 20)
        if tanggal_clean and len(tanggal_clean) == 8:
            # Apakah angka '20180827' atau '27082018' ada di dalam nama file PDF?
            if tanggal_clean in pdf_clean or tanggal_balik in pdf_clean:
                score += 20
                match_reasons.append("Tanggal Cocok")

        # Masukkan ke daftar jika minimal salah satu nama ketemu
        if score >= 40:
            candidates.append({
                'pdf_name': pdf['name'],
                'pdf_link': pdf['link'],
                'score': score,
                'reasons': match_reasons
            })

    # Evaluasi Akhir
    if not candidates:
        return {'status': 'NOT FOUND', 'pdf_name': '-', 'pdf_link': '', 'score': 0}

    # Urutkan berdasarkan skor tertinggi (PDF dengan skor 100 karena nama & tanggal cocok akan di urutan pertama)
    candidates = sorted(candidates, key=lambda x: x['score'], reverse=True)
    best_candidate = candidates[0]

    # Lulus (MATCHED) jika total skor minimal 80 (bisa Suami+Istri, atau Suami+Tanggal dll)
    if best_candidate['score'] >= 80:
        if len(candidates) > 1 and candidates[1]['score'] == best_candidate['score']:
            return {'status': 'AMBIGUOUS', 'pdf_name': f"Ada {len(candidates)} PDF serupa", 'pdf_link': '', 'score': best_candidate['score']}
        return {'status': 'MATCHED', 'pdf_name': best_candidate['pdf_name'], 'pdf_link': best_candidate['pdf_link'], 'score': best_candidate['score']}
    else:
        return {'status': 'AMBIGUOUS', 'pdf_name': best_candidate['pdf_name'], 'pdf_link': best_candidate['pdf_link'], 'score': best_candidate['score']}
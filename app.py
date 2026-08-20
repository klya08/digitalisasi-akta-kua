import streamlit as st
import pandas as pd
from io import BytesIO
import streamlit_authenticator as stauth

# Memanggil fungsi layanan kita
from services.drive_service import get_drive_service, get_folder_id_by_name, get_pdfs_by_folder
from services.matching_service import match_data_row

# WAJIB DI PALING ATAS: Pengaturan halaman
st.set_page_config(page_title="Digitalisasi Arsip Akta Nikah KUA", page_icon="📖", layout="wide")

# ==========================================
# BAGIAN 1: LOGIKA KEAMANAN & LOGIN
# ==========================================
try:
    # Menarik data rahasia dari file secrets.toml
    credentials = dict(st.secrets["credentials"])
    cookie = st.secrets["cookie"]
    preauthorized = st.secrets["preauthorized"]

    # Mengaktifkan sistem login
    authenticator = stauth.Authenticate(
        credentials,
        cookie["name"],
        cookie["key"],
        cookie["expiry_days"],
        preauthorized
    )

    # Menampilkan form login
    name, authentication_status, username = authenticator.login('main')

    if authentication_status == False:
        st.error('❌ Username atau password salah! Silakan coba lagi.')
    elif authentication_status == None:
        st.info('🔒 Silakan masukkan username dan password untuk mengakses Arsip KUA.')
        
    # Jika Login Berhasil, tampilkan aplikasi utama:
    elif authentication_status == True:
        
        # ==========================================
        # BAGIAN 2: APLIKASI UTAMA (Hanya tampil jika login)
        # ==========================================
        
        # Menambahkan tombol Logout di sidebar beserta sapaan
        authenticator.logout('Logout', 'sidebar')
        st.sidebar.write(f'👤 Selamat datang, **{name}**!')

        st.title("📖 Digitalisasi Arsip Akta Nikah KUA")
        st.write("---")

        st.sidebar.header("📁 Panel Kontrol")
        st.sidebar.info("Cukup ketik tahun laporan, sistem akan otomatis mencari folder tersebut di Google Drive.")

        # Langkah 1: Upload dan Input Tahun
        st.write("### Langkah 1: Upload File Excel & Tentukan Tahun")
        col1, col2 = st.columns([2, 1])

        with col1:
            uploaded_file = st.file_uploader("Pilih file Excel (.xlsx)", type=["xlsx"])
        with col2:
            tahun_target = st.text_input("📅 Tahun Target Folder:", value="2018")

        if uploaded_file is not None:
            try:
                df = pd.read_excel(uploaded_file)
                
                st.info(f"📊 Ditemukan **{len(df)} baris data** di dalam file Excel yang siap diproses.")
                
                st.write("---")
                
                # Langkah 2: Proses Pencocokan
                st.write("### Langkah 2: Proses Pencocokan Otomatis")
                
                if st.button("🚀 Mulai Proses Pencocokan", type="primary"):
                    if not tahun_target:
                        st.warning("Harap isi Tahun Target terlebih dahulu!")
                    else:
                        with st.spinner(f"Mencari folder '{tahun_target}' di Google Drive KUA..."):
                            service = get_drive_service()
                            if not service:
                                st.error("Gagal terhubung ke Google Drive. Periksa 'credentials.json'.")
                            else:
                                target_folder_id = get_folder_id_by_name(service, tahun_target)
                                
                                if not target_folder_id:
                                    st.error(f"❌ Folder '{tahun_target}' TIDAK DITEMUKAN di Google Drive KUA.")
                                else:
                                    st.success(f"✅ Folder '{tahun_target}' ditemukan secara otomatis!")
                                    
                                    with st.spinner(f"Memindai seluruh isi PDF di dalam folder {tahun_target}..."):
                                        pdf_list = get_pdfs_by_folder(service, target_folder_id)
                                    
                                    if len(pdf_list) > 0:
                                        st.info(f"📁 Berhasil mengumpulkan **{len(pdf_list)} file PDF** dari Google Drive.")
                                        
                                        with st.spinner("Sedang mencocokkan data..."):
                                            results_data = []
                                            
                                            for index, row in df.iterrows():
                                                match_res = match_data_row(row, pdf_list)
                                                
                                                row_dict = row.to_dict()
                                                row_dict['STATUS_MATCH'] = match_res['status']
                                                row_dict['FILE_PDF_DRIVE'] = match_res['pdf_name']
                                                row_dict['LINK_AKTA_GDRIVE'] = match_res['pdf_link']
                                                
                                                results_data.append(row_dict)
                                            
                                            result_df = pd.DataFrame(results_data)
                                            
                                            # Menggunakan garis miring DD/MM/YYYY
                                            for col in result_df.select_dtypes(include=['datetime64[ns]', 'datetime64']).columns:
                                                result_df[col] = result_df[col].dt.strftime('%d/%m/%Y')
                                                
                                            if 'TGLNIKAHMASEHI' in result_df.columns:
                                                try:
                                                    result_df['TGLNIKAHMASEHI'] = pd.to_datetime(result_df['TGLNIKAHMASEHI']).dt.strftime('%d/%m/%Y')
                                                except:
                                                    pass
                                            
                                            st.session_state['result_df'] = result_df
                                            
                                        st.success(f"🎉 Proses pencocokan untuk **{len(df)} data Excel** telah selesai!")
                                    else:
                                        st.warning(f"Folder '{tahun_target}' ditemukan, tetapi tidak ada file PDF di dalamnya.")
                
                # Langkah 3: Preview Hasil dan Download
                if 'result_df' in st.session_state:
                    res_df = st.session_state['result_df']
                    
                    st.write("---")
                    st.write("### Langkah 3: Preview Interaktif & Unduh")
                    st.caption("💡 **TIPS EXCEL:** Tabel di bawah ini interaktif! Kamu bisa mengklik, menggeser, melakukan copy-paste, bahkan mengubah isi sel secara langsung sebelum mengunduhnya.")
                    
                    col_met1, col_met2, col_met3, col_met4 = st.columns(4)
                    col_met1.metric("Total Data", len(res_df))
                    col_met2.metric("Matched (Hijau)", len(res_df[res_df['STATUS_MATCH'] == 'MATCHED']))
                    col_met3.metric("Not Found (Merah)", len(res_df[res_df['STATUS_MATCH'] == 'NOT FOUND']))
                    col_met4.metric("Ambiguous (Kuning)", len(res_df[res_df['STATUS_MATCH'] == 'AMBIGUOUS']))
                    
                    def color_status(val):
                        if val == 'MATCHED': return 'background-color: #d4edda; color: #155724;'
                        elif val == 'NOT FOUND': return 'background-color: #f8d7da; color: #721c24;'
                        elif val == 'AMBIGUOUS': return 'background-color: #fff3cd; color: #856404;'
                        return ''

                    edited_df = st.data_editor(
                        res_df.style.map(color_status, subset=['STATUS_MATCH']),
                        use_container_width=True,
                        height=400,
                    )
                    
                    st.write("<br>", unsafe_allow_html=True) 
                    
                    nama_file_kustom = st.text_input("📝 Jika hasil pratinjau sudah sesuai, beri nama file untuk menyimpannya:", value=f"Laporan_Hasil_Pencocokan_{tahun_target}.xlsx")
                    
                    if not nama_file_kustom.endswith(".xlsx"):
                        nama_file_kustom += ".xlsx"
                    
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        edited_df.to_excel(writer, index=False, sheet_name='Laporan_Akta')
                    processed_data = output.getvalue()
                    
                    st.download_button(
                        label=f"📥 Download Data Sekarang",
                        data=processed_data,
                        file_name=nama_file_kustom,
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        type="primary"
                    )
                    
            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")


            except Exception as e:
                st.error(f"Error aslinya adalah: {e}")
                st.exception(e)

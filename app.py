import streamlit as st
import pandas as pd
import requests

# Set tampilan agar lebih rapi di HP
st.set_page_config(page_title="Sistem RT 03", layout="wide")

# --- 1. KONFIGURASI LINK (GANTI DI SINI) ---
# Link untuk BACA data (Sudah pakai link Juragan)
sheet_id = "1t1zxEQINPu7lPiPfEmlWLK8NWHjtt4cQdamsdINHfW0"
url_baca = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"

# Link untuk SIMPAN data (Tempel link Web App Apps Script Juragan di sini)
URL_JEMBATAN = "https://script.google.com/macros/s/AKfycbxq-kD7l3_YTbmdlLoUt5qSBTbFAJPQaZiVjuP9AyE-TYwd52fD6hYff94iKdSgizHO/exec"

# --- 2. MENU SAMPING ---
st.sidebar.title("Navigasi")
menu = st.sidebar.selectbox("Pilih Menu:", ["👥 Data Warga", "📝 Tambah Warga Baru"])

# --- 3. HALAMAN: DATA WARGA ---
if menu == "👥 Data Warga":
    st.title("🏡 Daftar Warga RT 03")
    
    try:
        # Load data dari Google Sheets
        df = pd.read_csv(url_baca)
        
        # Fitur Cari Nama
        cari = st.text_input("🔍 Cari Nama Tetangga:")
        if cari:
            df = df[df['Nama'].str.contains(cari, case=False, na=False)]
        
        # Tampilkan Tabel
        st.dataframe(df, use_container_width=True)
        st.caption(f"Total terdata: {len(df)} warga")
        
    except Exception as e:
        st.error("Gagal memuat data. Pastikan Google Sheets sudah di-Publish ke Web.")

# --- 4. HALAMAN: TAMBAH WARGA ---
elif menu == "📝 Tambah Warga Baru":
    st.title("📝 Input Data Warga")
    st.write("Isi formulir di bawah untuk menambah warga baru ke database.")

    with st.form("form_warga", clear_on_submit=True):
        nama = st.text_input("Nama Lengkap")
        alamat = st.text_input("Alamat / Nomor Rumah")
        status = st.selectbox("Status", ["Tetangga Tetap", "Kontrak/Kos", "Pribadi"])
        telepon = st.text_input("Nomor WA (Contoh: 0812...)")
        
        submit = st.form_submit_button("Simpan ke Database")
        
        if submit:
            if nama and alamat:
                # Bungkus data jadi JSON
                payload = {
                    "nama": nama,
                    "alamat": alamat,
                    "status": status,
                    "telepon": telepon
                }
                
                # Kirim data ke Jembatan Apps Script
                try:
                    res = requests.post(URL_JEMBATAN, json=payload)
                    if res.status_code == 200:
                        st.success(f"✅ Mantap! Data {nama} berhasil disimpan.")
                        st.balloons()
                    else:
                        st.error("Gagal terhubung ke Jembatan. Cek Deployment Apps Script.")
                except:
                    st.error("Koneksi Error! Pastikan URL JEMBATAN sudah benar.")
            else:
                st.error("Nama dan Alamat tidak boleh kosong, Bos!")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption("Sistem Administrasi RT 03 v2.0")

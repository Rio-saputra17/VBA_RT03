import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Sistem Administrasi RT 03", layout="wide")

# --- KONFIGURASI DATABASE ---
# Link ini untuk baca data (format CSV)
sheet_id = "1t1zxEQINPu7lPiPfEmlWLK8NWHjtt4cQdamsdINHfW0"
url_baca = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"

st.title("🏡 Dashboard RT 03")

# --- MENU SIDEBAR ---
menu = st.sidebar.selectbox("Pilih Menu:", ["👥 Data Warga", "📝 Input Warga Baru"])

# --- FUNGSI BACA DATA ---
def load_data():
    return pd.read_csv(url_baca)

# --- HALAMAN 1: DATA WARGA ---
if menu == "👥 Data Warga":
    st.header("Daftar Penduduk")
    df = load_data()
    
    # Fitur Cari Nama
    cari = st.text_input("🔍 Cari Nama Tetangga:")
    if cari:
        df = df[df['Nama'].str.contains(cari, case=False, na=False)]
    
    st.dataframe(df, use_container_width=True)
    st.info(f"Total Warga Terdata: {len(df)} orang")

# --- HALAMAN 2: INPUT WARGA BARU ---
elif menu == "📝 Input Warga Baru":
    st.header("Formulir Tambah Warga")
    
    with st.form("form_warga", clear_on_submit=True):
        nama = st.text_input("Nama Lengkap")
        alamat = st.text_input("Nomor Rumah / Alamat")
        status = st.selectbox("Status", ["Tetangga Tetap", "Kontrak/Kos", "Pribadi"])
        telepon = st.text_input("Nomor WA (Opsional)")
        
        submit = st.form_submit_tag("Simpan Data")
        
        if submit:
            if nama and alamat:
                st.warning("⚠️ Untuk fitur Simpan Otomatis, kita perlu satu langkah lagi yaitu pasang 'Google Apps Script'.")
                st.info(f"Data yang mau disimpan: {nama} - {alamat}")
                st.write("Mau saya buatkan kode 'Jembatan' Apps Script-nya sekarang, Bos?")
            else:
                st.error("Nama dan Alamat wajib diisi ya, Bos!")

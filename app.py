import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Sistem RT 03", layout="wide")

# Judul Utama
st.title("🏡 Sistem Administrasi RT 03")

# --- KONEKSI ---
try:
    # Kita paksa ambil koneksi dari secrets
    conn = st.connection("gsheets", type=GSheetsConnection)
    
    # Kita coba baca tab "Warga"
    df_warga = conn.read(worksheet="Warga")
    
    # Jika berhasil, tampilkan data
    st.success("✅ Berhasil Terhubung ke Google Sheets!")
    
    menu = st.sidebar.radio("Pilih Menu", ["Data Warga", "Laporan Kas"])
    
    if menu == "Data Warga":
        st.header("👥 Daftar Penduduk")
        st.dataframe(df_warga, use_container_width=True)
        
except Exception as e:
    st.error("❌ Waduh, Masih Belum Konek, Bos!")
    st.info(f"Pesan Error dari Sistem: {e}")
    st.warning("Cek 2 hal ini: \n1. Pastikan di Secrets sudah ada [connections.gsheets] \n2. Pastikan link di Secrets benar.")
    
    # Tombol Refresh Paksa
    if st.button("Coba Hubungkan Ulang"):
        st.rerun()

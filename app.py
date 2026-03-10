import streamlit as st
from streamlit_gsheets import GSheetConnection
import pandas as pd

st.set_page_config(page_title="Sistem Administrasi RT", layout="centered")

# --- KONEKSI DATABASE ---
conn = st.connection("gsheets", type=GSheetConnection)

# Fungsi ambil data
def get_data(sheet_name):
    return conn.read(worksheet=sheet_name)

# --- LOGIN SYSTEM ---
st.sidebar.title("🏡 Menu RT Digital")
user_role = st.sidebar.selectbox("Login Sebagai", ["Warga", "Admin"])
password_input = st.sidebar.text_input("Password (Khusus Admin)", type="password")

# Ambil password dari Google Sheets (Sheet: Config)
df_config = get_data("Config")
admin_pw = str(df_config.iloc[0, 0])

is_admin = (user_role == "Admin" and password_input == admin_pw)

# --- NAVIGASI ---
menu = ["Data Warga", "Iuran Warga", "Kas RT", "Struktur Organisasi"]
choice = st.sidebar.radio("Pilih Menu", menu)

# --- 1. DATA WARGA ---
if choice == "Data Warga":
    st.header("👥 Data Warga")
    df_warga = get_data("Warga")
    
    if is_admin:
        with st.expander("Tambah Warga Baru"):
            with st.form("form_warga"):
                n = st.text_input("Nama")
                a = st.text_input("Alamat")
                s = st.selectbox("Status", ["Tetap", "Kontrak"])
                t = st.text_input("No Telepon")
                if st.form_submit_button("Simpan"):
                    # Logika simpan ke GSheets (memerlukan setup write access)
                    st.success("Data masuk antrian simpan!")
    
    st.dataframe(df_warga, use_container_width=True)

# --- 2. IURAN WARGA ---
elif choice == "Iuran Warga":
    st.header("💰 Catatan Iuran")
    df_iuran = get_data("Iuran")
    st.table(df_iuran)

# --- 3. KAS RT ---
elif choice == "Kas RT":
    st.header("📈 Laporan Kas")
    df_kas = get_data("Kas")
    
    # Hitung Saldo Otomatis
    total_masuk = df_kas['Masuk'].sum()
    total_keluar = df_kas['Keluar'].sum()
    saldo_akhir = total_masuk - total_keluar
    
    col1, col2 = st.columns(2)
    col1.metric("Total Saldo", f"Rp {saldo_akhir:,}")
    col2.metric("Pengeluaran", f"Rp {total_keluar:,}")
    
    st.dataframe(df_kas)

# --- 4. STRUKTUR ---
elif choice == "Struktur Organisasi":
    st.header("🏗️ Kepengurusan RT")
    st.write("- **Ketua RT:** Pak Bos")
    st.write("- **Sekretaris:** Bu Sek")
    st.write("- **Bendahara:** Pak Bend")

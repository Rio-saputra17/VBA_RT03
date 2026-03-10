import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

st.set_page_config(page_title="Sistem Administrasi RT", layout="centered")

# --- KONEKSI DATABASE ---
# Pastikan GSheetsConnection pakai huruf 's' di tengah
conn = st.connection("gsheets", type=GSheetsConnection)

# Fungsi ambil data
def get_data(sheet_name):
    return conn.read(worksheet=sheet_name)

# --- LOGIN SYSTEM ---
st.sidebar.title("🏡 Menu RT Digital")
user_role = st.sidebar.selectbox("Login Sebagai", ["Warga", "Admin"])
password_input = st.sidebar.text_input("Password (Khusus Admin)", type="password")

# Ambil data config untuk password admin
try:
    df_config = get_data("Config")
    admin_pw = str(df_config.iloc[0, 0])
except:
    admin_pw = "admin123" # Password cadangan jika GSheets belum konek

is_admin = (user_role == "Admin" and password_input == admin_pw)

# --- NAVIGASI ---
menu = ["Data Warga", "Iuran Warga", "Kas RT", "Struktur Organisasi"]
choice = st.sidebar.radio("Pilih Menu", menu)

# --- 1. DATA WARGA ---
if choice == "Data Warga":
    st.header("👥 Data Warga")
    try:
        df_warga = get_data("Warga")
        st.dataframe(df_warga, use_container_width=True)
    except:
        st.warning("Belum terhubung ke Google Sheets. Pastikan Secrets sudah diisi.")

# --- 2. IURAN WARGA ---
elif choice == "Iuran Warga":
    st.header("💰 Catatan Iuran")
    try:
        df_iuran = get_data("Iuran")
        st.table(df_iuran)
    except:
        st.info("Menunggu data iuran...")

# --- 3. KAS RT ---
elif choice == "Kas RT":
    st.header("📈 Laporan Kas")
    try:
        df_kas = get_data("Kas")
        total_masuk = df_kas['Masuk'].sum()
        total_keluar = df_kas['Keluar'].sum()
        saldo_akhir = total_masuk - total_keluar
        
        col1, col2 = st.columns(2)
        col1.metric("Total Saldo", f"Rp {saldo_akhir:,}")
        col2.metric("Pengeluaran", f"Rp {total_keluar:,}")
        st.dataframe(df_kas)
    except:
        st.info("Menunggu data kas...")

# --- 4. STRUKTUR ---
elif choice == "Struktur Organisasi":
    st.header("🏗️ Kepengurusan RT")
    st.write("- **Ketua RT:** Pak Bos")
    st.write("- **Sekretaris:** Bu Sek")
    st.write("- **Bendahara:** Pak Bend")

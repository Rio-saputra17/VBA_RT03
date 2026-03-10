import streamlit as st
import pandas as pd
import requests

# Konfigurasi Tampilan
st.set_page_config(page_title="Sistem RT 03", layout="wide", page_icon="🏡")

# --- DATA KONFIGURASI ---
SHEET_ID = "1t1zxEQINPu7lPiPfEmlWLK8NWHjtt4cQdamsdINHfW0"
URL_BACA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
URL_JEMBATAN = "https://script.google.com/macros/s/AKfycbxq-kD7l3_YTbmdlLoUt5qSBTbFAJPQaZiVjuP9AyE-TYwd52fD6hYff94iKdSgizHO/exec" # <--- Masukkan Link /exec Juragan

# Password Sederhana (Ganti sesuai selera Juragan)
PASSWORD_RT = "rt03oke"

# --- FUNGSI SESSION STATE (Agar Login Gak Hilang) ---
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- SIDEBAR NAVIGASI ---
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/609/609803.png", width=80)
    st.title("Admin RT 03")
    
    if not st.session_state['logged_in']:
        st.subheader("🔑 Login Pengurus")
        pwd = st.text_input("Masukkan Password", type="password")
        if st.button("Masuk"):
            if pwd == PASSWORD_RT:
                st.session_state['logged_in'] = True
                st.rerun()
            else:
                st.error("Password Salah!")
    else:
        st.success("Mode Admin Aktif")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()

    st.markdown("---")
    menu = st.radio("Pilih Menu:", ["👥 Lihat Warga", "📝 Tambah Warga", "📊 Statistik RT"])

# --- HALAMAN 1: LIHAT WARGA ---
if menu == "👥 Lihat Warga":
    st.title("👥 Data Warga RT 03")
    try:
        df = pd.read_csv(URL_BACA)
        cari = st.text_input("🔍 Cari Nama atau Alamat...")
        if cari:
            df = df[df.astype(str).apply(lambda x: x.str.contains(cari, case=False)).any(axis=1)]
        
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        # Tombol download buat laporan Pak RT
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Excel (CSV)", csv, "data_warga_rt03.csv", "text/csv")
    except:
        st.error("Gagal ambil data. Pastikan Google Sheets 'Publish to Web'.")

# --- HALAMAN 2: TAMBAH WARGA (DIPROTEKSI) ---
elif menu == "📝 Tambah Warga":
    st.title("📝 Input Warga Baru")
    
    if st.session_state['logged_in']:
        with st.form("form_tambah"):
            nama = st.text_input("Nama Lengkap")
            alamat = st.text_input("No Rumah / Alamat")
            status = st.selectbox("Status", ["Warga Tetap", "Kontrak", "Kos", "Lainnya"])
            telepon = st.text_input("No WhatsApp")
            
            submit = st.form_submit_button("Simpan ke Database")
            
            if submit:
                if nama and alamat:
                    payload = {"nama": nama, "alamat": alamat, "status": status, "telepon": telepon}
                    res = requests.post(URL_JEMBATAN, json=payload)
                    if res.status_code == 200:
                        st.success(f"Berhasil! {nama} sudah masuk database.")
                        st.balloons()
                    else:
                        st.error("Gagal Simpan!")
                else:
                    st.warning("Mohon isi Nama dan Alamat!")
    else:
        st.warning("🔒 Silakan login di sidebar untuk menambah data.")

# --- HALAMAN 3: STATISTIK ---
elif menu == "📊 Statistik RT":
    st.title("📊 Statistik Wilayah")
    try:
        df = pd.read_csv(URL_BACA)
        col1, col2 = st.columns(2)
        col1.metric("Total Warga", len(df))
        # Hitung jumlah rumah unik (berdasarkan alamat)
        col2.metric("Total Rumah", df['Alamat'].nunique())
        
        st.subheader("Komposisi Status Warga")
        st.bar_chart(df['Status'].value_counts())
    except:
        st.info("Statistik akan muncul setelah data terisi.")

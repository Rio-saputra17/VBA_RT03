import streamlit as st
import pandas as pd
import urllib.parse

st.set_page_config(page_title="Sistem RT 03", layout="wide")

# --- KONFIGURASI DATA ---
sheet_id = "1t1zxEQINPu7lPiPfEmlWLK8NWHjtt4cQdamsdINHfW0"
url_baca = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"

st.title("🏡 Dashboard Administrasi RT 03")

# --- MENU ---
menu = st.sidebar.selectbox("Pilih Menu:", ["👥 Data Warga", "📝 Input Warga Baru"])

# --- HALAMAN 1: BACA DATA ---
if menu == "👥 Data Warga":
    st.header("Daftar Penduduk")
    try:
        df = pd.read_csv(url_baca)
        # Pencarian
        cari = st.text_input("🔍 Cari Nama Warga:")
        if cari:
            df = df[df['Nama'].str.contains(cari, case=False, na=False)]
        
        st.dataframe(df, use_container_width=True)
    except:
        st.error("Gagal memuat data. Pastikan Google Sheets sudah di-Publish.")

# --- HALAMAN 2: INPUT DATA (OTOMATIS) ---
elif menu == "📝 Input Warga Baru":
    st.header("Formulir Tambah Warga")
    st.write("Silakan isi data di bawah, lalu klik tombol Simpan.")
    
    with st.form("form_warga", clear_on_submit=True):
        nama = st.text_input("Nama Lengkap")
        alamat = st.text_input("Alamat / No Rumah")
        status = st.selectbox("Status", ["Tetangga Tetap", "Kontrak/Kos", "Pribadi"])
        telepon = st.text_input("No. WhatsApp")
        
        submitted = st.form_submit_button("Siapkan Data")
        
        if submitted:
            if nama and alamat:
                # Link Dasar Google Form Juragan
                base_url = "https://docs.google.com/forms/d/e/1FAIpQLSeqB63qYvhQR_mYRL9xoBH9d5ZAxEzlO1TOBJYh6qDdDn3szw/viewform?"
                
                # Parameter dari Link Sakti
                params = {
                    "entry.2014417019": nama,
                    "entry.1185567798": alamat,
                    "entry.1131533858": status,
                    "entry.1516880491": telepon
                }
                
                final_url = base_url + urllib.parse.urlencode(params)
                
                st.success(f"✅ Data {nama} siap dikirim!")
                st.link_button("KLIK DISINI UNTUK SIMPAN KE DATABASE", final_url)
                st.info("Setelah klik, tekan tombol 'Kirim' di halaman Google Form ya, Bos!")
            else:
                st.error("Nama dan Alamat wajib diisi!")

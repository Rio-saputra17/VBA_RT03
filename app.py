import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Sistem RT 03", layout="wide", page_icon="🏡")

# --- KONFIGURASI ---
SHEET_ID = "1t1zxEQINPu7lPiPfEmlWLK8NWHjtt4cQdamsdINHfW0"
URL_BACA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
URL_JEMBATAN = "https://script.google.com/macros/s/AKfycbwsYpeCMHnql1nIHTAZF34RGEsbWNtEl3xYIvdSnY13nvWmmwhlLb0LmpdJT1Dfss5J/exec" # <--- GANTI DENGAN LINK BARU

PASSWORD_RT = "rt03oke"

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏡 Menu RT 03")
    if not st.session_state['logged_in']:
        pwd = st.text_input("🔑 Login Admin", type="password")
        if st.button("Masuk"):
            if pwd == PASSWORD_RT:
                st.session_state['logged_in'] = True
                st.rerun()
    else:
        st.success("Admin Aktif")
        if st.button("Logout"):
            st.session_state['logged_in'] = False
            st.rerun()
    
    st.markdown("---")
    menu = st.radio("Pilih Navigasi:", ["👥 Lihat Warga", "📝 Tambah Warga", "🛠️ Edit Data", "📊 Statistik"])

# --- MENU: LIHAT ---
if menu == "👥 Lihat Warga":
    st.header("Daftar Warga")
    df = pd.read_csv(URL_BACA)
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- MENU: TAMBAH ---
elif menu == "📝 Tambah Warga":
    st.header("Tambah Warga Baru")
    if st.session_state['logged_in']:
        with st.form("tambah_form"):
            n = st.text_input("Nama")
            a = st.text_input("Alamat")
            s = st.selectbox("Status", ["Warga Tetap", "Kontrak", "Kos"])
            t = st.text_input("WhatsApp")
            if st.form_submit_button("Simpan"):
                res = requests.post(URL_JEMBATAN, json={"action":"tambah", "nama":n, "alamat":a, "status":s, "telepon":t})
                st.success("Berhasil ditambah!")
    else:
        st.warning("Silakan login dulu, Bos.")

# --- MENU: EDIT (Sakti!) ---
elif menu == "🛠️ Edit Data":
    st.header("Edit Data Warga")
    if st.session_state['logged_in']:
        df = pd.read_csv(URL_BACA)
        pilihan = st.selectbox("Pilih warga yang akan di-edit:", ["-- Pilih --"] + df['Nama'].tolist())
        
        if pilihan != "-- Pilih --":
            data = df[df['Nama'] == pilihan].iloc[0]
            with st.form("edit_form"):
                new_n = st.text_input("Nama Lengkap", value=data['Nama'])
                new_a = st.text_input("Alamat", value=data['Alamat'])
                new_s = st.selectbox("Status", ["Warga Tetap", "Kontrak", "Kos"], index=["Warga Tetap", "Kontrak", "Kos"].index(data['Status']))
                new_t = st.text_input("WhatsApp", value=str(data['Telepon']))
                
                if st.form_submit_button("Update Data"):
                    payload = {"action":"edit", "nama_lama":pilihan, "nama":new_n, "alamat":new_a, "status":new_s, "telepon":new_t}
                    requests.post(URL_JEMBATAN, json=payload)
                    st.success("Data Berhasil Diperbarui!")
                    st.rerun()
    else:
        st.warning("Hanya Admin yang bisa edit data.")

# --- MENU: STATISTIK ---
elif menu == "📊 Statistik":
    st.header("Laporan Statistik")
    df = pd.read_csv(URL_BACA)
    st.bar_chart(df['Status'].value_counts())

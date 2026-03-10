import streamlit as st
import pandas as pd
import requests

# Setting agar otomatis pas di layar HP
st.set_page_config(page_title="RT 03", layout="centered")

# --- KONFIGURASI (PASTIKAN GID BENAR) ---
S_ID = "1t1zxEQINPu7lPiPfEmlWLK8NWHjtt4cQdamsdINHfW0"
URL_W = f"https://docs.google.com/spreadsheets/d/{S_ID}/export?format=csv&gid=0"
URL_I = f"https://docs.google.com/spreadsheets/d/{S_ID}/export?format=csv&gid=1334887308"
URL_K = f"https://docs.google.com/spreadsheets/d/{S_ID}/export?format=csv&gid=249257041"
URL_J = "https://script.google.com/macros/s/AKfycbxI9d5S3YZXO6VT2S6Hec6FpVU_2xF52w3DwVdzgF5L0-UUebtvnqymVU-hkTNG356L/exec" # <--- GANTI INI

# Cek Login Sederhana
if 'admin' not in st.session_state: st.session_state['admin'] = False

# --- HEADER SIMPEL ---
st.title("🏡 Sistem RT 03")

if not st.session_state['admin']:
    if st.sidebar.text_input("Sandi Admin", type="password") == "rt03oke":
        st.session_state['admin'] = True
        st.sidebar.success("Admin Aktif")
        st.rerun()
else:
    if st.sidebar.button("Keluar Admin"):
        st.session_state['admin'] = False
        st.rerun()

# --- MENU UTAMA (Mode Tab agar gampang di HP) ---
menu = st.tabs(["👥 Warga", "💳 Iuran", "💰 Kas", "🛠️ Kelola"])

# --- TAB 1: DATA WARGA ---
with menu[0]:
    st.subheader("Data Warga")
    dfw = pd.read_csv(URL_W)
    st.dataframe(dfw, use_container_width=True, hide_index=True)

# --- TAB 2: IURAN (TABEL) ---
with menu[1]:
    st.subheader("Rekap Iuran")
    try:
        dfi = pd.read_csv(URL_I)
        st.table(dfi) # Pakai table agar full lebar di HP
    except: st.info("Belum ada data iuran.")
    
    if st.session_state['admin']:
        with st.expander("➕ Input Iuran"):
            with st.form("fi"):
                nm = st.selectbox("Warga", dfw['Nama'].tolist())
                bl = st.selectbox("Bulan", ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Ags", "Sep", "Okt", "Nov", "Des"])
                th = st.selectbox("Tahun", ["2025", "2026"])
                kt = st.selectbox("Status", ["Lunas", "Belum"])
                if st.form_submit_button("Simpan"):
                    al = dfw[dfw['Nama']==nm]['Alamat'].values[0]
                    requests.post(URL_J, json={"action":"iuran","nama":nm,"alamat":al,"bulan":bl,"tahun":th,"ket":kt})
                    st.success("Tersimpan!"); st.rerun()

# --- TAB 3: KAS (TABEL & SALDO) ---
with menu[2]:
    st.subheader("Buku Kas")
    try:
        dfk = pd.read_csv(URL_K)
        m = pd.to_numeric(dfk['Masuk'], errors='coerce').sum()
        k = pd.to_numeric(dfk['Keluar'], errors='coerce').sum()
        st.success(f"💰 Sisa Saldo: Rp {m-k:,.0f}")
        st.dataframe(dfk, use_container_width=True, hide_index=True)
    except: st.info("Kas kosong.")
    
    if st.session_state['admin']:
        with st.expander("➕ Input Kas"):
            with st.form("fk"):
                tp = st.radio("Tipe", ["Masuk", "Keluar"], horizontal=True)
                jml = st.number_input("Nominal", step=1000)
                ket = st.text_input("Keperluan")
                if st.form_submit_button("Catat"):
                    masuk, keluar = (jml, 0) if tp == "Masuk" else (0, jml)
                    requests.post(URL_J, json={"action":"kas","masuk":masuk,"keluar":keluar,"ket":ket})
                    st.success("Tercatat!"); st.rerun()

# --- TAB 4: KELOLA (TAMBAH & EDIT) ---
with menu[3]:
    if st.session_state['admin']:
        st.subheader("Edit/Tambah Warga")
        opsi = st.radio("Aksi", ["Tambah Baru", "Edit Data"], horizontal=True)
        
        if opsi == "Tambah Baru":
            with st.form("ft"):
                n, a = st.text_input("Nama"), st.text_input("Alamat")
                s = st.selectbox("Status", ["Tetap", "Kontrak"])
                t = st.text_input("WA")
                if st.form_submit_button("Simpan"):
                    requests.post(URL_J, json={"action":"tambah","nama":n,"alamat":a,"status":s,"telepon":t})
                    st.success("Berhasil!"); st.rerun()
        else:
            pilih = st.selectbox("Pilih Nama", ["--"] + dfw['Nama'].tolist())
            if pilih != "--":
                d = dfw[dfw['Nama']==pilih].iloc[0]
                with st.form("fe"):
                    en = st.text_input("Nama", value=d['Nama'])
                    ea = st.text_input("Alamat", value=d['Alamat'])
                    if st.form_submit_button("Update"):
                        requests.post(URL_J, json={"action":"edit","nama_lama":pilih,"nama":en,"alamat":ea,"status":d['Status'],"telepon":d['Telepon']})
                        st.success("Terupdate!"); st.rerun()
    else: st.warning("Menu ini khusus Admin.")

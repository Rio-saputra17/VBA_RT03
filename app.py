import streamlit as st
import pandas as pd
import requests

st.set_page_config(page_title="Sistem RT 03", layout="wide", page_icon="🏡")

# --- KONFIGURASI ---
SHEET_ID = "1t1zxEQINPu7lPiPfEmlWLK8NWHjtt4cQdamsdINHfW0"
URL_WARGA = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
URL_IURAN = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=1334887308" # Ganti GID Iuran
URL_KAS = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=249257041" # Ganti GID Kas
URL_JEMBATAN = "https://script.google.com/macros/s/AKfycbyKMxrINZXZpxRyn-LV8HWoYULlE8fB-5slUBrjEkjVOA5ImnFPwW_ES4ycdSYqHQMR/exec"

PASSWORD_RT = "rt03oke"

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

# --- SIDEBAR ---
with st.sidebar:
    st.title("🏡 Admin RT 03")
    if not st.session_state['logged_in']:
        pwd = st.text_input("🔑 Login", type="password")
        if st.button("Masuk"):
            if pwd == PASSWORD_RT:
                st.session_state['logged_in'] = True
                st.rerun()
    else:
        st.success("Admin Aktif")
        if st.button("Keluar"):
            st.session_state['logged_in'] = False
            st.rerun()
    
    st.markdown("---")
    menu = st.radio("Pilih Menu:", ["👥 Data Warga", "💳 Status Iuran", "💰 Kas Keuangan"])

# --- MENU: DATA WARGA ---
if menu == "👥 Data Warga":
    st.header("👥 Data Penduduk")
    df = pd.read_csv(URL_WARGA)
    st.dataframe(df, use_container_width=True, hide_index=True)

# --- MENU: IURAN (Sesuai Foto 11723) ---
elif menu == "💳 Status Iuran":
    st.title("💳 Rekap Iuran Warga")
    
    # Input Iuran (Admin)
    if st.session_state['logged_in']:
        with st.expander("➕ Catat Pembayaran Baru"):
            df_w = pd.read_csv(URL_WARGA)
            with st.form("form_iuran"):
                nama_p = st.selectbox("Nama Warga", df_w['Nama'].tolist())
                bulan = st.selectbox("Untuk Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
                tahun = st.selectbox("Tahun", ["2025", "2026"])
                ket = st.selectbox("Keterangan", ["Lunas", "Belum Lunas"])
                if st.form_submit_button("Simpan Iuran"):
                    alm = df_w[df_w['Nama'] == nama_p]['Alamat'].values[0]
                    requests.post(URL_JEMBATAN, json={"action":"input_iuran", "nama":nama_p, "alamat":alm, "bulan":bulan, "tahun":tahun, "keterangan":ket})
                    st.success("Tercatat!")
                    st.rerun()

    st.markdown("---")
    try:
        df_i = pd.read_csv(URL_IURAN)
        st.subheader("Daftar Warga Sudah Bayar")
        st.table(df_i)
    except:
        st.info("Belum ada data iuran.")

# --- MENU: KAS (Sesuai Foto 11724) ---
elif menu == "💰 Kas Keuangan":
    st.title("💰 Buku Kas RT 03")
    
    # Tampilan Saldo Otomatis
    try:
        df_k = pd.read_csv(URL_KAS)
        df_k['Masuk'] = pd.to_numeric(df_k['Masuk'], errors='coerce').fillna(0)
        df_k['Keluar'] = pd.to_numeric(df_k['Keluar'], errors='coerce').fillna(0)
        
        total_masuk = df_k['Masuk'].sum()
        total_keluar = df_k['Keluar'].sum()
        saldo_akhir = total_masuk - total_keluar

        c1, c2, c3 = st.columns(3)
        c1.metric("Total Masuk", f"Rp {total_masuk:,.0f}")
        c2.metric("Total Keluar", f"Rp {total_keluar:,.0f}")
        c3.metric("Sisa Saldo", f"Rp {saldo_akhir:,.0f}", delta_color="normal")

        st.markdown("---")
        st.subheader("Riwayat Transaksi")
        st.dataframe(df_k, use_container_width=True, hide_index=True)
    except:
        st.info("Belum ada transaksi kas.")

    # Input Kas (Admin)
    if st.session_state['logged_in']:
        with st.expander("➕ Catat Transaksi Kas (Masuk/Keluar)"):
            with st.form("form_kas"):
                tipe = st.radio("Tipe", ["Masuk", "Keluar"], horizontal=True)
                jml = st.number_input("Nominal (Rp)", min_value=0, step=1000)
                ket_k = st.text_input("Keterangan Penggunaan/Sumber Uang")
                if st.form_submit_button("Simpan Kas"):
                    m = jml if tipe == "Masuk" else 0
                    k = jml if tipe == "Keluar" else 0
                    requests.post(URL_JEMBATAN, json={"action":"input_kas", "masuk":m, "keluar":k, "keterangan":ket_k})
                    st.success("Kas Terupdate!")
                    st.rerun()

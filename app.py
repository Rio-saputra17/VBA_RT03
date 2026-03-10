import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Konfigurasi Tampilan Mobile
st.set_page_config(page_title="Update RT 03", layout="wide")

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.subheader("🔐 Login Sistem RT 03")
        pw = st.text_input("Password Admin", type="password")
        if st.button("Masuk"):
            if pw == "123": # Ganti password di sini
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Password Salah!")
        return False
    return True

if login():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Baca data sesuai nama sheet di gambar terakhir (Warga, Data Pembayaran, Kas RT)
        df_warga = conn.read(worksheet="Warga", ttl="0")
        df_bayar = conn.read(worksheet="Data Pembayaran", ttl="0")
        df_kas = conn.read(worksheet="Kas RT", ttl="0")

        st.sidebar.title("Sistem RT 03")
        menu = st.sidebar.radio("Navigasi Menu", 
            ["Update Warga", "Input Iuran", "History Pembayaran", "Kas RT (Keuangan)"])

        # --- 1. MENU UPDATE WARGA (TAMBAH & EDIT) ---
        if menu == "Update Warga":
            st.header("👥 Manajemen Data Warga")
            tab1, tab2 = st.tabs(["Tambah Warga Baru", "Edit/Hapus Warga"])
            
            with tab1:
                with st.form("form_tambah"):
                    n_nama = st.text_input("Nama Warga")
                    n_alamat = st.text_input("Alamat Rumah")
                    n_status = st.selectbox("Status Rumah", ["Pribadi", "Kontrak"])
                    n_kontak = st.text_input("Kontak (No Telepon)")
                    if st.form_submit_button("Simpan Warga"):
                        new_data = pd.DataFrame([{"Nama": n_nama, "Alamat": n_alamat, "Status": n_status, "Kontak": n_kontak}])
                        df_updated = pd.concat([df_warga, new_data], ignore_index=True)
                        conn.update(worksheet="Warga", data=df_updated)
                        st.success("Warga Berhasil Ditambahkan!")
                        st.rerun()

            with tab2:
                st.write("Edit data langsung di tabel bawah:")
                edited_w = st.data_editor(df_warga, use_container_width=True, num_rows="dynamic")
                if st.button("Simpan Perubahan Data"):
                    conn.update(worksheet="Warga", data=edited_w)
                    st.success("Data Warga Diperbarui!")

        # --- 2. MENU INPUT IURAN (OTOMATIS SINKRON KAS) ---
        elif menu == "Input Iuran":
            st.header("💰 Input Pembayaran Iuran")
            if df_warga.empty:
                st.warning("Data warga masih kosong. Isi dulu di menu Update Warga.")
            else:
                with st.form("form_bayar", clear_on_submit=True):
                    sel_nama = st.selectbox("Pilih Nama Warga", df_warga['Nama'].unique())
                    sel_bln = st.selectbox("Bulan/Tahun", [f"{b} 2026" for b in ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]])
                    sel_nominal = st.number_input("Jumlah Uang (Rp)", value=20000, step=5000)
                    
                    if st.form_submit_button("Proses Pembayaran"):
                        # Logika Update Data Pembayaran
                        new_iuran = pd.DataFrame([{"Nama": sel_nama, "Bulan/Tahun": sel_bln, "Status": "Lunas"}])
                        df_bayar_up = pd.concat([df_bayar, new_iuran], ignore_index=True)
                        conn.update(worksheet="Data Pembayaran", data=df_bayar_up)
                        
                        # Logika Sinkronisasi Kas RT
                        # Ambil saldo terakhir
                        try:
                            last_saldo = pd.to_numeric(df_kas['Sisa Saldo']).iloc[-1]
                        except:
                            last_saldo = 0
                            
                        new_kas = pd.DataFrame([{
                            "Masuk": sel_nominal, 
                            "Keluar": 0, 
                            "Keterangan": f"Iuran {sel_bln} - {sel_nama}", 
                            "Sisa Saldo": last_saldo + sel_nominal
                        }])
                        df_kas_up = pd.concat([df_kas, new_kas], ignore_index=True)
                        conn.update(worksheet="Kas RT", data=df_kas_up)
                        
                        st.success(f"Berhasil! {sel_nama} Lunas {sel_bln}. Kas otomatis bertambah.")

        # --- 3. MENU HISTORY PEMBAYARAN (CEK BULAN/TAHUN) ---
        elif menu == "History Pembayaran":
            st.header("📊 History Pembayaran Iuran")
            st.write("Gunakan kotak pencarian di tabel untuk cek per nama:")
            st.dataframe(df_bayar, use_container_width=True)

        # --- 4. MENU KAS RT (KEUANGAN & EDIT KAS) ---
        elif menu == "Kas RT (Keuangan)":
            st.header("📈 Laporan Kas & Sisa Saldo

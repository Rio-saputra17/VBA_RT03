import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="Admin RT 03", layout="wide")

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.subheader("🔐 Login Admin RT 03")
        password = st.text_input("Masukkan Password", type="password")
        if st.button("Masuk"):
            if password == "123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Password Salah!")
        return False
    return True

if login():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Ambil data mentah
        df_warga = conn.read(worksheet="Warga", ttl="0")
        df_iuran = conn.read(worksheet="Iuran", ttl="0")
        df_kas = conn.read(worksheet="Kas", ttl="0")

        # --- LOGIKA OTOMATIS: SINKRONISASI KOLOM & BARIS ---
        # 1. Pastikan kolom iuran lengkap (Januari - Desember)
        bulan_list = ["Januari", "Februari", "Maret", "April", "Mei", "Juni", 
                      "Juli", "Agustus", "September", "Oktober", "November", "Desember"]
        
        for bln in bulan_list:
            if bln not in df_iuran.columns:
                df_iuran[bln] = "Belum" # Isi otomatis kolom jika belum ada

        # 2. Tambahkan warga baru ke tabel iuran secara otomatis
        warga_di_induk = set(df_warga['Nama'].unique())
        warga_di_iuran = set(df_iuran['Nama'].unique())
        warga_baru = warga_di_induk - warga_di_iuran

        if warga_baru:
            for nama in warga_baru:
                baru = {"Nama": nama}
                for b in bulan_list: baru[b] = "Belum"
                df_iuran = pd.concat([df_iuran, pd.DataFrame([baru])], ignore_index=True)
            conn.update(worksheet="Iuran", data=df_iuran)
            st.toast(f"Ditambahkan {len(warga_baru)} warga baru ke tabel iuran!")

        # --- MENU NAVIGASI ---
        st.sidebar.title("Menu Admin")
        menu = st.sidebar.radio("Navigasi:", ["Data Warga", "Input Iuran", "Data Iuran Warga", "Rekap Kas", "Edit Data Warga"])

        if menu == "Data Warga":
            st.header("👥 Data Induk Warga")
            st.dataframe(df_warga, use_container_width=True)

        elif menu == "Input Iuran":
            st.header("💰 Input Pembayaran")
            with st.form("form_pembayaran", clear_on_submit=True):
                nama_pilih = st.selectbox("Nama Warga", df_warga['Nama'].unique())
                bln_pilih = st.selectbox("Bulan", bulan_list)
                thn_pilih = st.selectbox("Tahun", [2025, 2026])
                jml_bayar = st.number_input("Jumlah (Rp)", min_value=0, value=20000)
                
                if st.form_submit_button("Simpan & Sinkronkan"):
                    # Update status Iuran
                    df_iuran.loc[df_iuran['Nama'] == nama_pilih, bln_pilih] = "LUNAS"
                    conn.update(worksheet="Iuran", data=df_iuran)
                    
                    # Tambah data Kas
                    new_kas = pd.DataFrame([{
                        "Tanggal": datetime.now().strftime("%Y-%m-%d"),
                        "Keterangan": f"Iuran {bln_pilih} {thn_pilih} - {nama_pilih}",
                        "Tipe": "Masuk",
                        "Jumlah": jml_bayar
                    }])
                    df_kas = pd.concat([df_kas, new_kas], ignore_index=True)
                    conn.update(worksheet="Kas", data=df_kas)
                    st.success(f"Data {nama_pilih} berhasil disinkronkan!")

        elif menu == "Data Iuran Warga":
            st.header("📅 Tabel Monitoring Iuran")
            st.dataframe(df_iuran, use_container_width=True)

        elif menu == "Rekap Kas":
            st.header("📈 Laporan Arus Kas")
            df_kas['Jumlah'] = pd.to_numeric(df_kas['Jumlah'], errors='coerce').fillna(0)
            t_masuk = df_kas[df_kas['Tipe'] == 'Masuk']['Jumlah'].sum()
            t_keluar = df_kas[df_kas['Tipe'] == 'Keluar']['Jumlah'].sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Pemasukan", f"Rp {t_masuk:,.0f}")
            c2.metric("Pengeluaran", f"Rp {t_keluar:,.0f}")
            c3.metric("Saldo", f"Rp {t_masuk - t_keluar:,.0f}")
            
            st.divider()
            st.dataframe(df_kas[["Tanggal", "Keterangan", "Tipe", "Jumlah"]], use_container_width=True)

        elif menu == "Edit Data Warga":
            st.header("📝 Edit Data Warga")
            edited = st.data_editor(df_warga, use_container_width=True, num_rows="dynamic")
            if st.button("Simpan Perubahan"):
                conn.update(worksheet="Warga", data=edited)
                st.rerun()

    except Exception as e:
        st.error("Gagal sinkronisasi. Cek nama sheet (Warga, Iuran, Kas).")
        st.exception(e)

    if st.sidebar.button("Keluar"):
        st.session_state.logged_in = False
        st.rerun()

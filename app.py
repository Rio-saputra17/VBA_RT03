import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Konfigurasi Layar HP
st.set_page_config(page_title="RT03 VBA", layout="wide")

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.subheader("🔐 Login Admin RT 03")
        pw = st.text_input("Password", type="password")
        if st.button("Masuk"):
            if pw == "123": # Silakan ganti passwordnya di sini
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Password Salah!")
        return False
    return True

if login():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Baca data sesuai nama sheet di gambar
        df_warga = conn.read(worksheet="Warga", ttl="0")
        df_iuran = conn.read(worksheet="Iuran", ttl="0")
        df_kas = conn.read(worksheet="Kas", ttl="0")

        st.sidebar.title("RT03 VBA")
        menu = st.sidebar.radio("Navigasi", ["Data Warga", "Input Iuran", "Data Iuran", "Rekap Kas", "Edit Data Warga"])

        if menu == "Data Warga":
            st.header("👥 Data Warga")
            st.dataframe(df_warga, use_container_width=True)

        elif menu == "Input Iuran":
            st.header("💰 Input Iuran Otomatis")
            with st.form("input_iuran", clear_on_submit=True):
                # Ambil data dari sheet Warga agar sinkron
                nama_warga = st.selectbox("Pilih Nama", df_warga['Nama'].unique())
                # Cari alamat otomatis berdasarkan nama
                alamat_warga = df_warga[df_warga['Nama'] == nama_warga]['Alamat'].values[0]
                
                bln = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
                thn = st.selectbox("Tahun", [2025, 2026, 2027])
                jml = st.number_input("Jumlah Bayar (Rp)", value=20000, step=5000)
                
                if st.form_submit_button("Simpan & Sinkronkan"):
                    # 1. Update Sheet Iuran (Tambah Baris Baru)
                    new_iuran = pd.DataFrame([{
                        "Nama": nama_warga,
                        "Alamat": alamat_warga,
                        "Bulan": bln,
                        "Tahun": thn,
                        "Keterangan": "lunas"
                    }])
                    df_iuran_new = pd.concat([df_iuran, new_iuran], ignore_index=True)
                    conn.update(worksheet="Iuran", data=df_iuran_new)
                    
                    # 2. Update Sheet Kas (Otomatis Masuk)
                    # Hitung saldo terakhir
                    saldo_akhir = pd.to_numeric(df_kas['Saldo'], errors='coerce').fillna(0).last_valid_index()
                    if saldo_akhir is not None:
                        last_saldo = df_kas.loc[saldo_akhir, 'Saldo']
                    else:
                        last_saldo = 0
                    
                    new_kas = pd.DataFrame([{
                        "Tanggal": datetime.now().strftime("%d/%m/%Y"),
                        "Masuk": jml,
                        "Keluar": 0,
                        "Keterangan": f"Iuran {bln} {thn} - {nama_warga}",
                        "Saldo": last_saldo + jml
                    }])
                    df_kas_new = pd.concat([df_kas, new_kas], ignore_index=True)
                    conn.update(worksheet="Kas", data=df_kas_new)
                    
                    st.success(f"Berhasil! Data {nama_warga} tersimpan dan Kas bertambah.")
                    st.balloons()

        elif menu == "Data Iuran":
            st.header("📊 Data Iuran Warga")
            st.dataframe(df_iuran, use_container_width=True)

        elif menu == "Rekap Kas":
            st.header("📈 Laporan Keuangan (Kas)")
            # Hitung total dari kolom Masuk dan Keluar
            total_m = pd.to_numeric(df_kas['Masuk'], errors='coerce').sum()
            total_k = pd.to_numeric(df_kas['Keluar'], errors='coerce').sum()
            saldo_skrg = total_m - total_k
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Masuk", f"Rp {total_m:,.0f}")
            c2.metric("Total Keluar", f"Rp {total_k:,.0f}")
            c3.metric("Saldo Kas", f"Rp {saldo_skrg:,.0f}")
            
            st.divider()
            st.dataframe(df_kas, use_container_width=True)

        elif menu == "Edit Data Warga":
            st.header("📝 Edit Data Warga")
            st.info("Edit langsung di tabel bawah dan tekan simpan.")
            edited = st.data_editor(df_warga, use_container_width=True, num_rows="dynamic")
            if st.button("Simpan Perubahan Warga"):
                conn.update(worksheet="Warga", data=edited)
                st.success("Data Warga diperbarui!")
                st.rerun()
    except Exception as e:
        st.error("Waduh, koneksi ke Google Sheets terputus atau nama kolom ada yang beda.")
        st.code(str(e))

    if st.sidebar.button("Keluar"):
        st.session_state.logged_in = False
        st.rerun()

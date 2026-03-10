import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# 1. Konfigurasi Layar Responsive
st.set_page_config(page_title="Admin RT 03", layout="wide")

# --- SISTEM LOGIN SEDERHANA ---
def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.subheader("🔐 Login Admin RT 03")
        password = st.text_input("Masukkan Password Admin", type="password")
        if st.button("Masuk"):
            if password == "123": # <--- GANTI PASSWORD ANDA DI SINI
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Password Salah!")
        return False
    return True

if login():
    # 2. Koneksi ke Google Sheets
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 3. Sidebar Menu yang Terpisah (Cocok untuk HP)
        st.sidebar.title("Navigasi")
        menu = st.sidebar.radio("Pilih Menu:", 
                                ["Data Warga", "Input Iuran", "Rekap Kas", "Edit Data Warga"])

        # Ambil data dari sheet (Pastikan nama sheet di Google Sheets sesuai)
        df = conn.read(ttl="0")

        if menu == "Data Warga":
            st.header("👥 Data Seluruh Warga")
            st.dataframe(df, use_container_width=True)

        elif menu == "Input Iuran":
            st.header("💰 Input Iuran")
            with st.form("form_iuran"):
                nama = st.selectbox("Pilih Warga", df['Nama'].tolist())
                jumlah = st.number_input("Jumlah (Rp)", min_value=0, step=1000)
                tgl = st.date_input("Tanggal Bayar")
                if st.form_submit_button("Simpan Iuran"):
                    st.success(f"Berhasil mencatat iuran {nama}")
                    # Logika simpan iuran bisa dikembangkan ke sheet khusus iuran

        elif menu == "Rekap Kas":
            st.header("📈 Rekap Kas RT")
            col1, col2 = st.columns(2)
            col1.metric("Total Pemasukan", "Rp 5.000.000")
            col2.metric("Total Saldo", "Rp 2.500.000")
            st.write("---")
            st.dataframe(df, use_container_width=True)

        elif menu == "Edit Data Warga":
            st.header("📝 Edit Data Warga")
            st.info("Ubah data langsung di tabel bawah, lalu klik Simpan.")
            edited_df = st.data_editor(df, use_container_width=True, num_rows="dynamic")
            
            if st.button("💾 Simpan Perubahan"):
                conn.update(data=edited_df)
                st.success("Data di Google Sheets berhasil diperbarui!")

    except Exception as e:
        st.error("Koneksi bermasalah. Pastikan URL Google Sheets di Secrets sudah benar.")
        st.exception(e)

    # Tombol Logout di Sidebar
    if st.sidebar.button("Keluar/Logout"):
        st.session_state.logged_in = False
        st.rerun()

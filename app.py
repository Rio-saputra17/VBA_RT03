import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Setting layar agar pas di HP
st.set_page_config(page_title="Update RT 03", layout="wide")

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.subheader("🔐 Login Admin RT 03")
        pw = st.text_input("Password", type="password")
        if st.button("Masuk"):
            if pw == "123":
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Password Salah!")
        return False
    return True

if login():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Baca data - pastikan nama worksheet sama persis dengan tab di Google Sheets
        df_warga = conn.read(worksheet="Warga", ttl="0")
        df_bayar = conn.read(worksheet="Data Pembayaran", ttl="0")
        df_kas = conn.read(worksheet="Kas RT", ttl="0")

        st.sidebar.title("Menu RT 03")
        menu = st.sidebar.radio("Navigasi", ["Update Warga", "Input Pembayaran", "Kas RT"])

        # --- 1. UPDATE WARGA (Sesuai kolom: Nama, Alamat, Status, Kontak) ---
        if menu == "Update Warga":
            st.header("👥 Data Warga")
            tab1, tab2 = st.tabs(["Tambah Baru", "Edit Data"])
            with tab1:
                with st.form("tambah"):
                    n = st.text_input("Nama Warga")
                    a = st.text_input("Alamat Rumah")
                    s = st.selectbox("Status", ["Pribadi", "Kontrak"])
                    k = st.text_input("Kontak (Telepon)")
                    if st.form_submit_button("Simpan"):
                        new = pd.DataFrame([{"Nama": n, "Alamat": a, "Status": s, "Kontak": k}])
                        df_warga = pd.concat([df_warga, new], ignore_index=True)
                        conn.update(worksheet="Warga", data=df_warga)
                        st.success("Berhasil disimpan!")
                        st.rerun()
            with tab2:
                edited = st.data_editor(df_warga, use_container_width=True, num_rows="dynamic")
                if st.button("Update"):
                    conn.update(worksheet="Warga", data=edited)
                    st.success("Data diperbarui!")

        # --- 2. DATA PEMBAYARAN (Sesuai kolom: Nama, Bulan/Tahun, Status) ---
        elif menu == "Input Pembayaran":
            st.header("💰 Bayar Iuran")
            with st.form("bayar"):
                p_nama = st.selectbox("Pilih Warga", df_warga["Nama"].unique())
                p_tgl = st.text_input("Bulan/Tahun", value="Maret 2026")
                p_nom = st.number_input("Jumlah (Rp)", value=20000)
                if st.form_submit_button("Bayar Sekarang"):
                    # Update History Pembayaran
                    new_b = pd.DataFrame([{"Nama": p_nama, "Bulan/Tahun": p_tgl, "Status": "Lunas"}])
                    df_bayar = pd.concat([df_bayar, new_b], ignore_index=True)
                    conn.update(worksheet="Data Pembayaran", data=df_bayar)
                    
                    # Sinkron ke Kas RT (Masuk, Keluar, Keterangan, Sisa Saldo)
                    last_s = pd.to_numeric(df_kas["Sisa Saldo"]).iloc[-1] if not df_kas.empty else 0
                    new_k = pd.DataFrame([{"Masuk": p_nom, "Keluar": 0, "Keterangan": f"Iuran {p_tgl}-{p_nama}", "Sisa Saldo": last_s + p_nom}])
                    df_kas = pd.concat([df_kas, new_k], ignore_index=True)
                    conn.update(worksheet="Kas RT", data=df_kas)
                    st.success("Pembayaran Berhasil!")

        # --- 3. KAS RT (Sesuai kolom: Masuk, Keluar, Keterangan, Sisa Saldo) ---
        elif menu == "Kas RT":
            st.header("📈 Laporan Keuangan")
            st.dataframe(df_kas, use_container_width=True)
            with st.expander("Input Pengeluaran"):
                with st.form("keluar"):
                    k_jml = st.number_input("Jumlah Keluar", min_value=0)
                    k_ket = st.text_input("Keterangan Pengeluaran")
                    if st.form_submit_button("Simpan Pengeluaran"):
                        last_s = pd.to_numeric(df_kas["Sisa Saldo"]).iloc[-1] if not df_kas.empty else 0
                        new_k = pd.DataFrame([{"Masuk": 0, "Keluar": k_jml, "Keterangan": k_ket, "Sisa Saldo": last_s - k_jml}])
                        df_kas = pd.concat([df_kas, new_k], ignore_index=True)
                        conn.update(worksheet="Kas RT", data=df_kas)
                        st.success("Pengeluaran dicatat!")
                        st.rerun()

    except Exception as e:
        st.error("⚠️ Masalah Struktur Sheets!")
        st.write("Pastikan di Google Sheets ada tab: **Warga**, **Data Pembayaran**, dan **Kas RT**.")
        st.code(str(e))

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

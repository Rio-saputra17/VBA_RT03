import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Konfigurasi Tampilan Mobile
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
        
        # Baca data - pastikan nama worksheet sama dengan tab di Google Sheets
        df_warga = conn.read(worksheet="Warga", ttl="0")
        df_bayar = conn.read(worksheet="Data Pembayaran", ttl="0")
        df_kas = conn.read(worksheet="Kas RT", ttl="0")

        st.sidebar.title("Menu RT 03")
        menu = st.sidebar.radio("Navigasi", ["Update Warga", "Input Pembayaran", "Kas RT (Keuangan)"])

        # --- 1. MENU UPDATE WARGA ---
        if menu == "Update Warga":
            st.header("👥 Manajemen Warga")
            tab1, tab2 = st.tabs(["Tambah Warga Baru", "Edit Data Warga"])
            with tab1:
                with st.form("tambah_warga"):
                    n = st.text_input("Nama Warga")
                    a = st.text_input("Alamat Rumah")
                    s = st.selectbox("Status", ["Pribadi", "Kontrak"])
                    k = st.text_input("Kontak (Telepon)")
                    if st.form_submit_button("Simpan"):
                        new_w = pd.DataFrame([{"nama warga": n, "Alamat rumah": a, "status rumah": s, "Kontak": k}])
                        df_warga = pd.concat([df_warga, new_w], ignore_index=True)
                        conn.update(worksheet="Warga", data=df_warga)
                        st.success("Data Tersimpan!")
                        st.rerun()
            with tab2:
                edited = st.data_editor(df_warga, use_container_width=True, num_rows="dynamic")
                if st.button("Update Data"):
                    conn.update(worksheet="Warga", data=edited)
                    st.success("Data Berhasil Diperbarui!")

        # --- 2. MENU INPUT PEMBAYARAN (SINKRON KE KAS) ---
        elif menu == "Input Pembayaran":
            st.header("💰 Input Pembayaran Iuran")
            with st.form("form_bayar"):
                p_nama = st.selectbox("Pilih Nama", df_warga.iloc[:, 0].unique())
                p_tgl = st.text_input("Bulan/Tahun", value="Maret 2026")
                p_nom = st.number_input("Jumlah (Rp)", value=20000)
                if st.form_submit_button("Simpan Pembayaran"):
                    # Update History Iuran
                    new_b = pd.DataFrame([{"Nama": p_nama, "Bulan/tahun": p_tgl, "Status": "Lunas"}])
                    df_bayar = pd.concat([df_bayar, new_b], ignore_index=True)
                    conn.update(worksheet="Data Pembayaran", data=df_bayar)
                    
                    # Update Kas RT (Otomatis hitung sisa saldo)
                    last_s = pd.to_numeric(df_kas.iloc[:, 3]).iloc[-1] if not df_kas.empty else 0
                    new_k = pd.DataFrame([{
                        "Masuk": p_nom, 
                        "Keluar": 0, 
                        "keterangan": f"Iuran {p_tgl} - {p_nama}", 
                        "Sisa Saldo": last_s + p_nom
                    }])
                    df_kas = pd.concat([df_kas, new_k], ignore_index=True)
                    conn.update(worksheet="Kas RT", data=df_kas)
                    st.success("Pembayaran Berhasil & Kas Terupdate!")
                    st.balloons()

        # --- 3. MENU KAS RT ---
        elif menu == "Kas RT (Keuangan)":
            st.header("📈 Laporan Keuangan")
            # Hitung totalan
            t_masuk = pd.to_numeric(df_kas.iloc[:, 0], errors='coerce').sum()
            t_keluar = pd.to_numeric(df_kas.iloc[:, 1], errors='coerce').sum()
            st.metric("Total Sisa Saldo", f"Rp {t_masuk - t_keluar:,.0f}")
            
            st.divider()
            with st.expander("Input Pengeluaran Manual"):
                with st.form("form_keluar"):
                    k_jml = st.number_input("Jumlah Keluar", min_value=0)
                    k_ket = st.text_input("Keterangan Pengeluaran")
                    if st.form_submit_button("Simpan Pengeluaran"):
                        last_s = pd.to_numeric(df_kas.iloc[:, 3]).iloc[-1] if not df_kas.empty else 0
                        new_out = pd.DataFrame([{"Masuk": 0, "Keluar": k_jml, "keterangan": k_ket, "Sisa Saldo": last_s - k_jml}])
                        df_kas = pd.concat([df_kas, new_out], ignore_index=True)
                        conn.update(worksheet="Kas RT", data=df_kas)
                        st.success("Pengeluaran Tercatat!")
                        st.rerun()
            
            st.dataframe(df_kas, use_container_width=True)

    except Exception as e:
        st.error("⚠️ Masalah Struktur Google Sheets!")
        st.write("Cek kembali nama tab di bawah: Warga , Data Pembayaran , Kas RT")
        st.code(str(e))

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

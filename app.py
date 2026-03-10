import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# 1. Setting Tampilan Mobile
st.set_page_config(page_title="Admin RT 03", layout="wide")

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

        # --- LOGIKA OTOMATIS LOAD & HEADER ---
        def load_safe(sheet, cols):
            try:
                df = conn.read(worksheet=sheet, ttl="0")
                if df.empty: return pd.DataFrame(columns=cols)
                return df
            except:
                return pd.DataFrame(columns=cols)

        df_warga = load_safe("Warga", ["nama warga", "Alamat rumah", "status rumah", "Kontak"])
        df_bayar = load_safe("Data Pembayaran", ["Nama", "Bulan/tahun", "Status"])
        df_kas = load_safe("Kas RT", ["Masuk", "Keluar", "keterangan", "Sisa Saldo"])

        # --- NAVIGASI ---
        st.sidebar.title("RT 03 VBA")
        menu = st.sidebar.radio("Navigasi", ["Update Warga", "Input Iuran", "History Pembayaran", "Kas RT"])

        # 1. MENU UPDATE WARGA (INPUT & EDIT)
        if menu == "Update Warga":
            st.header("👥 Update Data Warga")
            tab1, tab2 = st.tabs(["Tambah Warga", "Edit/Hapus"])
            with tab1:
                with st.form("tambah"):
                    n = st.text_input("Nama Lengkap")
                    a = st.text_input("Alamat")
                    s = st.selectbox("Status", ["pribadi", "kontrak"])
                    k = st.text_input("No Telepon")
                    if st.form_submit_button("Simpan"):
                        new_w = pd.DataFrame([{"nama warga": n, "Alamat rumah": a, "status rumah": s, "Kontak": k}])
                        df_w = pd.concat([df_warga, new_w], ignore_index=True)
                        conn.update(worksheet="Warga", data=df_w)
                        st.success("Tersimpan!")
                        st.rerun()
            with tab2:
                edited = st.data_editor(df_warga, use_container_width=True, num_rows="dynamic")
                if st.button("Update Seluruh Data"):
                    conn.update(worksheet="Warga", data=edited)
                    st.success("Data Berhasil Disinkronkan!")

        # 2. MENU INPUT IURAN (SINKRON KAS)
        elif menu == "Input Iuran":
            st.header("💰 Input Pembayaran")
            if df_warga.empty:
                st.warning("Isi data warga dulu!")
            else:
                with st.form("bayar"):
                    p_nama = st.selectbox("Pilih Nama", df_warga["nama warga"].unique())
                    p_bln = st.text_input("Bulan/Tahun", value=datetime.now().strftime("%B %Y"))
                    p_jml = st.number_input("Jumlah (Rp)", value=20000)
                    if st.form_submit_button("Simpan & Sinkron"):
                        # Ke Data Pembayaran
                        new_b = pd.DataFrame([{"Nama": p_nama, "Bulan/tahun": p_bln, "Status": "Lunas"}])
                        df_b = pd.concat([df_bayar, new_b], ignore_index=True)
                        conn.update(worksheet="Data Pembayaran", data=df_b)
                        # Ke Kas (Otomatis Saldo)
                        last_s = pd.to_numeric(df_kas["Sisa Saldo"]).iloc[-1] if not df_kas.empty else 0
                        new_k = pd.DataFrame([{"Masuk": p_jml, "Keluar": 0, "keterangan": f"Iuran {p_bln}-{p_nama}", "Sisa Saldo": last_s + p_jml}])
                        df_k = pd.concat([df_kas, new_k], ignore_index=True)
                        conn.update(worksheet="Kas RT", data=df_k)
                        st.success("Pembayaran Berhasil Dicatat!")

        # 3. MENU HISTORY
        elif menu == "History Pembayaran":
            st.header("📊 History Iuran")
            st.dataframe(df_bayar, use_container_width=True)

        # 4. MENU KAS (EDIT & SINKRON)
        elif menu == "Kas RT":
            st.header("📈 Keuangan RT")
            t_masuk = pd.to_numeric(df_kas["Masuk"]).sum()
            t_keluar = pd.to_numeric(df_kas["Keluar"]).sum()
            st.metric("Total Sisa Saldo", f"Rp {t_masuk - t_keluar:,.0f}")
            st.divider()
            with st.expander("Input Pengeluaran Manual"):
                with st.form("keluar"):
                    k_jml = st.number_input("Jumlah Keluar")
                    k_ket = st.text_input("Keterangan")
                    if st.form_submit_button("Simpan Pengeluaran"):
                        last_s = t_masuk - t_keluar
                        new_out = pd.DataFrame([{"Masuk": 0, "Keluar": k_jml, "keterangan": k_ket, "Sisa Saldo": last_s - k_jml}])
                        df_ko = pd.concat([df_kas, new_out], ignore_index=True)
                        conn.update(worksheet="Kas RT", data=df_ko)
                        st.success("Pengeluaran Tercatat!")
                        st.rerun()
            st.dataframe(df_kas, use_container_width=True)

    except Exception as e:
        st.error("⚠️ Cek Nama Tab Sheets Bos!")
        st.write("Wajib ada tab: Warga, Data Pembayaran, Kas RT")
        st.code(str(e))

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Setting layar HP
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
        
        # --- FUNGSI AMBIL DATA AMAN ---
        def get_data(sheet_name):
            try:
                return conn.read(worksheet=sheet_name, ttl="0")
            except:
                # Jika error/sheet tidak ada, buatkan data kosong sementara agar aplikasi tidak crash
                if sheet_name == "Iuran":
                    return pd.DataFrame(columns=["Nama", "Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
                elif sheet_name == "Kas":
                    return pd.DataFrame(columns=["Tanggal", "Keterangan", "Tipe", "Jumlah"])
                else:
                    return pd.DataFrame(columns=["Nama", "Alamat", "Telepon"])

        df_warga = get_data("Warga")
        df_iuran = get_data("Iuran")
        df_kas = get_data("Kas")

        # --- AUTO SINKRONISASI NAMA WARGA ---
        if not df_warga.empty:
            warga_induk = set(df_warga['Nama'].dropna().unique())
            warga_iuran = set(df_iuran['Nama'].dropna().unique()) if 'Nama' in df_iuran.columns else set()
            
            baru = warga_induk - warga_iuran
            if baru:
                for n in baru:
                    row = {col: "Belum" for col in df_iuran.columns}
                    row["Nama"] = n
                    df_iuran = pd.concat([df_iuran, pd.DataFrame([row])], ignore_index=True)
                conn.update(worksheet="Iuran", data=df_iuran)

        # --- NAVIGASI ---
        st.sidebar.title("Menu RT 03")
        menu = st.sidebar.radio("Navigasi:", ["Data Warga", "Input Iuran", "Data Iuran Warga", "Rekap Kas", "Edit Data Warga"])

        if menu == "Data Warga":
            st.header("👥 Data Warga")
            st.dataframe(df_warga, use_container_width=True)

        elif menu == "Input Iuran":
            st.header("💰 Input Iuran")
            if df_warga.empty:
                st.warning("Isi data warga dulu di menu Edit Data Warga!")
            else:
                with st.form("pembayaran"):
                    nama = st.selectbox("Nama Warga", df_warga['Nama'].unique())
                    bln = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
                    jml = st.number_input("Jumlah (Rp)", value=20000)
                    if st.form_submit_button("Simpan"):
                        # Update Iuran
                        df_iuran.loc[df_iuran['Nama'] == nama, bln] = "LUNAS"
                        conn.update(worksheet="Iuran", data=df_iuran)
                        # Update Kas
                        new_kas = pd.DataFrame([{"Tanggal": datetime.now().strftime("%Y-%m-%d"), "Keterangan": f"Iuran {bln} - {nama}", "Tipe": "Masuk", "Jumlah": jml}])
                        df_kas = pd.concat([df_kas, new_kas], ignore_index=True)
                        conn.update(worksheet="Kas", data=df_kas)
                        st.success("Tersimpan!")
                        st.rerun()

        elif menu == "Data Iuran Warga":
            st.header("📅 Data Iuran Warga")
            st.dataframe(df_iuran, use_container_width=True)

        elif menu == "Rekap Kas":
            st.header("📈 Rekap Kas")
            df_kas['Jumlah'] = pd.to_numeric(df_kas['Jumlah'], errors='coerce').fillna(0)
            masuk = df_kas[df_kas['Tipe'] == 'Masuk']['Jumlah'].sum()
            keluar = df_kas[df_kas['Tipe'] == 'Keluar']['Jumlah'].sum()
            
            c1, c2 = st.columns(2)
            c1.metric("Total Masuk", f"Rp {masuk:,.0f}")
            c2.metric("Saldo", f"Rp {masuk - keluar:,.0f}")
            st.divider()
            st.subheader("Laporan Keluar/Masuk")
            st.dataframe(df_kas, use_container_width=True)

        elif menu == "Edit Data Warga":
            st.header("📝 Edit Data Warga")
            edited = st.data_editor(df_warga, use_container_width=True, num_rows="dynamic")
            if st.button("Simpan Perubahan"):
                conn.update(worksheet="Warga", data=edited)
                st.success("Berhasil!")
                st.rerun()

    except Exception as e:
        st.error("Cek Nama Sheet di Google Sheets Anda!")
        st.info("Pastikan ada 3 Sheet dengan nama persis: Warga , Iuran , Kas (Huruf besar kecil pengaruh)")
        st.code(str(e))

    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()
2

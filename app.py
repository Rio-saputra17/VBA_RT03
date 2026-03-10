import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Setting layar HP agar tidak perlu mode desktop
st.set_page_config(page_title="Admin RT 03", layout="centered")

st.title("📲 Sistem Administrasi RT 03")

# Koneksi ke Google Sheets
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # Ganti "Sheet1" dengan nama sheet iuran/warga Anda
    df = conn.read(ttl="0") 
    
    st.success("Terhubung ke Google Sheets!")

    # Menu Simpel
    tab1, tab2 = st.tabs(["📊 Rekap Iuran", "📝 Edit Data"])

    with tab1:
        st.subheader("Tabel Iuran & Kas")
        # Menampilkan tabel yang pas di layar HP
        st.dataframe(df, use_container_width=True)

    with tab2:
        st.subheader("Update Data Warga")
        # Editor tabel yang ringan
        edited_df = st.data_editor(df, use_container_width=True)
        
        if st.button("Simpan ke Google Sheets"):
            conn.update(data=edited_df)
            st.balloons()
            st.success("Data Berhasil Disimpan!")

except Exception as e:
    st.error("Waduh, ada kendala koneksi:")
    st.code(str(e))

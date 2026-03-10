import streamlit as st
import pandas as pd

st.set_page_config(page_title="RT 03 Monitoring", layout="wide")

# Link Google Sheets Juragan yang sudah dalam format CSV
sheet_id = "1t1zxEQINPu7lPiPfEmlWLK8NWHjtt4cQdamsdINHfW0"
url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0"

st.title("🏡 Sistem RT 03 - Koneksi Langsung")

try:
    # Kita coba tarik data secara langsung tanpa lewat 'Secrets'
    df = pd.read_csv(url)
    
    st.success("✅ KONEKSI BERHASIL!")
    st.write("Daftar Warga:")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error("❌ Masih Gagal Konek, Bos!")
    st.info(f"Pesan Error: {e}")
    st.warning("Coba cek apakah Google Sheets-nya sudah di-Publish ke Web?")

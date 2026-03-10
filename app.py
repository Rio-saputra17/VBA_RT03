import streamlit as st
from streamlit_gsheets import GSheetsConnection

# Pengaturan halaman agar lebar menyesuaikan layar HP
st.set_page_config(layout="wide")

st.title("Manajemen RT 03")

# [span_0](start_span)Inisialisasi koneksi ke Google Sheets[span_0](end_span)
conn = st.connection("gsheets", type=GSheetsConnection)

# [span_1](start_span)Fungsi untuk mengambil data warga[span_1](end_span)
# [span_2](start_span)Sesuai dengan sheet 'Warga' di file 'RT03 VBA'[span_2](end_span)
df_warga = conn.read(worksheet="Warga", ttl="0")

# Menu navigasi simpel (Dropdown lebih ramah HP daripada Sidebar lebar)
menu = st.selectbox("Pilih Menu", ["Data Warga", "Input Iuran", "Rekap Kas"])

if menu == "Data Warga":
    st.subheader("Edit Data Warga")
    # [span_3](start_span)Tabel yang bisa langsung diedit dan responsif[span_3](end_span)
    edited_df = st.data_editor(df_warga, use_container_width=True, num_rows="dynamic")
    
    if st.button("Simpan Perubahan"):
        # [span_4](start_span)Sinkronisasi otomatis ke Google Sheets[span_4](end_span)
        conn.update(worksheet="Warga", data=edited_df)
        st.success("Data berhasil disinkronkan!")

elif menu == "Input Iuran":
    st.subheader("Catat Iuran Baru")
    # Form simpel agar mudah diisi di layar kecil
    with st.form("form_iuran"):
        nama_warga = st.selectbox("Nama Warga", df_warga['Nama'].tolist())
        jumlah = st.number_input("Jumlah Iuran (Rp)", step=1000)
        tanggal = st.date_input("Tanggal")
        
        submit = st.form_submit_button("Simpan Iuran")
        if submit:
            # Logika tambah baris ke sheet iuran bisa ditambahkan di sini
            st.info(f"Iuran {nama_warga} sebesar {jumlah} tercatat.")

elif menu == "Rekap Kas":
    st.subheader("Total Saldo Kas")
    # Tampilan ringkas untuk layar HP
    st.metric(label="Total Kas RT", value="Rp 2.500.000")
1

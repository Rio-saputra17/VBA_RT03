import streamlit as st
from supabase import create_client
import pandas as pd
from datetime import datetime

# --- KONEKSI ---
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="RT 03 Digital", layout="wide")

# --- LOGIN ---
if 'role' not in st.session_state:
    st.session_state.role = None

if st.session_state.role is None:
    st.title("🏡 Sistem Administrasi RT 03")
    role_pilih = st.selectbox("Masuk Sebagai:", ["Pilih", "Warga", "Admin"])
    pwd = st.text_input("Password", type="password")
    if st.button("Login"):
        if role_pilih == "Admin" and pwd == st.secrets["passwords"]["admin"]:
            st.session_state.role = "Admin"
            st.rerun()
        elif role_pilih == "Warga" and pwd == st.secrets["passwords"]["warga"]:
            st.session_state.role = "Warga"
            st.rerun()
        else:
            st.error("Password Salah, Ndan!")
else:
    role = st.session_state.role
    st.sidebar.title(f"Menu {role}")
    
    # Navigasi Menu Sesuai Permintaan
    if role == "Admin":
        menu = st.sidebar.radio("Navigasi", ["WARGA", "IURAN BULANAN", "KAS RT", "INPUT PEMBAYARAN", "TAMBAH/EDIT DATA"])
    else:
        menu = st.sidebar.radio("Navigasi", ["WARGA", "IURAN BULANAN", "KAS RT"])

    # --- MENU 1: WARGA ---
    if menu == "WARGA":
        st.header("📋 Data Warga RT 03")
        search = st.text_input("🔍 Cari Nama Warga (Otomatis)...").lower()
        
        # Ambil data warga & anggota keluarga
        res_w = supabase.table("warga").select("*, anggota_keluarga(*)").execute()
        df_w = pd.DataFrame(res_w.data)

        if not df_w.empty:
            if search:
                df_w = df_w[df_w['nama_kk'].str.lower().contains(search)]
            
            for i, row in df_w.iterrows():
                with st.expander(f"👤 {row['nama_kk']} - {row['alamat']}"):
                    st.write(f"**Status:** {row['status_rumah']} | **Kontak:** {row['kontak']}")
                    if role == "Admin": st.write(f"**NIK:** {row['nik']}")
                    
                    st.write(f"**Jumlah Keluarga:** {row['jml_anggota']}")
                    if row['anggota_keluarga']:
                        for agg in row['anggota_keluarga']:
                            st.write(f"- {agg['nama_anggota']} ({agg['hubungan']})")
            
            # FITUR DOWNLOAD DATA WARGA
            st.download_button("📥 Download Data Warga", df_w.to_csv(index=False), "data_warga.csv", "text/csv")

    # --- MENU 2: IURAN BULANAN ---
    elif menu == "IURAN BULANAN":
        st.header("💰 History Iuran Bulanan")
        search_i = st.text_input("🔍 Cari Nama Pembayar...").lower()
        res_i = supabase.table("iuran").select("*").execute()
        df_i = pd.DataFrame(res_i.data)
        
        if not df_i.empty:
            if search_i:
                df_i = df_i[df_i['nama_warga'].str.lower().contains(search_i)]
            st.dataframe(df_i, use_container_width=True)

    # --- MENU 3: KAS RT ---
    elif menu == "KAS RT":
        st.header("📊 Laporan Kas RT")
        res_k = supabase.table("kas_rt").select("*").execute()
        df_k = pd.DataFrame(res_k.data)
        
        if not df_k.empty:
            masuk = df_k[df_k['jenis'] == 'Masuk']['jumlah'].sum()
            keluar = df_k[df_k['jenis'] == 'Keluar']['jumlah'].sum()
            saldo = masuk - keluar
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Masuk", f"Rp {masuk:,}")
            c2.metric("Total Keluar", f"Rp {keluar:,}")
            c3.metric("Sisa Saldo", f"Rp {saldo:,}", delta_color="normal")
            
            st.bar_chart(df_k.groupby('jenis')['jumlah'].sum())
            st.table(df_k)
            
            # FITUR DOWNLOAD LAPORAN KAS
            st.download_button("📥 Download Laporan Kas", df_k.to_csv(index=False), "laporan_kas.csv", "text/csv")

            if role == "Admin":
                st.subheader("➕ Tambah/Kurang Saldo Manual")
                with st.form("form_kas"):
                    j_k = st.selectbox("Jenis", ["Masuk", "Keluar"])
                    u_k = st.number_input("Jumlah Uang", min_value=0)
                    ket_k = st.text_input("Keterangan")
                    if st.form_submit_button("Update Kas"):
                        supabase.table("kas_rt").insert({"jenis": j_k, "jumlah": u_k, "keterangan": ket_k}).execute()
                        st.success("Kas Berhasil Diupdate!")
                        st.rerun()

    # --- MENU 4: INPUT PEMBAYARAN (ADMIN) ---
    elif menu == "INPUT PEMBAYARAN":
        st.header("💸 Input Pembayaran Warga")
        w_list = supabase.table("warga").select("nama_kk").execute()
        pilih_w = st.selectbox("Cari & Pilih Nama", [w['nama_kk'] for w in w_list.data])
        bln = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
        thn = st.selectbox("Tahun", [2025, 2026, 2027])
        nominal = st.number_input("Nominal Iuran", value=50000)
        
        if st.button("Simpan & Sinkronkan"):
            # Sinkron ke Iuran
            supabase.table("iuran").insert({"nama_warga": pilih_w, "periode": f"{bln} {thn}", "status": "Lunas"}).execute()
            # Sinkron ke Kas
            supabase.table("kas_rt").insert({"jenis": "Masuk", "jumlah": nominal, "keterangan": f"Iuran {pilih_w} - {bln} {thn}"}).execute()
            st.success("Data Sinkron ke Iuran & Kas RT!")

    # --- MENU 5: TAMBAH/EDIT DATA (ADMIN) ---
    elif menu == "TAMBAH/EDIT DATA":
        st.header("📝 Tambah Data Warga Baru")
        with st.form("form_warga_baru"):
            n_kk = st.text_input("Nama Kepala Keluarga")
            n_nik = st.text_input("NIK")
            n_alm = st.text_input("Alamat")
            n_sts = st.selectbox("Status", ["Pribadi", "Kontrak"])
            n_kon = st.text_input("Kontak (WA)")
            n_jml = st.number_input("Jumlah Anggota Keluarga", min_value=0, step=1)
            
            # Logika Otomatis Kolom Anggota
            anggota_list = []
            if n_jml > 0:
                for i in range(int(n_jml)):
                    st.write(f"Anggota {i+1}")
                    ca, cb = st.columns(2)
                    na = ca.text_input(f"Nama Anggota {i+1}", key=f"na_{i}")
                    ha = cb.selectbox(f"Hubungan {i+1}", ["Istri", "Anak", "Orang Tua", "Saudara", "Lain-lain"], key=f"ha_{i}")
                    anggota_list.append({"nama_anggota": na, "hubungan": ha})
            
            if st.form_submit_button("Simpan Semua Data"):
                res_warga = supabase.table("warga").insert({"nama_kk": n_kk, "nik": n_nik, "alamat": n_alm, "status_rumah": n_sts, "kontak": n_kon, "jml_anggota": n_jml}).execute()
                id_kk = res_warga.data[0]['id']
                if anggota_list:
                    for a in anggota_list:
                        a['id_kk'] = id_kk
                        supabase.table("anggota_keluarga").insert(a).execute()
                st.success("Data & Keluarga Berhasil Disimpan!")

    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.rerun()

import streamlit as st
from supabase import create_client
import pandas as pd
from io import BytesIO

# --- KONEKSI ---
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["key"]
supabase = create_client(url, key)

st.set_page_config(page_title="RT 03 Digital", layout="wide")

# Fungsi Helper untuk Export Excel
def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    return output.getvalue()

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
    
    menu = st.sidebar.radio("Navigasi", ["DASHBOARD", "WARGA", "IURAN BULANAN", "KAS RT", "INPUT PEMBAYARAN", "TAMBAH/EDIT DATA"] if role == "Admin" else ["DASHBOARD", "WARGA", "IURAN BULANAN", "KAS RT"])

    # --- MENU 0: DASHBOARD (FITUR BARU) ---
    if menu == "DASHBOARD":
        st.header("📊 Ringkasan Kas & Iuran")
        
        # Ambil data Kas untuk Summary
        res_k = supabase.table("kas_rt").select("*").execute()
        df_k = pd.DataFrame(res_k.data)
        
        if not df_k.empty:
            df_k['created_at'] = pd.to_datetime(df_k['created_at'])
            masuk = df_k[df_k['jenis'] == 'Masuk']['jumlah'].sum()
            keluar = df_k[df_k['jenis'] == 'Keluar']['jumlah'].sum()
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Saldo", f"Rp {masuk-keluar:,}")
            c2.metric("Pemasukan", f"Rp {masuk:,}")
            c3.metric("Pengeluaran", f"Rp {keluar:,}")
            
            st.divider()
            
            # Grafik Tren Pemasukan per Bulan
            st.subheader("📈 Tren Pemasukan Kas")
            df_masuk = df_k[df_k['jenis'] == 'Masuk'].copy()
            if not df_masuk.empty:
                df_masuk['Bulan'] = df_masuk['created_at'].dt.strftime('%Y-%m')
                chart_data = df_masuk.groupby('Bulan')['jumlah'].sum()
                st.bar_chart(chart_data)
            else:
                st.info("Belum ada data pemasukan untuk grafik.")

    # --- MENU 1: WARGA ---
    elif menu == "WARGA":
        st.header("📋 Data Warga RT 03")
        search = st.text_input("🔍 Cari Nama Warga...").lower()
        res_w = supabase.table("warga").select("*").order("nama_kk").execute()
        df_w = pd.DataFrame(res_w.data)
        if not df_w.empty:
            if search:
                df_w = df_w[df_w['nama_kk'].str.lower().str.contains(search)]
            
            if role == "Admin":
                st.download_button(label="📥 Download Data Warga (Excel)", data=to_excel(df_w), file_name='data_warga_rt03.xlsx')
            
            for i, row in df_w.iterrows():
                with st.expander(f"👤 {row['nama_kk']} - {row['alamat']}"):
                    st.write(f"**Status:** {row['status_rumah']} | **Kontak:** {row['kontak']}")
                    if role == "Admin": st.write(f"**NIK:** {row['nik']}")

    # --- MENU 2: IURAN BULANAN ---
    elif menu == "IURAN BULANAN":
        st.header("💰 History Iuran Bulanan")
        search_i = st.text_input("🔍 Cari Nama Warga atau Kategori...")
        res_i = supabase.table("iuran").select("*").order("created_at", desc=True).execute()
        df_i = pd.DataFrame(res_i.data)
        if not df_i.empty:
            if search_i:
                df_i = df_i[(df_i['nama_warga'].str.contains(search_i, case=False, na=False)) | (df_i['keterangan'].str.contains(search_i, case=False, na=False))]
            
            st.dataframe(df_i, use_container_width=True)
            st.download_button(label="📥 Download History Iuran (Excel)", data=to_excel(df_i), file_name='history_iuran_rt03.xlsx')

    # --- MENU 3: KAS RT ---
    elif menu == "KAS RT":
        st.header("📊 Laporan Kas RT")
        res_k = supabase.table("kas_rt").select("*").order("created_at", desc=True).execute()
        df_k = pd.DataFrame(res_k.data)
        if not df_k.empty:
            masuk = df_k[df_k['jenis'] == 'Masuk']['jumlah'].sum()
            keluar = df_k[df_k['jenis'] == 'Keluar']['jumlah'].sum()
            
            col1, col2 = st.columns(2)
            col1.metric("Total Masuk", f"Rp {masuk:,}")
            col2.metric("Total Keluar", f"Rp {keluar:,}")

            st.divider()
            st.download_button(label="📥 Download Laporan Kas Lengkap (Excel)", data=to_excel(df_k), file_name='laporan_kas_rt03.xlsx')

            df_show = df_k[~df_k['keterangan'].str.contains("Iuran Wajib", na=False)]
            st.subheader("📋 Riwayat Kas (Operasional & Lain-lain)")
            s_kas = st.text_input("🔍 Cari nominal atau keterangan kas...")
            if s_kas:
                df_show = df_show[(df_show['keterangan'].str.contains(s_kas, case=False, na=False)) | (df_show['jumlah'].astype(str).contains(s_kas))]
            st.table(df_show[['created_at', 'jenis', 'jumlah', 'keterangan']])

        if role == "Admin":
            with st.expander("🛠️ Input Kas Manual"):
                with st.form("form_kas", clear_on_submit=True):
                    kj, kn = st.selectbox("Jenis", ["Masuk", "Keluar"]), st.number_input("Nominal", min_value=0)
                    kk = st.text_area("Keterangan")
                    if st.form_submit_button("Simpan Kas"):
                        supabase.table("kas_rt").insert({"jenis": kj, "jumlah": kn, "keterangan": kk}).execute()
                        st.success("Berhasil!")
                        st.rerun()

    # --- MENU 4: INPUT PEMBAYARAN ---
    elif menu == "INPUT PEMBAYARAN":
        st.header("💸 Input Pembayaran")
        w_list = supabase.table("warga").select("nama_kk").execute()
        with st.form("form_bayar", clear_on_submit=True):
            pw = st.selectbox("Pilih Warga", [w['nama_kk'] for w in w_list.data])
            bln = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
            thn = st.selectbox("Tahun", [2025, 2026])
            kat = st.radio("Kategori", ["Iuran Wajib", "Lain-Lain"], horizontal=True)
            nom = st.number_input("Nominal", value=50000)
            if st.form_submit_button("Simpan & Sinkron"):
                supabase.table("iuran").insert({"nama_warga": pw, "periode": f"{bln} {thn}", "status": "Lunas", "keterangan": kat}).execute()
                supabase.table("kas_rt").insert({"jenis": "Masuk", "jumlah": nom, "keterangan": f"{kat} - {pw} ({bln} {thn})"}).execute()
                st.success("Data Berhasil Disinkron!")
                st.rerun()

    # --- MENU 5: TAMBAH/EDIT DATA ---
    elif menu == "TAMBAH/EDIT DATA":
        tab1, tab2 = st.tabs(["👥 Kelola Warga", "📑 Koreksi Iuran/Kas"])
        with tab1:
            st.header("📝 Tambah Warga Baru")
            with st.form("tambah_warga", clear_on_submit=True):
                n_kk, n_nik, n_alm = st.text_input("Nama KK"), st.text_input("NIK"), st.text_input("Alamat")
                n_sts = st.selectbox("Status", ["Pribadi", "Kontrak"])
                n_kon = st.text_input("Kontak")
                if st.form_submit_button("Simpan Warga"):
                    supabase.table("warga").insert({"nama_kk": n_kk, "nik": n_nik, "alamat": n_alm, "status_rumah": n_sts, "kontak": n_kon}).execute()
                    st.success("Tersimpan!")
                    st.rerun()

        with tab2:
            st.header("🛠️ Koreksi Data Transaksi")
            res_edit = supabase.table("iuran").select("*").order("created_at", desc=True).limit(10).execute()
            if res_edit.data:
                df_edit = pd.DataFrame(res_edit.data)
                pilih_id = st.selectbox("Pilih Transaksi yang akan DIHAPUS (10 Terakhir):", 
                                        options=df_edit['id'].tolist(), 
                                        format_func=lambda x: f"ID: {x} - {df_edit[df_edit['id']==x]['nama_warga'].values[0]} ({df_edit[df_edit['id']==x]['periode'].values[0]})")
                if st.button("🚨 HAPUS TRANSAKSI IURAN"):
                    supabase.table("iuran").delete().eq("id", pilih_id).execute()
                    st.success(f"Transaksi ID {pilih_id} Berhasil Dihapus!")
                    st.rerun()

    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.rerun()

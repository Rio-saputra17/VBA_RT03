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

    # --- MENU 0: DASHBOARD ---
    if menu == "DASHBOARD":
        st.header("📊 Ringkasan Kas & Iuran")
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
            st.subheader("📈 Tren Pemasukan Kas")
            df_masuk = df_k[df_k['jenis'] == 'Masuk'].copy()
            if not df_masuk.empty:
                df_masuk['Bulan'] = df_masuk['created_at'].dt.strftime('%Y-%m')
                chart_data = df_masuk.groupby('Bulan')['jumlah'].sum()
                st.bar_chart(chart_data)

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
        res_i = supabase.table("iuran").select("*").order("created_at", desc=True).execute()
        df_i = pd.DataFrame(res_i.data)
        if not df_i.empty:
            st.dataframe(df_i, use_container_width=True)
            st.download_button(label="📥 Download History Iuran (Excel)", data=to_excel(df_i), file_name='history_iuran_rt03.xlsx')

    # --- MENU 3: KAS RT ---
    elif menu == "KAS RT":
        st.header("📊 Laporan Kas RT")
        res_k = supabase.table("kas_rt").select("*").order("created_at", desc=True).execute()
        df_k = pd.DataFrame(res_k.data)
        if not df_k.empty:
            masuk, keluar = df_k[df_k['jenis'] == 'Masuk']['jumlah'].sum(), df_k[df_k['jenis'] == 'Keluar']['jumlah'].sum()
            c1, c2 = st.columns(2)
            c1.metric("Total Masuk", f"Rp {masuk:,}")
            c2.metric("Total Keluar", f"Rp {keluar:,}")
            st.table(df_k.head(10)[['created_at', 'jenis', 'jumlah', 'keterangan']])

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
                st.success("Tersimpan!")
                st.rerun()

    # --- MENU 5: TAMBAH/EDIT DATA ---
    elif menu == "TAMBAH/EDIT DATA":
        tab1, tab2, tab3 = st.tabs(["➕ Tambah Warga", "👥 Kelola Warga", "📑 Koreksi Iuran/Kas"])
        
        with tab1:
            st.header("📝 Tambah Warga Baru")
            with st.form("tambah_warga_baru", clear_on_submit=True):
                n_kk = st.text_input("Nama Kepala Keluarga (KK)")
                n_nik = st.text_input("NIK Kepala Keluarga")
                n_alm = st.text_input("Alamat")
                n_sts = st.selectbox("Status Rumah", ["Pribadi", "Kontrak"])
                n_kon = st.text_input("Kontak (No HP)")
                st.markdown("---")
                st.subheader("👨‍👩‍👧‍👦 Data Anggota Keluarga")
                st.markdown("### **⌨️ Tekan ENTER setelah isi angka untuk memunculkan kolom nama**")
                jml_kel = st.number_input("Jumlah Anggota Keluarga (Selain KK)", min_value=0, step=1)
                
                anggota_list = []
                for i in range(int(jml_kel)):
                    col_a, col_b = st.columns(2)
                    na = col_a.text_input(f"Nama Anggota {i+1}", key=f"n_new_{i}")
                    sa = col_b.selectbox(f"Status Anggota {i+1}", ["Istri", "Anak", "Orang Tua", "Saudara", "Lainnya"], key=f"s_new_{i}")
                    if na: anggota_list.append({"nama": na, "status": sa})
                
                if st.form_submit_button("💾 Simpan Warga Baru"):
                    supabase.table("warga").insert({"nama_kk": n_kk, "nik": n_nik, "alamat": n_alm, "status_rumah": n_sts, "kontak": n_kon, "anggota_keluarga": anggota_list}).execute()
                    st.success("Warga Berhasil Ditambahkan!")
                    st.rerun()

        with tab2:
            st.header("⚙️ Kelola Data Warga")
            res_w_all = supabase.table("warga").select("*").order("nama_kk").execute()
            df_w_all = pd.DataFrame(res_w_all.data)
            warga_list = ["-- Pilih Warga --"] + df_w_all['nama_kk'].tolist()
            warga_pilih = st.selectbox("Pilih Warga untuk Edit/Hapus:", warga_list)
            
            if warga_pilih != "-- Pilih Warga --":
                data_edit = df_w_all[df_w_all['nama_kk'] == warga_pilih].iloc[0]
                with st.form("form_edit_warga"):
                    e_nama = st.text_input("Edit Nama KK", value=data_edit['nama_kk'])
                    e_nik = st.text_input("Edit NIK", value=data_edit['nik'])
                    e_alm = st.text_input("Edit Alamat", value=data_edit['alamat'])
                    e_sts = st.selectbox("Edit Status", ["Pribadi", "Kontrak"], index=0 if data_edit['status_rumah']=="Pribadi" else 1)
                    e_kon = st.text_input("Edit Kontak", value=data_edit['kontak'])
                    
                    old_ak = data_edit.get('anggota_keluarga', [])
                    if not isinstance(old_ak, list): old_ak = []
                    
                    st.markdown("### **⌨️ Tekan ENTER untuk update jumlah kolom**")
                    e_jml = st.number_input("Jumlah Anggota Baru", min_value=0, step=1, value=len(old_ak))
                    e_list = []
                    for j in range(int(e_jml)):
                        dn = old_ak[j]['nama'] if j < len(old_ak) else ""
                        ds = old_ak[j]['status'] if j < len(old_ak) else "Istri"
                        ca, cb = st.columns(2)
                        en = ca.text_input(f"Nama Anggota {j+1}", value=dn, key=f"en_{j}")
                        es = cb.selectbox(f"Status {j+1}", ["Istri", "Anak", "Orang Tua", "Saudara", "Lainnya"], index=["Istri", "Anak", "Orang Tua", "Saudara", "Lainnya"].index(ds) if ds in ["Istri", "Anak", "Orang Tua", "Saudara", "Lainnya"] else 0, key=f"es_{j}")
                        if en: e_list.append({"nama": en, "status": es})
                    
                    if st.form_submit_button("💾 Update Data"):
                        supabase.table("warga").update({"nama_kk": e_nama, "nik": e_nik, "alamat": e_alm, "status_rumah": e_sts, "kontak": e_kon, "anggota_keluarga": e_list}).eq("id", data_edit['id']).execute()
                        st.success("Data Terupdate!")
                        st.rerun()
                if st.button("🗑️ HAPUS WARGA"):
                    supabase.table("warga").delete().eq("id", data_edit['id']).execute()
                    st.rerun()

        with tab3:
            st.header("🛠️ Koreksi Iuran & Kas")
            mode_koreksi = st.radio("Pilih Data yang Akan Dikoreksi:", ["Hapus Transaksi Iuran", "Hapus Transaksi Kas"])
            
            if mode_koreksi == "Hapus Transaksi Iuran":
                res_i = supabase.table("iuran").select("*").order("created_at", desc=True).limit(20).execute()
                df_i = pd.DataFrame(res_i.data)
                if not df_i.empty:
                    pilih_i = st.selectbox("Pilih Iuran untuk DIHAPUS:", df_i['id'].tolist(), format_func=lambda x: f"ID {x} - {df_i[df_i['id']==x]['nama_warga'].values[0]} ({df_i[df_i['id']==x]['periode'].values[0]})")
                    if st.button("🚨 HAPUS IURAN"):
                        supabase.table("iuran").delete().eq("id", pilih_i).execute()
                        st.success("Terhapus!"); st.rerun()
            else:
                res_k = supabase.table("kas_rt").select("*").order("created_at", desc=True).limit(20).execute()
                df_k = pd.DataFrame(res_k.data)
                if not df_k.empty:
                    pilih_k = st.selectbox("Pilih Kas untuk DIHAPUS:", df_k['id'].tolist(), format_func=lambda x: f"ID {x} - {df_k[df_k['id']==x]['jenis'].values[0]} Rp{df_k[df_k['id']==x]['jumlah'].values[0]} ({df_k[df_k['id']==x]['keterangan'].values[0]})")
                    if st.button("🚨 HAPUS KAS"):
                        supabase.table("kas_rt").delete().eq("id", pilih_k).execute()
                        st.success("Terhapus!"); st.rerun()

    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.rerun()

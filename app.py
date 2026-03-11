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
            st.info("Pilih menu di samping untuk melihat detail data.")

    # --- MENU 1: WARGA (URUT ABJAD ALAMAT) ---
    elif menu == "WARGA":
        st.header("📋 Data Warga RT 03")
        search = st.text_input("🔍 Cari Nama Warga...").lower()
        # Perbaikan: Diurutkan berdasarkan kolom ALAMAT
        res_w = supabase.table("warga").select("*").order("alamat").execute()
        df_w = pd.DataFrame(res_w.data)
        if not df_w.empty:
            if search:
                df_w = df_w[df_w['nama_kk'].str.lower().str.contains(search)]
            
            if role == "Admin":
                st.download_button(label="📥 Download Data Warga (Excel)", data=to_excel(df_w), file_name='data_warga_rt03.xlsx')
            
            for i, row in df_w.iterrows():
                with st.expander(f"🏠 {row['alamat']} | 👤 {row['nama_kk']}"):
                    st.write(f"**Status:** {row['status_rumah']} | **Kontak:** {row['kontak']}")
                    if role == "Admin": st.write(f"**NIK:** {row['nik']}")
                    # Tampilkan anggota keluarga jika ada
                    ak = row.get('anggota_keluarga', [])
                    if ak:
                        st.write("**Anggota Keluarga:**")
                        for member in ak:
                            st.write(f"- {member['nama']} ({member['status']})")

    # --- MENU 2: IURAN BULANAN (AKTIF KEMBALI) ---
    elif menu == "IURAN BULANAN":
        st.header("💰 History Iuran Bulanan")
        res_i = supabase.table("iuran").select("*").order("created_at", desc=True).execute()
        df_i = pd.DataFrame(res_i.data)
        if not df_i.empty:
            st.dataframe(df_i, use_container_width=True)
            st.download_button(label="📥 Download Excel", data=to_excel(df_i), file_name='history_iuran.xlsx')
        else:
            st.info("Belum ada data iuran.")

    # --- MENU 3: KAS RT (AKTIF KEMBALI) ---
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
            st.table(df_k[['created_at', 'jenis', 'jumlah', 'keterangan']].head(20))
        else:
            st.info("Belum ada data kas.")

    # --- MENU 4: INPUT PEMBAYARAN ---
    elif menu == "INPUT PEMBAYARAN":
        st.header("💸 Input Pembayaran")
        w_list = supabase.table("warga").select("nama_kk").execute()
        # Form otomatis bersih saat rerun
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
                st.rerun() # Membersihkan kolom

    # --- MENU 5: TAMBAH/EDIT DATA ---
    elif menu == "TAMBAH/EDIT DATA":
        tab1, tab2, tab3 = st.tabs(["➕ Tambah Warga", "👥 Kelola Warga", "📑 Koreksi Iuran/Kas"])
        
        with tab1:
            st.header("📝 Tambah Warga Baru")
            n_kk = st.text_input("Nama Kepala Keluarga (KK)")
            n_nik = st.text_input("NIK Kepala Keluarga")
            n_alm = st.text_input("Alamat")
            n_sts = st.selectbox("Status Rumah", ["Pribadi", "Kontrak"])
            n_kon = st.text_input("Kontak (No HP)")
            
            st.divider()
            st.subheader("👨‍👩‍👧‍👦 Data Anggota Keluarga")
            jml_kel = st.number_input("Jumlah Anggota Keluarga (Selain KK)", min_value=0, step=1, value=0)
            
            anggota_list = []
            for i in range(int(jml_kel)):
                col_a, col_b = st.columns(2)
                na = col_a.text_input(f"Nama Anggota {i+1}", key=f"n_new_{i}")
                sa = col_b.selectbox(f"Status Anggota {i+1}", ["Istri", "Anak", "Orang Tua", "Saudara", "Lainnya"], key=f"s_new_{i}")
                if na: anggota_list.append({"nama": na, "status": sa})
            
            if st.button("💾 Simpan Warga Baru"):
                if n_kk:
                    supabase.table("warga").insert({"nama_kk": n_kk, "nik": n_nik, "alamat": n_alm, "status_rumah": n_sts, "kontak": n_kon, "anggota_keluarga": anggota_list}).execute()
                    st.success("Warga Berhasil Ditambahkan!")
                    st.rerun()
                else:
                    st.error("Nama KK wajib diisi!")

        with tab2:
            st.header("⚙️ Kelola Data Warga")
            res_w_all = supabase.table("warga").select("*").order("nama_kk").execute()
            df_w_all = pd.DataFrame(res_w_all.data)
            warga_list = ["-- Pilih Warga --"] + df_w_all['nama_kk'].tolist()
            warga_pilih = st.selectbox("Pilih Warga untuk Edit/Hapus:", warga_list)
            
            if warga_pilih != "-- Pilih Warga --":
                data_edit = df_w_all[df_w_all['nama_kk'] == warga_pilih].iloc[0]
                e_nama = st.text_input("Edit Nama KK", value=data_edit['nama_kk'])
                e_nik = st.text_input("Edit NIK", value=data_edit['nik'])
                e_alm = st.text_input("Edit Alamat", value=data_edit['alamat'])
                e_sts = st.selectbox("Edit Status", ["Pribadi", "Kontrak"], index=0 if data_edit['status_rumah']=="Pribadi" else 1)
                e_kon = st.text_input("Edit Kontak", value=data_edit['kontak'])
                
                old_ak = data_edit.get('anggota_keluarga', [])
                if not isinstance(old_ak, list): old_ak = []
                
                e_jml = st.number_input("Update Jumlah Anggota", min_value=0, step=1, value=len(old_ak))
                e_list = []
                for j in range(int(e_jml)):
                    dn = old_ak[j]['nama'] if j < len(old_ak) else ""
                    ds = old_ak[j]['status'] if j < len(old_ak) else "Istri"
                    ca, cb = st.columns(2)
                    en = ca.text_input(f"Nama Anggota {j+1}", value=dn, key=f"en_{j}")
                    es = cb.selectbox(f"Status {j+1}", ["Istri", "Anak", "Orang Tua", "Saudara", "Lainnya"], index=["Istri", "Anak", "Orang Tua", "Saudara", "Lainnya"].index(ds) if ds in ["Istri", "Anak", "Orang Tua", "Saudara", "Lainnya"] else 0, key=f"es_{j}")
                    if en: e_list.append({"nama": en, "status": es})
                
                col1, col2 = st.columns(2)
                if col1.button("💾 Update Data"):
                    supabase.table("warga").update({"nama_kk": e_nama, "nik": e_nik, "alamat": e_alm, "status_rumah": e_sts, "kontak": e_kon, "anggota_keluarga": e_list}).eq("id", data_edit['id']).execute()
                    st.success("Data Terupdate!")
                    st.rerun()
                if col2.button("🗑️ HAPUS WARGA"):
                    supabase.table("warga").delete().eq("id", data_edit['id']).execute()
                    st.rerun()

        with tab3:
            st.header("🛠️ Koreksi Iuran & Kas")
            mode_koreksi = st.radio("Pilih Data:", ["Hapus Iuran", "Hapus Kas"])
            if mode_koreksi == "Hapus Iuran":
                res_i = supabase.table("iuran").select("*").order("created_at", desc=True).limit(15).execute()
                df_i = pd.DataFrame(res_i.data)
                if not df_i.empty:
                    pilih_i = st.selectbox("Pilih Iuran:", df_i['id'].tolist(), format_func=lambda x: f"{df_i[df_i['id']==x]['nama_warga'].values[0]} ({df_i[df_i['id']==x]['periode'].values[0]})")
                    if st.button("🚨 Hapus Transaksi"):
                        supabase.table("iuran").delete().eq("id", pilih_i).execute()
                        st.success("Terhapus!"); st.rerun()
            else:
                res_k = supabase.table("kas_rt").select("*").order("created_at", desc=True).limit(15).execute()
                df_k = pd.DataFrame(res_k.data)
                if not df_k.empty:
                    pilih_k = st.selectbox("Pilih Kas:", df_k['id'].tolist(), format_func=lambda x: f"{df_k[df_k['id']==x]['jenis'].values[0]} Rp{df_k[df_k['id']==x]['jumlah'].values[0]} - {df_k[df_k['id']==x]['keterangan'].values[0]}")
                    if st.button("🚨 Hapus Kas"):
                        supabase.table("kas_rt").delete().eq("id", pilih_k).execute()
                        st.success("Terhapus!"); st.rerun()

    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.rerun()

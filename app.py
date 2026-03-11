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
        tab1, tab2, tab3 = st.tabs(["➕ Tambah Warga", "👥 Kelola Warga", "📑 Koreksi Iuran/Kas"])
        
        # TAB 1: TAMBAH WARGA
        with tab1:
            st.header("📝 Tambah Warga Baru")
            # Kita pecah form agar input jumlah keluarga bisa memicu perubahan kolom di bawahnya
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
                st.write(f"**Anggota {i+1}**")
                col_a, col_b = st.columns(2)
                nama_a = col_a.text_input(f"Nama Anggota {i+1}", key=f"n_{i}")
                status_a = col_b.selectbox(f"Status Anggota {i+1}", ["Istri", "Anak", "Orang Tua", "Saudara", "Lainnya"], key=f"s_{i}")
                if nama_a:
                    anggota_list.append({"nama": nama_a, "status": status_a})
            
            if st.button("💾 Simpan Warga Baru"):
                if n_kk and n_nik:
                    data_simpan = {
                        "nama_kk": n_kk, 
                        "nik": n_nik, 
                        "alamat": n_alm, 
                        "status_rumah": n_sts, 
                        "kontak": n_kon,
                        "anggota_keluarga": anggota_list # Disimpan sebagai JSON/List
                    }
                    supabase.table("warga").insert(data_simpan).execute()
                    st.success(f"Warga {n_kk} Berhasil Tersimpan!")
                    st.rerun()
                else:
                    st.error("Nama KK dan NIK wajib diisi, Ndan!")

        # TAB 2: KELOLA WARGA (EDIT/HAPUS)
        with tab2:
            st.header("⚙️ Edit atau Hapus Data Warga")
            res_w_all = supabase.table("warga").select("*").order("nama_kk").execute()
            df_w_all = pd.DataFrame(res_w_all.data)
            
            if not df_w_all.empty:
                warga_pilih = st.selectbox("Pilih Warga yang akan di Kelola:", df_w_all['nama_kk'].tolist())
                data_edit = df_w_all[df_w_all['nama_kk'] == warga_pilih].iloc[0]
                
                st.divider()
                e_nama = st.text_input("Edit Nama KK", value=data_edit['nama_kk'])
                e_nik = st.text_input("Edit NIK", value=data_edit['nik'])
                e_alm = st.text_input("Edit Alamat", value=data_edit['alamat'])
                e_sts = st.selectbox("Edit Status", ["Pribadi", "Kontrak"], index=0 if data_edit['status_rumah'] == "Pribadi" else 1)
                e_kon = st.text_input("Edit Kontak", value=data_edit['kontak'])
                
                # Logic Edit Anggota Keluarga
                st.subheader("👨‍👩‍👧‍👦 Edit Anggota Keluarga")
                # Ambil data lama jika ada, kalau tidak ada buat list kosong
                old_anggota = data_edit.get('anggota_keluarga', [])
                if not isinstance(old_anggota, list): old_anggota = []
                
                e_jml = st.number_input("Jumlah Anggota Keluarga Baru", min_value=0, step=1, value=len(old_anggota))
                
                e_anggota_list = []
                for j in range(int(e_jml)):
                    st.write(f"**Anggota {j+1}**")
                    # Coba ambil value lama untuk default di kolom input
                    def_nama = old_anggota[j]['nama'] if j < len(old_anggota) else ""
                    def_stat = old_anggota[j]['status'] if j < len(old_anggota) else "Istri"
                    
                    ce_a, ce_b = st.columns(2)
                    enama_a = ce_a.text_input(f"Nama Anggota {j+1}", value=def_nama, key=f"en_{j}")
                    estat_a = ce_b.selectbox(f"Status Anggota {j+1}", ["Istri", "Anak", "Orang Tua", "Saudara", "Lainnya"], 
                                             index=["Istri", "Anak", "Orang Tua", "Saudara", "Lainnya"].index(def_stat) if def_stat in ["Istri", "Anak", "Orang Tua", "Saudara", "Lainnya"] else 0,
                                             key=f"es_{j}")
                    if enama_a:
                        e_anggota_list.append({"nama": enama_a, "status": estat_a})

                col_bt1, col_bt2 = st.columns(2)
                if col_bt1.button("💾 Update Semua Data"):
                    supabase.table("warga").update({
                        "nama_kk": e_nama, "nik": e_nik, "alamat": e_alm, 
                        "status_rumah": e_sts, "kontak": e_kon,
                        "anggota_keluarga": e_anggota_list
                    }).eq("id", data_edit['id']).execute()
                    st.success("Data Berhasil di Update!")
                    st.rerun()
                
                if col_bt2.button("🗑️ HAPUS WARGA (Permanen)"):
                    supabase.table("warga").delete().eq("id", data_edit['id']).execute()
                    st.success("Data Berhasil Dihapus!")
                    st.rerun()
            else:
                st.info("Belum ada data warga.")

        # TAB 3: KOREKSI IURAN/KAS (Tetap sama)
        with tab3:
            st.header("🛠️ Koreksi Data Transaksi")
            # ... (Logika tab 3 tetap sama seperti sebelumnya)


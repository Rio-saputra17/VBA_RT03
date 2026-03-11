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
    
    if role == "Admin":
        menu = st.sidebar.radio("Navigasi", ["WARGA", "IURAN BULANAN", "KAS RT", "INPUT PEMBAYARAN", "TAMBAH/EDIT DATA"])
    else:
        menu = st.sidebar.radio("Navigasi", ["WARGA", "IURAN BULANAN", "KAS RT"])

    # --- MENU 1: WARGA ---
    if menu == "WARGA":
        st.header("📋 Data Warga RT 03")
        search = st.text_input("🔍 Cari Nama Warga...").lower()
        res_w = supabase.table("warga").select("*").order("nama_kk").execute()
        df_w = pd.DataFrame(res_w.data)

        if not df_w.empty:
            if search:
                df_w = df_w[df_w['nama_kk'].str.lower().str.contains(search)]
            
            for i, row in df_w.iterrows():
                with st.expander(f"👤 {row['nama_kk']} - {row['alamat']}"):
                    st.write(f"**Status:** {row['status_rumah']} | **Kontak:** {row['kontak']}")
                    if role == "Admin": st.write(f"**NIK:** {row['nik']}")
                    res_agg = supabase.table("anggota_keluarga").select("*").eq("id_kk", row["id"]).execute()
                    if res_agg.data:
                        st.write(f"**Anggota Keluarga ({len(res_agg.data)}):**")
                        for agg in res_agg.data:
                            st.write(f"- {agg['nama_anggota']} ({agg['hubungan']})")

    # --- MENU 2: IURAN BULANAN (FITUR CARI HISTORY) ---
    elif menu == "IURAN BULANAN":
        st.header("💰 History Iuran Bulanan")
        search_iuran = st.text_input("🔍 Cari Nama Warga untuk lihat history...").lower()
        res_i = supabase.table("iuran").select("*").order("created_at", desc=True).execute()
        df_i = pd.DataFrame(res_i.data)
        
        if not df_i.empty:
            if search_iuran:
                df_i = df_i[df_i['nama_warga'].str.lower().str.contains(search_iuran)]
            st.dataframe(df_i, use_container_width=True)
        else:
            st.info("Belum ada data iuran.")

    # --- MENU 3: KAS RT (EDIT SALDO & OPERASIONAL) ---
    elif menu == "KAS RT":
        st.header("📊 Laporan Kas RT")
        
        # Fitur Edit Kas Manual untuk Admin
        if role == "Admin":
            with st.expander("🛠️ Menu Admin: Input Operasional / Sumbangan Luar"):
                with st.form("form_kas_manual"):
                    k_jenis = st.selectbox("Jenis Dana", ["Masuk", "Keluar"])
                    k_nom = st.number_input("Nominal (Rp)", min_value=0, step=1000)
                    k_ket = st.text_area("Keterangan (Contoh: Sumbangan Donatur A / Belanja Alat Kebersihan)")
                    if st.form_submit_button("Update Saldo Kas"):
                        supabase.table("kas_rt").insert({"jenis": k_jenis, "jumlah": k_nom, "keterangan": k_ket}).execute()
                        st.success("Saldo Berhasil Diupdate secara Otomatis!")
                        st.rerun()

        res_k = supabase.table("kas_rt").select("*").order("created_at", desc=True).execute()
        df_k = pd.DataFrame(res_k.data)
        
        if not df_k.empty:
            masuk = df_k[df_k['jenis'] == 'Masuk']['jumlah'].sum()
            keluar = df_k[df_k['jenis'] == 'Keluar']['jumlah'].sum()
            saldo = masuk - keluar
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Masuk", f"Rp {masuk:,}")
            c2.metric("Total Keluar", f"Rp {keluar:,}")
            c3.metric("Sisa Saldo", f"Rp {saldo:,}")
            
            st.subheader("Rincian Transaksi")
            st.table(df_k[['created_at', 'jenis', 'jumlah', 'keterangan']])
        else:
            st.info("Belum ada mutasi kas.")

    # --- MENU 4: INPUT PEMBAYARAN (SINKRON OTOMATIS) ---
    elif menu == "INPUT PEMBAYARAN":
        st.header("💸 Input Pembayaran Warga")
        w_res = supabase.table("warga").select("nama_kk").execute()
        pilih_w = st.selectbox("Pilih Nama Kepala Keluarga", [w['nama_kk'] for w in w_res.data])
        
        col1, col2 = st.columns(2)
        bln = col1.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
        thn = col2.selectbox("Tahun", [2025, 2026])
        
        # Tambahan Opsi Keterangan
        opsi_iuran = st.radio("Kategori Pembayaran", ["Iuran Wajib", "Lain-Lain (Sumbangan/Denda/Dll)"], horizontal=True)
        nom = st.number_input("Nominal Pembayaran", value=50000)
        
        if st.button("Simpan & Sinkronkan ke Kas"):
            # Sinkron ke tabel Iuran
            supabase.table("iuran").insert({"nama_warga": pilih_w, "periode": f"{bln} {thn}", "status": "Lunas", "keterangan": opsi_iuran}).execute()
            # Sinkron ke tabel Kas secara otomatis
            supabase.table("kas_rt").insert({"jenis": "Masuk", "jumlah": nom, "keterangan": f"{opsi_iuran} - {pilih_w} ({bln} {thn})"}).execute()
            st.success(f"Data {pilih_w} berhasil masuk ke laporan Iuran & Kas RT!")
            st.rerun()

    # --- MENU 5: TAMBAH/EDIT DATA (ADMIN) ---
    elif menu == "TAMBAH/EDIT DATA":
        st.header("📝 Kelola Data Warga")
        aksi = st.radio("Aksi:", ["Tambah Baru", "Edit / Hapus Data"], horizontal=True)

        if aksi == "Tambah Baru":
            with st.form("form_tambah"):
                n_kk = st.text_input("Nama Kepala Keluarga")
                n_nik = st.text_input("NIK")
                n_alm = st.text_input("Alamat")
                n_sts = st.selectbox("Status Rumah", ["Pribadi", "Kontrak"])
                n_kon = st.text_input("Kontak (WA)")
                n_jml = st.number_input("Jumlah Anggota Keluarga", min_value=0, step=1)
                
                anggota_data = []
                if n_jml > 0:
                    st.write("---")
                    st.subheader("Data Anggota Keluarga")
                    for i in range(int(n_jml)):
                        c1, c2 = st.columns(2)
                        nama_a = c1.text_input(f"Nama Anggota {i+1}", key=f"new_nama_{i}")
                        hub_a = c2.selectbox(f"Hubungan {i+1}", ["Istri", "Anak", "Orang Tua", "Saudara", "Lain-lain"], key=f"new_hub_{i}")
                        anggota_data.append({"nama_anggota": nama_a, "hubungan": hub_a})
                
                if st.form_submit_button("Simpan Semua Data"):
                    res_w = supabase.table("warga").insert({"nama_kk": n_kk, "nik": n_nik, "alamat": n_alm, "status_rumah": n_sts, "kontak": n_kon, "jml_anggota": n_jml}).execute()
                    if res_w.data and n_jml > 0:
                        new_id = res_w.data[0]['id']
                        for a in anggota_data:
                            a['id_kk'] = new_id
                            supabase.table("anggota_keluarga").insert(a).execute()
                    st.success("Data Berhasil Disimpan!")
                    st.rerun()

        elif aksi == "Edit / Hapus Data":
            w_res = supabase.table("warga").select("id, nama_kk").execute()
            w_opt = {w['nama_kk']: w['id'] for w in w_res.data}
            pilih = st.selectbox("Pilih Warga", ["-- Pilih --"] + list(w_opt.keys()))
            
            if pilih != "-- Pilih --":
                id_target = w_opt[pilih]
                d = supabase.table("warga").select("*").eq("id", id_target).single().execute().data
                res_old_agg = supabase.table("anggota_keluarga").select("*").eq("id_kk", id_target).execute()
                
                with st.form("form_edit"):
                    e_nama = st.text_input("Nama KK", value=d['nama_kk'])
                    e_nik = st.text_input("NIK", value=d['nik'])
                    e_alm = st.text_input("Alamat", value=d['alamat'])
                    e_kon = st.text_input("Kontak", value=d['kontak'])
                    e_jml = st.number_input("Total Anggota Keluarga", value=int(d['jml_anggota']), min_value=0)
                    
                    update_agg = []
                    for i in range(int(e_jml)):
                        old_n = res_old_agg.data[i]['nama_anggota'] if i < len(res_old_agg.data) else ""
                        old_h = res_old_agg.data[i]['hubungan'] if i < len(res_old_agg.data) else "Anak"
                        c1, c2 = st.columns(2)
                        na = c1.text_input(f"Nama Anggota {i+1}", value=old_n, key=f"edit_n_{i}")
                        ha = c2.selectbox(f"Hubungan {i+1}", ["Istri", "Anak", "Orang Tua", "Saudara", "Lain-lain"], index=["Istri", "Anak", "Orang Tua", "Saudara", "Lain-lain"].index(old_h), key=f"edit_h_{i}")
                        update_agg.append({"nama_anggota": na, "hubungan": ha, "id_kk": id_target})

                    if st.form_submit_button("Simpan Perubahan"):
                        supabase.table("warga").update({"nama_kk": e_nama, "nik": e_nik, "alamat": e_alm, "kontak": e_kon, "jml_anggota": e_jml}).eq("id", id_target).execute()
                        supabase.table("anggota_keluarga").delete().eq("id_kk", id_target).execute()
                        if update_agg: supabase.table("anggota_keluarga").insert(update_agg).execute()
                        st.success("Data Berhasil Diperbarui!")
                        st.rerun()
                
                if st.button("🚨 HAPUS WARGA INI"):
                    supabase.table("anggota_keluarga").delete().eq("id_kk", id_target).execute()
                    supabase.table("warga").delete().eq("id", id_target).execute()
                    st.warning(f"Data {pilih} Telah Dihapus!")
                    st.rerun()

    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.rerun()

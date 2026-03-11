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
    
    # Navigasi Menu
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
            
            st.download_button("📥 Download CSV Warga", df_w.to_csv(index=False), "data_warga.csv", "text/csv")

    # --- MENU 2: IURAN BULANAN ---
    elif menu == "IURAN BULANAN":
        st.header("💰 History Iuran Bulanan")
        res_i = supabase.table("iuran").select("*").order("created_at", desc=True).execute()
        df_i = pd.DataFrame(res_i.data)
        
        if not df_i.empty:
            st.dataframe(df_i, use_container_width=True)

    # --- MENU 3: KAS RT ---
    elif menu == "KAS RT":
        st.header("📊 Laporan Kas RT")
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
            st.table(df_k)

    # --- MENU 4: INPUT PEMBAYARAN (ADMIN) ---
    elif menu == "INPUT PEMBAYARAN":
        st.header("💸 Input Pembayaran")
        w_list = supabase.table("warga").select("nama_kk").execute()
        pilih_w = st.selectbox("Pilih Warga", [w['nama_kk'] for w in w_list.data])
        bln = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
        thn = st.selectbox("Tahun", [2025, 2026])
        nom = st.number_input("Nominal", value=50000)
        
        if st.button("Proses Bayar & Sinkron Kas"):
            supabase.table("iuran").insert({"nama_warga": pilih_w, "periode": f"{bln} {thn}", "status": "Lunas"}).execute()
            supabase.table("kas_rt").insert({"jenis": "Masuk", "jumlah": nom, "keterangan": f"Iuran {pilih_w} ({bln} {thn})"}).execute()
            st.success("Pembayaran Berhasil!")

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
                
                if st.form_submit_button("Simpan"):
                    res = supabase.table("warga").insert({"nama_kk": n_kk, "nik": n_nik, "alamat": n_alm, "status_rumah": n_sts, "kontak": n_kon, "jml_anggota": n_jml}).execute()
                    st.success("Data Tersimpan!")
                    st.rerun()

        elif aksi == "Edit / Hapus Data":
            w_res = supabase.table("warga").select("id, nama_kk").execute()
            w_opt = {w['nama_kk']: w['id'] for w in w_res.data}
            pilih = st.selectbox("Pilih Warga", list(w_opt.keys()))
            
            if pilih:
                id_target = w_opt[pilih]
                d = supabase.table("warga").select("*").eq("id", id_target).single().execute().data
                
                with st.form("form_edit"):
                    st.subheader(f"Update Data: {pilih}")
                    e_nama = st.text_input("Nama KK", value=d['nama_kk'])
                    e_nik = st.text_input("NIK", value=d['nik'])
                    e_alm = st.text_input("Alamat", value=d['alamat'])
                    e_kon = st.text_input("Kontak", value=d['kontak'])
                    
                    if st.form_submit_button("Update Data"):
                        supabase.table("warga").update({"nama_kk": e_nama, "nik": e_nik, "alamat": e_alm, "kontak": e_kon}).eq("id", id_target).execute()
                        st.success("Update Berhasil!")
                        st.rerun()
                
                st.divider()
                st.subheader("⚠️ Zona Bahaya")
                if st.button("🚨 HAPUS WARGA INI"):
                    # Hapus anggota keluarga dulu (Cascade manual)
                    supabase.table("anggota_keluarga").delete().eq("id_kk", id_target).execute()
                    # Hapus warga utama
                    supabase.table("warga").delete().eq("id", id_target).execute()
                    st.warning(f"Data {pilih} Telah Dihapus Selamanya!")
                    st.rerun()

    if st.sidebar.button("Logout"):
        st.session_state.role = None
        st.rerun()

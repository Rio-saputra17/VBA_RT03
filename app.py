    # --- MENU 5: TAMBAH/EDIT DATA ---
    elif menu == "TAMBAH/EDIT DATA":
        tab1, tab2, tab3 = st.tabs(["➕ Tambah Warga", "👥 Kelola Warga", "📑 Koreksi Iuran/Kas"])
        
        # TAB 1: TAMBAH WARGA
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

        # TAB 2: KELOLA WARGA (EDIT/HAPUS)
        with tab2:
            st.header("⚙️ Edit atau Hapus Data Warga")
            res_w_all = supabase.table("warga").select("*").order("nama_kk").execute()
            df_w_all = pd.DataFrame(res_w_all.data)
            
            if not df_w_all.empty:
                warga_pilih = st.selectbox("Pilih Warga yang akan di Kelola:", df_w_all['nama_kk'].tolist())
                data_edit = df_w_all[df_w_all['nama_kk'] == warga_pilih].iloc[0]
                
                with st.form("edit_warga"):
                    e_nama = st.text_input("Nama KK", value=data_edit['nama_kk'])
                    e_nik = st.text_input("NIK", value=data_edit['nik'])
                    e_alm = st.text_input("Alamat", value=data_edit['alamat'])
                    e_sts = st.selectbox("Status", ["Pribadi", "Kontrak"], index=0 if data_edit['status_rumah'] == "Pribadi" else 1)
                    e_kon = st.text_input("Kontak", value=data_edit['kontak'])
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.form_submit_button("💾 Update Data"):
                            supabase.table("warga").update({
                                "nama_kk": e_nama, "nik": e_nik, "alamat": e_alm, 
                                "status_rumah": e_sts, "kontak": e_kon
                            }).eq("id", data_edit['id']).execute()
                            st.success("Data Berhasil di Update!")
                            st.rerun()
                    with c2:
                        # Tombol hapus ditaruh di luar form utama supaya tidak sengaja terpencet saat edit
                        pass 
                
                if st.button("🗑️ HAPUS WARGA (Permanen)"):
                    if st.warning(f"Apakah yakin ingin menghapus data {warga_pilih}?"):
                        supabase.table("warga").delete().eq("id", data_edit['id']).execute()
                        st.success("Data Berhasil Dihapus!")
                        st.rerun()
            else:
                st.info("Belum ada data warga.")

        # TAB 3: KOREKSI IURAN/KAS
        with tab3:
            st.header("🛠️ Koreksi Data Transaksi")
            st.warning("Gunakan fitur ini hanya jika ada kesalahan input data pembayaran.")
            res_edit = supabase.table("iuran").select("*").order("created_at", desc=True).limit(15).execute()
            if res_edit.data:
                df_edit = pd.DataFrame(res_edit.data)
                pilih_id = st.selectbox("Pilih Transaksi yang akan DIHAPUS (15 Terakhir):", 
                                        options=df_edit['id'].tolist(), 
                                        format_func=lambda x: f"ID: {x} - {df_edit[df_edit['id']==x]['nama_warga'].values[0]} ({df_edit[df_edit['id']==x]['periode'].values[0]})")
                
                if st.button("🚨 HAPUS TRANSAKSI IURAN"):
                    supabase.table("iuran").delete().eq("id", pilih_id).execute()
                    st.success(f"Transaksi ID {pilih_id} Berhasil Dihapus!")
                    st.rerun()

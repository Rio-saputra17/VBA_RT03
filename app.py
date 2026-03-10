import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# Konfigurasi Tampilan Mobile
st.set_page_config(page_title="Update RT 03", layout="wide")

def login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if not st.session_state.logged_in:
        st.subheader("🔐 Login Sistem RT 03")
        pw = st.text_input("Password Admin", type="password")
        if st.button("Masuk"):
            if pw == "123": # Silakan ganti password di sini
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Password Salah!")
        return False
    return True

if login():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # Baca data sesuai nama sheet: Warga, Data Pembayaran, Kas RT
        df_warga = conn.read(worksheet="Warga", ttl="0")
        df_bayar = conn.read(worksheet="Data Pembayaran", ttl="0")
        df_kas = conn.read(worksheet="Kas RT", ttl="0")

        st.sidebar.title("Sistem RT 03")
        menu = st.sidebar.radio("Navigasi Menu", 
            ["Update Warga", "Input Iuran", "History Pembayaran", "Kas RT (Keuangan)"])

        # --- 1. MENU UPDATE WARGA ---
        if menu == "Update Warga":
            st.header("👥 Manajemen Data Warga")
            tab1, tab2 = st.tabs(["Tambah Warga Baru", "Edit/Hapus Warga"])
            
            with tab1:
                with st.form("form_tambah"):
                    n_nama = st.text_input("Nama Warga")
                    n_alamat = st.text_input("Alamat Rumah")
                    n_status = st.selectbox("Status Rumah", ["Pribadi", "Kontrak"])
                    n_kontak = st.text_input("Kontak (No Telepon)")
                    if st.form_submit_button("Simpan Warga"):
                        new_data = pd.DataFrame([{"Nama": n_nama, "Alamat": n_alamat, "Status": n_status, "Kontak": n_kontak}])
                        df_updated = pd.concat([df_warga, new_data], ignore_index=True)
                        conn.update(worksheet="Warga", data=df_updated)
                        st.success("Warga Berhasil Ditambahkan!")
                        st.rerun()

            with tab2:
                st.write("Edit data langsung di tabel bawah:")
                edited_w = st.data_editor(df_warga, use_container_width=True, num_rows="dynamic")
                if st.button("Simpan Perubahan Data"):
                    conn.update(worksheet="Warga", data=edited_w)
                    st.success("Data Warga Diperbarui!")

        # --- 2. MENU INPUT IURAN ---
        elif menu == "Input Iuran":
            st.header("💰 Input Pembayaran Iuran")
            if df_warga.empty:
                st.warning("Data warga masih kosong.")
            else:
                with st.form("form_bayar", clear_on_submit=True):
                    sel_nama = st.selectbox("Pilih Nama Warga", df_warga['Nama'].unique())
                    sel_bln = st.selectbox("Bulan/Tahun", [f"{b} 2026" for b in ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"]])
                    sel_nominal = st.number_input("Jumlah Uang (Rp)", value=20000, step=5000)
                    
                    if st.form_submit_button("Proses Pembayaran"):
                        # Update Data Pembayaran
                        new_iuran = pd.DataFrame([{"Nama": sel_nama, "Bulan/Tahun": sel_bln, "Status": "Lunas"}])
                        df_bayar_up = pd.concat([df_bayar, new_iuran], ignore_index=True)
                        conn.update(worksheet="Data Pembayaran", data=df_bayar_up)
                        
                        # Sinkronisasi Kas RT
                        last_saldo = pd.to_numeric(df_kas['Sisa Saldo'], errors='coerce').fillna(0).iloc[-1] if not df_kas.empty else 0
                        new_kas = pd.DataFrame([{
                            "Masuk": sel_nominal, 
                            "Keluar": 0, 
                            "Keterangan": f"Iuran {sel_bln} - {sel_nama}", 
                            "Sisa Saldo": last_saldo + sel_nominal
                        }])
                        df_kas_up = pd.concat([df_kas, new_kas], ignore_index=True)
                        conn.update(worksheet="Kas RT", data=df_kas_up)
                        st.success(f"Berhasil! {sel_nama} Lunas {sel_bln}.")

        # --- 3. MENU HISTORY PEMBAYARAN ---
        elif menu == "History Pembayaran":
            st.header("📊 History Pembayaran Iuran")
            st.dataframe(df_bayar, use_container_width=True)

        # --- 4. MENU KAS RT ---
        elif menu == "Kas RT (Keuangan)":
            st.header("📈 Laporan Kas & Sisa Saldo")
            
            t_masuk = pd.to_numeric(df_kas['Masuk'], errors='coerce').sum()
            t_keluar = pd.to_numeric(df_kas['Keluar'], errors='coerce').sum()
            total_saldo = t_masuk - t_keluar
            
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Pemasukan", f"Rp {t_masuk:,.0f}")
            c2.metric("Total Pengeluaran", f"Rp {t_keluar:,.0f}")
            c3.metric("Sisa Saldo", f"Rp {total_saldo:,.0f}")
            
            st.divider()
            with st.expander("Klik untuk tambah catatan manual (Keluar/Masuk)"):
                with st.form("form_kas_manual"):
                    k_tipe = st.radio("Jenis Transaksi", ["Uang Masuk", "Uang Keluar"])
                    k_jml = st.number_input("Jumlah (Rp)", min_value=0)
                    k_ket = st.text_input("Keterangan")
                    if st.form_submit_button("Simpan Transaksi Kas"):
                        v_m = k_jml if k_tipe == "Uang Masuk" else 0
                        v_k = k_jml if k_tipe == "Uang Keluar" else 0
                        new_ent = pd.DataFrame([{"Masuk": v_m, "Keluar": v_k, "Keterangan": k_ket, "Sisa Saldo": total_saldo + v_m - v_k}])
                        df_kas_final = pd.concat([df_kas, new_ent], ignore_index=True)
                        conn.update(worksheet="Kas RT", data=df_kas_final)
                        st.success("Kas Diupdate!")
                        st.rerun()
            
            st.dataframe(df_kas, use_container_width=True)

    except Exception as e:
        st.error("⚠️ Masalah Koneksi/Struktur Sheets")
        st.code(str(e))

    if st.sidebar.button("Keluar"):
        st.session_state.logged_in = False
        st.rerun()

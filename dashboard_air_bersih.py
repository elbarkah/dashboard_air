import streamlit as st
import pandas as pd
import plotly.express as px
import pydeck as pdk
import io
from streamlit_folium import st_folium
import folium

st.set_page_config(page_title="Dashboard Air Bersih Desa", layout="wide")

@st.cache_data
def load_data():
    df = pd.read_excel("DATA AIR BERSIH.xlsx", usecols="A:Q")
    df.columns = df.columns.str.strip()

    # Buat kolom KONDISI SARANA berdasarkan ceklist '√'
    kondisi_cols = ["BAIK", "RUSAK RINGAN", "RUSAK SEDANG", "RUSAK BERAT"]
    def get_kondisi(row):
        for col in kondisi_cols:
            if str(row.get(col)).strip() == "√":
                return col
        return "Tidak Diketahui"
    df["KONDISI SARANA"] = df.apply(get_kondisi, axis=1)

    return df

df_raw = load_data()

st.title("🚰 Dashboard Air Bersih Desa")

if "show_data" not in st.session_state:
    st.session_state["show_data"] = False

with st.form("filter_form"):
    col1, col2, col3 = st.columns(3)

    kabupaten_options = ["Semua"] + sorted(df_raw["KABUPATEN"].dropna().unique())
    kabupaten = col1.selectbox("📍 Kabupaten", kabupaten_options)

    if kabupaten != "Semua":
        kecamatan_options = ["Semua"] + sorted(df_raw[df_raw["KABUPATEN"] == kabupaten]["KECAMATAN"].dropna().unique())
    else:
        kecamatan_options = ["Semua"] + sorted(df_raw["KECAMATAN"].dropna().unique())
    kecamatan = col2.selectbox("🏙️ Kecamatan", kecamatan_options)

    if kecamatan != "Semua":
        desa_options = ["Semua"] + sorted(df_raw[df_raw["KECAMATAN"] == kecamatan]["DESA"].dropna().unique())
    else:
        desa_options = ["Semua"] + sorted(df_raw["DESA"].dropna().unique())
    desa = col3.selectbox("🏘️ Desa", desa_options)

    col4, col5, col6 = st.columns(3)
    sumber = col4.selectbox("💧 Sumber Air", ["Semua"] + sorted(df_raw["SUMBER AIR BERSIH"].dropna().unique()))
    kepemilikan = col5.selectbox("🏠 Status Kepemilikan", ["Semua"] + sorted(df_raw["STATUS KEPEMILIKAN SARANA PRASARANA AIR BERSIH"].dropna().unique()))
    kondisi = col6.selectbox("⚙️ Kondisi Sarana", ["Semua", "BAIK", "RUSAK RINGAN", "RUSAK SEDANG", "RUSAK BERAT"])
    
    submit = st.form_submit_button("Tampilkan Data")

if submit:
    st.session_state["show_data"] = True


if st.session_state["show_data"]:
    df = df_raw.copy()

    if kabupaten != "Semua":
        df = df[df["KABUPATEN"] == kabupaten]
    if kecamatan != "Semua":
        df = df[df["KECAMATAN"] == kecamatan]
    if desa != "Semua":
        df = df[df["DESA"] == desa]
    if sumber != "Semua":
        df = df[df["SUMBER AIR BERSIH"] == sumber]
    if kepemilikan != "Semua":
        df = df[df["STATUS KEPEMILIKAN SARANA PRASARANA AIR BERSIH"] == kepemilikan]
    if kondisi != "Semua":
        df = df[df["KONDISI SARANA"] == kondisi]

    tab1, tab2, tab3, tab4 = st.tabs(["📋 Ringkasan", "📊 Grafik", "🗺️ Peta", "📄 Data Mentah"])

    with tab1:
        # Hitung nilai ringkasan
        df["JUMLAH KK YANG TERLAYANI"] = pd.to_numeric(df["JUMLAH KK YANG TERLAYANI"], errors="coerce")
        total_kk = int(df["JUMLAH KK YANG TERLAYANI"].sum())
        df["JUMLAH DEBIT AIR PERTAHUN (m³)"] = pd.to_numeric(df["JUMLAH DEBIT AIR PERTAHUN (m³)"], errors='coerce')
        total_debit = float(df["JUMLAH DEBIT AIR PERTAHUN (m³)"].sum())
        total_debit = float(df["JUMLAH DEBIT AIR PERTAHUN (m³)"].sum())
        jumlah_sarana = df["SUMBER AIR BERSIH"].dropna().astype(str).str.strip().str.lower()
        jumlah_sarana = jumlah_sarana[jumlah_sarana != "tidak ada"].count()

        # Satu panggilan markdown: box besar + CSS + grid layout
        st.markdown(f"""
        <style>
        .ringkasan-box {{
            background-color: #f0f4f8;
            padding: 30px 20px;
            border-radius: 12px;
            box-shadow: 2px 4px 8px rgba(0,0,0,0.05);
            margin-bottom: 30px;
        }}

        .ringkasan-box h3 {{
            text-align: center;
            color: #333;
            margin-bottom: 30px;
        }}

        .ringkasan-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }}

        .card {{
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            font-size: 18px;
            box-shadow: 0px 2px 6px rgba(0,0,0,0.08);
        }}

        .bg1 {{ background-color: #ede7f6; }}
        .bg2 {{ background-color: #ede7f6; }}
        .bg3 {{ background-color: #ede7f6; }}

        .card-value {{
            font-size: 30px;
            font-weight: bold;
            color: #333;
        }}

        .card-header {{
            font-weight: 600;
            margin-bottom: 8px;
            color: #444;
        }}
        </style>

        <div class="ringkasan-box">
            <h3>Pelayanan Air Bersih</h3>
            <div class="ringkasan-grid">
                <div class="card bg1">
                    <div class="card-header">Jumlah Sarana Air Bersih</div>
                    <div class="card-value">{jumlah_sarana:,}</div>
                </div>
                <div class="card bg2">
                    <div class="card-header">Total Debit Air per tahun</div>
                    <div class="card-value">{total_debit:,.2f}</div>
                </div>
                <div class="card bg3">
                    <div class="card-header">Jumlah KK Terlayani</div>
                    <div class="card-value">{total_kk:,}</div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


        st.subheader("📋 Ringkasan Kondisi Sarana")
        kondisi_labels = ["BAIK", "RUSAK RINGAN", "RUSAK SEDANG", "RUSAK BERAT", "Tidak Diketahui"]
        kondisi_counts = df["KONDISI SARANA"].value_counts()

        col_k = st.columns(len(kondisi_labels))
        for i, label in enumerate(kondisi_labels):
            value = kondisi_counts.get(label, 0)
            html_box = f"""
            <div style='
                padding:12px;
                border-radius:12px;
                background:#e0f7fa;
                text-align:center;
                font-size:18px;
                box-shadow: 1px 2px 6px rgba(0,0,0,0.1);'>
                <div><strong>{label}</strong></div>
                <div style='font-size:24px; font-weight:bold'>{value}</div>
            </div>"""
            col_k[i].markdown(html_box, unsafe_allow_html=True)
        st.markdown("<div style='margin-top: 0px;'></div>", unsafe_allow_html=True)

        kondisi_table = df.groupby(["KABUPATEN", "KECAMATAN", "DESA"])["KONDISI SARANA"].value_counts().unstack(fill_value=0)
        st.dataframe(kondisi_table)

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            kondisi_table.drop(index="Total", errors="ignore").to_excel(writer, sheet_name="Ringkasan Kondisi", index=True)
        excel_buffer.seek(0)

        st.download_button(
            label="📥 Unduh Ringkasan Kondisi Sarana",
            data=excel_buffer,
            file_name="ringkasan_kondisi_sarana.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.subheader("📋 Ringkasan Sumber Air Bersih")
        sumber_labels = ["Mata Air", "Sumur Dalam", "Sumur Dangkal", "Air Hujan", "Air Permukaan", "Lainnya", "tidak ada"]
        sumber_counts = df["SUMBER AIR BERSIH"].value_counts()
        col_s = st.columns(len(sumber_labels))
        for i, label in enumerate(sumber_labels):
            value = sumber_counts.get(label, 0)
            html_box = f"""
            <div style='
                padding:12px;
                border-radius:12px;
                background:#e8f5e9;
                text-align:center;
                font-size:18px;
                box-shadow: 1px 2px 6px rgba(0,0,0,0.1);'>
                <div><strong>{label}</strong></div>
                <div style='font-size:24px; font-weight:bold'>{value}</div>
            </div>"""
            col_s[i].markdown(html_box, unsafe_allow_html=True)
        st.markdown("<div style='margin-top: 0px;'></div>", unsafe_allow_html=True)

        sumber_table = df.groupby(["KABUPATEN", "KECAMATAN", "DESA"])["SUMBER AIR BERSIH"].value_counts().unstack(fill_value=0)
        st.dataframe(sumber_table)

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            sumber_table.drop(index="Total", errors="ignore").to_excel(writer, sheet_name="Ringkasan Sumber", index=True)
        excel_buffer.seek(0)

        st.download_button(
            label="📥 Unduh Ringkasan Sumber Air Bersih",
            data=excel_buffer,
            file_name="ringkasan_sumber_air.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.subheader("📋 Ringkasan Status Kepemilikan")
        status_labels = ["Milik Desa", "Milik Swasta", "Milik Pribadi", "Hibah", "Lainnya", "Belum Terdata"]
        status_counts = df["STATUS KEPEMILIKAN SARANA PRASARANA AIR BERSIH"].value_counts()
        col_s = st.columns(len(status_labels))
        for i, label in enumerate(status_labels):
            value = status_counts.get(label, 0)
            html_box = f"""
            <div style='
                padding:12px;
                border-radius:12px;
                background:#faf2d4;
                text-align:center;
                font-size:18px;
                box-shadow: 1px 2px 6px rgba(0,0,0,0.1);'>
                <div><strong>{label}</strong></div>
                <div style='font-size:24px; font-weight:bold'>{value}</div>
            </div>"""
            col_s[i].markdown(html_box, unsafe_allow_html=True)
        st.markdown("<div style='margin-top: 0px;'></div>", unsafe_allow_html=True)

        status_table = df.groupby(["KABUPATEN", "KECAMATAN", "DESA"])["STATUS KEPEMILIKAN SARANA PRASARANA AIR BERSIH"].value_counts().unstack(fill_value=0)
        st.dataframe(status_table)

        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="xlsxwriter") as writer:
            status_table.drop(index="Total", errors="ignore").to_excel(writer, sheet_name="Ringkasan Status", index=True)
        excel_buffer.seek(0)

        st.download_button(
            label="📥 Unduh Ringkasan Status Kepemilikan",
            data=excel_buffer,
            file_name="ringkasan_status_kepemilikan.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    with tab2:
        st.subheader("📊 Grafik Interaktif")

        # ======================
        # Grafik 1: Kondisi Sarana
        # ======================

        kondisi_order = ["BAIK", "RUSAK RINGAN", "RUSAK SEDANG", "RUSAK BERAT", "Tidak Diketahui"]
        df_kondisi = df.copy()
        df_kondisi["KONDISI SARANA"] = df_kondisi["KONDISI SARANA"].astype(str).str.upper().str.strip()
        df_kondisi["KONDISI SARANA"] = df_kondisi["KONDISI SARANA"].where(df_kondisi["KONDISI SARANA"].isin(kondisi_order[:-1]), "Tidak Diketahui")

        kondisi_counts = df_kondisi["KONDISI SARANA"].value_counts().reindex(kondisi_order, fill_value=0)
        kondisi_percent = (kondisi_counts / kondisi_counts.sum() * 100).round(2)

        kondisi_df = kondisi_counts.reset_index()
        kondisi_df.columns = ["KONDISI SARANA", "JUMLAH"]
        kondisi_df["PERSEN"] = kondisi_percent.values

        fig1 = px.bar(
            kondisi_df,
            x="KONDISI SARANA",
            y="JUMLAH",
            color="KONDISI SARANA",
            text="JUMLAH",
            category_orders={"KONDISI SARANA": kondisi_order},
            title="Distribusi Kondisi Sarana",
            hover_data={"PERSEN": True, "JUMLAH": True}
        )
        fig1.update_traces(textposition="outside")
        fig1.update_layout(uniformtext_minsize=8, uniformtext_mode="hide")
        st.plotly_chart(fig1, use_container_width=True)

        # ======================
        # Grafik 2: Sumber Air Bersih
        # ======================

        sumber_order = ["MATA AIR", "SUMUR DALAM", "SUMUR DANGKAL", "AIR HUJAN", "AIR PERMUKAAN", "LAINNYA", "TIDAK ADA"]
        df_sumber = df.copy()
        df_sumber["SUMBER AIR BERSIH"] = df_sumber["SUMBER AIR BERSIH"].astype(str).str.upper().str.strip()
        df_sumber["SUMBER AIR BERSIH"] = df_sumber["SUMBER AIR BERSIH"].where(df_sumber["SUMBER AIR BERSIH"].isin(sumber_order), "LAINNYA")

        sumber_counts = df_sumber["SUMBER AIR BERSIH"].value_counts().reindex(sumber_order, fill_value=0)
        sumber_percent = (sumber_counts / sumber_counts.sum() * 100).round(2)

        sumber_df = sumber_counts.reset_index()
        sumber_df.columns = ["SUMBER AIR BERSIH", "JUMLAH"]
        sumber_df["PERSEN"] = sumber_percent.values

        fig2 = px.bar(
            sumber_df,
            x="SUMBER AIR BERSIH",
            y="JUMLAH",
            color="SUMBER AIR BERSIH",
            text="JUMLAH",
            category_orders={"SUMBER AIR BERSIH": sumber_order},
            title="Distribusi Sumber Air Bersih",
            hover_data={"PERSEN": True, "JUMLAH": True}
        )
        fig2.update_traces(textposition="outside")
        fig2.update_layout(uniformtext_minsize=8, uniformtext_mode="hide")
        st.plotly_chart(fig2, use_container_width=True)


    with tab3:
        st.subheader("🗺️ Peta Titik Lokasi Sarana Air Bersih")

        # Ubah koma ke titik, lalu konversi ke float
        df["LATITUDE"] = df["LATITUDE"].astype(str).str.replace(",", ".", regex=False)
        df["LONGITUDE"] = df["LONGITUDE"].astype(str).str.replace(",", ".", regex=False)
        df["LATITUDE"] = pd.to_numeric(df["LATITUDE"], errors="coerce")
        df["LONGITUDE"] = pd.to_numeric(df["LONGITUDE"], errors="coerce")
        map_df = df.dropna(subset=["LATITUDE", "LONGITUDE"]).copy()

        if not map_df.empty:
            # Peta awal
            m = folium.Map(
                location=[map_df["LATITUDE"].mean(), map_df["LONGITUDE"].mean()],
                zoom_start=10,
                control_scale=True
            )

            # Fungsi warna berdasarkan kondisi
            def warna_kondisi(kondisi):
                if kondisi == "BAIK":
                    return "blue"
                elif kondisi == "RUSAK RINGAN":
                    return "yellow"
                elif kondisi == "RUSAK SEDANG":
                    return "orange"
                elif kondisi == "RUSAK BERAT":
                    return "red"
                else:
                    return "gray"

            # Tambahkan marker
            for _, row in map_df.iterrows():
                lokasi = f"{row.get('LOKASI SARANA PRASARANA AIR BERSIH', '-')}"
                sumber = row.get("SUMBER AIR BERSIH", "-")
                kepemilikan = row.get("STATUS KEPEMILIKAN SARANA PRASARANA AIR BERSIH", "-")
                kondisi = row.get("KONDISI SARANA", "Tidak Diketahui")
                kec = row.get("KECAMATAN", "-")
                desa = row.get("DESA", "-")
                gmap_link = f"https://www.google.com/maps/search/?api=1&query={row['LATITUDE']},{row['LONGITUDE']}"

                popup_html = f"""
                <b>Kecamatan:</b> {kec}<br>
                <b>Desa:</b> {desa}<br>
                <b>Lokasi:</b> {lokasi}<br>
                <b>Sumber Air:</b> {sumber}<br>
                <b>Status Kepemilikan:</b> {kepemilikan}<br>
                <b>Kondisi:</b> {kondisi}<br>
                <a href="{gmap_link}" target="_blank">🛣️ Lihat di Google Maps</a>
                """

                folium.CircleMarker(
                    location=[row["LATITUDE"], row["LONGITUDE"]],
                    radius=6,
                    color=warna_kondisi(kondisi),
                    fill=True,
                    fill_color=warna_kondisi(kondisi),
                    fill_opacity=0.9,
                    popup=folium.Popup(popup_html, max_width=300)
                ).add_to(m)

            st_folium(m, use_container_width=True, height=700)
        else:
            st.warning("Tidak ada data koordinat valid untuk ditampilkan.")
        
        # Tambahkan legenda warna
        st.markdown("### 🗂️ Keterangan Warna Kondisi Sarana")
        legend_html = """
            <div style="display: flex; gap: 20px; flex-wrap: wrap; font-size: 15px;">
            <div style="display: flex; align-items: center;">
            <div style="width: 18px; height: 18px; background-color: rgb(0, 0, 255, 160); margin-right: 6px; border-radius: 50%;"></div>
            Baik
            </div>
            <div style="display: flex; align-items: center;">
            <div style="width: 18px; height: 18px; background-color: rgb(255, 215, 0); margin-right: 6px; border-radius: 50%;"></div>
            Rusak Ringan
            </div>
            <div style="display: flex; align-items: center;">
            <div style="width: 18px; height: 18px; background-color: rgb(255, 140, 0); margin-right: 6px; border-radius: 50%;"></div>
            Rusak Sedang
            </div>
            <div style="display: flex; align-items: center;">
            <div style="width: 18px; height: 18px; background-color: rgb(200, 0, 0); margin-right: 6px; border-radius: 50%;"></div>
            Rusak Berat
            </div>
            <div style="display: flex; align-items: center;">
            <div style="width: 18px; height: 18px; background-color: rgb(100, 100, 100); margin-right: 6px; border-radius: 50%;"></div>
            Tidak Diketahui
            </div>
            </div>
            """
        st.markdown(legend_html, unsafe_allow_html=True)
                
    with tab4:
        st.subheader("📄 Data Mentah")
        st.dataframe(df)

        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            df.to_excel(writer, index=False, sheet_name="Data Air Bersih")
        buffer.seek(0)

        st.download_button(
            label="📥 Unduh Data Excel",
            data=buffer,
            file_name="data_air_bersih_filtered.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

else:
    st.info("Silakan pilih filter dan tekan tombol **Tampilkan Data** untuk melihat hasil.")

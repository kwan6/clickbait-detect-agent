"""
Dashboard visualisasi hasil deteksi clickbait — versi styled.
Baca langsung dari database SQLite yang sama dipakai agent/scraper.

Jalankan dengan:
    streamlit run dashboard.py
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from db import get_all_headlines, init_db

st.set_page_config(page_title="Deteksi Clickbait", layout="wide", page_icon="🔍")

init_db()

# ---------- CSS custom ----------
st.markdown("""
<style>
[data-testid="stMetric"] {
    background-color: #1C2128;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #2D333B;
}
[data-testid="stMetricLabel"] {
    color: #8B949E;
}
h1 {
    background: linear-gradient(90deg, #00D4AA, #00A3FF);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: 800;
}
[data-testid="stExpander"] {
    background-color: #1C2128;
    border-radius: 10px;
    border: 1px solid #2D333B;
}
hr {
    border-color: #2D333B;
}
</style>
""", unsafe_allow_html=True)

# palet warna konsisten dipakai di semua chart
COLOR_MAP = {"clickbait": "#FF6B6B", "non-clickbait": "#00D4AA"}

st.title("🔍 Dashboard Deteksi Clickbait")
st.caption("Sistem agentic pemantauan headline berita Indonesia — IndoBERT-p1 + agent reasoning")

rows = get_all_headlines(limit=500)

if not rows:
    st.info("Belum ada data. Jalankan scraper_mock.py atau scheduler.py dulu untuk mengisi database.")
    st.stop()

df = pd.DataFrame(
    rows,
    columns=["source_url", "headline", "label", "confidence", "verified_explanation", "created_at"],
)

# ---------- ringkasan angka ----------
col1, col2, col3, col4 = st.columns(4)
total = len(df)
clickbait_count = int((df["label"] == "clickbait").sum())
non_clickbait_count = total - clickbait_count
verified_count = int(df["verified_explanation"].notna().sum())

col1.metric("Total headline diproses", total)
col2.metric("Terdeteksi clickbait", clickbait_count, delta=f"{clickbait_count/total*100:.1f}%" if total else None)
col3.metric("Bukan clickbait", non_clickbait_count)
col4.metric("Diverifikasi lanjut", verified_count)

st.divider()

# ---------- grafik ----------
left, right = st.columns([1, 2])

with left:
    st.subheader("Distribusi label")
    label_counts = df["label"].value_counts().reset_index()
    label_counts.columns = ["label", "jumlah"]
    fig_pie = px.pie(
        label_counts, names="label", values="jumlah",
        color="label", color_discrete_map=COLOR_MAP, hole=0.55,
    )
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#FAFAFA", showlegend=True, margin=dict(t=10, b=10, l=10, r=10),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

with right:
    st.subheader("Sebaran confidence per headline")
    plot_df = df.head(30).copy()
    plot_df["headline_short"] = plot_df["headline"].str.slice(0, 40) + "..."
    fig_bar = px.bar(
        plot_df, x="headline_short", y="confidence", color="label",
        color_discrete_map=COLOR_MAP,
    )
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font_color="#FAFAFA", xaxis_tickangle=-45,
        margin=dict(t=10, b=10, l=10, r=10),
        xaxis_title=None, yaxis_title="Confidence",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

st.divider()

# ---------- tabel detail ----------
st.subheader("Detail semua headline")

filter_label = st.selectbox("Filter berdasarkan label", ["Semua", "clickbait", "non-clickbait"])
display_df = df if filter_label == "Semua" else df[df["label"] == filter_label]

st.dataframe(
    display_df[["headline", "label", "confidence", "created_at"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "confidence": st.column_config.ProgressColumn(
            "confidence", min_value=0, max_value=1, format="%.2f",
        ),
    },
)

# ---------- headline yang diverifikasi lanjut ----------
verified_rows = display_df[display_df["verified_explanation"].notna()]
if not verified_rows.empty:
    st.subheader("🔎 Headline yang sempat diverifikasi lanjut oleh agent")
    for _, row in verified_rows.iterrows():
        with st.expander(row["headline"]):
            st.write(f"**Confidence:** {row['confidence']}")
            st.write(f"**Penjelasan verifikasi:** {row['verified_explanation']}")
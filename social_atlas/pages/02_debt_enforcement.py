import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import folium
from streamlit_folium import st_folium

API_BASE_URL = os.getenv("API_URL", "http://localhost:8000")

ORP_COLORS = {
    "Most": "#E24B4A", "Chomutov": "#EF9F27", "Ústí nad Labem": "#378ADD",
    "Teplice": "#7F77DD", "Děčín": "#1D9E75", "Litoměřice": "#639922", "Louny": "#888780",
}

ORP_COORDS = {
    "Děčín": [50.7822, 14.2148], "Chomutov": [50.4605, 13.4178],
    "Litoměřice": [50.5335, 14.1318], "Louny": [50.3565, 13.7967],
    "Most": [50.5030, 13.6362], "Teplice": [50.6404, 13.8245],
    "Ústí nad Labem": [50.6607, 14.0322],
}

st.set_page_config(layout="wide")
st.title("⚖️ Exekuce v Ústeckém kraji")
st.caption("Fyzické osoby v exekuci a počet vedených exekucí podle okresů. Zdroj: Exekutorská komora ČR (statistiky.ekcr.info).")


@st.cache_data(show_spinner="Načítám data o exekucích…")
def load_okresy():
    r = requests.get(f"{API_BASE_URL}/exekuce", timeout=30)
    r.raise_for_status()
    payload = r.json()
    if isinstance(payload, dict) and payload.get("error"):
        raise RuntimeError(payload["error"])
    return pd.DataFrame(payload)


@st.cache_data(show_spinner=False)
def load_obce():
    r = requests.get(f"{API_BASE_URL}/exekuce/obce", timeout=30)
    r.raise_for_status()
    payload = r.json()
    if isinstance(payload, dict) and payload.get("error"):
        raise RuntimeError(payload["error"])
    return pd.DataFrame(payload)


try:
    df = load_okresy()
except Exception as e:
    st.error(f"Nepodařilo se načíst data z backendu: {e}")
    st.info("Backend pravděpodobně ještě nahrává data (~100 MB). Počkejte chvíli a klikněte na **Zkusit znovu**.")
    if st.button("🔄 Zkusit znovu"):
        st.cache_data.clear()
        st.rerun()
    st.stop()

# Honor sidebar ORP filter (year filter doesn't apply – data is point-in-time)
all_orps = list(df["orp"].unique())
selected_orps = st.session_state.get("filter_orp", all_orps)
selected_orps = [o for o in selected_orps if o in all_orps] or all_orps
df = df[df["orp"].isin(selected_orps)]

# ── 1. KPI cards ──────────────────────────────────────────────────────────────
st.markdown("### Klíčové ukazatele")
c1, c2, c3, c4 = st.columns(4)

total_people = int(df["people_in_enforcement"].sum())
total_enf = int(df["num_enforcements"].sum())
avg_per_person = (total_enf / total_people) if total_people else 0
worst_row = df.sort_values("people_in_enforcement", ascending=False).iloc[0]

with c1:
    st.metric("Lidé v exekuci", f"{total_people:,}".replace(",", " "))
with c2:
    st.metric("Vedených exekucí", f"{total_enf:,}".replace(",", " "))
with c3:
    st.metric("Exekucí na osobu (Ø)", f"{avg_per_person:.1f}")
with c4:
    st.metric("Nejvíce zasažený okres", worst_row["orp"],
              f"{int(worst_row['people_in_enforcement']):,} osob".replace(",", " "))

# ── 2. Map ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Mapa zasažených okresů")

m = folium.Map(location=[50.58, 13.9], zoom_start=9, tiles="CartoDB positron")
min_v = df["people_in_enforcement"].min()
max_v = df["people_in_enforcement"].max()
v_range = (max_v - min_v) or 1

def _fmt(n):
    return f"{int(n):,}".replace(",", " ")

for _, row in df.iterrows():
    if row["orp"] not in ORP_COORDS:
        continue
    ratio = (row["people_in_enforcement"] - min_v) / v_range
    size = 40 + ratio * 35
    # Amber (low) → deep red (high) gradient
    r_ = int(245 - 65 * ratio)   # 245 → 180
    g_ = int(170 - 140 * ratio)  # 170 → 30
    b_ = int(40 - 10 * ratio)    # 40  → 30
    rgba_bg = f"rgba({r_},{g_},{b_},0.92)"
    rgba_glow = f"rgba({r_},{g_},{b_},0.45)"

    people_str = _fmt(row["people_in_enforcement"])
    enf_str = _fmt(row["num_enforcements"])
    obci_str = _fmt(row["num_municipalities"])

    tooltip_html = (
        '<div style="font-family: sans-serif; font-size: 13px; line-height: 1.4;">'
        f'<b style="font-size: 15px;">Okres {row["orp"]}</b><br>'
        f'Lidé v exekuci: <b>{people_str}</b><br>'
        f'Vedených exekucí: <b>{enf_str}</b><br>'
        f'Exekucí na osobu: <b>{row["enforcements_per_person"]:.1f}</b><br>'
        f'Obcí v okrese: {obci_str}'
        '</div>'
    )

    icon_html = (
        f'<div style="'
        f'background-color: {rgba_bg};'
        f'border: 2px solid white;'
        f'border-radius: 50%;'
        f'width: {size}px; height: {size}px;'
        f'display: flex; justify-content: center; align-items: center;'
        f'color: white; font-weight: 800; font-family: \'Segoe UI\', sans-serif;'
        f'font-size: {11 + ratio * 4}px;'
        f'box-shadow: 0 4px 10px {rgba_glow};'
        f'">{people_str}</div>'
    )

    folium.Marker(
        location=ORP_COORDS[row["orp"]],
        icon=folium.DivIcon(html=icon_html, icon_anchor=(size / 2, size / 2)),
        tooltip=folium.Tooltip(tooltip_html),
    ).add_to(m)

st_folium(m, width="stretch", height=500, returned_objects=[])

# ── 3. Bar charts ─────────────────────────────────────────────────────────────
st.markdown("---")
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Lidé v exekuci podle okresu")
    df_a = df.sort_values("people_in_enforcement", ascending=True)
    fig_a = px.bar(
        df_a, x="people_in_enforcement", y="orp", orientation="h",
        color="orp", color_discrete_map=ORP_COLORS,
        text="people_in_enforcement",
        labels={"people_in_enforcement": "Počet osob", "orp": "Okres"},
    )
    fig_a.update_traces(texttemplate="%{text:,}", textposition="outside")
    fig_a.update_layout(showlegend=False, plot_bgcolor="white", height=420,
                        margin=dict(l=10, r=40, t=30, b=10))
    st.plotly_chart(fig_a, width="stretch")

with col_b:
    st.subheader("Průměrný počet exekucí na osobu")
    df_b = df.sort_values("enforcements_per_person", ascending=True)
    fig_b = px.bar(
        df_b, x="enforcements_per_person", y="orp", orientation="h",
        color="orp", color_discrete_map=ORP_COLORS,
        text="enforcements_per_person",
        labels={"enforcements_per_person": "Exekucí / osoba", "orp": "Okres"},
    )
    fig_b.update_traces(texttemplate="%{text:.1f}", textposition="outside")
    fig_b.update_layout(showlegend=False, plot_bgcolor="white", height=420,
                        margin=dict(l=10, r=40, t=30, b=10))
    st.plotly_chart(fig_b, width="stretch")

# ── 4. Top municipalities ─────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Nejhůře zasažené obce")

try:
    obce_df = load_obce()
except Exception:
    obce_df = pd.DataFrame()

if not obce_df.empty:
    obce_filtered = obce_df[obce_df["okres"].isin(selected_orps)]
    top_n = st.slider("Počet obcí", 5, 30, 15)
    top = obce_filtered.nlargest(top_n, "pocet_osob")[
        ["nazev_obce", "okres", "pocet_osob", "pocet_exekuci"]
    ].rename(columns={
        "nazev_obce": "Obec",
        "okres": "Okres",
        "pocet_osob": "Lidé v exekuci",
        "pocet_exekuci": "Vedených exekucí",
    })
    st.dataframe(top, width="stretch", hide_index=True)

# ── 5. Summary table + export ─────────────────────────────────────────────────
st.markdown("---")
st.subheader("Souhrn za okresy")
summary = df.sort_values("people_in_enforcement", ascending=False)
st.dataframe(summary, width="stretch", hide_index=True)
st.download_button(
    "⬇ Stáhnout CSV (okresy)",
    summary.to_csv(index=False).encode("utf-8"),
    "exekuce_okresy_ustecky_kraj.csv",
    "text/csv",
)

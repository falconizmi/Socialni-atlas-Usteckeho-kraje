import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import folium
from streamlit_folium import st_folium
import pandas as pd

from data.mock_data import ORPS, get_excluded_localities

SEVERITY_COLOR = {"Critical": "red", "Moderate": "orange", "Monitored": "green"}
SEVERITY_BG = {"Critical": "#ffd7d7", "Moderate": "#fff3cd", "Monitored": "#d4edda"}

st.set_page_config(layout="wide")
st.title("🏘️ Socially Excluded Localities")
st.caption("Localities at risk of social exclusion in the Ústecký Region — severity, residents, and map.")


@st.cache_data
def load():
    return get_excluded_localities()


df = load()
selected_orps = st.session_state.get("filter_orp", ORPS)
df = df[df["orp"].isin(selected_orps)]

# ── Styled table ──────────────────────────────────────────────────────────────
st.subheader("Localities Overview")

severity_icon = {"Critical": "🔴", "Moderate": "🟠", "Monitored": "🟢"}
display = df[["name", "orp", "num_residents", "severity"]].copy()
display["severity"] = display["severity"].map(lambda s: f"{severity_icon.get(s, '')} {s}")
display = display.sort_values("num_residents", ascending=False)

def row_style(row):
    raw = row["severity"].split(" ", 1)[-1].strip()
    bg = SEVERITY_BG.get(raw, "white")
    return [f"background-color: {bg}"] * len(row)

st.dataframe(
    display.style.apply(row_style, axis=1),
    use_container_width=True,
    hide_index=True,
)

# ── Folium map ────────────────────────────────────────────────────────────────
st.subheader("Map of Excluded Localities")

m = folium.Map(location=[50.62, 13.85], zoom_start=9, tiles="CartoDB positron")

for _, row in df.iterrows():
    color = SEVERITY_COLOR.get(row["severity"], "gray")
    popup_html = f"""
    <b>{row['name']}</b><br>
    ORP: {row['orp']}<br>
    Residents: {row['num_residents']:,}<br>
    Severity: {row['severity']}
    """
    folium.CircleMarker(
        location=[row["lat"], row["lon"]],
        radius=max(6, row["num_residents"] / 120),
        color=color,
        fill=True,
        fill_color=color,
        fill_opacity=0.7,
        popup=folium.Popup(popup_html, max_width=200),
        tooltip=row["name"],
    ).add_to(m)

st_folium(m, width=None, height=480, use_container_width=True)

# ── Download ──────────────────────────────────────────────────────────────────
st.download_button("⬇ Download CSV", df.to_csv(index=False).encode("utf-8"),
                   "excluded_localities.csv", "text/csv")

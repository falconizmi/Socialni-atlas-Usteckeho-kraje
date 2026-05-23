import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import plotly.express as px

from data.mock_data import ORPS

API_BASE_URL = os.environ.get("API_URL", "https://socialni-atlas-usteckeho-kraje.onrender.com")

SEVERITY_ORDER = ["Critical", "Moderate", "Monitored", "Low"]
SEVERITY_COLOR = {"Critical": "#d62728", "Moderate": "#ff9f1c", "Monitored": "#2ca02c", "Low": "#9ecae1"}
SEVERITY_BG = {"Critical": "#ffd7d7", "Moderate": "#fff3cd", "Monitored": "#d4edda", "Low": "#eaf3fb"}
SEVERITY_ICON = {"Critical": "🔴", "Moderate": "🟠", "Monitored": "🟢", "Low": "⚪"}
SEVERITY_CZ = {"Critical": "Kritické", "Moderate": "Zvýšené", "Monitored": "Sledované", "Low": "Nízké"}

# Okres-level coordinates (same set as on the unemployment page) — used for
# the aggregated bubble map, since the source dataset has no per-municipality
# lat/lon.
ORP_COORDS = {
    "Děčín": [50.7822, 14.2148], "Chomutov": [50.4605, 13.4178],
    "Litoměřice": [50.5335, 14.1318], "Louny": [50.3565, 13.7967],
    "Most": [50.5030, 13.6362], "Teplice": [50.6404, 13.8245],
    "Ústí nad Labem": [50.6607, 14.0322],
}

st.set_page_config(layout="wide")
st.title("🏘️ Sociálně vyloučené lokality")
st.caption("Obce ohrožené sociálním vyloučením v Ústeckém kraji — Index sociálního vyloučení MMR 2023.")


# ── 1. LOAD ───────────────────────────────────────────────────────────────────
@st.cache_data
def load_real_data():
    try:
        response = requests.get(f"{API_BASE_URL}/vylouceni", timeout=30)
        response.raise_for_status()
        payload = response.json()
        if isinstance(payload, dict) and "error" in payload:
            return pd.DataFrame(), payload["error"]
        return pd.DataFrame(payload), None
    except requests.exceptions.RequestException as e:
        return pd.DataFrame(), f"Nepodařilo se připojit k backendu: {e}"


df, err = load_real_data()
if err:
    st.error(err)
if df.empty:
    st.warning("Čekám na data z API. Zkontrolujte, zda běží backend.")
    st.stop()

selected_orps = st.session_state.get("filter_orp", ORPS)
df = df[df["orp"].isin(selected_orps)].copy()
if df.empty:
    st.info("Pro vybrané okresy nejsou k dispozici žádná data.")
    st.stop()



# ── 2. KPI ────────────────────────────────────────────────────────────────────
st.markdown("### Klíčové ukazatele (2023)")
c1, c2, c3, c4 = st.columns(4)

high_risk = df[df["severity"].isin(["Critical", "Moderate"])]
with c1:
    st.metric("Obce celkem", f"{len(df):,}".replace(",", " "))
with c2:
    st.metric("Ohrožené (Kritické + Zvýšené)", f"{len(high_risk):,}".replace(",", " "))
with c3:
    pop_at_risk = int(high_risk["num_residents"].sum())
    st.metric("Obyvatel v ohrožených obcích", f"{pop_at_risk:,}".replace(",", " "))
with c4:
    pop_total = int(df["num_residents"].sum())
    share = (pop_at_risk / pop_total * 100) if pop_total else 0
    st.metric("Podíl ohrožené populace", f"{share:.1f} %")


# ── 3. TOP MUNICIPALITIES TABLE ───────────────────────────────────────────────
st.markdown("---")
st.subheader("Obce s nejvyšším indexem sociálního vyloučení")

top_n = st.slider("Kolik obcí zobrazit", min_value=10, max_value=80, value=25, step=5)

display = (
    df.sort_values(["index", "num_residents"], ascending=[False, False])
      .head(top_n)
      [["name", "orp_detail", "orp", "num_residents", "exekuce_pct",
        "pnb_pct", "long_unemployment_pct", "index", "severity"]]
      .rename(columns={
          "name": "Obec",
          "orp_detail": "ORP",
          "orp": "Okres",
          "num_residents": "Obyvatel 15+",
          "exekuce_pct": "Exekuce %",
          "pnb_pct": "Příspěvek na bydlení %",
          "long_unemployment_pct": "Dlouhodobá nezaměstnanost %",
          "index": "Index vyloučení (0–30)",
          "severity": "Závažnost",
      })
      .copy()
)
display["Závažnost"] = display["Závažnost"].map(lambda s: f"{SEVERITY_ICON.get(s, '')} {SEVERITY_CZ.get(s, s)}")


def row_style(row):
    label = row["Závažnost"].split(" ", 1)[-1].strip()
    raw = next((k for k, v in SEVERITY_CZ.items() if v == label), label)
    bg = SEVERITY_BG.get(raw, "white")
    return [f"background-color: {bg}"] * len(row)


st.dataframe(
    display.style.apply(row_style, axis=1).format({
        "Obyvatel 15+": "{:,.0f}",
        "Exekuce %": "{:.1f}",
        "Příspěvek na bydlení %": "{:.1f}",
        "Dlouhodobá nezaměstnanost %": "{:.1f}",
    }),
    use_container_width=True,
    hide_index=True,
)


# ── 4. MAP (district-level bubbles) ───────────────────────────────────────────
st.markdown("---")
st.subheader("Mapa ohrožených obcí podle okresů")

agg = (
    df.assign(at_risk=df["severity"].isin(["Critical", "Moderate"]).astype(int))
      .groupby("orp")
      .agg(
          total_municipalities=("name", "count"),
          at_risk=("at_risk", "sum"),
          residents=("num_residents", "sum"),
          avg_index=("index", "mean"),
          critical=("severity", lambda s: (s == "Critical").sum()),
          moderate=("severity", lambda s: (s == "Moderate").sum()),
      )
      .reset_index()
)

m = folium.Map(location=[50.62, 13.95], zoom_start=9, tiles="CartoDB positron")

max_avg = agg["avg_index"].max() if not agg.empty else 1
for _, row in agg.iterrows():
    if row["orp"] not in ORP_COORDS:
        continue
    ratio = row["avg_index"] / max_avg if max_avg else 0
    size = 30 + ratio * 45
    r = 255
    g = int(220 - 180 * ratio)
    b = 30
    rgba_bg = f"rgba({r}, {g}, {b}, 0.9)"
    rgba_glow = f"rgba({r}, {g}, {b}, 0.4)"

    hover_html = f"""
    <div style="font-family: sans-serif; font-size: 13px; line-height: 1.4; padding: 2px;">
        <b style="font-size: 15px; color: #333;">Okres {row['orp']}</b><br>
        Obcí celkem: <b>{int(row['total_municipalities'])}</b><br>
        Ohrožené (Kritické + Zvýšené): <b>{int(row['at_risk'])}</b><br>
        <hr style="margin: 4px 0; border: 0; border-top: 1px solid #ccc;">
        🔴 Kritické: {int(row['critical'])}<br>
        🟠 Zvýšené: {int(row['moderate'])}<br>
        <hr style="margin: 4px 0; border: 0; border-top: 1px solid #ccc;">
        Obyvatel 15+: {int(row['residents']):,}<br>
        Průměrný index vyloučení: {row['avg_index']:.1f}
    </div>
    """

    icon_html = f"""
    <div style="
        background-color: {rgba_bg};
        border: 2px solid white;
        border-radius: 50%;
        width: {size}px;
        height: {size}px;
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        font-weight: 800;
        font-family: 'Segoe UI', sans-serif;
        font-size: {12 + ratio * 4}px;
        box-shadow: 0 4px 10px {rgba_glow};
    ">
        {int(row['at_risk'])}
    </div>
    """

    folium.Marker(
        location=ORP_COORDS[row["orp"]],
        icon=folium.DivIcon(html=icon_html, icon_anchor=(size / 2, size / 2)),
        tooltip=folium.Tooltip(hover_html),
    ).add_to(m)

st_folium(m, width=None, height=500, use_container_width=True, returned_objects=[])
st.caption("Číslo v bublině = počet ohrožených obcí (Kritické + Zvýšené) v okrese. Intenzita barvy = průměrný index vyloučení.")


# ── 5. SEVERITY DISTRIBUTION PER DISTRICT ─────────────────────────────────────
st.markdown("---")
st.subheader("Rozložení závažnosti podle okresů")

dist = (
    df.groupby(["orp", "severity"]).size().reset_index(name="municipalities")
)
dist["severity_cz"] = dist["severity"].map(SEVERITY_CZ)
severity_order_cz = [SEVERITY_CZ[s] for s in SEVERITY_ORDER]
severity_color_cz = {SEVERITY_CZ[k]: v for k, v in SEVERITY_COLOR.items()}
dist["severity_cz"] = pd.Categorical(dist["severity_cz"], categories=severity_order_cz, ordered=True)
dist = dist.sort_values(["orp", "severity_cz"])

fig_dist = px.bar(
    dist, x="orp", y="municipalities", color="severity_cz",
    color_discrete_map=severity_color_cz,
    category_orders={"severity_cz": severity_order_cz},
    labels={"orp": "Okres", "municipalities": "Počet obcí", "severity_cz": "Závažnost"},
)
fig_dist.update_layout(barmode="stack", height=380, plot_bgcolor="white",
                       legend=dict(orientation="h", y=-0.2))
st.plotly_chart(fig_dist, use_container_width=True)


# ── 6. DOWNLOAD ───────────────────────────────────────────────────────────────
st.markdown("---")
st.download_button(
    "⬇ Stáhnout CSV",
    df.to_csv(index=False).encode("utf-8"),
    "socialne_vyloucene_lokality_2023.csv",
    "text/csv",
)

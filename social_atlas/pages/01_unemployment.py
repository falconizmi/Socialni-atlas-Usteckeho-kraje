import os
import streamlit as st
import pandas as pd
import requests
import folium
from streamlit_folium import st_folium
import plotly.express as px

API_BASE_URL = "https://socialni-atlas-usteckeho-kraje.onrender.com"

# ── 1. NAČTENÍ DAT ────────────────────────────────────────────────────────────
@st.cache_data
def load_real_data():
    try:
        response = requests.get(f"{API_BASE_URL}/nezamestnanost")
        response.raise_for_status()
        # Originální backend posílá přímo list, takže stačí rovnou pd.DataFrame
        return pd.DataFrame(response.json())
    except requests.exceptions.RequestException as e:
        st.error(f"Nepodařilo se připojit k backendu: {e}")
        return pd.DataFrame()
    
df = load_real_data()

if df.empty:
    st.warning("Čekám na data z API. Zkontrolujte, zda běží backend.")
    st.stop()

# ── 2. DATA BRIDGE (Záchranná síť pro nové API) ──────────────────────────────
if 'rozhodne_datum' in df.columns:
    df = df.rename(columns={
        'okres': 'orp',
        'uchazec_pohlavi': 'gender',
        'pocet_uchazeci_v_evidenci': 'value',
        'vzdelani_kategorie': 'education',
        'vek_kategorie': 'age'
    })
    df['year'] = pd.to_datetime(df['rozhodne_datum']).dt.year
    
    # Agregace: Sečteme všechny absolutní počty pro dané kombinace
    df = df.groupby(['year', 'orp', 'gender', 'education', 'age'])['value'].sum().reset_index()


# ── 3. HLAVNÍ UI A FILTRY ─────────────────────────────────────────────────────
st.title("Nezaměstnanost v Ústeckém kraji")

available_years = sorted(df['year'].unique(), reverse=True)
selected_year = st.selectbox("Vyberte rok pro analýzu:", available_years)


# ── 4. KPI KARTY (Agregace za celý kraj) ──────────────────────────────────────
st.markdown("### Klíčové ukazatele")
c1, c2, c3, c4 = st.columns(4)

df_total = df.groupby(['year', 'orp']).agg({
    'value': 'sum',
    'inflow': 'sum',
    'outflow': 'sum',
    'avg_age': 'mean', # Zjednodušeno pro zobrazení v kartě
    'avg_duration': 'mean'
}).reset_index()

df_current = df_total[df_total['year'] == selected_year]
df_previous = df_total[df_total['year'] == (selected_year - 1)]

with c1:
    current_total = int(df_current['value'].sum())
    if not df_previous.empty:
        prev_total = int(df_previous['value'].sum())
        delta = current_total - prev_total
        st.metric("Lidé bez práce (Kraj)", f"{current_total:,}".replace(',', ' '), f"{delta:+,}".replace(',', ' '), delta_color="inverse")
    else:
        st.metric("Lidé bez práce (Kraj)", f"{current_total:,}".replace(',', ' '))

with c2:
    current_inflow = int(df_current['inflow'].sum())
    st.metric("Nově v evidenci", f"{current_inflow:,}".replace(',', ' '))

with c3:
    avg_age = df_current['avg_age'].mean()
    st.metric("Průměrný věk", f"{avg_age:.1f} let")

with c4:
    avg_duration = df_current['avg_duration'].mean()
    st.metric("Průměrná délka evidence", f"{int(avg_duration)} dní")


# ── 5. MAPA (Světlý moderní podklad + Detailní Hover Tooltip) ─────────────────
st.markdown("---")
st.subheader(f"Mapa nezaměstnanosti v okresech ({selected_year})")

ORP_COORDS = {
    "Děčín": [50.7822, 14.2148], "Chomutov": [50.4605, 13.4178],
    "Litoměřice": [50.5335, 14.1318], "Louny": [50.3565, 13.7967],
    "Most": [50.5030, 13.6362], "Teplice": [50.6404, 13.8245],
    "Ústí nad Labem": [50.6607, 14.0322]
}

# ZMĚNA: CartoDB positron pro čistý, světlý, profesionální vzhled
m = folium.Map(location=[50.58, 13.9], zoom_start=9, tiles="CartoDB positron")

min_val = df_current['value'].min() if not df_current.empty else 0
max_val = df_current['value'].max() if not df_current.empty else 1
val_range = max_val - min_val if max_val > min_val else 1

for _, row in df_current.iterrows():
    orp_name = row['orp']
    val = row['value']
    
    if orp_name in ORP_COORDS:
        ratio = (val - min_val) / val_range
        size = 40 + (ratio * 35)
        
        r = 255
        g = int(220 - (180 * ratio))
        b = 30
        rgba_bg = f"rgba({r}, {g}, {b}, 0.9)"
        rgba_glow = f"rgba({r}, {g}, {b}, 0.4)"
        
        # 1. Získání dodatečných dat pro daný okres a rok
        detail_df = df[(df['year'] == selected_year) & (df['orp'] == orp_name)]
        muzi = detail_df[detail_df['gender'] == 'M']['value'].sum()
        zeny = detail_df[detail_df['gender'] == 'Ž']['value'].sum()
        
        inflow = detail_df['inflow'].sum()
        outflow = detail_df['outflow'].sum()
        
        # 2. Vytvoření HTML pro Hover (Tooltip) s dodatečnými informacemi
        hover_html = f"""
        <div style="font-family: sans-serif; font-size: 13px; line-height: 1.4; padding: 2px;">
            <b style="font-size: 15px; color: #333;">Okres {orp_name}</b><br>
            Celkem nezaměstnaných: <b>{int(val):,}</b><br>
            <hr style="margin: 4px 0; border: 0; border-top: 1px solid #ccc;">
            Muži: {int(muzi):,}<br>
            Ženy: {int(zeny):,}<br>
            <hr style="margin: 4px 0; border: 0; border-top: 1px solid #ccc;">
            Nástup do evidence: {int(inflow):,}<br>
            Ukončení evidence: {int(outflow):,}
        </div>
        """
        
        # CSS pro bublinu (drobná úprava stínu pro světlé pozadí)
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
            font-size: {12 + (ratio * 4)}px;
            box-shadow: 0 4px 10px {rgba_glow};
            backdrop-filter: blur(4px);
        ">
            {int(val)}
        </div>
        """
        
        folium.Marker(
            location=ORP_COORDS[orp_name],
            icon=folium.DivIcon(html=icon_html, icon_anchor=(size/2, size/2)),
            # Folium Tooltip nyní přijímá naše naformátované HTML
            tooltip=folium.Tooltip(hover_html)
        ).add_to(m)

st_folium(m, width=None, height=500, use_container_width=True, returned_objects=[])


# ── 6. HEATMAPA (Samostatný řádek) ────────────────────────────────────────────
st.markdown("---")
st.subheader("Vývoj nezaměstnanosti v čase (Heatmapa)")

# Agregace jen přes roky a okresy
df_heat = df.groupby(['year', 'orp'])['value'].sum().reset_index()
fig_heat = px.density_heatmap(
    df_heat, x="year", y="orp", z="value", histfunc="sum", text_auto=".0f",
    color_continuous_scale="Reds",
    labels={"year": "Rok", "orp": "Okres", "value": "Počet nezaměstnaných"}
)
st.plotly_chart(fig_heat, use_container_width=True)


# ── 7. MOTÝLKOVÝ GRAF POHLAVÍ (Samostatný řádek) ──────────────────────────────
st.markdown("---")
st.subheader(f"Nezaměstnanost podle pohlaví ({selected_year})")

# 1. Agregace dat
df_pyramid = df[df['year'] == selected_year].groupby(['orp', 'gender'])['value'].sum().reset_index()

df_pyramid['gender'] = df_pyramid['gender'].replace({'M': 'Muži', 'Ž': 'Ženy'})

# Pokud máš desetinná čísla, můžeš přidat .round(1)
df_pyramid['display_value'] = df_pyramid['value'].abs()

# 4. Trik: Muže dáme do mínusu, aby šli doleva
df_pyramid.loc[df_pyramid['gender'] == 'Muži', 'value'] *= -1

# 5. Vykreslení grafu s parametrem text='display_value'
fig_gender = px.bar(
    df_pyramid, 
    x='value', 
    y='orp', 
    color='gender', 
    orientation='h', 
    barmode='relative',
    text='display_value', # Vloží hodnoty na konec sloupců
    color_discrete_map={'Muži': '#1f77b4', 'Ženy': '#d62728'},
    labels={'value': 'Počet lidí', 'orp': 'Okres', 'gender': 'Pohlaví'}
)

# 6. Nastavení pozice textu a layoutu
fig_gender.update_traces(textposition='outside') # Umístí čísla hned za sloupce

fig_gender.update_layout(
    xaxis=dict(
        visible=False # Úplně skryje osu X i s čarami a popisy
    ),
    yaxis_title=None,
    legend=dict(
        orientation="h",       # Horizontální výpis
        yanchor="top",
        y=-0.1,                # Posune legendu pod graf
        xanchor="center",
        x=0.5,                 # Vystředí legendu
        title=None             # Skryje nadpis "Pohlaví", u Muži/Ženy je to jasné
    ),
    margin=dict(l=0, r=40, t=20, b=0) # Přidá trochu místa napravo (r=40), aby se oříznutá čísla u žen vešla
)

st.plotly_chart(fig_gender, use_container_width=True)


# ── 8. GRAF VZDĚLÁNÍ (Samostatný řádek) ───────────────────────────────────────
st.markdown("---")
st.subheader(f"Struktura nezaměstnaných podle vzdělání ({selected_year})")

if 'education' in df.columns:
    # 1. Agregace dat pro vybraný rok
    df_edu = df[df['year'] == selected_year].groupby('education')['value'].sum().reset_index()

    # 2. Vypočítáme procenta pro filtraci
    total = df_edu['value'].sum()
    df_edu['percent'] = (df_edu['value'] / total) * 100

    # 3. Rozdělení na "Velké" kategorie (>= 4%) a "Malé" (< 4%)
    df_main = df_edu[df_edu['percent'] >= 4].copy()
    other_value = df_edu[df_edu['percent'] < 4]['value'].sum()

    # Pokud máme nějaké malé hodnoty, vytvoříme z nich nový řádek "Ostatní"
    if other_value > 0:
        df_other = pd.DataFrame([{'education': 'Ostatní', 'value': other_value}])
        # Spojíme hlavní kategorie s "Ostatní"
        df_final = pd.concat([df_main, df_other], ignore_index=True)
    else:
        df_final = df_main

    # 4. Vykreslení grafu (odstraněn parametr 'hole' pro plný koláč)
    fig_edu = px.pie(
        df_final, 
        values='value', 
        names='education',
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    # 5. Úprava popisků (čáry vedoucí ven z grafu) a skrytí legendy
    fig_edu.update_traces(
        textinfo='label+percent', # Zobrazí název i procento
        textposition='outside',   # Vytáhne text ven na vodících čarách
        pull=[0.05 if edu == 'Ostatní' else 0 for edu in df_final['education']] # Vizuální detail: lehce "vysune" kousek Ostatní
    )

    fig_edu.update_layout(
        showlegend=False, # Zruší boční legendu
        margin=dict(t=30, b=30, l=100, r=100) # Přidá okraje, aby se dlouhé texty venku neusekly
    )

    st.plotly_chart(fig_edu, use_container_width=True)


# ── 9. DATOVÁ TABULKA ─────────────────────────────────────────────────────────
st.markdown("---")
st.subheader("Surová data pro export")

# 1. Filtrační komponenta podle okresu
c_filter1, _ = st.columns([2, 2])
with c_filter1:
    # Získáme unikátní okresy z hlavního DataFrame a přidáme možnost "Všechny"
    orp_options = ["Všechny"] + sorted(list(df['orp'].unique()))
    selected_orp = st.selectbox("Filtrovat podle okresu:", orp_options)

# Aplikace filtru na data pro tabulku
if selected_orp != "Všechny":
    filtered_df = df[df['orp'] == selected_orp]
else:
    filtered_df = df

# 2. Správa stavu stránkování v st.session_state
if "table_page" not in st.session_state:
    st.session_state.table_page = 1

# Pokud uživatel změní filtr okresu, vrátíme ho na 1. stránku
if "last_selected_orp" not in st.session_state:
    st.session_state.last_selected_orp = selected_orp
elif st.session_state.last_selected_orp != selected_orp:
    st.session_state.table_page = 1
    st.session_state.last_selected_orp = selected_orp

# 3. Výpočet stránkování
PAGE_SIZE = 15  # Kolik řádků chceme vidět na jedné stránce
total_records = len(filtered_df)

# Spočítáme celkový počet stránek (celočíselné dělení s horním zaokrouhlením)
total_pages = (total_records + PAGE_SIZE - 1) // PAGE_SIZE if total_records > 0 else 1

# Pojistka: pokud by se kvůli filtru snížil počet stránek pod aktuální stránku
if st.session_state.table_page > total_pages:
    st.session_state.table_page = total_pages

# Výpočet indexů pro oříznutí (slice) tabulky
start_idx = (st.session_state.table_page - 1) * PAGE_SIZE
end_idx = start_idx + PAGE_SIZE

# Ořízneme DataFrame pouze na řádky pro aktuální stránku
paginated_df = filtered_df.iloc[start_idx:end_idx]

# 4. Zobrazení tabulky
if not paginated_df.empty:
    st.dataframe(paginated_df, use_container_width=True, hide_index=True)
else:
    st.info("Pro tento výběr nejsou k dispozici žádná data.")

# 5. Ovládací prvky stránkování (Tlačítka a info)
st.markdown(f"**Stránka {st.session_state.table_page} z {total_pages}** (Zobrazeno {len(paginated_df)} z {total_records} nalezených záznamů)")

c_nav1, c_nav2, _ = st.columns([1, 1, 4])

with c_nav1:
    # Tlačítko Předchozí (vypnuté na 1. stránce)
    if st.button("⬅️ Předchozí", disabled=(st.session_state.table_page <= 1)):
        st.session_state.table_page -= 1
        st.rerun()

with c_nav2:
    # Tlačítko Další (vypnuté na poslední stránce)
    if st.button("Další ➡️", disabled=(st.session_state.table_page >= total_pages)):
        st.session_state.table_page += 1
        st.rerun()
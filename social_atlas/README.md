# Social Atlas of the Ústecký Region

Interactive Streamlit dashboard visualising social indicators across the 7 ORP municipalities of the Ústecký Region (Czech Republic): **Most, Chomutov, Ústí nad Labem, Teplice, Děčín, Litoměřice, Louny**.

---

## Features

| Page | Indicators |
|------|-----------|
| **Overview** | 5 KPI cards, unemployment bar chart, excluded localities table, dual-axis trend chart, care summary |
| **Unemployment** | Time series by ORP, ORP × Year heatmap, data table |
| **Debt Enforcement** | Trend lines, heatmap, debt vs. unemployment scatter (bubble size = population) |
| **Housing Benefits** | Stacked bar — number of recipients or share of households |
| **Demographics** | Population trend lines, waterfall chart (natural increase + migration) |
| **Excluded Localities** | Severity-coded table, interactive Folium map with popups |
| **Crime** | Crimes per 1 000 residents, property vs. violent breakdown, trend lines |
| **Social & Healthcare Care** | Availability table, radar/spider chart per ORP |

**Global sidebar filters** (ORP multiselect + year-range slider) propagate to every page via `st.session_state`.  
**Export** — CSV per dataset and a multi-sheet Excel file from the sidebar.

---

## Project Structure

```
social_atlas/
├── app.py                        # Main entry point — overview page + sidebar
├── requirements.txt
├── data/
│   └── mock_data.py              # Deterministic mock data for 2015–2024
├── components/
│   ├── metric_card.py            # st.metric wrapper
│   ├── bar_chart_orp.py          # Horizontal unemployment bar (severity colours)
│   ├── trend_chart.py            # Dual-axis trend chart (Plotly)
│   └── export.py                 # CSV + Excel download buttons
└── pages/
    ├── 01_unemployment.py
    ├── 02_debt_enforcement.py
    ├── 03_housing.py
    ├── 04_demographics.py
    ├── 05_excluded_localities.py
    ├── 06_crime.py
    └── 07_care.py
```

---

## Requirements

- Python 3.10+
- See `requirements.txt` for all dependencies

```
streamlit>=1.35.0
pandas>=2.0.0
plotly>=5.20.0
openpyxl>=3.1.0
folium>=0.16.0
streamlit-folium>=0.20.0
numpy>=1.26.0
```

---

## Setup & Run

### 1. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the app

```bash
streamlit run app.py
```

The app opens at **http://localhost:8501** by default.

### Run headless (e.g. in a sandbox / server)

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0 --server.headless true
```

---

## ORP Colour Palette

Consistent colours are used across all charts:

| ORP | Hex |
|-----|-----|
| Most | `#E24B4A` |
| Chomutov | `#EF9F27` |
| Ústí nad Labem | `#378ADD` |
| Teplice | `#7F77DD` |
| Děčín | `#1D9E75` |
| Litoměřice | `#639922` |
| Louny | `#888780` |

---

## Data

All data is **mock / synthetic**, generated in `data/mock_data.py` with a fixed random seed (`numpy.random.default_rng(42)`) for reproducibility. Values are calibrated to realistic ranges based on publicly available statistics for the Ústecký Region:

- Unemployment: Most ~13–15 %, Louny ~3–5 %, COVID spike in 2020
- Debt enforcement: Most ~20 %, declining trend across all ORP
- Demographics: overall regional population decline, net emigration
- Excluded localities: 12 named localities with approximate coordinates

To replace mock data with real data, implement the same function signatures in `data/mock_data.py` and return `pandas.DataFrame` objects with the same column names.

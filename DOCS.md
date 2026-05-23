# 1. Přehled projektu

Sociální atlas Ústeckého kraje je moderní analytický nástroj navržený k vizualizaci klíčových socio-ekonomických dat v regionu. Aplikace umožňuje koncovým uživatelům (odborníkům, široké veřejnosti i zástupcům samospráv) snadno a intuitivně sledovat vývojové trendy v oblastech, jako jsou nezaměstnanost, zadluženost, bydlení, kriminalita a celkový demografický vývoj.

## 2. Architektura systému

Projekt využívá moderní mikroslužbový datový stack, přičemž je plně kontejnerizován pro snadnou přenositelnost.

*   **Frontend (Dashboard):** Streamlit – Zajišťuje interaktivní uživatelské rozhraní, filtrování a vykreslování grafů.
*   **Backend (API):** FastAPI – Rychlé API, které se stará o zpracování dat a jejich poskytování frontendu.
*   **Zpracování dat:** Python (Pandas) – Transformace, čištění a agregace vládních datových sad.
*   **Infrastruktura:** Docker & Docker Compose – Zajišťuje konzistentní vývojové i produkční prostředí nezávisle na operačním systému.

## 3. Instalace a lokální spuštění

Celý projekt je připraven k rychlému spuštění pomocí nástroje Docker Compose. Tím se předejde jakýmkoliv konfliktům verzí Pythonu.

### Prerekvizity

*   **Windows / Mac:** Nainstalovaný a spuštěný Docker Desktop.
*   **Linux:** Nainstalovaný Docker Engine a Docker Compose plugin.
*   **Git** pro naklonování repozitáře.

### Postup spuštění

1. Naklonujte repozitář a přejděte do kořenové složky projektu:
```bash
git clone https://github.com/falconizmi/Socialni-atlas-Usteckeho-kraje.git
cd Socialni-atlas-Usteckeho-kraje
```

2. Spusťte build a sestavení kontejnerů:
```bash
docker compose up --build
```

3. Jakmile terminál ohlásí, že služby běží, aplikace je dostupná v prohlížeči na následujících adresách:
*   **Frontend (Uživatelské rozhraní):** http://localhost:8501
*   **Backend (API dokumentace):** http://localhost:8000/docs

*(Poznámka: Backendové API může při prvním startu nabíhat několik sekund, protože do paměti (in-memory cache) načítá objemný 100MB dataset z vládních zdrojů. Dokončení načítání se zobrazí v lozích terminálu.)*

### Ukončení aplikace

Pro zastavení běžících kontejnerů stiskněte Ctrl + C v terminálu. Pokud chcete kontejnery kompletně smazat a vyčistit systém, použijte příkaz:
```bash
docker compose down
```

## 4. Datová vrstva a Backend

Data jsou klíčovou součástí projektu a jsou spravována odděleně od prezentační vrstvy.

*   **FastAPI Backend (/backend):** Komunikuje s datovými zdroji, provádí agregace a vystavuje data přes REST API pro frontend.
*   **Cache mechanismus:** Většina historických a objemných dat je při startu API načítána přímo do operační paměti. Ve frontendu (Streamlit) je následně využíván dekorátor `@st.cache_data`, což zajišťuje bleskovou odezvu dashboardu při přepínání filtrů.
*   **Struktura dat:** Aplikace primárně operuje s tabulkovými strukturami (Pandas DataFrames). Mezi hlavní indexové sloupce patří `orp` (Obec s rozšířenou působností), `rok` a metrické ukazatele (např. procento nezaměstnanosti). V původních prototypech zajišťoval čtení dat modul `mock_data.py`.

## 5. Frontend a struktura repozitáře

Uživatelské rozhraní je modulárně rozděleno do několika logických celků v rámci adresáře `social_atlas/`:

*   **`app.py`:** Hlavní vstupní bod Streamlit aplikace. Definuje globální filtry (Sidebar), základní rozvržení (layout) a routování.
*   **`pages/`:** Složka obsahující jednotlivé tematické podstránky, mezi kterými může uživatel přepínat (např. Nezaměstnanost, Zadluženost, Bydlení).
*   **`components/`:** Znovupoužitelné vizuální prvky (UI moduly) pro udržení čistého kódu:
    *   `bar_chart_orp.py`: Generuje srovnávací sloupcové grafy mezi jednotlivými ORP.
    *   `trend_chart.py`: Vykresluje liniové grafy časových řad.
    *   `metric_card.py`: Formátuje karty klíčových ukazatelů výkonnosti (KPI).
    *   `export.py`: Logika umožňující uživatelům stahovat aktuálně vyfiltrovaná data ve formátech CSV/Excel.

## 6. Průvodce pro vývojáře

### Jak přidat nový datový set

1.  **Zdroj dat:** Nahrajte nový dataset do datové složky na backendu (nebo upravte stahovací skript/DB spojení).
2.  **Backend (API):** Vytvořte nový endpoint ve FastAPI, který data načte (případně využije existující cachovací logiku) a vrátí je ve formátu JSON.
3.  **Frontend (Načtení):** V souboru `app.py` (v rámci načítací funkce, např. `load_all()`) přidejte volání nového backend endpointu.
4.  **Vizualizace:** Vytvořte novou analytickou stránku ve složce `social_atlas/pages/` nebo implementujte existující komponenty pro vizualizaci nových dat.

### Pravidla pro stylizaci a UI

*   **CSS:** Globální CSS styly pro specifické úpravy Streamlit komponent (skrytí hamburger menu, úprava okrajů) jsou definovány primárně v `app.py` pomocí `st.markdown(..., unsafe_allow_html=True)`.
*   **Design manuál:** Při tvorbě nových grafů a vizualizací udržujte stávající barevnou paletu (v základu blue a green) a responzivní chování. Moduly v `components/` by měly zůstat maximálně nezávislé.

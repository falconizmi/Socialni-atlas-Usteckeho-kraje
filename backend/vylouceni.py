# vylouceni.py
from fastapi import APIRouter
import pandas as pd
from store import data_cache

router = APIRouter()

# Source columns from the MMR Index sociálního vyloučení 2023 XLSX
COL_OBEC = "Název obce"
COL_ORP = "Název ORP"
COL_OKRES = "Název okres"
COL_KRAJ = "Název kraj"
COL_POP_15 = "Počet obyvyatel - starších 15 let (k 31. 12. 2023)"
COL_EXEKUCE_PCT = "% podíl obyvatel v exekuci (k 31. 12. 2023; vztaženo na obyvatelstvo 15+)"
COL_PNB_PCT = "% podíl příjemců PnB (průměrný měsíc r. 2023; vztaženo na obyvatelstvo 15+)"
COL_UNEMP_LONG_PCT = "% podíl uchazečů o zaměstnání evidovaných ÚP déle než 6 měsíců (prosinec 2023; vztaženo na obyvatelstvo 15 až 64)"
COL_INDEX = "Index soc. vyloučení 2023 (0-30 bodů)"
COL_CATEGORY = "Index soc. vyloučení 2023 (4 kategorie bodů)"

# 4-category index → severity label used by the frontend
SEVERITY_MAP = {
    "0 až 1": "Low",
    "2 až 7": "Monitored",
    "8 až 11": "Moderate",
    "12 až 30": "Critical",
}


@router.get("/vylouceni")
def get_vylouceni():
    if "vylouceni" not in data_cache:
        return {"error": "Data is loading..."}

    df = data_cache["vylouceni"].copy()

    if COL_KRAJ in df.columns:
        df = df[df[COL_KRAJ] == "Ústecký kraj"]

    out = pd.DataFrame({
        "name": df[COL_OBEC],
        "orp": df[COL_OKRES],
        "orp_detail": df[COL_ORP],
        "num_residents": pd.to_numeric(df[COL_POP_15], errors="coerce").fillna(0).astype(int),
        "exekuce_pct": pd.to_numeric(df[COL_EXEKUCE_PCT], errors="coerce").fillna(0).round(2),
        "pnb_pct": pd.to_numeric(df[COL_PNB_PCT], errors="coerce").fillna(0).round(2),
        "long_unemployment_pct": pd.to_numeric(df[COL_UNEMP_LONG_PCT], errors="coerce").fillna(0).round(2),
        "index": pd.to_numeric(df[COL_INDEX], errors="coerce").fillna(0).astype(int),
        "category": df[COL_CATEGORY].astype(str),
    })
    out["severity"] = out["category"].map(SEVERITY_MAP).fillna("Low")
    out["year"] = 2023

    return out.to_dict(orient="records")

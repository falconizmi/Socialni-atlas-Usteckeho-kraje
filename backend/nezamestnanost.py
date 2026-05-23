# nezamestnanost.py
from fastapi import APIRouter
import pandas as pd
from store import data_cache

router = APIRouter()

@router.get("/nezamestnanost")
def get_nezamestnanost():
    # Zkontrolujeme, jestli se data už načetla do cache
    if "nezamestnanost" not in data_cache:
        return {"error": "Data is loading..."}
        
    df = data_cache["nezamestnanost"].copy()
    
    # Filtrujeme na Ústecký kraj
    if "kraj" in df.columns:
        df = df[df["kraj"] == "Ústecký kraj"]

    # Vytvoření sloupce 'year' z rozhodneho data
    if "rozhodne_datum" in df.columns:
        df["year"] = pd.to_datetime(df["rozhodne_datum"]).dt.year
    else:
        df["year"] = None 

    # Přejmenování sloupců podle očekávání frontend dashboardu
    rename_map = {
        "okres": "orp",
        "uchazec_pohlavi": "gender",
        "vzdelani_kategorie": "education",
        "vek_kategorie": "age",
        "pocet_uchazeci_v_evidenci": "value"
    }
    
    # Přejmenujeme pouze ty sloupce, které v datasetu reálně existují
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    
    # Ošetření chybějících sloupců pro jistotu (aby API vždy vracelo konzistentní strukturu)
    expected_cols = ["year", "orp", "gender", "education", "age", "value"]
    for col in expected_cols:
        if col not in df.columns:
            df[col] = 0 if col == "value" else "N/A"

    # Zajištění, že hodnota je číselná
    df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0)

    # Agregace dat:
    # Sečteme absolutní počty nezaměstnaných přes všechny ostatní dimenze (např. ISCO profese),
    # abychom do frontendu posílali už jen čistý souhrn pro zadané filtry.
    grouped = df.groupby(["year", "orp", "gender", "education", "age"], dropna=False).agg(
        value=("value", "sum")
    ).reset_index()
    
    # Seřazení a výběr finálních sloupců
    final_df = grouped[["year", "orp", "gender", "education", "age", "value"]]

    return final_df.to_dict(orient="records")
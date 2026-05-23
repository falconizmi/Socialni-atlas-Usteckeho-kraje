# nezamestnanost.py
from fastapi import APIRouter
import pandas as pd
from store import data_cache

router = APIRouter()

NEZAMESTNANOST_METADATA = {
    "rozhodne_datum": "Poslední den období, ke kterému data businessově platí včetně tohoto dne",
    "kraj": "Kraj zvolené pobočky Úřadu práce",
    "kraj_kod": "Kód kraje zvolené pobočky Úřadu práce",
    "okres": "Okres zvolené pobočky Úřadu práce",
    "okres_kod": "Kód okresu zvolené pobočky Úřadu práce",
    "ind_uchazec_narok_pvn_ppr": "Indikátor uchazeče v evidenci k rozhodnému datu, který má nárok na podporu v nezaměstnanosti/podporu při zabezpečované rekvalifikaci",
    "ind_uchazec_zarazen_do_evidence": "Indikátor nově zařazeného uchazeče ve sledovaném období",
    "ind_uchazec_ukoncen_evidence": "Indikátor ukončeného nebo vyřazeného uchazeče z evidence ve sledovaném období",
    "ind_uchazec_v_evidenci": "Indikátor uchazeče v evidenci k rozhodnému datu",
    "uchazec_pohlavi": "Pohlaví uchazeče",
    "vek_kategorie": "Kategorie věkové struktury uchazeče v evidenci",
    "vzdelani_kategorie": "Kategorie uchazeče v evidenci podle stupně vzdělání",
    "pozad_zamestnani_isco_kategorie": "Kategorie požadované profese uchazečů v evidenci dle CZ ISCO kódu",
    "pocet_uchazeci_zarazeni_do_evidence": "Počet nově zařazených uchazečů ve sledovaném období",
    "pocet_uchazeci_ukonceni_evidence": "Počet ukončených nebo vyřazených uchazečů z evidence ve sledovaném období",
    "pocet_uchazeci_v_evidenci": "Počet uchazečů v evidenci k rozhodnému datu",
    "suma_pvn_ppr_vyse": "Suma výše nároku na podporu v nezaměstnanosti nebo nároku podpory při zabezpečované rekvalifikaci",
    "prumer_vek": "Průměrný věk uchazečů k rozhodnému dni",
    "prumer_evidence_delka_dny": "Průměrná délka evidence uchazeče ve dnech",
    "ind_uchazec_ukoncen_narok_pvn_ppr": "Indikátor ukončeného nebo vyřazeného uchazeče z evidence ve sledovaném období, který měl v tomto období nárok na podporu v nezaměstnanosti/podporu při zabezpečované rekvalifikaci"
}

@router.get("/nezamestnanost/metadata")
def get_metadata():
    return NEZAMESTNANOST_METADATA

@router.get("/nezamestnanost")
def get_nezamestnanost():
    if "nezamestnanost" not in data_cache:
        print("DEBUG: Data not in cache")
        return {"error": "Data is loading..."}
        
    df = data_cache["nezamestnanost"].copy()
    print(f"DEBUG: Data loaded from cache, shape: {df.shape}")
    
    # Filtrujeme na Ústecký kraj
    if "kraj" in df.columns:
        df = df[df["kraj"] == "Ústecký kraj"]
    print(f"DEBUG: Data filtered for Ústecký kraj, shape: {df.shape}")

    # Vytvoření sloupce 'year' z rozhodneho data
    if "rozhodne_datum" in df.columns:
        df["year"] = pd.to_datetime(df["rozhodne_datum"]).dt.year
    else:
        df["year"] = 0

    # Přejmenování základních dimenzí
    rename_map = {
        "okres": "orp",
        "uchazec_pohlavi": "gender",
        "vzdelani_kategorie": "education",
        "vek_kategorie": "age"
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Zajištění existence sloupců pro agragaci
    required_cols = ["year", "orp", "gender", "education", "age"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = "N/A"

    # Numerické sloupce
    num_cols = [
        "pocet_uchazeci_v_evidenci", 
        "pocet_uchazeci_zarazeni_do_evidence", 
        "pocet_uchazeci_ukonceni_evidence",
        "prumer_vek",
        "prumer_evidence_delka_dny"
    ]
    for col in num_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        else:
            df[col] = 0

    # Výpočet pro vážené průměry
    df["weighted_age"] = df["prumer_vek"] * df["pocet_uchazeci_v_evidenci"]
    df["weighted_duration"] = df["prumer_evidence_delka_dny"] * df["pocet_uchazeci_v_evidenci"]

    # Agregace
    grouped = df.groupby(required_cols, dropna=False).agg(
        value=("pocet_uchazeci_v_evidenci", "sum"),
        inflow=("pocet_uchazeci_zarazeni_do_evidence", "sum"),
        outflow=("pocet_uchazeci_ukonceni_evidence", "sum"),
        sum_weighted_age=("weighted_age", "sum"),
        sum_weighted_duration=("weighted_duration", "sum")
    ).reset_index()

    # Výpočet průměrů zpět
    grouped["avg_age"] = (grouped["sum_weighted_age"] / grouped["value"]).fillna(0)
    grouped["avg_duration"] = (grouped["sum_weighted_duration"] / grouped["value"]).fillna(0)
    
    # Ošetření případných nekonečen (pokud by value bylo 0)
    grouped.loc[grouped["value"] == 0, ["avg_age", "avg_duration"]] = 0

    # Finální výběr sloupců
    final_cols = required_cols + ["value", "inflow", "outflow", "avg_age", "avg_duration"]
    print(f"DEBUG: Returning {len(grouped)} records")
    return grouped[final_cols].to_dict(orient="records")
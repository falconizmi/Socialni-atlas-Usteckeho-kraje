# main.py
from fastapi import FastAPI
import requests
import pandas as pd

# Načteme prázdnou paměť a soubor s routou pro nezaměstnanost
from store import data_cache
import nezamestnanost 

app = FastAPI()

# 1. Tímto propojíme endpoint z nezamestnanost.py s hlavní aplikací
app.include_router(nezamestnanost.router)

# 2. Zde si definujete všechny URL adresy, které se mají stáhnout při startu
DATA_SOURCES = {
    "nezamestnanost": "https://data.mpsv.cz/portal/api/reports/by-table/evid_evidence_stat_2_agr_frz_odata/data/json",
    # sem si kolega přidá další:
    # "exekuce": "https://url-na-data-o-exekucich.cz",
}

@app.on_event("startup")
def load_data_on_startup():
    """
    Spustí se JEN JEDNOU při startu backendu.
    Projdede slovník DATA_SOURCES, stáhne JSONy a uloží je do data_cache.
    """
    print("Fetching datasets... this might take a moment.")
    
    for name, url in DATA_SOURCES.items():
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # Nahrajeme do globální cache, na kterou kouká i nezamestnanost.py
            data_cache[name] = pd.DataFrame(response.json())
            print(f"Successfully loaded '{name}': {len(data_cache[name])} rows into memory!")
            
        except Exception as e:
            print(f"CRITICAL ERROR loading data for '{name}': {e}")
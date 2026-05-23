# main.py
from fastapi import FastAPI
import subprocess
import pandas as pd
import os
import json

# Načteme prázdnou paměť a soubor s routou pro nezaměstnanost
from store import data_cache
import nezamestnanost 

app = FastAPI()

# 1. Tímto propojíme endpoint z nezamestnanost.py s hlavní aplikací
app.include_router(nezamestnanost.router)

# 2. Zde si definujete všechny URL adresy, které se mají stáhnout při startu
DATA_SOURCES = {
    "nezamestnanost": {
        "local": "nezamestnanost.json",
        "fallback_url": "https://data.mpsv.cz/portal/api/reports/by-table/evid_evidence_stat_2_agr_frz_odata/data/json"
    },
    # sem si kolega přidá další:
    # "exekuce": "https://url-na-data-o-exekucich.cz",
}

@app.on_event("startup")
def load_data_on_startup():
    print("Loading datasets... this might take a moment.")
    
    for name, config in DATA_SOURCES.items():
        file_path = config["local"]
        url = config["fallback_url"]
        raw_data = None
        
        # 1. POKUS: Zkusíme načíst lokální soubor
        if os.path.exists(file_path):
            try:
                print(f"Loading '{name}' from LOCAL FILE: {file_path}")
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
            except Exception as e:
                print(f"Poškozený lokální soubor '{file_path}'. Chyba: {e}")
                raw_data = None

        # 2. POKUS (FALLBACK): Stažení a filtrace přes terminál (Ochrana proti OOM Erroru)
        if raw_data is None:
            print(f"Lokální soubor nenalezen. Stahuji a rovnou filtruji z URL: {url}")
            
            # Trik s jq: Očekáváme formát {"value": [...]}. JQ to rozbalí, vyfiltruje jen Ústecký kraj a zase zabalí.
            # Rourou (>) to rovnou uložíme do souboru, aniž by to prošlo přes paměť Pythonu.
            jq_filter = '{value: [.value[]? | select(.kraj == "Ústecký kraj" or .kraj == "Ústecký")]}'
            cmd = f"curl -s '{url}' | jq '{jq_filter}' > {file_path}"
            
            try:
                # Spuštění systémového příkazu
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                if result.returncode != 0:
                    print(f"CRITICAL ERROR (curl/jq): {result.stderr}")
                    continue
                
                print(f"Data úspěšně stažena, vyfiltrována a uložena do '{file_path}'")
                
                # Nyní můžeme bezpečně načíst ten už malý a vyfiltrovaný soubor
                with open(file_path, "r", encoding="utf-8") as f:
                    raw_data = json.load(f)
                    
            except Exception as e:
                print(f"CRITICAL ERROR při stahování a filtrování dat pro '{name}': {e}")
                continue # Přeskočíme na další dataset
        
        # 3. ZPRACOVÁNÍ DAT: Rozbalení MPSV struktury ("value") a uložení do cache
        try:
            if isinstance(raw_data, dict) and "value" in raw_data:
                records = raw_data["value"]
            else:
                records = raw_data
                
            data_cache[name] = pd.DataFrame(records)
            print(f"Successfully loaded '{name}': {len(data_cache[name])} rows into memory!\n")
            
        except Exception as e:
            print(f"CRITICAL ERROR při parsování dat do DataFrame pro '{name}': {e}")
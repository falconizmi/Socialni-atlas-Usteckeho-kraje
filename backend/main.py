# main.py
from fastapi import FastAPI
import requests
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
                print(f"Poškozený lokální soubor '{file_path}', zkusím stáhnout nový. Chyba: {e}")

        # 2. POKUS (FALLBACK): Pokud soubor neexistuje nebo byl poškozený, stáhneme data z API
        if raw_data is None:
            try:
                print(f"Lokální soubor pro '{name}' nenalezen. Stahuji z URL: {url}")
                response = requests.get(url)
                response.raise_for_status()
                raw_data = response.json()
                
                # BONUS: Stažený JSON rovnou uložíme lokálně, aby se příště načetl bleskově ze disku
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(raw_data, f, ensure_ascii=False, indent=4)
                print(f"Stažená data úspěšně uložena do lokálního souboru '{file_path}'")
                
            except Exception as e:
                print(f"CRITICAL ERROR: Nepodařilo se načíst lokální soubor ani stáhnout data z URL pro '{name}': {e}")
                continue # Přeskočíme na další dataset, pokud jich je víc
        
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
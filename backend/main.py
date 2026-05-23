# main.py
from fastapi import FastAPI
import pandas as pd
import json
import os
from store import data_cache
import nezamestnanost 

app = FastAPI()
app.include_router(nezamestnanost.router)

@app.on_event("startup")
def load_data_on_startup():
    print("STARTUP: Načítám předpřipravená data z lokálního disku...")
    file_path = "ustecky_nezamestnanost.json"
    
    if not os.path.exists(file_path):
        print(f"CRITICAL ERROR: Soubor '{file_path}' nebyl nalezen! Ujisti se, že je ve stejné složce jako main.py.")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            records = json.load(f)
            
        # Ošetření, kdyby to náhodou byl slovník
        if isinstance(records, dict) and "value" in records:
            records = records["value"]
            
        data_cache["nezamestnanost"] = pd.DataFrame(records)
        print(f"ÚSPĚCH: Načteno {len(data_cache['nezamestnanost'])} záznamů do paměti!")
        
    except Exception as e:
        print(f"CRITICAL ERROR: Nepodařilo se zpracovat statický soubor: {e}")
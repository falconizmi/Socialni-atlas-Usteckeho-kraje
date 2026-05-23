import os
import json
import pandas as pd
from fastapi import FastAPI
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Načteme prázdnou paměť a soubor s routou pro nezaměstnanost
from store import data_cache
import nezamestnanost 

# 1. Inicializace Limiteru (bude sledovat IP adresy uživatelů)
# default_limits nastaví globální limit pro VŠECHNY endpointy v aplikaci
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute"]
)

app = FastAPI()

# 2. Propojení limiteru s FastAPI a registrace chybového handleru
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 3. Tímto propojíme endpoint z nezamestnanost.py s hlavní aplikací
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
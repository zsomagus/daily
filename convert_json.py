import json
import os
from datetime import datetime

def convert_saved_persons():
    # Meghatározzuk a static/saved_persons.json elérési útját
    base_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(base_dir, "static", "saved_persons.json")
    
    if not os.path.exists(json_path):
        print(f"❌ A fájl nem található a megadott helyen: {json_path}")
        return

    # 1. Beolvassuk a régi JSON tartalmát
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    converted_data = {}

    # 2. Végigmegyünk a személyeken és átalakítjuk a dátum formátumot
    for name, info in data.items():
        birth_date_str = info.get("birth_date", "")
        
        if not birth_date_str:
            continue
            
        try:
            # Levágjuk a felesleges nanoszekundumokat vagy extra nullákat (pl. "00:00:00:00")
            if birth_date_str.count(":") > 2:
                parts = birth_date_str.split(":")
                birth_date_str = ":".join(parts[:3]) # Csak az ÉÉÉÉ-MM-DD ÓÓ:PP:MP részt hagyjuk meg
                
            # Beolvassuk datetime objektumként
            dt = datetime.strptime(birth_date_str.strip(), "%Y-%m-%d %H:%M:%S")
            
            # Elkészítjük az új, szétbontott struktúrát a GUI elvárásaihoz igazítva
            converted_data[name] = {
                "name": info.get("name", name),
                # Szöveges formátumok, amiket a gui_main.py _set_entries() metódusa közvetlenül be tud írni a mezőkbe:
                "date": dt.strftime("%Y-%m-%d"),  # ÉÉÉÉ-MM-DD (Pl: 1976-03-15)
                "time": dt.strftime("%H:%M"),     # ÓÓ:PP       (Pl: 21:53)
                
                # Szétszedett numerikus értékek (egész számokként), ha a háttérmotor kérné
                "year": dt.year,
                "month": dt.month,
                "day": dt.day,
                "hour": dt.hour,
                "minute": dt.minute,
                
                # Megtartjuk a földrajzi és időzóna adatokat stringként, ahogy a GUI mezők kezelik
                "lat": str(info.get("latitude", "")),
                "lng": str(info.get("longitude", "")),
                "tz": str(info.get("timezone_offset", ""))
            }
        except Exception as e:
            print(f"⚠️ Nem sikerült átalakítani {name} dátumát ('{birth_date_str}'): {e}")

    # 3. Elmentjük a frissített adatokat (felülírva a régit, biztonsági mentéssel)
    backup_path = json_path + ".bak"
    try:
        if os.path.exists(json_path):
            if os.path.exists(backup_path):
                os.remove(backup_path) # Régi biztonsági mentés takarítása
            os.rename(json_path, backup_path)
            print(f"📦 Biztonsági mentés létrehozva: saved_persons.json.bak")
            
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(converted_data, f, ensure_ascii=False, indent=4)
            print("🎯 SIKER: A saved_persons.json sikeresen átalakítva a GUI formátumához!")
            
    except Exception as e:
        print(f"❌ Hiba történt a mentés során: {e}")
        # Ha elakadt a mentés, visszaállítjuk az eredetit a .bak fájlból
        if os.path.exists(backup_path) and not os.path.exists(json_path):
            os.rename(backup_path, json_path)

if __name__ == "__main__":
    convert_saved_persons()
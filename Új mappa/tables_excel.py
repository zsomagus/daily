# modulok/tables_excel.py

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
EXCEL_PATH = BASE_DIR / "static" / "asztrológiai_adatbázis.xlsx"


# ---------------------------------------------------------
# 1) Excel betöltése
# ---------------------------------------------------------

def load_sheet(sheet_name: str):
    return pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)


# ---------------------------------------------------------
# 2) Jegyek
# ---------------------------------------------------------

def load_jegyek():
    df = load_sheet("Jegyek")
    jegyek = {}

    for _, row in df.iterrows():
        name = str(row["Jegy"]).strip()
        jegyek[name] = {
            "tulajdonsagok": row.get("Tulajdonságok", ""),
            "uralkodo": row.get("Uralkodó", ""),
            "szimbolum": row.get("szimbólum", ""),
        }

    return jegyek


# ---------------------------------------------------------
# 3) Házak
# ---------------------------------------------------------

def load_hazak():
    df = load_sheet("Házak")
    hazak = {}

    for _, row in df.iterrows():
        num = int(row["Ház száma"])
        hazak[num] = {
            "tulajdonsagok": row.get("Tulajdonságok", ""),
            "uralkodo": row.get("Uralkodó bolygó", ""),
            "purushartha": row.get("purusharták", ""),
            "purushartha_leiras": row.get("purusharta tulajdonságok", ""),
        }

    return hazak


# ---------------------------------------------------------
# 4) Bolygók
# ---------------------------------------------------------

def load_bolygok():
    df = load_sheet("Bolygók")
    bolygok = {}

    for _, row in df.iterrows():
        name = str(row["Bolygó"]).strip()
        bolygok[name] = {
            "tulajdonsagok": row.get("Tulajdonságok", ""),
            "szam": row.get("számaik", ""),
            "nap": row.get("napok", ""),
            "noveny": row.get("növény", ""),
            "kristaly": row.get("kristály", ""),
            "szimbolum": row.get("Szimbólum", ""),
        }

    return bolygok


# ---------------------------------------------------------
# 5) Nakshatra + Pada
# ---------------------------------------------------------

def load_nakshatra_pada():
    df = load_sheet("Nakshatra _ Pada")
    nak = {}

    for _, row in df.iterrows():
        name = str(row["Nakshatra"]).strip()
        nak[name] = {
            "ura": row.get("ura", ""),
            "tulajdonsag": row.get("tulajdonság", ""),
            "mantra": row.get("mantra", ""),
            "frekvencia": row.get("frekvencia", ""),
            "pada_1": row.get("1. Páda (Dharma)", ""),
            "pada_2": row.get("2. Páda (Artha)", ""),
            "pada_3": row.get("3. Páda (Kama)", ""),
            "pada_4": row.get("4. Páda (Moksha)", ""),
        }

    return nak


# ---------------------------------------------------------
# 6) Karakák
# ---------------------------------------------------------

def load_karakak():
    df = load_sheet("Chara karakák")
    karakak = {}

    for _, row in df.iterrows():
        name = str(row["karakák"]).strip()
        karakak[name] = row.get("Tulajdonságok", "")

    return karakak


# ---------------------------------------------------------
# 7) Vargák
# ---------------------------------------------------------

def load_vargak():
    df = load_sheet("részhoroszkópok")
    vargak = {}

    for _, row in df.iterrows():
        d = str(row["D"]).strip()
        vargak[d] = {
            "jelentes": row.get("mire haszználjuk", ""),
            "fok": row.get("hány fok 1 jegy", ""),
        }

    return vargak


# ---------------------------------------------------------
# 8) Elemek
# ---------------------------------------------------------

def load_elemek():
    df = load_sheet("elemek")
    elemek = {}

    for _, row in df.iterrows():
        elem = str(row["VÍZ"]).strip() if "VÍZ" in row else None
        # Ez a sheet nem strukturált → egyszerű listát adunk vissza
        # Ha később kell, normalizáljuk
        pass

    # Egyelőre csak placeholder
    return {
        "Tűz": "hevesség, dinamizmus, akarat, cselekvés",
        "Víz": "érzelmek, intuíció, áramlás, érzékenység",
        "Föld": "stabilitás, kitartás, gyakorlatiasság",
        "Levegő": "kommunikáció, gondolkodás, mozgékonyság",
    }


# ---------------------------------------------------------
# 9) Fő betöltő
# ---------------------------------------------------------

def load_all():
    return {
        "jegyek": load_jegyek(),
        "hazak": load_hazak(),
        "bolygok": load_bolygok(),
        "nakshatra": load_nakshatra_pada(),
        "karakak": load_karakak(),
        "vargak": load_vargak(),
        "elemek": load_elemek(),
    }

# modulok/sonic_bridge.py

from modulok.varga_adapter import get_varga_chart
import os
import json


def compute_full_chart(bd: dict, varga_label: str):
    
    """
    A GUI csak ezt hívja.
    Visszaad:
      - D1 chart
      - kiválasztott varga chart
      - pañcānga
      - szöveges összefoglaló
      - rajzolt SVG/PNG elérési útvonalak
    """

    year = int(bd["date"].split("-")[0])
    month = int(bd["date"].split("-")[1])
    day = int(bd["date"].split("-")[2])
    hour = int(bd["time"].split(":")[0])
    minute = int(bd["time"].split(":")[1])
    lat = float(bd["lat"] or 47.0)
    lon = float(bd["lon"] or 19.0)

    # időzóna offset
    import pendulum
    tz = pendulum.timezone(bd["timezone"])
    dt = tz.datetime(year, month, day, hour, minute)
    timezone_offset = dt.utcoffset().total_seconds() / 3600

    # --- D1 ---
    d1 = get_varga_chart(
        year=year, month=month, day=day,
        hour=hour, minute=minute,
        lat=lat, lon=lon,
        timezone_offset=timezone_offset,
        varga_label="D1 (Rashi)"
    )

    # --- Varga ---
    varga = get_varga_chart(
        year=year, month=month, day=day,
        hour=hour, minute=minute,
        lat=lat, lon=lon,
        timezone_offset=timezone_offset,
        varga_label=varga_label
    )

    # --- Szöveg összeállítása ---
    text = []
    text.append("=== D1 (Rashi) ===")

    asc = d1["rasi_chart"].houses[0]
    text.append(f"Ascendant: {asc.sign} {float(asc.sign_degrees):.2f}°")
    text.append("Bolygók:")

    for planet, pdata in d1["planet_data"].items():
        text.append(
            f"  {planet}: {pdata['sign']} {pdata['longitude']:.2f}° ({pdata['nakshatra']})"
        )

    text.append("")
    text.append(f"=== {varga_label} ===")
    text.append("Bolygók:")

    for planet, pdata in varga["planet_data"].items():
        text.append(
            f"  {planet}: {pdata['sign']} {pdata['longitude']:.2f}° ({pdata['nakshatra']})"
        )

    # --- Pañcānga ---
    tithi = d1["tithi"]
    nakshatra = d1["nakshatra"]
    yoga = d1["chart_obj"].panchanga.yoga
    karana = d1["chart_obj"].panchanga.karana
    vaara = d1["chart_obj"].panchanga.vaara

    text.append("")
    text.append(f"Tithi: {tithi}")
    text.append(f"Nakshatra: {nakshatra}")
    text.append(f"Yoga: {yoga}")
    text.append(f"Karana: {karana}")
    text.append(f"Vaara: {vaara}")

    # --- Rajzolás ---
    
    from modulok.draw import rajzol_del_indiai_horoszkop_svg

    svg_path_d1 = rajzol_del_indiai_horoszkop_svg(
        d1["planet_data"], bd, d1["planet_data"],
        varga_name="D1 (Rashi)",
        tithi=tithi,
        horoszkop_nev="D1",
        date_str=bd["date"],
        time_str=bd["time"],
    )

    svg_path_varga = rajzol_del_indiai_horoszkop_svg(
        varga["planet_data"], bd, varga["planet_data"],
        varga_name=varga_label,
        tithi=tithi,
        horoszkop_nev=varga_label,
        date_str=bd["date"],
        time_str=bd["time"],
    )

    return {
        "text": "\n".join(text),
        "d1": d1,
        "varga": varga,
        "svg_d1": svg_path_d1,
        "svg_varga": svg_path_varga,
    }
# ============================
#   SZEMÉLYKEZELÉS (BRIDGE)
# ============================


PERSONS_FILE = os.path.join(
    os.path.expanduser("~"),
    "Documents",
    "SonicJyotish",
    "saved_persons.json"
)

# biztosítjuk, hogy a mappa létezzen
os.makedirs(os.path.dirname(PERSONS_FILE), exist_ok=True)


def _convert_old_record(old):
    """Régi formátum → új formátum konverzió."""
    if "birth_date" in old:
        return old  # már új formátum

    dst_flag = old.get("dst", "").lower().strip()
    offset = 2.0 if dst_flag == "igen" else 1.0

    birth_dt = f"{old['date']} {old['time']}:00"

    return {
        "name": old["name"],
        "birth_date": birth_dt,
        "latitude": float(old["lat"]),
        "longitude": float(old["lon"]),
        "timezone_offset": offset
    }


def _load_all_persons():
    """Betölti az összes mentett személyt, és konvertálja a régi formátumot."""
    if not os.path.exists(PERSONS_FILE):
        return {}

    try:
        with open(PERSONS_FILE, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except:
        return {}

    converted = {}
    for name, rec in raw.items():
        converted[name] = _convert_old_record(rec)

    return converted


def bridge_save_person(bd: dict):
    """
    bd = {
        "name": "...",
        "date": "YYYY-MM-DD",
        "time": "HH:MM",
        "lat": "...",
        "lon": "...",
        "timezone": "Europe/Budapest"
    }
    """
    persons = _load_all_persons()
    persons[bd["name"]] = convert_gui_to_bridge(bd)
    _save_all_persons(persons)
    return True


def bridge_load_person(name: str):
    """Visszaadja a névhez tartozó bd dict-et, vagy None-t."""
    persons = _load_all_persons()
    return persons.get(name)

def convert_bridge_to_gui(bd):
    # birth_date → date + time
    date_str, time_full = bd["birth_date"].split(" ")
    time_str = time_full[:5]  # HH:MM

    # timezone_offset → timezone + DST
    # 1.0 = téli idő (UTC+1)
    # 2.0 = nyári idő (UTC+2)
    if bd.get("timezone_offset", 1.0) >= 2.0:
        tz = "Europe/Budapest"
        dst = True
    else:
        tz = "Europe/Budapest"
        dst = False

    return {
        "name": bd["name"],
        "date": date_str,
        "time": time_str,
        "lat": str(bd["latitude"]),
        "lon": str(bd["longitude"]),
        "timezone": tz,
        "dst": dst
    }
def convert_gui_to_bridge(bd):
    # DST → timezone_offset
    offset = 2.0 if bd.get("dst") else 1.0

    return {
        "name": bd["name"],
        "birth_date": f"{bd['date']} {bd['time']}:00",
        "latitude": float(bd["lat"]),
        "longitude": float(bd["lon"]),
        "timezone_offset": offset
    }

def bridge_list_persons():
    """Visszaadja az összes mentett név listáját."""
    persons = _load_all_persons()
    return sorted(persons.keys())


def _save_all_persons(persons: dict):
    """Elmenti az összes személyt a JSON fájlba."""
    try:
        with open(PERSONS_FILE, "w", encoding="utf-8") as f:
            json.dump(persons, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("Hiba a személyek mentésekor:", e)

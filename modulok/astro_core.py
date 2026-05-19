import os
from datetime import datetime
import jyotishganit
import pendulum
from jyotishganit import calculate_birth_chart  # ha máshonnan jön, igazítsd
from modulok import sonicjyotish
from modulok.config import YANTRA_PATH
# Ha máshol definiáltad, importáld onnan; ha nem, itt egy alapértelmezett:
#YANTRA_PATH = os.path.join(os.path.dirname(__file__), "static", "yantrák")


# 🌌 Nakshatra és pada számítása
def calculate_nakshatra(longitude, ayanamsa, nakshatras):
    sidereal_longitude = (longitude - ayanamsa) % 360
    nakshatra_index = int(sidereal_longitude // 13.3333) % 27
    nakshatra = nakshatras[nakshatra_index]
    pada = int((sidereal_longitude % 13.3333) // 3.3333) + 1
    return nakshatra, pada


# 🧘 Yantra fájl keresése tithi alapján
def find_yantra_by_tithi(tithi, yantra_folder=YANTRA_PATH):
    for fname in os.listdir(yantra_folder):
        if fname.lower().endswith(".jpg") and fname.startswith(str(tithi)):
            return os.path.join(yantra_folder, fname)
    return None


def get_chart_data(source, name, year, month, day, hour, minute,
                   tz_str, lng, lat, varga_name="D1"):

    if source != "jyotishganit":
        raise ValueError(f"Ismeretlen source: {source}")

    # időzóna pontosítása pendulum-mal
    dt = pendulum.datetime(year, month, day, hour, minute, tz=tz_str)
    timezone_offset = dt.utcoffset().total_seconds() / 3600

    birth_date = datetime(year, month, day, hour, minute, 0)

    chart = calculate_birth_chart(
        birth_date=birth_date,
        latitude=lat,
        longitude=lng,
        timezone_offset=timezone_offset,
    )

    # varga kiválasztása
    if varga_name == "D1":
        rasi_chart = chart.d1_chart
    else:
        rasi_chart = chart.divisional_charts.get(varga_name)
        if rasi_chart is None:
            raise ValueError(f"Nincs ilyen varga: {varga_name}")

    # bolygók
    planet_data = {}
    for p in rasi_chart.planets:
        pname = p.celestial_body
        planet_data[pname] = {
            "longitude": float(p.sign_degrees),
            "sign": p.sign,
            "nakshatra": p.nakshatra,
            "house": p.house,
        }

    return {
        "source": "jyotishganit",
        "planet_data": planet_data,
        "tithi": chart.panchanga.tithi,
        "nakshatra": chart.panchanga.nakshatra,
        "chart_obj": chart,
        "rasi_chart": rasi_chart,
    }

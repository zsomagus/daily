# modulok/prashna_core.py
import pendulum
# Lokális import vagy meglévő astro_core használata
from modulok import astro_core

# modulok/prashna_core.py
import pendulum

def get_current_prashna_data(latitude: float = 47.30, longitude: float = 19.05):
    """
    Lekéri a Prashna (pillanatnyi kérdés) aktuális idő- és helyadatait.
    Nem számol fix horoszkópot, hogy a GUI-ban a Varga váltó szabadon működhessen!
    """
    now = pendulum.now("Europe/Budapest")

    return {
        "date": now.format("YYYY-MM-DD"),
        "time": now.format("HH:mm"),
        "latitude": latitude,
        "longitude": longitude,
        "tz_offset": now.utcoffset().total_seconds() / 3600
    }
   # Ha a prashna_core-ban van egy függvény, ami a planet_data-ból dolgozik, 
# így kell megjavítani, hogy az Ayanamsát levonva számoljon, HA a res-ben nincs benne:

    if "tithi" in res:
        tithi = res["tithi"]
    else:
            # Biztonsági számítás, de már szigorúan VÉDIKUS (sziderikus) fokokból!
        ayanamsa = res["planet_data"].get("ayanamsa", 24.24)
        moon_sidereal = (res["planet_data"]["Moon"]["longitude"] - ayanamsa) % 360
        sun_sidereal = (res["planet_data"]["Sun"]["longitude"] - ayanamsa) % 360
        tithi = int(((moon_sidereal - sun_sidereal) % 360) / 12) + 1
    return {
        "date": date_str,
        "time": time_str,
        "latitude": latitude,
        "longitude": longitude,
        "tithi": tithi,
        "planet_data": res.get("planet_data", {}),
        "varga_label": "D1 (Rashi)",
        "varga_code": "D1",
        "raw_res": res
    }
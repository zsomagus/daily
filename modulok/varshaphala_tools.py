# modulok/varshaphala_tools.py

import pendulum
import swisseph as swe
from modulok import astro_core

# modulok/varshaphala_tools.py

import pendulum
import swisseph as swe
from modulok import astro_core

def get_sun_sidereal_longitude(dt_utc):
    """Visszaadja a Nap sziderikus hosszúságát Swiss Ephemeris alapján."""
    jd = swe.julday(dt_utc.year, dt_utc.month, dt_utc.day,
                    dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600)

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    
    # 1. Lekérjük a Swiss Ephemeris adatait (Visszatérési érték: egy tömb és egy flag)
    calc_res, ret_flag = swe.calc_ut(jd, swe.SUN)
    
    # 2. Kicsomagoljuk a hosszúsági fokot (a calc_res tömb legelső, 0. indexű eleme)
    lon = calc_res[0]
    
    # 3. Lekérjük az ayanamsát, majd kiszámoljuk a sziderikus pozíciót
    ayan = swe.get_ayanamsa(jd)
    return (lon - ayan) % 360

def find_solar_return_datetime(birth_dt, age, lat, lon):
    """
    Megkeresi azt az időpontot, amikor a Nap visszatér
    a születési sziderikus hosszúságra (Varshaphala).
    """

    # 1) Születési Nap sziderikus hosszúsága
    birth_dt_utc = birth_dt.in_timezone("UTC")
    target_long = get_sun_sidereal_longitude(birth_dt_utc)

    # 2) Célév (születés + age)
    approx = birth_dt.add(years=age)

    # 3) Iteráció ±48 órában, 10 perces lépésekben
    best_dt = None
    best_diff = 999

    for minutes in range(-48 * 60, 48 * 60, 10):
        test_dt = approx.add(minutes=minutes)
        test_dt_utc = test_dt.in_timezone("UTC")

        sun_long = get_sun_sidereal_longitude(test_dt_utc)
        diff = abs((sun_long - target_long + 180) % 360 - 180)

        if diff < best_diff:
            best_diff = diff
            best_dt = test_dt

    return best_dt

def compute_varshaphala_chart(last_chart_data, target_year=None):
    """
    Kibővített, GUI-kompatibilis Varshaphala horoszkóp számítás.
    A valós születési hely koordinátáit használja Budapest helyett.
    """
    try:
        # 1. Kicsomagoljuk a születési dátum és idő adatokat
        raw_year = int(last_chart_data["raw_year"])
        raw_month = int(last_chart_data["raw_month"])
        raw_day = int(last_chart_data["raw_day"])
        raw_hour = int(last_chart_data.get("raw_hour", 12))
        raw_min = int(last_chart_data.get("raw_min", 0))

        # 2. 🔥 DINAMIKUS KOORDINÁTÁK: Kikeressük a valódi adatokat, amiket a felhasználó megadott
        lat = float(last_chart_data.get("lat", 47.4979))
        lon = float(last_chart_data.get("lng", 19.0402))

        # 3. Pendulum születési dátum objektum felépítése
        birth_dt = pendulum.datetime(raw_year, raw_month, raw_day, raw_hour, raw_min, tz="Europe/Budapest")

        # 4. Életkor (Age) kiszámítása a célév alapján
        if target_year is None:
            target_year = pendulum.now().year
        else:
            target_year = int(target_year)

        age = target_year - raw_year
        if age < 0: age = 0

        print(f"[DEBUG VARSHAPHALA] Valós Helyszín -> Lat: {lat}, Lon: {lon}")
        print(f"[DEBUG VARSHAPHALA] Születési év: {raw_year}, Célév: {target_year} -> Számított életkor: {age} év")

        # 5. Meghívjuk a solar return keresőt a valós koordinátákkal
        solar_return_dt = find_solar_return_datetime(birth_dt, age, lat, lon)
        print(f"[DEBUG VARSHAPHALA] Pontos Szolár visszatérés (UTC/Local): {solar_return_dt}")

        # 6. Legeneráljuk a horoszkópot a szolár visszatérési időpontra
        varsha_chart = astro_core.generate_chart(
            name=f"Varshaphala - {target_year}",
            year=solar_return_dt.year,
            month=solar_return_dt.month,
            day=solar_return_dt.day,
            hour=solar_return_dt.hour,
            minute=solar_return_dt.minute,
            lat=lat,
            lng=lon
        )

        return varsha_chart

    except Exception as e:
        print(f"❌ Hiba a Varshaphala számításban: {e}")
        return None
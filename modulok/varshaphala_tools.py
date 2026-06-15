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


def compute_varshaphala_chart(birth_dt, age, lat, lon):
    """
    Visszaadja a Varshaphala horoszkóp teljes adatait
    astro_core.generate_chart() formátumban.
    """

    solar_return_dt = find_solar_return_datetime(birth_dt, age, lat, lon)
    dt = solar_return_dt.in_timezone("UTC")

    chart = astro_core.generate_chart(
        name=f"Varshaphala {age}",
        year=dt.year,
        month=dt.month,
        day=dt.day,
        hour=dt.hour,
        minute=dt.minute,
        lat=lat,
        lng=lon,
    )

    return {
        "datetime": solar_return_dt,
        "chart": chart,
        "planet_data": chart["planets"],
        "tithi": chart["tithi"],
        "ascendant": chart["ascendant"],
        "houses": chart["houses"],
    }

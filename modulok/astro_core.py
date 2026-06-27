import swisseph as swe
import math
import datetime
import pytz
import os
from modulok.tables import varga_factors, SIGN_MAP, SIGN_TRANSLATION 
# ---------------------------------------------------------
# 0) Swiss Ephemeris path
# ---------------------------------------------------------
from modulok.settings import SWEPH_PATH, check_sweph_files

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "..", "static")
# modulok/astro_core.py teteje felé (a meglévők alá)

# FIX TESZTSZEMÉLY ADATAI A HANGMODUL KÖZVETLEN TESZTELÉSÉHEZ
TESZT_SZEMELY = {
    "name": "Zsombor",
    "year": 1976,
    "month": 3,
    "day": 15,
    "hour": 21,
    "minute": 53,
    "lat": 47.2954,
    "lng": 19.0227,
    "tz_offset": 1
}
def set_swe_path():
    swe.set_ephe_path(SWEPH_PATH)
    print("SwissEph path set:", SWEPH_PATH)
    check_sweph_files()

# ---------------------------------------------------------
# 1) Alap táblák (Signs, Varga factors)
# ---------------------------------------------------------

SIGNS = [
    "Aries", "Taurus", "Gemini", "Cancer",
    "Leo", "Virgo", "Libra", "Scorpio",
    "Sagittarius", "Capricorn", "Aquarius", "Pisces"
]

SIGN_TRANSLATION = {
    "Aries": "Kos",
    "Taurus": "Bika",
    "Gemini": "Ikrek",
    "Cancer": "Rák",
    "Leo": "Oroszlán",
    "Virgo": "Szűz",
    "Libra": "Mérleg",
    "Scorpio": "Skorpió",
    "Sagittarius": "Nyilas",
    "Capricorn": "Bak",
    "Aquarius": "Vízöntő",
    "Pisces": "Halak",
}

SIGN_MAP = {
    "Aries": 1, "Taurus": 2, "Gemini": 3, "Cancer": 4,
    "Leo": 5, "Virgo": 6, "Libra": 7, "Scorpio": 8,
    "Sagittarius": 9, "Capricorn": 10, "Aquarius": 11, "Pisces": 12,
}

VARGA_DIVISIONS = {
    "D1": 1, "D2": 2, "D3": 3, "D4": 4, "D5": 5, "D6": 6, "D7": 7,
    "D8": 8, "D9": 9, "D10": 10, "D11": 11, "D12": 12,
    "D16": 16, "D20": 20, "D24": 24, "D27": 27, "D30": 30,
    "D40": 40, "D45": 45, "D60": 60,
}

# ---------------------------------------------------------
# 2) Swiss Ephemeris segédfüggvények
# ---------------------------------------------------------

PLANETS = {
    "Sun": swe.SUN,
    "Moon": swe.MOON,
    "Mars": swe.MARS,
    "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER,
    "Venus": swe.VENUS,
    "Saturn": swe.SATURN,
    "Rahu": swe.MEAN_NODE
}


def jd_from_datetime(dt_utc):
    y, m, d = dt_utc.year, dt_utc.month, dt_utc.day
    h = dt_utc.hour + dt_utc.minute/60 + dt_utc.second/3600
    return swe.julday(y, m, d, h)

def get_sidereal_longitude(jd, planet):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    res = swe.calc_ut(jd, planet)

    # 1) Ha hiba: res = (rc, errmsg)
    if isinstance(res[0], (int, float)) and isinstance(res[1], str):
        rc, msg = res
        raise ValueError(f"swe.calc_ut hiba (ipl={planet}): {rc} – {msg}")

    # 2) Ha figyelmeztetés: res = ((lon, lat, dist, speed, ...), rc)
    if isinstance(res[0], tuple):
        lon = res[0][0]
        lat = res[0][1]
        dist = res[0][2]
        speed = res[0][3]
    else:
        # 3) Normál eset: res = (lon, lat, dist, speed)
        lon, lat, dist, speed = res

    ayan = swe.get_ayanamsa(jd)
    return (lon - ayan) % 360

def get_sign_and_degree(lon):
    sign_index = int(lon // 30)
    deg = lon % 30
    return SIGNS[sign_index], deg

# ---------------------------------------------------------
# 3) Ascendant + Whole Sign Houses
# ---------------------------------------------------------
def get_ascendant(jd, lat, lng):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    cusps, ascmc = swe.houses(jd, lat, lng)
    asc = ascmc[0]  # tropical ascendant
    ayan = swe.get_ayanamsa(jd)
    return (asc - ayan) % 360


def get_whole_sign_houses(asc_sid):
    asc_sign_index = int(asc_sid // 30)
    return {i+1: SIGNS[(asc_sign_index + i) % 12] for i in range(12)}

# ---------------------------------------------------------
# 4) Nakshatra + Pada
# ---------------------------------------------------------

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
    "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
    "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra",
    "Swati", "Vishakha", "Anuradha", "Jyeshtha", "Mula",
    "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishta",
    "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

def calculate_nakshatra(lon_sid):
    nak_index = int(lon_sid // 13.3333)
    pada = int((lon_sid % 13.3333) // 3.3333) + 1
    return NAKSHATRAS[nak_index], pada

# ---------------------------------------------------------
# 5) Varga számítás (D1–D60)
# ---------------------------------------------------------

def compute_varga(lon_sid, varga_code):
    if varga_code not in VARGA_DIVISIONS:
        raise ValueError(f"Ismeretlen varga: {varga_code}")

    divisions = VARGA_DIVISIONS[varga_code]
    sign_index = int(lon_sid // 30)
    deg_in_sign = lon_sid % 30

    segment_size = 30 / divisions
    segment_index = int(deg_in_sign // segment_size)

    varga_sign_index = (sign_index * divisions + segment_index) % 12
    return SIGNS[varga_sign_index], segment_index + 1

# ---------------------------------------------------------
# 6) Teljes képlet generálása (D1)
# ---------------------------------------------------------
# ---------------- 6) Teljes képlet generálása (D1) ----------------
def generate_chart(name, year, month, day, hour, minute, lat, lng):
    set_swe_path()

    # --- ULTRA DEBUG ÉS AUTOMATIKUS JAVÍTÁS ---
    print(f"[ASTRO_CORE BEÉRKEZŐ NYERS ADATOK] year={year}, month={month}, day={day}")
    
    if int(float(month)) > 12 and int(float(day)) <= 12:
        print("   [ASTRO_CORE RIASZTÁS]: A hónap és a nap fel van cserélve! Automatikusan megfordítom...")
        temp = month
        month = day
        day = temp

    clean_year = int(float(year))
    clean_month = int(float(month))
    clean_day = int(float(day))
    clean_hour = int(float(hour))
    clean_minute = int(float(minute))
    
    print(f"[ASTRO_CORE TISZTÍTOTT ADATOK] year={clean_year}, month={clean_month}, day={clean_day}")

    # 🔥 IDŐZÓNA MEGHATÁROZÁSA (Áttéve ide, a localize ELÉ!)
    tz = pytz.timezone("Europe/Budapest")

    # Most már a 'tz' garantáltan létezik, a hiba megszűnik!
    dt_local = tz.localize(datetime.datetime(clean_year, clean_month, clean_day, clean_hour, clean_minute))    
    dt_utc = dt_local.astimezone(pytz.utc)
    jd = jd_from_datetime(dt_utc)
    # ASC
    asc_lon_sid = get_ascendant(jd, lat, lng)
    asc_sign, asc_deg = get_sign_and_degree(asc_lon_sid)
    houses = get_whole_sign_houses(asc_lon_sid)

    planets = {}
    for pname, code in PLANETS.items():
        res = swe.calc_ut(jd, code)
        if isinstance(res[0], tuple):
            lon_trop = res[0][0]
        else:
            lon_trop = res[0]

        lon_sid = get_sidereal_longitude(jd, code)
        sign, deg = get_sign_and_degree(lon_sid)
        nak, pada = calculate_nakshatra(lon_sid)

        planets[pname] = {
            "sign": sign,
            "deg": deg,
            "lon_trop": lon_trop,
            "lon_sid": lon_sid,
            "nakshatra": nak,
            "pada": pada
        }

    # KETU
    rahu_lon_sid = planets["Rahu"]["lon_sid"]
    rahu_lon_trop = planets["Rahu"]["lon_trop"]

    ketu_lon_sid = (rahu_lon_sid + 180) % 360
    ketu_lon_trop = (rahu_lon_trop + 180) % 360

    ksign, kdeg = get_sign_and_degree(ketu_lon_sid)
    knak, kpada = calculate_nakshatra(ketu_lon_sid)

    planets["Ketu"] = {
        "sign": ksign,
        "deg": kdeg,
        "lon_trop": ketu_lon_trop,
        "lon_sid": ketu_lon_sid,
        "nakshatra": knak,
        "pada": kpada
    }

    # 🌙 TITHI
    tithi = calculate_tithi(planets["Sun"]["lon_sid"], planets["Moon"]["lon_sid"])

    return {
        "name": name,
        "ascendant": {
            "sign": asc_sign,
            "deg": asc_deg,
            "lon_sid": asc_lon_sid
        },
        "houses": houses,
        "planets": planets,
        "ayanamsa": swe.get_ayanamsa(jd),
        "datetime_utc": dt_utc.isoformat(),
        "tithi": tithi,
    }

# ---------------------------------------------------------
# 7) Varga táblázat generálása
# ---------------------------------------------------------
def compute_all_vargas(planets, varga_list):
    results = {}
    for varga in varga_list:
        results[varga] = {}
        for pname, pdata in planets.items():
            lon = pdata["lon_sid"]   # ← EZ A HELYES
            vsign, vpart = compute_varga(lon, varga)
            results[varga][pname] = {"sign": vsign, "part": vpart}
    return results

# ---------------------------------------------------------
# 7) Tithi számító és Varga táblázat generálása
# ---------------------------------------------------------
def calculate_tithi(sun_lon, moon_lon):
    """ Kiszámolja a holdfázist (Tithi 1 és 30 között) """
    diff = (moon_lon - sun_lon) % 360
    tithi = int(diff // 12) + 1
    return 30 if tithi > 30 else tithi

def compute_all_vargas(planets, varga_list):
    results = {}
    for varga in varga_list:
        results[varga] = {}
        for pname, pdata in planets.items():
            lon = pdata["lon_sid"]
            vsign, vpart = compute_varga(lon, varga)
            results[varga][pname] = {"sign": vsign, "part": vpart}
    return results

def find_yantra_by_tithi(tithi, yantra_folder=None):
    import os
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    kivalasztott_mappa = os.path.join(base_dir, "static", "yantra")
    
    if not os.path.exists(kivalasztott_mappa):
        os.makedirs(kivalasztott_mappa, exist_ok=True)

    tithi_str = str(tithi).lower().strip()
    tithi_szam = "1"  # Alapértelmezett fallback

    # Kiszűrjük a tiszta számot (pl. "25")
    digits = "".join([c for c in tithi_str if c.isdigit()])
    if digits:
        tithi_szam = str(int(digits))
    else:
        if "trayodashi" in tithi_str: tithi_szam = "13"
        elif "chaturdashi" in tithi_str: tithi_szam = "14"
        elif "purnima" in tithi_str: tithi_szam = "15"
        elif "ekadashi" in tithi_str: tithi_szam = "11"
        elif "dvadashi" in tithi_str: tithi_szam = "12"

    try:
        # VÉGIGBÖNGÉSSZÜK A MAPPÁT CSAK A SZÁM ALAPJÁN
        for fname in os.listdir(kivalasztott_mappa):
            # Megtisztítjuk a fájlnevet a kiterjesztésektől (kezelve a .jpg.jpg-t is)
            alap_nev = fname.lower()
            for ext in [".jpg", ".png", ".jpeg"]:
                alap_nev = alap_nev.replace(ext, "")
            alap_nev = alap_nev.strip()

            # Ha a megtisztított név pontosan megegyezik a keresett számmal
            if alap_nev == tithi_szam:
                teljes_ut = os.path.join(kivalasztott_mappa, fname)
                print(f"🎯 SIKER: Yantra megtalálva csak a szám alapján: {fname}")
                return teljes_ut
    except Exception as e:
        print(f"❌ Hiba a yantra mappa olvasásakor: {e}")

    # Ha egyáltalán nincs ilyen számú fájl, adjon vissza egy vészhelyzeti első képet
    try:
        for fname in os.listdir(kivalasztott_mappa):
            if fname.lower().endswith((".jpg", ".png", ".jpeg")):
                return os.path.join(kivalasztott_mappa, fname)
    except:
        pass

    return ""
# modulok/astro_core.py alján cseréld le ezt a részt:
def get_varga_chart_data(year, month, day, hour, minute, lat, lng, tz_offset, varga_label="D1", name="Ismeretlen"):
    """
    Kiszámítja a kiválasztott Varga (részhoroszkóp) adatait a D1 alapképletből kiindulva...
    """
    chart_base = generate_chart(name, year, month, day, hour, minute, lat, lng)
    
    varga_code = "D1"
    if "(" in varga_label:
        varga_code = varga_label.split("(")[0].strip()
    else:
        varga_code = varga_label.strip()
            
    # ÚJ, OKOS KERESÉS: Először megnézzük a teljes varga_labelt a szótárban (pl. "D9 (Navamsha)")
    # Ha nincs meg, akkor jön a kényszerített matematikai osztás/szorzás faktor
    factor = varga_factors.get(varga_label, 1)
    
    if factor == 1 or factor == 15 or factor == 10: # Ha a régi egyedi faktorok jönnének vissza
        # KÉNYSZERÍTETT ASZTROLÓGIAI OSZTÁSSZÁMOK (D9 = 9 részre osztás, D10 = 10 részre osztás, stb.)
        # Így a compute_varga függvény pontosan megkapja a felosztási számot
        if varga_code.upper() == "D9": factor = 9
        elif varga_code.upper() == "D2": factor = 2
        elif varga_code.upper() == "D3": factor = 3
        elif varga_code.upper() == "D4": factor = 4
        elif varga_code.upper() == "D5": factor = 5
        elif varga_code.upper() == "D6": factor = 6
        elif varga_code.upper() == "D7": factor = 7
        elif varga_code.upper() == "D8": factor = 8
        elif varga_code.upper() == "D10": factor = 10
        elif varga_code.upper() == "D11": factor = 11
        elif varga_code.upper() == "D12": factor = 12
        elif varga_code.upper() == "D16": factor = 16
        elif varga_code.upper() == "D20": factor = 20
        elif varga_code.upper() == "D24": factor = 24
        elif varga_code.upper() == "D27": factor = 27
        elif varga_code.upper() == "D30": factor = 30
        elif varga_code.upper() == "D40": factor = 40
        elif varga_code.upper() == "D45": factor = 45
        elif varga_code.upper() == "D60": factor = 60

    print(f"[DEBUG ASTRO_CORE] varga_label='{varga_label}', varga_code={varga_code}, kiszámolt faktor={factor}")

    planet_data = {}
    
    for pname, pdata in chart_base["planets"].items():
        lon_sid = pdata["lon_sid"]
        
        if factor > 1:
            vsign, vpart = compute_varga(lon_sid, varga_code)
            jegy_idx = SIGNS.index(vsign)
            fok_belul = (lon_sid % 30) * factor % 30
        else:
            vsign = pdata["sign"]
            jegy_idx = SIGNS.index(vsign)
            fok_belul = pdata["deg"]
            
        planet_data[pname] = {
            "vedic_longitude": float((jegy_idx * 30) + fok_belul),
            "sign": vsign,
            "deg": float(fok_belul),  # 🔥 EZ HIÁNYZOTT! A chart_drawer a "deg" kulcsot keresi a rajzoláshoz!
            "rasi_deg": float(fok_belul),
            "nakshatra": pdata["nakshatra"],
            "house": 1, 
        }
        
    asc_lon = chart_base["ascendant"]["lon_sid"]
    if factor > 1:
        vsign_asc, _ = compute_varga(asc_lon, varga_code)
        jegy_idx_asc = SIGNS.index(vsign_asc)
        fok_asc = (asc_lon % 30) * factor % 30
    else:
        vsign_asc = chart_base["ascendant"]["sign"]
        jegy_idx_asc = SIGNS.index(vsign_asc)
        fok_asc = chart_base["ascendant"]["deg"]
        
    planet_data["ASC"] = {
        "vedic_longitude": float((jegy_idx_asc * 30) + fok_asc),
        "sign": vsign_asc,
        "deg": float(fok_asc),  # 🔥 EZ IS KELL A RAJZOLÓNAK!
        "rasi_deg": float(fok_asc)
    }

    # 🔥 DINAMIKUS TITHI SZÁMÍTÁS JAVÍTÁSA VAGY TITHI ÁTVÉTEL
    if varga_code == "D1":
        varga_tithi = str(chart_base["tithi"])
    else:
        try:
            varga_sun_lon = planet_data["Sun"]["vedic_longitude"]
            varga_moon_lon = planet_data["Moon"]["vedic_longitude"]
            diff = (varga_moon_lon - varga_sun_lon) % 360
            calculated_tithi = int(diff // 12) + 1
            if calculated_tithi > 30: calculated_tithi = 30
            elif calculated_tithi < 1: calculated_tithi = 1
            varga_tithi = str(int(calculated_tithi))
        except Exception:
            varga_tithi = str(chart_base["tithi"])

    return {
        "varga_label": varga_label,
        "varga_code": varga_code,
        "factor": factor,
        "planet_data": planet_data,
        "ASC": planet_data["ASC"],  
        "tithi": varga_tithi,
        "nakshatra": planet_data["Moon"]["nakshatra"],
    }
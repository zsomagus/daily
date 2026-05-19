# modulok/varga_adapter.py

from modulok.tables import varga_factors
from jyotishganit import calculate_birth_chart
from datetime import datetime



# -----------------------------
# 1) Segédfüggvény: varga label → varga kód
# "D9 (Navamsha)" → "D9"
# -----------------------------
def extract_varga_code(label: str) -> str:
    return label.split()[0]  # első token: "D9"


# -----------------------------
# 2) Segédfüggvény: varga label → factor
# -----------------------------
def get_varga_factor(label: str) -> float:
    return varga_factors.get(label, 1.0)


# -----------------------------
# 3) Fő függvény: varga chart lekérése
# -----------------------------
def get_varga_chart(
    year: int,
    month: int,
    day: int,
    hour: int,
    minute: int,
    lat: float,
    lon: float,
    timezone_offset: float,
    varga_label: str = "D1 (Rashi)"
):
    """
    Egységes varga-adapter:
    - varga_label alapján kiválasztja a megfelelő varga chartot
    - visszaadja a bolygókat egységes formátumban
    - visszaadja a varga factor értékét
    """

    # 1) Varga kód kinyerése
    varga_code = extract_varga_code(varga_label)  # pl. "D9"

    # 2) Chart kiszámítása
    birth_date = datetime(year, month, day, hour, minute)
    chart = calculate_birth_chart(
        birth_date=birth_date,
        latitude=lat,
        longitude=lon,
        timezone_offset=timezone_offset
    )

    # 3) Megfelelő varga kiválasztása
    if varga_code == "D1":
        rasi_chart = chart.d1_chart
    else:
        rasi_chart = chart.divisional_charts.get(varga_code)
        if rasi_chart is None:
            raise ValueError(f"Nincs ilyen varga a jyotishganit-ban: {varga_code}")
    
    # 4) Bolygók egységes formátumban
    planet_data = {}


    for p in rasi_chart.planets:
        pname = p.celestial_body  # <-- EZ A HELYES MEZŐ
        planet_data[pname] = {
            "longitude": float(p.sign_degrees),   # 0–30° a jegyben
            "sign": p.sign,                       # jegy neve
            "nakshatra": p.nakshatra,
            "house": p.house,
        }

    # 5) Varga factor
    factor = get_varga_factor(varga_label)

    with open("rasi_debug.txt", "w", encoding="utf-8") as f:
        f.write("DIR:\n")
        f.write(str(dir(rasi_chart)) + "\n\n")
        f.write("VARS:\n")
        f.write(str(vars(rasi_chart)) + "\n\n")

    return {
        "varga_label": varga_label,
        "varga_code": varga_code,
        "factor": factor,
        "planet_data": planet_data,
        "chart_obj": chart,
        "rasi_chart": rasi_chart,
        "tithi": chart.panchanga.tithi,
        "nakshatra": chart.panchanga.nakshatra,
    }
    
    
def get_varga_chart_gui(varga_name, birth_data):
    from jyotish.varga import generate_varga_chart
    chart = generate_varga_chart(varga_name, birth_data)

    return {
        "text": chart["text"],
        "svg": chart["svg_path"],
        "png_path": chart["png_path"],
        # később:
        # "rotation": get_rotation_for_varga(varga_name)
    }

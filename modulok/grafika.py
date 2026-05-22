# modulok/grafika.py
import os
import matplotlib.pyplot as plt
from PIL import Image
import svgwrite

from modulok.tables import house_positions, north_indian_house_positions, planet_abbreviations

# --- 1. DÉL-INDIAI HOROSZKÓP RAJZOLÓ (Eredetileg draw.py) ---
def rajzol_del_indiai_horoszkop_svg(varga_pos, bd, planet_data, varga_name="Rasi", tithi=None, horoszkop_nev="D1", date_str=None, time_str=None, is_prashna=False):
    # Helyi import az astro_core tithi-yantra funkciójához, így nincs körkörösség
    from modulok.astro_core import find_yantra_by_tithi
    yantra_path = find_yantra_by_tithi(tithi)

    downloads = os.path.join(os.path.expanduser("~"), "Downloads", "SonicJyotish")
    os.makedirs(downloads, exist_ok=True)

    safe_name = bd["name"].lower().replace(" ", "_")
    base = f"{safe_name}_horoszkop_{horoszkop_nev}"
    svg_path = os.path.join(downloads, base + ".svg")
    png_path = os.path.join(downloads, base + ".png")

    # (Itt fut a meglévő, jól működő SVG generáló és matplotlib PNG-re alakító logikád...)
    # A példa kedvéért a generált fájlneveket adjuk vissza:
    return svg_path, png_path


# --- 2. ÉSZAK-INDIAI HOROSZKÓP RAJZOLÓ (Eredetileg draw.py) ---
def rajzol_eszak_indiai_horoszkop_svg(varga_pos, bd, planet_data, varga_name="Rasi", tithi=None, horoszkop_nev="D1"):
    downloads = os.path.join(os.path.expanduser("~"), "Downloads", "SonicJyotish")
    os.makedirs(downloads, exist_ok=True)
    safe_name = bd["name"].lower().replace(" ", "_")
    png_path = os.path.join(downloads, f"{safe_name}_horoszkop_{horoszkop_nev}_north.png")
    
    # Kiválóan felépített matplotlib rácsgenerálásod helye...
    return png_path


# --- 3. RASHI LORD TÉRKÉP (Eredetileg draw_lord.py) ---
def generate_rashi_lord_chart(res, bd):
    downloads = os.path.join(os.path.expanduser("~"), "Downloads", "SonicJyotish")
    safe_name = bd["name"].lower().replace(" ", "_")
    png_path = os.path.join(downloads, f"{safe_name}_rashi_lord.png")
    
    # SVG/PNG uralkodó bolygóháló kirajzolása...
    return png_path


# --- 4. NAKSHATRA LORD TÉRKÉP (Eredetileg draw_lord.py) ---
def generate_nakshatra_lord_chart(res, bd):
    downloads = os.path.join(os.path.expanduser("~"), "Downloads", "SonicJyotish")
    safe_name = bd["name"].lower().replace(" ", "_")
    png_path = os.path.join(downloads, f"{safe_name}_nakshatra_lord.png")
    
    # Nakshatra urak pozícióinak grafikus leképezése...
    return png_path
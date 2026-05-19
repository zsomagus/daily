import os  # noqa: F401
import pendulum
from modulok.config import convert_to_utc
from modulok import tables
import jyotishganit
import matplotlib.pyplot as plt
from PIL import Image  # noqa: F401
from modulok.tables import house_positions, varga_factors, north_indian_house_positions, planet_abbreviations
from modulok.astro_core import  find_yantra_by_tithi
import os
import svgwrite
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QPixmap
def rajzol_del_indiai_horoszkop_svg(varga_pos, bd, planet_data, varga_name="Rasi", 
    tithi=None,
    horoszkop_nev="D1",
    date_str=None,
    time_str=None,
    vezeteknev=None,
    keresztnev=None,
    is_prashna=False,
):
    out_dir = get_output_folder()
    base = f"user_{bd['name'].lower()}_{varga_name}"
    svg_path = os.path.join(out_dir, base + ".svg")

    dwg = svgwrite.Drawing(svg_path, size=("1200px","1200px"))
    # ... ide jön a horoszkóp rajzolás logikája, amit most PNG‑ben csinálsz ...


    
    fig, ax = plt.subplots(figsize=(6, 6))

    # Háttérszín narancs
    fig.patch.set_facecolor("#FFA500")
    ax.set_facecolor("#FFA500")

    # Zöld rács – 12 ház, középső 4 mező kihagyva
    exclude_coords = [(1, 1), (2, 1), (1, 2), (2, 2)]
    for x in range(4):
        for y in range(4):
            if (x, y) not in exclude_coords:
                ax.plot([x, x + 1], [y, y], color="green", linewidth=2)
                ax.plot([x + 1, x + 1], [y, y + 1], color="green", linewidth=2)
                ax.plot([x + 1, x], [y + 1, y + 1], color="green", linewidth=2)
                ax.plot([x, x], [y + 1, y], color="green", linewidth=2)

    # Yantra beillesztése középre
    yantra_path = find_yantra_by_tithi(tithi)
    if yantra_path:
        try:
            yantra = Image.open(yantra_path).resize((150, 150))
            ax.imshow(yantra, extent=[1.0, 3.0, 1.0, 3.0])
        except Exception as e:
            print(f"Yantra megnyitási hiba: {e}")
    else:
        print(f"Nincs yantra fájl a(z) {tithi}. tithi-hez.")

    # Bolygók házba rendezése
    house_planets = {i: [] for i in range(1, 13)}
    for planet, data in planet_data.items():
        degrees = data["longitude"] % 360
        sign = int(degrees // 30) + 1
        abbreviation = tables.planet_abbreviations.get(planet, planet[:2].upper())
        house_planets[sign].append((planet, abbreviation))

    # Bolygók megjelenítése
    for hszam, (x, y) in tables.house_positions.items():
        bolygok = house_planets[hszam]
        for idx, (full_name, abbrev) in enumerate(bolygok):
            planet_deg = planet_data[full_name]["longitude"] % 30
            fok = int(planet_deg)
            perc = int((planet_deg - fok) * 60)
            label = f"{abbrev} {fok}° {perc}'"
            ax.text(
                x + 0.5,
                y + 0.8 - 0.25 * idx,
                label,
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                color="black",
            )

    # ASC átló
    if "ASC" in planet_data:
        asc_deg = planet_data["ASC"]["longitude"] % 360
        asc_sign = int(asc_deg // 30) + 1
        if asc_sign in tables.house_positions:
            x, y = tables.house_positions[asc_sign]
            ax.plot([x, x + 1], [y, y + 1], color="red", linewidth=3)

    ax.set_title(
        f"Dél-indiai horoszkóp – {horoszkop_nev} – Tithi: {tithi}",
        fontsize=14,
        fontweight="bold",
    )

    # Mentés fájlba
    safe_name = bd["name"].lower().replace(" ", "_")
    downloads = os.path.join(os.path.expanduser("~"), "Downloads", "SonicJyotish")
    os.makedirs(downloads, exist_ok=True)  # ha nincs, létrehozza

    if is_prashna and date_str and time_str:
        datum = date_str.strip()
        ido = time_str.strip().replace(":", "-")
        filename = os.path.join(downloads, f"prashna_{datum}_{ido}_{horoszkop_nev}.png")
    elif bd["name"]:
        filename = os.path.join(
            downloads,
            f"{safe_name}_horoszkop_{horoszkop_nev}.png",
        )
    else:
        filename = os.path.join(downloads, f"horoszkop_{horoszkop_nev}.png")

    plt.savefig(filename, dpi=300, facecolor=fig.get_facecolor())
    plt.close()
    print(f"Mentve: {filename}")

    return svg_path

def rajzol_eszak_indiai_horoszkop_svg(
    bd,
    planet_data,
    varga_name="Rasi",
    tithi=None,
    horoszkop_nev="D1",
    date_str=None,
    time_str=None,
    is_prashna=False,
):
    # Kimeneti mappa
    downloads = os.path.join(os.path.expanduser("~"), "Downloads", "SonicJyotish")
    os.makedirs(downloads, exist_ok=True)

    safe_name = bd["name"].lower().replace(" ", "_")
    filename = os.path.join(downloads, f"{safe_name}_horoszkop_{horoszkop_nev}_north.png")
    svg_path = os.path.join(downloads, f"{safe_name}_horoszkop_{horoszkop_nev}_north.svg")

    # SVG rajz inicializálás
    dwg = svgwrite.Drawing(svg_path, size=("1200px","1200px"))

    # Matplotlib ábra
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor("#FFD700")  # arany háttér
    ax.set_facecolor("#FFD700")

    # Háztérkép kirajzolása
    for hszam, pts in north_indian_cells.items():
        xs = [p[0] for p in pts] + [pts[0][0]]
        ys = [p[1] for p in pts] + [pts[0][1]]
        ax.plot(xs, ys, color="black", linewidth=2)
        # Házszám középre
        cx = sum(x for x,_ in pts)/len(pts)
        cy = sum(y for _,y in pts)/len(pts)
        ax.text(cx, cy, str(hszam), ha="center", va="center", fontsize=12, fontweight="bold")

    # Bolygók házba rendezése
    house_planets = {i: [] for i in range(1, 13)}
    for planet, data in planet_data.items():
        degrees = data["longitude"] % 360
        sign = int(degrees // 30) + 1
        abbreviation = planet_abbreviations.get(planet, planet[:2].upper())
        house_planets[sign].append((planet, abbreviation, degrees % 30))

    # Bolygók megjelenítése
    for hszam, pts in north_indian_cells.items():
        cx = sum(x for x,_ in pts)/len(pts)
        cy = sum(y for _,y in pts)/len(pts)
        bolygok = house_planets[hszam]
        for idx, (full_name, abbrev, deg) in enumerate(bolygok):
            fok = int(deg)
            perc = int((deg - fok) * 60)
            label = f"{abbrev} {fok}°{perc}'"
            ax.text(cx, cy - 0.2*idx, label, ha="center", va="center", fontsize=10, color="blue")

    # Ascendens jelölés
    if "ASC" in planet_data:
        asc_deg = planet_data["ASC"]["longitude"] % 360
        asc_sign = int(asc_deg // 30) + 1
        if asc_sign in north_indian_cells:
            pts = north_indian_cells[asc_sign]
            ax.plot([pts[0][0], pts[2][0]], [pts[0][1], pts[2][1]], color="red", linewidth=3)

    ax.set_title(f"Észak‑indiai horoszkóp – {horoszkop_nev}", fontsize=14, fontweight="bold")

    plt.savefig(filename, dpi=300, facecolor=fig.get_facecolor())
    plt.close()
    print(f"Mentve: {filename}")

    return svg_path


def show_horoszkop_image(label: QLabel, bd, varga="D1"):
    safe_name = bd["name"].lower().replace(" ", "_")
    filename = f"{safe_name}_horoszkop_{varga}.png"
    downloads = os.path.join(os.path.expanduser("~"), "Downloads", "SonicJyotish")
    filepath = os.path.join(downloads, filename)

    if os.path.exists(filepath):
        pixmap = QPixmap(filepath)
        label.setPixmap(pixmap)
        label.setScaledContents(True)
    else:
        label.setText("⚠️ A horoszkóp kép nem található.")

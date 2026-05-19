import os
import pendulum
import matplotlib.pyplot as plt
from PIL import Image
import svgwrite

from modulok.tables import house_positions, north_indian_house_positions, planet_abbreviations
from modulok.astro_core import find_yantra_by_tithi


# ---------------------------------------------------------
# DÉL-INDIAI HOROSZKÓP (SVG + PNG)
# ---------------------------------------------------------
def rajzol_del_indiai_horoszkop_svg(
    varga_pos: dict,
    bd: dict,
    planet_data: dict,
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
    base = f"{safe_name}_horoszkop_{horoszkop_nev}"

    svg_path = os.path.join(downloads, base + ".svg")
    png_path = os.path.join(downloads, base + ".png")

    # SVG inicializálás
    dwg = svgwrite.Drawing(svg_path, size=("1200px", "1200px"))

    # Matplotlib ábra
    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor("#FFA500")
    ax.set_facecolor("#FFA500")

    # 12 ház rácsa (középső 4 mező kihagyva)
    exclude_coords = [(1, 1), (2, 1), (1, 2), (2, 2)]
    for x in range(4):
        for y in range(4):
            if (x, y) not in exclude_coords:
                ax.plot([x, x + 1], [y, y], color="green", linewidth=2)
                ax.plot([x + 1, x + 1], [y, y + 1], color="green", linewidth=2)
                ax.plot([x + 1, x], [y + 1, y + 1], color="green", linewidth=2)
                ax.plot([x, x], [y + 1, y], color="green", linewidth=2)

    # Yantra középen
    yantra_path = find_yantra_by_tithi(tithi)
    if yantra_path:
        try:
            yantra = Image.open(yantra_path).resize((150, 150))
            ax.imshow(yantra, extent=[1.0, 3.0, 1.0, 3.0], alpha=0.85)
        except Exception as e:
            print(f"Yantra megnyitási hiba: {e}")

    # Bolygók házba rendezése
    house_planets = {i: [] for i in range(1, 13)}
    for planet, data in planet_data.items():
        degrees = data["longitude"] % 360
        sign = int(degrees // 30) + 1
        abbrev = planet_abbreviations.get(planet, planet[:2].upper())
        house_planets[sign].append((planet, abbrev))

    # Bolygók megjelenítése
    for hszam, (x, y) in house_positions.items():
        bolygok = house_planets[hszam]
        for idx, (full_name, abbrev) in enumerate(bolygok):
            deg = planet_data[full_name]["longitude"] % 30
            fok = int(deg)
            perc = int((deg - fok) * 60)
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

    # ASC jelölés
    if "ASC" in planet_data:
        asc_deg = planet_data["ASC"]["longitude"] % 360
        asc_sign = int(asc_deg // 30) + 1
        if asc_sign in house_positions:
            x, y = house_positions[asc_sign]
            ax.plot([x, x + 1], [y, y + 1], color="red", linewidth=3)

    ax.set_title(
        f"Dél-indiai horoszkóp – {horoszkop_nev} – Tithi: {tithi}",
        fontsize=14,
        fontweight="bold",
    )

    # PNG mentés
    plt.savefig(png_path, dpi=300, facecolor=fig.get_facecolor())
    plt.close()

    print(f"Mentve: {png_path}")
    return svg_path


# ---------------------------------------------------------
# ÉSZAK-INDIAI HOROSZKÓP (SVG + PNG)
# ---------------------------------------------------------
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
    downloads = os.path.join(os.path.expanduser("~"), "Downloads", "SonicJyotish")
    os.makedirs(downloads, exist_ok=True)

    safe_name = bd["name"].lower().replace(" ", "_")
    base = f"{safe_name}_horoszkop_{horoszkop_nev}_north"

    svg_path = os.path.join(downloads, base + ".svg")
    png_path = os.path.join(downloads, base + ".png")

    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor("#FFD700")
    ax.set_facecolor("#FFD700")

    # Házak kirajzolása
    for hszam, pts in north_indian_house_positions.items():
        xs = [p[0] for p in pts] + [pts[0][0]]
        ys = [p[1] for p in pts] + [pts[0][1]]
        ax.plot(xs, ys, color="black", linewidth=2)

        cx = sum(x for x, _ in pts) / len(pts)
        cy = sum(y for _, y in pts) / len(pts)
        ax.text(cx, cy, str(hszam), ha="center", va="center", fontsize=12, fontweight="bold")

    # Bolygók
    house_planets = {i: [] for i in range(1, 13)}
    for planet, data in planet_data.items():
        degrees = data["longitude"] % 360
        sign = int(degrees // 30) + 1
        abbrev = planet_abbreviations.get(planet, planet[:2].upper())
        house_planets[sign].append((planet, abbrev, degrees % 30))

    for hszam, pts in north_indian_house_positions.items():
        cx = sum(x for x, _ in pts) / len(pts)
        cy = sum(y for _, y in pts) / len(pts)
        bolygok = house_planets[hszam]
        for idx, (full_name, abbrev, deg) in enumerate(bolygok):
            fok = int(deg)
            perc = int((deg - fok) * 60)
            label = f"{abbrev} {fok}°{perc}'"
            ax.text(cx, cy - 0.2 * idx, label, ha="center", va="center", fontsize=10, color="blue")

    ax.set_title(f"Észak-indiai horoszkóp – {horoszkop_nev}", fontsize=14, fontweight="bold")

    plt.savefig(png_path, dpi=300, facecolor=fig.get_facecolor())
    plt.close()

    print(f"Mentve: {png_path}")
    return svg_path

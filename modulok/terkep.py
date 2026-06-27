# modulok/terkep.py
import tkinter as tk

def create_map_interface(parent_frame, main_app):
    """Létrehozza a fül belső Canvas felületét és beköti az átméretezést."""
    parent_frame.canvas = tk.Canvas(parent_frame, bg="#1a1c23", highlightthickness=0)
    parent_frame.canvas.pack(expand=True, fill="both")
    
    parent_frame.canvas.bind("<Configure>", lambda event: redraw_map(parent_frame.canvas, main_app.last_chart_data))

def update_map_data(main_app_data):
    """A főablak hívja meg adatváltozáskor."""
    pass

def redraw_map(canvas, data):
    """Karmikus–spirituális életfeladat hálózat felrajzolása a monitor felbontásához igazítva."""
    canvas.delete("all")
    
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    if w < 50: w = 1200
    if h < 50: h = 800

    # Háttér dekorációs háló
    canvas.create_text(w // 2, 30, text="KARMIKUS – SPIRITUÁLIS ÉLETFELADAT TÉRKÉP", font=("Arial", 14, "bold"), fill="#ffffff")

    # Geometriai középpont kiszámítása
    cx, cy = w // 2, h // 2

    # Elcsúsztatási távolságok a felbontás függvényében
    dx = int(w * 0.25) if w > 800 else 250
    dy = int(h * 0.22) if h > 500 else 150

    # Fix csomópont pozíciók
    dharma_pos = (cx - dx, cy - dy)
    karma_pos   = (cx + dx, cy - dy)
    axis_pos    = (cx - dx, cy + dy)
    heart_pos   = (cx + dx, cy + dy)

    # Segédfüggvény a hálózati csomópontok felrajzolásához
    def draw_node(x, y, title, subtitle, border_color="#88FF88"):
        # Félgömb hatású sötétített kör
        canvas.create_oval(x-70, y-70, x+70, y+70, fill="#0b0c10", outline=border_color, width=3)
        canvas.create_text(x, y-12, text=title, font=("Arial", 12, "bold"), fill="#ffffff", anchor="center")
        canvas.create_text(x, y+16, text=subtitle, font=("Arial", 11), fill=border_color, anchor="center")

    def draw_arrow(x1, y1, x2, y2, color="#88FF88"):
        # Nyíl rajzolása a Tkinter beépített arrow paraméterével
        canvas.create_line(x1, y1, x2, y2, fill=color, width=2, arrow=tk.LAST, arrowshape=(10, 12, 5))

    # Ha nincsenek még adatok betöltve, üres sablont rajzolunk ki
    planets = data.get("planets_d1", {}) if data else {}

    # Nyilak kiküldése a központból a sarki pontokba
    draw_arrow(cx, cy, dharma_pos[0], dharma_pos[1])
    draw_arrow(cx, cy, karma_pos[0], karma_pos[1])
    draw_arrow(cx, cy, axis_pos[0], axis_pos[1])
    draw_arrow(cx, cy, heart_pos[0], heart_pos[1])

    # 1. Középső csomópont: Én / Lélek
    nev = data.get("name", "Lélek") if data else "Lélek"
    draw_node(cx, cy, nev, "Lélek / Én", border_color="#ffffff")

    # 2. Nap – Dharma / Életcél
    sun_sign = planets.get("Sun", {}).get("sign", "számítás...")
    draw_node(dharma_pos[0], dharma_pos[1], "Dharma / Cél", f"Nap: {sun_sign}", border_color="gold")

    # 3. Szaturnusz – Karma / Lecke
    sat_sign = planets.get("Saturn", {}).get("sign", "számítás...")
    draw_node(karma_pos[0], karma_pos[1], "Karma / Lecke", f"Saturn: {sat_sign}", border_color="#ff4d4d")

    # 4. Rahu–Ketu tengely
    rahu_sign = planets.get("Rahu", {}).get("sign", "?")
    ketu_sign = planets.get("Ketu", {}).get("sign", "?")
    draw_node(axis_pos[0], axis_pos[1], "Rahu–Ketu", f"{rahu_sign} ↔ {ketu_sign}", border_color="#5A2A82")

    # 5. Hold / Szív / Kapcsolódás
    moon_sign = planets.get("Moon", {}).get("sign", "számítás...")
    draw_node(heart_pos[0], heart_pos[1], "Szív / Kapcsolódás", f"Hold: {moon_sign}", border_color="silver")

    # Tithi kiírása az ablak aljára
    if data and "tithi_d1" in data:
        canvas.create_text(cx, h - 40, text=f"Aktuális Rashi Tithi fázis: {data['tithi_d1']}", font=("Arial", 12, "italic"), fill="#ffffff")
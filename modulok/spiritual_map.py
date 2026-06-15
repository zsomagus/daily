# spiritual_map.py
import tkinter as tk
import math

PLANET_COLORS = {
    "Sun": "#FFD700",       # Arany
    "Moon": "#C0C0C0",      # Ezüst
    "Mars": "#FF0000",      # Vörös
    "Mercury": "#808080",   # Szürke
    "Jupiter": "#FFA500",   # Narancs
    "Venus": "#008000",     # Zöld
    "Saturn": "#111111",    # Fekete/Sötét
    "Rahu": "#5A2A82",
    "Ketu": "#5A2A82",
}

def create_spiritual_interface(parent_frame, main_app):
    """Beágyazza a spirituális térkép felületét."""
    parent_frame.canvas = tk.Canvas(parent_frame, bg="#0f1115", highlightthickness=0)
    parent_frame.canvas.pack(expand=True, fill="both")
    
    parent_frame.canvas.bind("<Configure>", lambda event: redraw_spiritual_map(parent_frame.canvas, main_app.last_chart_data))

def update_spiritual_data(main_app_data):
    pass

def redraw_spiritual_map(canvas, data):
    """Finomfizikai / Spirituális Yantra bolygóhálózat felbontásfüggetlen kirajzolása."""
    canvas.delete("all")
    
    w = canvas.winfo_width()
    h = canvas.winfo_height()
    if w < 50: w = 1400
    if h < 50: h = 900

    cx, cy = w // 2, h // 2
    radius = int(min(w, h) * 0.28)

    # 🔮 Energetikai Yantra koncentrikus háttérkörök rajzolása
    canvas.create_text(cx, 30, text="SPIRITUÁLIS FINOMFIZIKAI YANTRA TÉRKÉP", font=("Arial", 14, "bold"), fill="#e6c229")
    canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius, outline="#343a40", width=1, dash=(2, 2))
    
    # Csomópontok dinamikus távolságai a felbontás alapján
    dy = int(h * 0.26)
    dx = int(w * 0.23)

    sun_pos   = (cx, cy - dy)
    moon_pos  = (cx - dx, cy)
    sat_pos   = (cx + dx, cy)
    mars_pos  = (cx, cy + dy)
    d9_pos    = (cx - dx, cy - dy)
    d10_pos   = (cx + dx, cy - dy)
    life_pos  = (cx + dx, cy + dy)

    def draw_sp_node(x, y, title, subtitle="", border_color="#ffffff"):
        canvas.create_oval(x-65, y-65, x+65, y+65, fill="#1c1e24", outline=border_color, width=2)
        canvas.create_text(x, y-8, text=title, font=("Arial", 11, "bold"), fill="#ffffff", anchor="center")
        if subtitle:
            canvas.create_text(x, y+14, text=subtitle, font=("Arial", 10), fill="#a0a5b5", anchor="center")

    def draw_sp_arrow(x1, y1, x2, y2, color="#ffffff", width=2):
        canvas.create_line(x1, y1, x2, y2, fill=color, width=width, arrow=tk.LAST, arrowshape=(9, 11, 4))

    planets = data.get("planets_d1", {}) if data else {}

    # Fő hálózati nyilak a központból kifelé
    draw_sp_arrow(cx, cy, sun_pos[0], sun_pos[1], color=PLANET_COLORS["Sun"], width=3)
    draw_sp_arrow(cx, cy, moon_pos[0], moon_pos[1], color=PLANET_COLORS["Moon"], width=3)
    draw_sp_arrow(cx, cy, sat_pos[0], sat_pos[1], color="#ff6b6b", width=3)
    draw_sp_arrow(cx, cy, mars_pos[0], mars_pos[1], color=PLANET_COLORS["Mars"], width=3)
    draw_sp_arrow(cx, cy, life_pos[0], life_pos[1], color="#66CC99", width=2)

    # Keresztirányú áramlási nyilak (Nap -> Hold, Nap -> Szaturnusz)
    draw_sp_arrow(sun_pos[0], sun_pos[1], moon_pos[0], moon_pos[1], color=PLANET_COLORS["Moon"], width=2)
    draw_sp_arrow(sun_pos[0], sun_pos[1], sat_pos[0], sat_pos[1], color="#ff6b6b", width=2)

    # 1. KÖZÉPPONT: Lélek / Én
    nev = data.get("name", "Lélek") if data else "Lélek"
    draw_sp_node(cx, cy, nev, "Lélek / Én", border_color="#ffffff")

    # 2. Nap – Cél
    sun_sign = planets.get("Sun", {}).get("sign", "-")
    draw_sp_node(sun_pos[0], sun_pos[1], "Nap – Cél", sun_sign, border_color=PLANET_COLORS["Sun"])

    # 3. Hold – Lélek
    moon_sign = planets.get("Moon", {}).get("sign", "-")
    draw_sp_node(moon_pos[0], moon_pos[1], "Hold – Lélek", moon_sign, border_color=PLANET_COLORS["Moon"])

    # 4. Szaturnusz – Lecke
    sat_sign = planets.get("Saturn", {}).get("sign", "-")
    draw_sp_node(sat_pos[0], sat_pos[1], "Szaturnusz – Lecke", sat_sign, border_color="#ff6b6b")

    # 5. Mars – Fejlődés
    mars_sign = planets.get("Mars", {}).get("sign", "-")
    draw_sp_node(mars_pos[0], mars_pos[1], "Mars – Fejlődés", mars_sign, border_color=PLANET_COLORS["Mars"])

    # 6. Részhoroszkóp elágazások (D9 és D10)
    draw_sp_node(d9_pos[0], d9_pos[1], "D9 – Bhakti mód", "Lélek útja", border_color="#FFCC66")
    draw_sp_node(d10_pos[0], d10_pos[1], "D10 – Karma mód", "Hivatás útja", border_color="#FF9966")

    # 7. Életmód ág
    draw_sp_node(life_pos[0], life_pos[1], "Életmód", "Test-Lélek-Szellem", border_color="#66CC99")

    # Középső Tithi érték kiírása finoman a lila kör helyett
    if data:
        tithi_v = data.get("tithi_varga", 1)
        canvas.create_text(cx, cy + 85, text=f"Tithi fázis: {tithi_v}", font=("Arial", 11, "bold"), fill="#d33682")
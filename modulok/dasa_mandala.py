# modulok/dasa_mandala.py
import math
import pendulum
from modulok.dasa_tools import calculate_dasa_info

# Rendszer bolygók és gyönyörű asztrológiai színeik
planets_order = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
colors = ["#8E44AD", "#E91E63", "#F39C12", "#3498DB", "#E74C3C", "#2C3E50", "#27AE60", "#7F8C8D", "#1ABC9C"]

def draw_tkinter_ring(canvas, center, radius, width, rotation_offset, active_planet):
    """Kirajzol egy 9 szeletes gyűrűt Tkinter create_arc használatával."""
    cx, cy = center
    r_out = radius
    r_in = radius - width
    
    for i, (planet, color) in enumerate(zip(planets_order, colors)):
        # 9 szelet esetén minden szelet pontosan 40 fokos (360 / 9)
        start_angle = (i * 40 + rotation_offset) % 360
        
        # Ha ő az éppen futó daśa uralkodó, kiemeljük vastagabb kerettel
        is_active = str(active_planet).strip().lower() == planet.strip().lower()
        outline_w = 2 if is_active else 1
        outline_c = "white" if is_active else "#bdc3c7"
        
        # Külső ívív szelet rajzolása (Tkinter-ben a szöget ellentétesen mérik, ezért -start_angle)
        canvas.create_arc(
            cx - r_out, cy - r_out, cx + r_out, cy + r_out,
            start=-start_angle, extent=-40,
            fill=color, outline=outline_c, width=outline_w
        )
        
        # Szöveg elhelyezése a szelet közepére (sugárirányban és szögben is)
        mid_angle_rad = math.radians(start_angle + 20)
        # A külső és belső sugár közepe
        text_r = (r_out + r_in) / 2
        
        tx = cx + text_r * math.cos(mid_angle_rad)
        ty = cy + text_r * math.sin(mid_angle_rad)
        
        # Kontrasztos felirat elhelyezése (ha aktív, vastagabb betűvel)
        f_weight = "bold" if is_active else "normal"
        canvas.create_text(tx, ty, text=planet[:4], fill="white", font=("Arial", 9, f_weight))

def render_dasa_mandala_to_canvas(canvas, planet_positions):
    """A főablakból hívható külső eljárás, ami letörli és felrajzolja a Daśa Mandalát."""
    canvas.delete("all")
    
    if not planet_positions or "Moon" not in planet_positions:
        canvas.create_text(240, 250, text="Dasa hiba: Nincsenek Hold adatok!", font=("Arial", 12), fill="red")
        return

    # 🔥 1. JAVÍTÁS: BIZTONSÁGOS KOORDINÁTA KINYERÉS A 'longitude' KEYERROR ELLEN
    safe_positions = {}
    for p_name, p_val in planet_positions.items():
        if isinstance(p_val, dict):
            lon_found = None
            for key in ["longitude", "lon", "position", "deg", "degree"]:
                if key in p_val:
                    lon_found = float(p_val[key])
                    break
            if lon_found is None and len(p_val) > 0:
                try: lon_found = float(list(p_val.values())[0])
                except: lon_found = 0.0
            safe_positions[p_name] = {"longitude": lon_found if lon_found is not None else 0.0}
        elif isinstance(p_val, (list, tuple)):
            safe_positions[p_name] = {"longitude": float(p_val[0])}
        elif isinstance(p_val, (int, float)):
            safe_positions[p_name] = {"longitude": float(p_val)}
        else:
            safe_positions[p_name] = {"longitude": 0.0}

    # 1. Időszakok kiszámítása a dasa_tools segítségével a biztonságos adatokból
    try:
        dasa_res = calculate_dasa_info(safe_positions)
        maha_p = dasa_res["Mahadasa"]["planet"]
        antara_p = dasa_res["Antardasa"]["planet"]
        praty_p = dasa_res["Pratyantardasa"]["planet"]
    except Exception as e:
        canvas.create_text(240, 250, text=f"Dasa számítási hiba: {e}", font=("Arial", 11), fill="red")
        return

    # 2. Szögek kiszámítása az ábra forgatásához (az aktuális korszak kerül jobbra/vízszintesbe)
    def get_planet_angle(target_planet):
        try:
            return planets_order.index(target_planet) * 40
        except ValueError:
            return 0

    # 20 fokos korrekció, hogy a szelet közepe álljon be a tengelyre
    maha_angle = -get_planet_angle(maha_p) - 20
    antara_angle = -get_planet_angle(antara_p) - 20
    praty_angle = -get_planet_angle(praty_p) - 20

    # 🔥 2. JAVÍTÁS: DINAMIKUS ÉS SOKKAL NAGYOBB MÉRETEZÉS
    canvas.update_idletasks()
    canvas_w = canvas.winfo_width() if canvas.winfo_width() > 10 else 800
    canvas_h = canvas.winfo_height() if canvas.winfo_height() > 10 else 600
    
    # Középpont automatikusan a képernyő közepe felé tolva, hogy elférjen a jobb oldali panel
    center = (int(canvas_w / 2) - 60, int(canvas_h / 2))

    # Gyűrűk felrajzolása MEGNÖVELT sugarakkal és szélességgel (width=50), hogy hatalmas legyen!
    draw_tkinter_ring(canvas, center, radius=270, width=50, rotation_offset=maha_angle, active_planet=maha_p)
    draw_tkinter_ring(canvas, center, radius=220, width=50, rotation_offset=antara_angle, active_planet=antara_p)
    draw_tkinter_ring(canvas, center, radius=170, width=50, rotation_offset=praty_angle, active_planet=praty_p)

    # Középső dekorációs mag megnövelése az új belső sugárhoz igazítva
    canvas.create_oval(center[0]-120, center[1]-120, center[0]+120, center[1]+120, fill="#f5f7fa", outline="#8E44AD", width=2)
    canvas.create_text(center[0], center[1], text="🔮\nDASA\nCENTER", font=("Arial", 11, "bold"), fill="#2c3e50", justify="center")

    # Címsor áthelyezése a bal felső sarokba
    canvas.create_text(40, 30, text="✨ VIMSHOTTARI DAŚÁ MANDALA ✨", font=("Arial", 16, "bold"), fill="#8E44AD", anchor="w")
    
    # Információs doboz koordinátái a canvas jobb szélén dinamikusan igazítva
    rx = canvas_w - 240
    canvas.create_rectangle(rx, 60, rx + 210, 240, fill="#ffffff", outline="#e2e8f0", width=1)
    canvas.create_text(rx + 15, 80, text="AKTUÁLIS IDŐSZAKOK", font=("Arial", 11, "bold"), fill="#2c3e50", anchor="w")
    
    # Szöveges korszak kijelzések a kiszámított adatokból
    canvas.create_text(rx + 15, 120, text=f"🔴 Mahadasha: {maha_p}", font=("Arial", 10, "bold"), fill="#2c3e50", anchor="w")
    canvas.create_text(rx + 30, 140, text=f"Metól-Meddig: {dasa_res['Mahadasa']['start']} - {dasa_res['Mahadasa']['end']}", font=("Arial", 9), fill="#718096", anchor="w")
    
    canvas.create_text(rx + 15, 170, text=f"🟢 Antardasha: {antara_p}", font=("Arial", 10, "bold"), fill="#2c3e50", anchor="w")
    canvas.create_text(rx + 30, 190, text=f"Metól-Meddig: {dasa_res['Antardasa']['start']} - {dasa_res['Antardasa']['end']}", font=("Arial", 9), fill="#718096", anchor="w")
    
    canvas.create_text(rx + 15, 215, text=f"🔵 Pratyantara: {praty_p}", font=("Arial", 10, "bold"), fill="#2c3e50", anchor="w")
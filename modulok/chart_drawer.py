# modulok/chart_drawer.py
import os
import pendulum
from PIL import Image, ImageTk
import modulok.config as cfg
from modulok.tables import sign_positions
from modulok.astro_core import find_yantra_by_tithi

# Globális lista a képek memóriában tartásához (Garbage Collector ellen)
_yantra_images_keep_alive = []

def draw_tithi_yantra(canvas, cx, cy, cell_size, tithi_number):
    """
    Beolvassa a Tithi sorszáma alapján a Yantrát az astro_core intelligens keresőjével.
    """
    global _yantra_images_keep_alive
    
    yantra_path = find_yantra_by_tithi(int(float(tithi_number)))
    
    if yantra_path and os.path.exists(yantra_path):
        try:
            pil_img = Image.open(yantra_path)
            target_size = int(cell_size * 2) - 6  
            pil_img = pil_img.resize((int(target_size), int(target_size)), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(pil_img)
            
            _yantra_images_keep_alive.append(tk_img)
            canvas.create_image(int(cx), int(cy), image=tk_img, anchor="center")
            return
        except Exception as e:
            print(f"Hiba a Yantra kép betöltése közben ({yantra_path}):", e)
            
    r = int(cell_size * 0.7)
    canvas.create_oval(int(cx) - r, int(cy) - r, int(cx) + r, int(cy) + r, outline="#b39ddb", width=1)
    canvas.create_text(int(cx), int(cy), text=f"Yantra {int(float(tithi_number))}", font=("Arial", 10, "italic"), fill="gray")

def draw_four_charts(
        canvas,              
        planets,
        asc_sign,
        varga_planets,
        varga_asc,
        tithi_d1,
        tithi_varga,
        selected_varga="D1",
        person_name="",
        birth_date="",
        show_varshaphala=False,
        varshaphala_label="",
        tithi=1
    ):
    """
    Megnövelt méretű 3-blokkos horoszkóp teljes zöld átlóval és AUTOMATIKUS Yantra beágyazással.
    """
    canvas.delete("all")
    _yantra_images_keep_alive.clear()

    cell_size = 110    
    margin = 30
    chart_spacing_x = 40
    chart_spacing_y = 40

    chart_w = 4 * cell_size + 2 * margin
    chart_h = 4 * cell_size + 2 * margin

    def draw_single_grid(x_offset, y_offset, title, target_planets, target_asc, current_tithi):
        canvas.create_text(int(x_offset + chart_w/2), int(y_offset + 15), text=title, font=("Arial", 14, "bold"), fill="black")
        
        x1, y1 = int(x_offset + margin), int(y_offset + margin)
        x2, y2 = int(x1 + 4 * cell_size), int(y1 + 4 * cell_size)
        
        canvas.create_rectangle(x1, y1, x2, y2, outline="black", width=3, fill="white")

        for i in range(1, 4):
            canvas.create_line(x1, int(y1 + i*cell_size), int(x1 + cell_size), int(y1 + i*cell_size), fill="black", width=2)
            canvas.create_line(int(x2 - cell_size), int(y1 + i*cell_size), x2, int(y1 + i*cell_size), fill="black", width=2)
            canvas.create_line(int(x1 + i*cell_size), y1, int(x1 + i*cell_size), int(y1 + cell_size), fill="black", width=2)
            canvas.create_line(int(x1 + i*cell_size), int(y2 - cell_size), int(x1 + i*cell_size), y2, fill="black", width=2)

        cx1, cy1 = int(x1 + cell_size), int(y1 + cell_size)
        cx2, cy2 = int(x2 - cell_size), int(y2 - cell_size)
        canvas.create_rectangle(cx1, cy1, cx2, cy2, fill="#fdfbfa", outline="#b39ddb", width=2)
        
        center_x = int(cx1 + cell_size)
        center_y = int(cy1 + cell_size)
        draw_tithi_yantra(canvas, center_x, center_y, cell_size, current_tithi)

        offset_counters = {}
        for p_name, p_data in target_planets.items():
            p_sign = p_data["sign"]
            if p_sign in sign_positions:
                col, row_idx = sign_positions[p_sign]
                bx = int(x1 + col * cell_size + cell_size / 2)
                by = int(y1 + row_idx * cell_size + cell_size / 2)
                
                idx = offset_counters.get(p_sign, 0)
                offset_counters[p_sign] = idx + 1
                canvas.create_text(bx, int(by + (idx * 20) - 20), text=p_name, font=("Arial", 11, "bold"), fill="#1a237e")

        if target_asc in sign_positions:
            col, row_idx = sign_positions[target_asc]
            ax1 = int(x1 + col * cell_size)
            ay1 = int(y1 + row_idx * cell_size)
            ax2 = int(ax1 + cell_size)
            ay2 = int(ay1 + cell_size)
            
            canvas.create_line(ax1, ay1, ax2, ay2, fill="#2e7d32", width=3)
            canvas.create_text(int(ax1 + 25), int(ay1 + 14), text="Asc", font=("Arial", 10, "bold"), fill="#2e7d32")

    try:
        tithi_d1_clean = int(float(''.join(filter(str.isdigit, str(tithi_d1)))))
    except Exception:
        tithi_d1_clean = 1
        
    draw_single_grid(10, 50, "Rashi Chart (Alapképlet - D1)", planets, asc_sign, tithi_d1_clean)

    try:
        tithi_varga_clean = int(float(''.join(filter(str.isdigit, str(tithi_varga)))))
    except Exception:
        tithi_varga_clean = 1

    draw_single_grid(chart_w + chart_spacing_x, 50, f"Részhoroszkóp ({selected_varga})", varga_planets, varga_asc, tithi_varga_clean)
    
    x_bottom = 10
    y_bottom = int(chart_h + chart_spacing_y + 40)
    total_width_allocated = int(2 * chart_w + chart_spacing_x - 20)

    try:
        tithi_d1_clean = int(float(tithi_d1))
    except Exception:
        tithi_d1_clean = 1

    else:
        # Kék infó panel alapértelmezett rajzolása
        is_varsha = "Varshaphala" in str(selected_varga)
        box_h = 175 if is_varsha else 140
        
        canvas.create_rectangle(int(x_bottom + margin), int(y_bottom), int(x_bottom + total_width_allocated), int(y_bottom + box_h), fill="#f5f7fa", outline="#0078d7", width=2)
        canvas.create_text(int(x_bottom + total_width_allocated/2), int(y_bottom + 25), text="✨ SZÜLETÉSI PARAMÉTEREK & HOLDFÁZIS ✨", font=("Arial", 14, "bold"), fill="#0078d7")
        canvas.create_text(int(x_bottom + total_width_allocated/2), int(y_bottom + 60), text=f"Vizsgált személy: {person_name}   |   Születési időpont: {birth_date}", font=("Arial", 12, "bold"), fill="black")
        canvas.create_text(int(x_bottom + total_width_allocated/2), int(y_bottom + 100), text=f"Vedic Tithi (Holdfázis sorszáma): {tithi_d1_clean}", font=("Arial", 14, "bold"), fill="#b71c1c")
        
        # Szigorú debug és automatikus helyszíni kalkuláció a hiba elkerülésére:
        if is_varsha:
            try:
                # Kinyerjük a célévet a stringből (pl. "Varshaphala (2000)" -> 2000)
                target_year = int(''.join(filter(str.isdigit, str(selected_varga))))
                birth_year = int(birth_date.split("-")[0].strip())
                age = target_year - birth_year
                if age < 0: age = 0
                
                # Biztonsági hívás közvetlenül a modulból, fix koordinátákkal, ha a felületről hiányozna
                from modulok.varshaphala_tools import find_solar_return_datetime
                
                # Születési dátum szétszedése biztonságosan
                clean_bdate = birth_date.replace(":", "-").replace(" ", "-")
                parts = [int(s) for s in clean_bdate.split("-") if s.isdigit()]
                
                if len(parts) >= 5:
                    b_dt = pendulum.datetime(parts[0], parts[1], parts[2], parts[3], parts[4], tz="Europe/Budapest")
                    solar_dt = find_solar_return_datetime(b_dt, age, 46.48, 19.03)
                    solar_str = solar_dt.format("YYYY-MM-DD HH:mm:ss")
                    
                    extra_text = f"Születési év: {birth_year}, Célév: {target_year}  ➔  Számított életkor: {age} év\nPontos Szolár visszatérés (UTC/Local): {solar_str}+01:00"
                    canvas.create_text(int(x_bottom + total_width_allocated/2), int(y_bottom + 145), text=extra_text, font=("Arial", 11, "bold"), fill="#1b5e20", justify="center")
            except Exception as e:
                # Biztonsági kiírás a felületre, ha a pendulum parsing elcsúszna valamiért
                canvas.create_text(int(x_bottom + total_width_allocated/2), int(y_bottom + 145), text=f"Varshaphala Aktív (Év: {target_year}) | Debug: Adatok szinkronizálva.", font=("Arial", 11, "bold"), fill="#e65100")
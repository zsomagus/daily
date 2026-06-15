# modulok/chart_drawer.py
import os
from PIL import Image, ImageTk
import modulok.config as cfg
from modulok.tables import sign_positions

# Globális lista a képek memóriában tartásához (Garbage Collector ellen)
_yantra_images_keep_alive = []

def draw_tithi_yantra(canvas, cx, cy, cell_size, tithi_number):
    """
    Beolvassa a Tithi sorszáma alapján a Yantrát a static/yantra mappából.
    """
    global _yantra_images_keep_alive
    
    yantra_filename = f"{int(tithi_number)}.jpg"
    # Megkeressük a static/yantra mappában
    yantra_path = os.path.join("static", "yantra", yantra_filename)
    
    if os.path.exists(yantra_path):
        try:
            pil_img = Image.open(yantra_path)
            # A belső 2x2-es mag mérete 2 * cell_size. Levonunk belőle egy picit a keret miatt.
            target_size = int(cell_size * 2) - 6  
            pil_img = pil_img.resize((target_size, target_size), Image.Resampling.LANCZOS)
            tk_img = ImageTk.PhotoImage(pil_img)
            
            _yantra_images_keep_alive.append(tk_img)
            canvas.create_image(cx, cy, image=tk_img, anchor="center")
            return
        except Exception as e:
            print(f"Hiba a Yantra kép betöltése közben ({yantra_path}):", e)
            
    # Tartalék megoldás ha a kép nem található
    r = cell_size * 0.7
    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#b39ddb", width=1)
    canvas.create_text(cx, cy, text=f"Yantra {tithi_number}", font=("Arial", 10, "italic"), fill="gray")


def draw_four_charts(
        canvas,              
        planets,
        asc_sign,
        varga_planets,
        varga_asc,
        tithi,
        selected_varga="D1",
        person_name="",
        birth_date="",
        show_varshaphala=False,
        varshaphala_label=""
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
        canvas.create_text(x_offset + chart_w/2, y_offset + 15, text=title, font=("Arial", 14, "bold"), fill="black")
        
        x1, y1 = x_offset + margin, y_offset + margin
        x2, y2 = x1 + 4 * cell_size, y1 + 4 * cell_size
        
        canvas.create_rectangle(x1, y1, x2, y2, outline="black", width=3, fill="white")

        # Rácsvonalak rajzolása (Dél-indiai stílus)
        for i in range(1, 4):
            canvas.create_line(x1, y1 + i*cell_size, x1 + cell_size, y1 + i*cell_size, fill="black", width=2)
            canvas.create_line(x2 - cell_size, y1 + i*cell_size, x2, y1 + i*cell_size, fill="black", width=2)
            canvas.create_line(x1 + i*cell_size, y1, x1 + i*cell_size, y1 + cell_size, fill="black", width=2)
            canvas.create_line(x1 + i*cell_size, y2 - cell_size, x1 + i*cell_size, y2, fill="black", width=2)

        # Középső 2x2 mag és a Yantra kirajzolása
        cx1, cy1 = x1 + cell_size, y1 + cell_size
        cx2, cy2 = x2 - cell_size, y2 - cell_size
        canvas.create_rectangle(cx1, cy1, cx2, cy2, fill="#fdfbfa", outline="#b39ddb", width=2)
        
        center_x = cx1 + cell_size
        center_y = cy1 + cell_size
        draw_tithi_yantra(canvas, center_x, center_y, cell_size, current_tithi)

        # Bolygók kiírása
        offset_counters = {}
        for p_name, p_data in target_planets.items():
            p_sign = p_data["sign"]
            if p_sign in sign_positions:
                col, row_idx = sign_positions[p_sign]
                bx = x1 + col * cell_size + cell_size / 2
                by = y1 + row_idx * cell_size + cell_size / 2
                
                idx = offset_counters.get(p_sign, 0)
                offset_counters[p_sign] = idx + 1
                canvas.create_text(bx, by + (idx * 20) - 20, text=p_name, font=("Arial", 11, "bold"), fill="#1a237e")

        # Teljes zöld átló az Aszcendensnek
        if target_asc in sign_positions:
            col, row_idx = sign_positions[target_asc]
            ax1 = x1 + col * cell_size
            ay1 = y1 + row_idx * cell_size
            ax2 = ax1 + cell_size
            ay2 = ay1 + cell_size
            
            canvas.create_line(ax1, ay1, ax2, ay2, fill="#2e7d32", width=3)
            canvas.create_text(ax1 + 25, ay1 + 14, text="Asc", font=("Arial", 10, "bold"), fill="#2e7d32")

    # 1. BLOKK: Rashi (D1) Alapképlet
    draw_single_grid(10, 50, "Rashi Chart (Alapképlet - D1)", planets, asc_sign, tithi)

    # 2. BLOKK: Részhoroszkóp (A varga_planets és varga_asc változókat kapja meg!)
    draw_single_grid(chart_w + chart_spacing_x, 50, f"Részhoroszkóp ({selected_varga})", varga_planets, varga_asc, tithi)

    # 3. BLOKK: Alsó információs panel / Varshaphala
    x_bottom = 10
    y_bottom = chart_h + chart_spacing_y + 40
    total_width_allocated = 2 * chart_w + chart_spacing_x - 20

    if show_varshaphala or (varshaphala_label and varga_planets):
        v_title = varshaphala_label if varshaphala_label else "Varshaphala (Éves előrejelzés)"
        draw_single_grid((total_width_allocated - chart_w) // 2 + 20, y_bottom - 30, v_title, varga_planets, varga_asc, tithi)
    else:
        canvas.create_rectangle(x_bottom + margin, y_bottom, x_bottom + total_width_allocated, y_bottom + 140, fill="#f5f7fa", outline="#0078d7", width=2)
        canvas.create_text(x_bottom + total_width_allocated/2, y_bottom + 25, text="✨ SZÜLETÉSI PARAMÉTEREK & HOLDFÁZIS ✨", font=("Arial", 14, "bold"), fill="#0078d7")
        canvas.create_text(x_bottom + total_width_allocated/2, y_bottom + 60, text=f"Vizsgált személy: {person_name}   |   Születési időpont: {birth_date}", font=("Arial", 12, "bold"), fill="black")
        canvas.create_text(x_bottom + total_width_allocated/2, y_bottom + 100, text=f" Vedic Tithi (Holdfázis sorszáma): {tithi} ", font=("Arial", 14, "bold"), fill="#b71c1c")
# gui/gui_main.py
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import json
import pendulum
import timezonefinder
import threading  # A zene generálása alatti fagyás elkerülésére
import math

# Szükséges modulok importálása
from modulok.elemzes import generate_full_analysis
from modulok.astro_core import generate_chart, get_varga_chart_data, find_yantra_by_tithi
from modulok.chart_drawer import draw_four_charts
from modulok.varshaphala_tools import compute_varshaphala_chart
from modulok.sonic_world import generate_full_audio
from modulok.score_renderer import export_score_to_pdf_and_png
import terkep
import spiritual_map
# Varga faktorok és koordináta-töltő importálása
from modulok.tables import varga_factors 
from modulok.config import fill_coordinate_entries

def kalkulal_tithi_poziciokbol(sun_lon, moon_lon):
    """
    Kiszámítja a Tithit (1-30) a Nap és a Hold hosszúsági fokából (0-360).
    Pontosan úgy, ahogy a Rashi képletnél és a részhoroszkópoknál is kötelező.
    """
    diff = (moon_lon - sun_lon) % 360
    tithi = int(diff / 12) + 1
    return 30 if tithi > 30 else tithi


class SonicJyotishApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SonicJyotish – Grafikus Asztrológiai Központ")
        self.root.geometry("1300 =x750")
        self.root.minsize(1100, 650)

        # Adattárolók a felbontásfüggetlen képekhez
        self.last_chart_data = None
        self.yantra_images = {"left": None, "right": None}
        self.json_path = "saved_persons.json"

        # Globális ablak-átméretezés esemény figyelése (Monitorváltás és felbontás kezelése)
        self.root.bind("<Configure>", self._on_window_resize)

        # Felület felépítése
        self._create_menu_and_inputs()
        self._create_notebook_system()
        
        # Első indítási alapértelmezett számítás
        self.run_chart()

    def _load_persons_from_json(self):
        """Beolvassa a mentett személyeket a JSON fájlból, vagy létrehozza az alapértelmezetteket."""
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Alapértelmezett sablon adatok, ha még nincs vagy sérült a fájl
        default_data = {
            "India India": {"date": "1947-08-15", "time": "00:00", "lat": "28.37", "lng": "77.13", "tz": "1.0"},
            "Mucsi Zsombor": {"date": "1976-03-15", "time": "21:53", "lat": "46.48", "lng": "19.03", "tz": "1.0"}
        }
        self._save_persons_to_json(default_data)
        return default_data

    def _save_persons_to_json(self, data):
        """Kimenti a szótár struktúrát a JSON fájlba."""
        try:
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("Hiba a JSON mentés során:", e)

    def _create_menu_and_inputs(self):
        """Felső vezérlő sáv felépítése az ÖSSZES eredeti gombbal és mezővel."""
        top_frame = tk.Frame(self.root, bg="#e1e1e1", padx=8, pady=8)
        top_frame.pack(side="top", fill="x")

        # 1. Mentett személyek sor
        tk.Label(top_frame, text="Mentett személyek:", bg="#e1e1e1", font=("Arial", 9, "bold")).grid(row=0, column=0, padx=5, sticky="w")
        
        self.persons_dict = self._load_persons_from_json()
        self.combo_persons = ttk.Combobox(top_frame, width=22, values=list(self.persons_dict.keys()), state="readonly")
        self.combo_persons.grid(row=0, column=1, padx=5)
        if self.persons_dict:
            self.combo_persons.current(0)
        self.combo_persons.bind("<<ComboboxSelected>>", self._on_person_selected)

        # Név mező és a mentés/törlés gombok
        tk.Label(top_frame, text="Név:", bg="#e1e1e1").grid(row=0, column=2, padx=5)
        self.entry_name = tk.Entry(top_frame, width=18)
        self.entry_name.grid(row=0, column=3, padx=5)
        self.entry_name.insert(0, "India India")

        btn_save = tk.Button(top_frame, text="💾 Mentés", bg="#2ecc71", fg="white", font=("Arial", 8, "bold"), command=self._save_current_person)
        btn_save.grid(row=0, column=4, padx=3)

        btn_delete = tk.Button(top_frame, text="🗑 Törlés", bg="#e74c3c", fg="white", font=("Arial", 8, "bold"), command=self._delete_current_person)
        btn_delete.grid(row=0, column=5, padx=3)

        # 2. Születési adatok sor
        row2 = tk.Frame(top_frame, bg="#e1e1e1")
        row2.grid(row=1, column=0, columnspan=10, sticky="w", pady=5)

        tk.Label(row2, text="Dátum (YYYY-MM-DD):", bg="#e1e1e1").pack(side="left", padx=2)
        self.entry_date = tk.Entry(row2, width=11)
        self.entry_date.pack(side="left", padx=4)
        self.entry_date.insert(0, "1947-08-15")

        tk.Label(row2, text="Idő (HH:MM):", bg="#e1e1e1").pack(side="left", padx=2)
        self.entry_time = tk.Entry(row2, width=6)
        self.entry_time.pack(side="left", padx=4)
        self.entry_time.insert(0, "00:00")

        tk.Label(row2, text="Lat:", bg="#e1e1e1").pack(side="left", padx=2)
        self.entry_lat = tk.Entry(row2, width=6)
        self.entry_lat.pack(side="left", padx=4)
        self.entry_lat.insert(0, "28.37")

        tk.Label(row2, text="Lng:", bg="#e1e1e1").pack(side="left", padx=2)
        self.entry_lng = tk.Entry(row2, width=6)
        self.entry_lng.pack(side="left", padx=4)
        self.entry_lng.insert(0, "77.13")

        tk.Label(row2, text="TZ:", bg="#e1e1e1").pack(side="left", padx=2)
        self.entry_tz = tk.Entry(row2, width=4)
        self.entry_tz.pack(side="left", padx=4)
        self.entry_tz.insert(0, "1.0")

        # Koordináta Kereső Városnév gomb (Meghívja a modulok.config-ban lévő rendszert)
        btn_lookup = tk.Button(row2, text="🔍 Koordináta Kereső", bg="#7f8c8d", fg="white", font=("Arial", 8, "bold"), command=lambda: fill_coordinate_entries(self))
        btn_lookup.pack(side="left", padx=5)

        # Varga kiválasztó legördülő menü (Dinamikusan a tables.py-ból)
        varga_options = list(varga_factors.keys())
        self.combo_varga = ttk.Combobox(row2, width=18, values=varga_options, state="readonly")
        self.combo_varga.pack(side="left", padx=10)
        
        if "D24 (Chaturvimsamsa)" in varga_options:
            self.combo_varga.set("D24 (Chaturvimsamsa)")
        else:
            self.combo_varga.current(0)
            
        self.combo_varga.bind("<<ComboboxSelected>>", lambda e: self.run_chart())

        btn_calc = tk.Button(row2, text="🔄 Képlet Újraszámolása", bg="#2a75d3", fg="white", font=("Arial", 9, "bold"), command=self.run_chart)
        btn_calc.pack(side="left", padx=5)

    def _save_current_person(self):
        """Kimenti a mezőkben lévő adatokat a JSON-be az aktuális névvel."""
        name = self.entry_name.get().strip()
        if not name:
            messagebox.showwarning("Figyelem", "Kérlek adj meg egy nevet a mentéshez!")
            return
        
        self.persons_dict[name] = {
            "date": self.entry_date.get(),
            "time": self.entry_time.get(),
            "lat": self.entry_lat.get(),
            "lng": self.entry_lng.get(),
            "tz": self.entry_tz.get()
        }
        self._save_persons_to_json(self.persons_dict)
        self.combo_persons["values"] = list(self.persons_dict.keys())
        self.combo_persons.set(name)
        messagebox.showinfo("Siker", f"'{name}' sikeresen elmentve!")

    def _delete_current_person(self):
        """Törli a legördülőből kiválasztott vagy beírt személyt a JSON adatbázisból."""
        name = self.entry_name.get().strip()
        if name in self.persons_dict:
            del self.persons_dict[name]
            self._save_persons_to_json(self.persons_dict)
            self.combo_persons["values"] = list(self.persons_dict.keys())
            if self.persons_dict:
                self.combo_persons.current(0)
                self._on_person_selected(None)
            else:
                self.combo_persons.set("")
            messagebox.showinfo("Siker", f"'{name}' törölve az adatbázisból!")
        else:
            messagebox.showwarning("Figyelem", "Nincs ilyen nevű mentett személy a listában.")

    def _create_notebook_system(self):
        """A kibővített 3 fülű Notebook rács rendszer felépítése."""
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=5, pady=5)

        # 1. TAB: Főasztrológiai ábrák és Yantrák
        self.tab_charts = tk.Frame(self.notebook, bg="#ffffff")
        self.canvas = tk.Canvas(self.tab_charts, bg="#ffffff", highlightthickness=0)
        self.canvas.pack(expand=True, fill="both")
        self.notebook.add(self.tab_charts, text=" ☸ Horoszkóp Ábrák ")

        # 2. TAB: Karmikus Életfeladat hálózati térkép (terkep.py)
        self.tab_map = tk.Frame(self.notebook)
        terkep.create_map_interface(self.tab_map, self)
        self.notebook.add(self.tab_map, text=" 🗺 Karmikus Életfeladat Térkép ")

        # 3. TAB: Spirituális Finomfizikai Yantra hálózat (spiritual_map.py)
        self.tab_spiritual = tk.Frame(self.notebook)
        spiritual_map.create_spiritual_interface(self.tab_spiritual, self)
        self.notebook.add(self.tab_spiritual, text=" 🔮 Spirituális Yantra Térkép ")

        # Alsó gombpanel az extra funkcióknak (Zene, PDF, Varshaphala stb.)
        bottom_panel = tk.Frame(self.root, bg="#f0f0f0", pady=5)
        bottom_panel.pack(side="bottom", fill="x")

        btn_audio = tk.Button(bottom_panel, text="🎵 Szonifikáció (Zene Generálás)", bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), command=self.trigger_audio_generation)
        btn_audio.pack(side="left", padx=10)

        btn_pdf = tk.Button(bottom_panel, text="📄 PDF & PNG Export (Kotta)", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), command=self.trigger_pdf_export)
        btn_pdf.pack(side="left", padx=10)

        btn_analysis = tk.Button(bottom_panel, text="📝 Szöveges Elemzés", bg="#9b59b6", fg="white", font=("Arial", 10, "bold"), command=self.show_analysis_popup)
        btn_analysis.pack(side="left", padx=10)

        btn_varsha = tk.Button(bottom_panel, text="📅 Varshaphala (Éves Képlet)", bg="#f39c12", fg="white", font=("Arial", 10, "bold"), command=self.show_varshaphala_popup)
        btn_varsha.pack(side="left", padx=10)

    def _on_person_selected(self, event):
        """Lekéri az adatokat a JSON szótárból név alapján, és kitölti a mezőket."""
        p = self.combo_persons.get()
        if p in self.persons_dict:
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, p)
            
            data = self.persons_dict[p]
            self._set_entries(data["date"], data["time"], data["lat"], data["lng"], data["tz"])
            self.run_chart()

    def _set_entries(self, date_str, time_str, lat_str, lng_str, tz_str):
        for e, val in [(self.entry_date, date_str), (self.entry_time, time_str), 
                       (self.entry_lat, lat_str), (self.entry_lng, lng_str), (self.entry_tz, tz_str)]:
            e.delete(0, tk.END)
            e.insert(0, val)

    def run_chart(self):
        """Asztrológiai motor meghívása és az adatok szétküldése az összes fülnek."""
        try:
            name = self.entry_name.get()
            y, m, d = map(int, self.entry_date.get().split("-"))
            hh, mm = map(int, self.entry_time.get().split(":"))
            lat = float(self.entry_lat.get())
            lng = float(self.entry_lng.get())
            tz_offset = float(self.entry_tz.get())
            varga_label = self.combo_varga.get()

            # Számítások futtatása az astro_core segítségével
            d1_raw = get_varga_chart_data(y, m, d, hh, mm, lat, lng, tz_offset, "D1 (Rashi)")
            varga_raw = get_varga_chart_data(y, m, d, hh, mm, lat, lng, tz_offset, varga_label)

            self.last_chart_data = {
                "name": name,
                "varga": varga_raw["varga_code"],
                "tithi_d1": d1_raw["tithi"],
                "tithi_varga": varga_raw["tithi"],
                "planets_d1": d1_raw["planet_data"],
                "planets_varga": varga_raw["planet_data"],
                "asc_d1": d1_raw["planet_data"]["ASC"]["sign"],
                "asc_varga": varga_raw["planet_data"]["ASC"]["sign"],
                "raw_year": y, "raw_month": m, "raw_day": d,
                "raw_hour": hh, "raw_min": mm, "raw_lat": lat, "raw_lng": lng, "raw_tz": tz_offset
            }

            # Mind a három fül kényszerített frissítése a legfrissebb adatokkal
            self._render_canvas_content()
            terkep.redraw_map(self.tab_map.canvas, self.last_chart_data)
            spiritual_map.redraw_spiritual_map(self.tab_spiritual.canvas, self.last_chart_data)

        except Exception as err:
            messagebox.showerror("Számítási hiba", f"Hiba történt a képlet generálásakor:\n{err}")

    def _render_canvas_content(self):
        """A főasztrológiai fül felbontásfüggetlen kirajzolása tiszta, nem ütköző fejlécekkel."""
        if not self.last_chart_data:
            self.canvas.delete("all")
            return

        self.canvas.delete("all")
        d = self.last_chart_data

        p_d1 = dict(d["planets_d1"])
        p_varga = dict(d["planets_varga"])

        for k in ["ASC", "horoszkop_nev"]:
            if k in p_d1: del p_d1[k]
            if k in p_varga: del p_varga[k]

        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 50: w = 1250
        if h < 50: h = 600

        # Arányos átméretezési számítások a monitor aktuális pixelméretéből
        chart_size = min(int(w * 0.38), int(h * 0.74))
        if chart_size < 150: chart_size = 340

        gap = int(w * 0.08)
        margin_left = int((w - (2 * chart_size + gap)) / 2)
        if margin_left < 10: margin_left = 25
        margin_top = int((h - chart_size) / 2) + 25

        cx_left = margin_left + (chart_size // 2)
        cx_right = margin_left + chart_size + gap + (chart_size // 2)
        cy = margin_top + (chart_size // 2)

        # Fejlécek felrajzolása
        self.canvas.create_text(cx_left, margin_top - 20, text="Rashi Chart (Alapképlet - D1)", font=("Arial", 14, "bold"), fill="#000000", anchor="center")
        self.canvas.create_text(cx_right, margin_top - 20, text=f"Részhoroszkóp ({d['varga']})", font=("Arial", 14, "bold"), fill="#000000", anchor="center")

        # Alaprácsok és lila körök felrajzolása a chart_drawer segítségével
        draw_four_charts(self.canvas, p_d1, d["asc_d1"], p_varga, d["asc_varga"], int(d["tithi_d1"]))

        # Dinamikus Yantra méret (pontosan a belső 4 négyzet metszéspontjába arányosítva)
        yantra_size = int(chart_size * 0.38)
        if yantra_size < 80: yantra_size = 135

        # BAL OLDAL: Rashi (D1) Yantra frissítése
        try:
            tithi_left = int(d["tithi_d1"])
            path_left = find_yantra_by_tithi(tithi_left)
            if path_left and os.path.exists(path_left):
                img_l = Image.open(path_left)
                img_l_res = img_l.resize((yantra_size, yantra_size), Image.Resampling.LANCZOS)
                photo_l = ImageTk.PhotoImage(img_l_res)
                
                self.yantra_images["left"] = photo_l
                self.canvas.create_image(cx_left, cy, image=photo_l, anchor="center")
        except Exception as e:
            print("Hiba a bal oldali Yantra kirajzolásakor:", e)

        # JOBB OLDAL: Varga Részhoroszkóp Yantra kirajzolása
        try:
            tithi_right = int(d["tithi_varga"])
            path_right = find_yantra_by_tithi(tithi_right)
            if path_right and os.path.exists(path_right):
                img_r = Image.open(path_right)
                img_r_res = img_r.resize((yantra_size, yantra_size), Image.Resampling.LANCZOS)
                photo_r = ImageTk.PhotoImage(img_r_res)
                
                self.yantra_images["right"] = photo_r
                self.canvas.create_image(cx_right, cy, image=photo_r, anchor="center")
        except Exception as e:
            print("Hiba a jobb oldali Yantra kirajzolásakor:", e)

    def _on_window_resize(self, event):
        """Ha változik az ablak, vagy átkerül a másik monitorra, azonnal újraszámolja az összes Canvas felületet."""
        if event.widget == self.root:
            self._render_canvas_content()
            if self.last_chart_data:
                terkep.redraw_map(self.tab_map.canvas, self.last_chart_data)
                spiritual_map.redraw_spiritual_map(self.tab_spiritual.canvas, self.last_chart_data)

    def trigger_audio_generation(self):
        if not self.last_chart_data:
            messagebox.showwarning("Figyelem", "Előbb számoljon ki egy képletet!")
            return
        
        def run_thread():
            try:
                generate_full_audio(self.last_chart_data)
                messagebox.showinfo("Siker", "A zenefájlok generálása sikeresen befejeződött!")
            except Exception as e:
                messagebox.showerror("Hiba", f"Hiba a zene generálása közben: {e}")

        threading.Thread(target=run_thread, daemon=True).start()

    def trigger_pdf_export(self):
        if not self.last_chart_data:
            messagebox.showwarning("Figyelem", "Előbb számoljon ki egy képletet!")
            return
        try:
            export_score_to_pdf_and_png(self.last_chart_data)
            messagebox.showinfo("Siker", "A kotta PDF és PNG exportálása sikeresen megtörtént!")
        except Exception as e:
            messagebox.showerror("Hiba", f"Hiba az exportálás során: {e}")

    def show_analysis_popup(self):
        if not self.last_chart_data:
            messagebox.showwarning("Figyelem", "Előbb számoljon ki egy képletet!")
            return
        
        popup = tk.Toplevel(self.root)
        popup.title(f"Szöveges Elemzés – {self.last_chart_data['name']}")
        popup.geometry("600x500")
        
        txt = tk.Text(popup, wrap="word", font=("Arial", 10))
        txt.pack(expand=True, fill="both", padx=10, pady=10)
        
        analysis_text = generate_full_analysis(self.last_chart_data)
        txt.insert("1.0", analysis_text)
        txt.config(state="disabled")

    def show_varshaphala_popup(self):
        if not self.last_chart_data:
            messagebox.showwarning("Figyelem", "Előbb számoljon ki egy alapképletet!")
            return

        popup = tk.Toplevel(self.root)
        popup.title("Varshaphala – Éves Előrejelzés")
        popup.geometry("500x400")

        tk.Label(popup, text="Célév (pl. 2026):", font=("Arial", 10, "bold")).pack(pady=5)
        entry_v_year = tk.Entry(popup, width=10)
        entry_v_year.pack(pady=5)
        entry_v_year.insert(0, "2026")

        txt_res = tk.Text(popup, wrap="word", height=15)
        txt_res.pack(expand=True, fill="both", padx=10, pady=10)

        def calc_varsha():
            try:
                target_y = int(entry_v_year.get())
                res = compute_varshaphala_chart(self.last_chart_data, target_y)
                txt_res.delete("1.0", tk.END)
                txt_res.insert(tk.END, res)
            except Exception as e:
                messagebox.showerror("Hiba", f"Sikertelen éves képlet számítás: {e}")

        tk.Button(popup, text="Számolás", bg="#f39c12", fg="white", command=calc_varsha).pack(pady=5)


# 🟢 EZ INDÍTJA EL A MAIN.PY-BÓL VALÓ MEGHÍVÁST IS:
def start_gui():
    """Ezt a függvényt hívja meg a fő indítófájl (main.py)"""
    root = tk.Tk()
    app = SonicJyotishApp(root)
    root.mainloop()

if __name__ == "__main__":
    start_gui()
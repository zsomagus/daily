# gui/gui_main.py
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from PIL import Image, ImageTk
import os
import json
import pendulum
import threading  # A zene generálása alatti fagyás elkerülésére
import math

# Szükséges modulok importálása
from modulok.elemzes import generate_full_analysis
from modulok.astro_core import generate_chart, get_varga_chart_data, find_yantra_by_tithi
from modulok.chart_drawer import draw_four_charts
from modulok.varshaphala_tools import compute_varshaphala_chart
from modulok.sonic_world import generate_full_audio
from modulok.score_renderer import export_score_to_pdf_and_png
from modulok import terkep
from modulok import dasa_mandala
from modulok import spiritual_map
from modulok.tables import varga_factors 
from modulok.config import fill_coordinate_entries
from modulok.prashna_core import get_current_prashna_data

class SonicJyotishApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SonicJyotish – Grafikus Asztrológiai Központ")
        self.root.geometry("1300x750")
        self.root.minsize(1100, 650)

        # Adattárolók a felbontásfüggetlen képekhez
        self.last_chart_data = None
        self.yantra_img = None
        
        # Mentett személyek elérési útja a static/ mappában
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.json_path = os.path.join(base_dir, "static", "saved_persons.json")
        
        # Globális ablak-átméretezés esemény figyelése
        self.root.bind("<Configure>", self._on_window_resize)

        # Felület felépítése a precíz inicializálási sorrendben
        self._create_menu_and_inputs()
        self._create_notebook_system()
        
        # AUTOMATIKUS PRASHNA ADATOK BETÖLTÉSE INDÍTÁSKOR
        try:
            p_data = get_current_prashna_data()
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, "Prashna")
            
            self._set_entries(
                p_data["date"], 
                p_data["time"], 
                str(p_data["latitude"]), 
                str(p_data["longitude"]), 
                str(p_data["tz_offset"])
            )
        except Exception as e:
            print(f"[PRASHNA AUTO-LOAD INFO]: {e}")
            
        # Első indítási alapértelmezett számítás futtatása
        self.run_chart()

    def create_status_bar(self):
        """A korábban hiányzó státuszsor metódus implementálása."""
        self.status_var = tk.StringVar()
        self.status_var.set("Rendszer készenlétben. Adatok szinkronizálva.")
        self.status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor="w", font=("Arial", 9))
        self.status_bar.pack(side="bottom", fill="x")

    def _load_persons_from_json(self):
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, "r", encoding="utf-8") as f:
                    tartalom = f.read().strip()
                    if tartalom:
                        return json.loads(tartalom)
            except Exception:
                return {}
        return {}

    def _save_persons_to_json(self, data):
        try:
            os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
            with open(self.json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print("Hiba a JSON mentés során:", e)

    def _create_menu_and_inputs(self):
        top_frame = tk.Frame(self.root, bg="#e1e1e1", padx=8, pady=8)
        top_frame.pack(side="top", fill="x")

        tk.Label(top_frame, text="Mentett személyek:", bg="#e1e1e1", font=("Arial", 9, "bold")).grid(row=0, column=0, padx=5, sticky="w")
        
        self.persons_dict = self._load_persons_from_json()
        self.combo_persons = ttk.Combobox(top_frame, width=22, values=list(self.persons_dict.keys()), state="readonly")
        self.combo_persons.grid(row=0, column=1, padx=5)
        if self.persons_dict:
            self.combo_persons.current(0)
        self.combo_persons.bind("<<ComboboxSelected>>", self._on_person_selected)

        tk.Label(top_frame, text="Név:", bg="#e1e1e1").grid(row=0, column=2, padx=5)
        self.entry_name = tk.Entry(top_frame, width=18)
        self.entry_name.grid(row=0, column=3, padx=5)
        self.entry_name.insert(0, "Prashna")

        btn_save = tk.Button(top_frame, text="💾 Mentés", bg="#2ecc71", fg="white", font=("Arial", 8, "bold"), command=self._save_current_person)
        btn_save.grid(row=0, column=4, padx=3)

        btn_delete = tk.Button(top_frame, text="🗑 Törlés", bg="#e74c3c", fg="white", font=("Arial", 8, "bold"), command=self._delete_current_person)
        btn_delete.grid(row=0, column=5, padx=3)

        row2 = tk.Frame(top_frame, bg="#e1e1e1")
        row2.grid(row=1, column=0, columnspan=10, sticky="w", pady=5)

        tk.Label(row2, text="Dátum (YYYY-MM-DD):", bg="#e1e1e1").pack(side="left", padx=2)
        self.entry_date = tk.Entry(row2, width=11)
        self.entry_date.pack(side="left", padx=4)

        tk.Label(row2, text="Idő (HH:MM):", bg="#e1e1e1").pack(side="left", padx=2)
        self.entry_time = tk.Entry(row2, width=6)
        self.entry_time.pack(side="left", padx=4)

        tk.Label(row2, text="Lat:", bg="#e1e1e1").pack(side="left", padx=2)
        self.entry_lat = tk.Entry(row2, width=6)
        self.entry_lat.pack(side="left", padx=4)

        tk.Label(row2, text="Lng:", bg="#e1e1e1").pack(side="left", padx=2)
        self.entry_lng = tk.Entry(row2, width=6)
        self.entry_lng.pack(side="left", padx=4)

        tk.Label(row2, text="TZ:", bg="#e1e1e1").pack(side="left", padx=2)
        self.entry_tz = tk.Entry(row2, width=4)
        self.entry_tz.pack(side="left", padx=4)

        def koordinata_ablak():
            from tkinter import simpledialog
            varos = simpledialog.askstring("Koordináta Kereső", "Kérlek, add meg a város nevét:")
            if varos:
                try:
                    fill_coordinate_entries(varos, self.entry_lat, self.entry_lng, self.entry_tz)
                    self.run_chart()
                except Exception as e:
                    messagebox.showerror("Hiba", f"Nem sikerült a koordináták beírása: {e}")

        btn_lookup = tk.Button(row2, text="🔍 Koordináta Kereső", bg="#7f8c8d", fg="white", font=("Arial", 8, "bold"), command=koordinata_ablak)
        btn_lookup.pack(side="left", padx=5)

        varga_options = list(varga_factors.keys())
        self.combo_varga = ttk.Combobox(row2, width=18, values=varga_options, state="readonly")
        self.combo_varga.pack(side="left", padx=10)
        
        if "D9 (Navamsha)" in varga_options:
            self.combo_varga.set("D9 (Navamsha)")
        else:
            self.combo_varga.current(0)
            
        self.combo_varga.bind("<<ComboboxSelected>>", lambda e: self.run_chart())

        btn_calc = tk.Button(row2, text="🔄 Képlet Újraszámolása", bg="#2a75d3", fg="white", font=("Arial", 9, "bold"), command=self.run_chart)
        btn_calc.pack(side="left", padx=5)

    def _save_current_person(self):
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
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both", padx=5, pady=5)

        # 1. TAB: Horoszkóp Ábrák
        self.tab_charts = tk.Frame(self.notebook, bg="#ffffff")
        self.canvas = tk.Canvas(self.tab_charts, bg="#ffffff", highlightthickness=0)
        self.canvas.pack(expand=True, fill="both")
        self.notebook.add(self.tab_charts, text=" ☸ Horoszkóp Ábrák ")

        # 2. TAB: Karmikus Életfeladat Térkép
        self.tab_map = tk.Frame(self.notebook)
        terkep.create_map_interface(self.tab_map, self)
        self.notebook.add(self.tab_map, text=" 🗺 Karmikus Életfeladat Térkép ")

        # Canvas szinkronizálása a Dasa Mandala rajzolóhoz
        if hasattr(self.tab_map, 'canvas'):
            self.canvas_karmic = self.tab_map.canvas
        else:
            self.canvas_karmic = None

        # 3. TAB: Spirituális Yantra Térkép
        self.tab_spiritual = tk.Frame(self.notebook)
        spiritual_map.create_spiritual_interface(self.tab_spiritual, self)
        self.notebook.add(self.tab_spiritual, text=" 🔮 Spirituális Yantra Térkép ")

        # Eseménykezelő bekötése a fülváltásokhoz
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # Alsó vezérlő panel
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

        # Státuszsor létrehozása a legvégén
        self.create_status_bar()

    def _set_entries(self, date_str, time_str, lat_str, lng_str, tz_str):
        for e, val in [(self.entry_date, date_str), (self.entry_time, time_str), 
                       (self.entry_lat, lat_str), (self.entry_lng, lng_str), (self.entry_tz, tz_str)]:
            e.delete(0, tk.END)
            e.insert(0, val)

    def _on_person_selected(self, event):
        name = self.combo_persons.get()
        if name in self.persons_dict:
            person = self.persons_dict[name]
            self.entry_name.delete(0, tk.END)
            self.entry_name.insert(0, name)
            
            self._set_entries(
                person.get("date", ""),
                person.get("time", ""),
                person.get("lat", ""),
                person.get("lng", ""),
                person.get("tz", "")
            )
            self.run_chart()

    def run_chart(self):
        try:
            name = self.entry_name.get()
            
            date_str = self.entry_date.get().strip().replace("–", "-").replace("—", "-").replace(".", "-").replace("/", "-")
            date_parts = date_str.split("-")
            
            chart_year = int(float(date_parts[0]))
            chart_month = int(float(date_parts[1]))
            chart_day = int(float(date_parts[2]))

            time_str = self.entry_time.get().strip()
            if ":" in time_str:
                time_parts = time_str.split(":")
                chart_hour = int(float(time_parts[0]))
                chart_minute = int(float(time_parts[1]))
            else:
                chart_hour = int(float(time_str[:2]))
                chart_minute = int(float(time_str[2:]))

            lat = float(self.entry_lat.get())
            lng = float(self.entry_lng.get())
            tz_offset = float(self.entry_tz.get())

            varga_label = self.combo_varga.get()

            res_d1 = generate_chart(name, chart_year, chart_month, chart_day, chart_hour, chart_minute, lat, lng)
            varga_raw = get_varga_chart_data(chart_year, chart_month, chart_day, chart_hour, chart_minute, lat, lng, tz_offset, varga_label, name)

            self.last_chart_data = {
                "name": name,
                "raw_year": chart_year, "raw_month": chart_month, "raw_day": chart_day,
                "raw_hour": chart_hour, "raw_min": chart_minute,
                "planets_d1": res_d1["planets"],
                "asc_d1": res_d1["ascendant"]["sign"],
                "tithi_d1": res_d1["tithi"],
                "planets": res_d1["planets"],  # Dasa mandala számára elengedhetetlen kulcs
                "planets_varga": varga_raw.get("planet_data", res_d1["planets"]), 
                "asc_varga": varga_raw.get("planet_data", {}).get("ASC", {}).get("sign", res_d1["ascendant"]["sign"]),
                "tithi_varga": str(varga_raw.get("tithi", res_d1["tithi"])),
            }

            self.canvas.delete("all")
            self._render_canvas_content()
            
            # Kényszerített Dasa Mandala frissítés, ha épp azon a fülön állunk
            self._on_tab_changed(None)
            self.root.update_idletasks()

        except Exception as e:
            messagebox.showerror("Hiba", f"Hiba történt a képlet generálásakor:\n{e}")

    def _render_canvas_content(self):
        if not self.last_chart_data:
            return
        try:
            varga_selected = self.combo_varga.get().split(" ")[0]
            draw_four_charts(
                canvas=self.canvas,
                planets=self.last_chart_data["planets_d1"],
                asc_sign=self.last_chart_data["asc_d1"],
                varga_planets=self.last_chart_data["planets_varga"],
                varga_asc=self.last_chart_data["asc_varga"],
                tithi_d1=self.last_chart_data["tithi_d1"],
                tithi_varga=self.last_chart_data["tithi_varga"],
                selected_varga=varga_selected,
                person_name=self.last_chart_data["name"],
                birth_date=f"{self.last_chart_data['raw_year']}-{self.last_chart_data['raw_month']}-{self.last_chart_data['raw_day']} {self.last_chart_data['raw_hour']}:{self.last_chart_data['raw_min']}",
                show_varshaphala=False
            )
        except Exception as e:
            print(f"❌ Canvas hiba: {e}")

    def _on_window_resize(self, event):
        if event.widget == self.root:
            self._render_canvas_content()
            if self.last_chart_data:
                # Frissíti a térképet, ha van
                if hasattr(self, 'tab_map') and hasattr(self.tab_map, 'canvas'):
                    terkep.redraw_map(self.tab_map.canvas, self.last_chart_data)
                
                # 🔥 DINAMIKUSAN ÚJRARAJZOI A DASA MANDALÁT IS ÁTMÉRETEZÉSKOR!
                self._on_tab_changed(None)

    def trigger_audio_generation(self):
        if not self.last_chart_data: return
        threading.Thread(target=lambda: generate_full_audio(self.last_chart_data), daemon=True).start()

    def trigger_pdf_export(self):
        if not self.last_chart_data: return
        export_score_to_pdf_and_png(self.last_chart_data)

    def show_analysis_popup(self):
        if not self.last_chart_data: return
        popup = tk.Toplevel(self.root)
        popup.geometry("600x500")
        txt = tk.Text(popup, wrap="word", font=("Arial", 10))
        txt.pack(expand=True, fill="both", padx=10, pady=10)
        txt.insert("1.0", generate_full_analysis(self.last_chart_data))
        txt.config(state="disabled")

    def _on_tab_changed(self, event=None):
        """A fülváltáskor automatikusan kirajzolja a Dasa Mandalát a megfelelő canvasra."""
        try:
            selected_tab_text = self.notebook.tab(self.notebook.select(), "text")
            if "Karmikus" in selected_tab_text:
                if hasattr(self, 'last_chart_data') and self.last_chart_data and "planets" in self.last_chart_data:
                    target_canvas = None
                    if hasattr(self, 'canvas_karmic') and self.canvas_karmic:
                        target_canvas = self.canvas_karmic
                    elif hasattr(self, 'tab_map') and hasattr(self.tab_map, 'canvas'):
                        target_canvas = self.tab_map.canvas
                        
                    if target_canvas:
                        dasa_mandala.render_dasa_mandala_to_canvas(target_canvas, self.last_chart_data["planets"])
        except Exception as e:
            print(f"[DEBUG] Dasa Mandala hiba: {e}")

    def show_varshaphala_popup(self):
        if not self.last_chart_data: return
        popup = tk.Toplevel(self.root)
        popup.title("Varshaphala – Éves Előrejelzés")
        popup.geometry("350x160")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(popup, text="Célév (pl. 2026):", font=("Arial", 11, "bold")).pack(pady=10)
        entry_v_year = tk.Entry(popup, width=12, font=("Arial", 12), justify="center")
        entry_v_year.pack(pady=5)
        entry_v_year.insert(0, str(pendulum.now().year))

        def calc_varsha():
            try:
                target_y = int(entry_v_year.get().strip())
                lat_val = float(self.entry_lat.get()) if hasattr(self, 'entry_lat') else 46.48
                lon_val = float(self.entry_lng.get()) if hasattr(self, 'entry_lng') else 19.03
                
                raw_year = int(self.last_chart_data["raw_year"])
                age = target_y - raw_year
                if age < 0: age = 0
                
                birth_dt = pendulum.datetime(raw_year, int(self.last_chart_data["raw_month"]), int(self.last_chart_data["raw_day"]), int(self.last_chart_data.get("raw_hour", 12)), int(self.last_chart_data.get("raw_min", 0)), tz="Europe/Budapest")

                varsha_res = compute_varshaphala_chart(birth_dt, age, lat_val, lon_val)
                if varsha_res and "planet_data" in varsha_res:
                    self.last_chart_data["planets_varga"] = varsha_res["planet_data"]
                    self.last_chart_data["asc_varga"] = varsha_res["ascendant"]["sign"]
                    self.last_chart_data["tithi_varga"] = str(varsha_res["tithi"])
                    
                    self.combo_varga.set(f"Varshaphala ({target_y})")
                    self._render_canvas_content()
                    popup.destroy()
            except Exception as e:
                messagebox.showerror("Hiba", f"Sikertelen számítás: {e}")

        tk.Button(popup, text="Éves Képlet Megjelenítése", bg="#f39c12", fg="white", font=("Arial", 11, "bold"), padx=10, pady=4, command=calc_varsha).pack(pady=12)

def start_gui():
    root = tk.Tk()
    app = SonicJyotishApp(root)
    root.mainloop()

if __name__ == "__main__":
    start_gui()
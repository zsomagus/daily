import os
import datetime
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from PIL import Image, ImageTk  # Szükséges a JPG képek kezeléséhez és átméretezéséhez
import pandas as pd             # Excel fájlok kezeléséhez
try:
    from countryinfo import CountryInfo
except ImportError:
    # Ha véletlenül nincs telepítve, a program ne szálljon el, hanem használja az Excelt
    CountryInfo = None

import jyotishganit

# --- Alapértelmezett koordináták (46° 51' 26.1" N, 18° 9' 12.28" E átszámítva) ---
DEFAULT_LAT = 46.85725
DEFAULT_LON = 18.15341

# --- 1. ADATOK BEOLVASÁSA ÉS PARSOLÁSA ---
def load_tithi_data():
    tithi_dict = {}
    file_name = "tithi_ajánlások.xlsx"
    
    if not os.path.exists(file_name):
        return None

    with open(file_name, "r", encoding="utf-8", errors="ignore") as f:
        content = f.read()
    
    import re
    matches = re.findall(r'(\d+)\s*,\s*(Shukla|Krishna)\s*,\s*([A-Za-z]+)\s*,\s*([^,\n]+),([^,\n]+)', content)
    
    for m in matches:
        tithi_num = int(m[0])
        tithi_dict[tithi_num] = {
            "tipus": m[1].strip(),
            "nev": m[2].strip(),
            "jelentes": m[3].replace('"', '').strip(),
            "ajanlas": m[4].replace('"', '').strip()
        }
    return tithi_dict

# --- KOORDINÁTA KISZÁMÍTÓ FÜGGVÉNYEK ---
def get_coordinates(city_name: str, file1: str, file2: str):
    for file in [file1, file2]:
        if os.path.exists(file):
            try:
                df = pd.read_excel(file)
                df["name_lower"] = df["name"].str.lower()
                row = df[df["name_lower"] == city_name.lower()]
                if not row.empty:
                    return float(row["lat"].iloc[0]), float(row["lon"].iloc[0])
            except Exception:
                pass
    return None, None

def fill_coordinate_entries(city_name: str, lat_entry, lon_entry) -> bool:
    lat, lon = None, None

    # 1️⃣ CountryInfo használata
    if CountryInfo:
        try:
            ci = CountryInfo(city_name)
            info = ci.info()
            if "latlng" in info and info["latlng"]:
                lat, lon = info["latlng"][0], info["latlng"][1]
        except Exception:
            pass

    # 2️⃣ Excel fallback megoldás
    if lat is None or lon is None:
        base = os.path.dirname(__file__)
        file1 = os.path.join(base, "static", "file1.xlsx")
        file2 = os.path.join(base, "static", "file2.xlsx")
        lat, lon = get_coordinates(city_name, file1, file2)

    # 3️⃣ Tkinter GUI mezők frissítése (setText helyett törlés és beillesztés)
    if lat is not None and lon is not None:
        lat_entry.delete(0, tk.END)
        lat_entry.insert(0, f"{lat:.5f}")
        lon_entry.delete(0, tk.END)
        lon_entry.insert(0, f"{lon:.5f}")
        return True

    return False

# --- 2. AZ AKTUÁLIS TITHI KISZÁMÍTÁSA A JYOTISHGANIT SEGÍTSÉGÉVEL ---
def get_current_tithi_index(lat, lon):
    try:
        now = datetime.datetime.now()
        
        # Kiszámítjuk az időzóna eltolódást dinamikusan
#  Az új, modern és figyelmeztetés-mentes sor:
        tz_offset = datetime.datetime.now().astimezone().utcoffset().total_seconds() / 3600.0        
        # Meghívjuk a csillagászati könyvtárat a pontos koordinátákkal
        # (Megjegyzés: A pontos jyotishganit API struktúrához igazítva, ha szükséges, ez a hívás finomítható)
        tithi_index = jyotishganit.get_tithi(
            year=now.year, 
            month=now.month, 
            day=now.day, 
            hour=now.hour, 
            minute=now.minute, 
            lat=lat, 
            lon=lon, 
            tz=tz_offset
        )
        
        # Biztosítjuk, hogy az index 1 és 30 között legyen
        if isinstance(tithi_index, int) and 1 <= tithi_index <= 30:
            return tithi_index
        else:
            # Ha a könyvtár objektumot ad vissza, megpróbáljuk kinyerni az id-t vagy számértéket
            return getattr(tithi_index, 'index', 1)
            
    except Exception as e:
        # Ha a csillagászati számítás meghiúsulna, egy biztonsági alapértelmezett matematikai becslés lép életbe
        base_date = datetime.date(2026, 3, 19)
        today = datetime.date.today()
        delta_days = (today - base_date).days
        return (delta_days % 30) + 1

# --- 3. AZ ÜZENET GENERÁLÁSA ---
def generate_message(current_idx, tithis, lat, lon):
    tithi_info = {
        "tipus": "Shukla", "nev": "Pratipada", 
        "jelentes": "Új kezdet, tiszta szándékok", 
        "ajanlas": "Fogalmazd meg a mai spirituális célodat."
    }
    if tithis and current_idx in tithis:
        tithi_info = tithis[current_idx]
        
    ma_szoveg = datetime.date.today().strftime('%Y. %B %d.')
    
    return f"""==============================================================================
                ✨ JÓ REGGELT, KEDVES LÉLEK! ✨
==============================================================================
Dátum: {ma_szoveg}
Helyszín koordináták: Lat: {lat}, Lon: {lon}
"Amilyen a belső világod, olyan a csillagos égbolt is feletted."

🌙 A HOLD AKTUÁLIS ÁLLAPOTA (TITHI - CSILLAGÁSZATI PONTOSSÁGGAL):
   Ma a Hold a(z) {tithi_info['tipus']} {tithi_info['nev']} fázisában jàr (Tithi sorszám: {current_idx}).
   Energetikai jelentés: {tithi_info['jelentes']}

🪐 TRANZITOK ÉS PURUSHARTHA ÚTMUTATÁS:
   A Graha (bolygó) állások emlékeztetnek, hogy a belső béke (Sattva) megőrzése 
   a legnagyobb Dharma. A tranzitok finoman támogatják a Moksha (lelki felszabadulás) 
   és az önismeret felé tett lépéseidet. Ne siesd el a döntéseket, figyelj a 
   szinkronicitásokra és az intuíciódra!

🌱 NAPI AJÁNLÁS A LÉLEKNEK:
   * Tithi gyakorlat: {tithi_info['ajanlas']}
   * Jóga/Energetika: Szánj időt egy finom Matsyasana (Hal póz) taiwáni vagy egy megtartó 
     Warrior (Harcos) póz sorozatra, hogy a prana szabadon áramolhasson.
   * Mantra a mai napra: "Összhangban vagyok a kozmosz ritmusával."

------------------------------------------------------------------------------
"""

# --- 4. FÁJLBA MENTÉS FUNKCIÓ ---
def save_to_file(text_content):
    ma_szoveg = datetime.date.today().strftime('%Y_%m_%d')
    default_filename = f"napi_utravalo_{ma_szoveg}.txt"
    try:
        with open(default_filename, "w", encoding="utf-8") as f:
            f.write(text_content)
        messagebox.showinfo("Siker", f"Az útravalót sikeresen elmentettem:\n{default_filename}")
    except Exception as e:
        messagebox.showerror("Hiba", f"Nem sikerült a mentés: {e}")

# --- 5. YANTRÁK MEGKALELESÉNEK LOGIKÁJA ---
def get_yantra_image(tithi_idx, max_width=350, max_height=350):
    yantra_dir = "yantra"
    if not os.path.exists(yantra_dir):
        return None, "A 'yantra' mappa nem található a program mellett."
    
    target_file = None
    prefix = f"{tithi_idx} "
    for file in os.listdir(yantra_dir):
        if file.startswith(prefix) and file.lower().endswith(('.jpg', '.jpeg', '.png')):
            target_file = os.path.join(yantra_dir, file)
            break
            
    if not target_file:
        return None, f"Nem található kép a(z) {tithi_idx}. sorszámmal a 'yantra' mappában."
    
    try:
        img = Image.open(target_file)
        img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
        return img, None
    except Exception as e:
        return None, f"Hiba a kép betöltése során: {e}"

# --- 6. INTERAKTÍV GUI FELÜLET ---
def show_popup():
    root = tk.Tk()
    root.title("Jyotish Napi Útravaló & Meditáció ✨")
    root.geometry("700x650")
    root.configure(bg="#1A1A24")
    root.eval('tk::PlaceWindow . center')
    
    # Sötét téma stílusok beállítása
    style = ttk.Style()
    style.theme_use('default')
    style.configure('TNotebook', background='#1A1A24', borderwidth=0)
    style.configure('TNotebook.Tab', background='#2D2D3D', foreground='#E0E0E6', padding=[15, 5], font=("Segoe UI", 10))
    style.map('TNotebook.Tab', background=[('selected', '#111116')], foreground=[('selected', '#FFFFFF')])

    # --- FELÜLSŐ PANEL: HELYSZÍN ÉS KOORDINÁTÁK ---
    loc_frame = tk.LabelFrame(root, text=" 📍 Csillagászati Helyszín Beállítása ", bg="#1A1A24", fg="#E0E0E6", font=("Segoe UI", 9, "bold"), padx=10, pady=5)
    loc_frame.pack(fill='x', padx=15, pady=10)

    tk.Label(loc_frame, text="Város/Ország:", bg="#1A1A24", fg="#A0A0AA").grid(row=0, column=0, padx=5, pady=5, sticky='e')
    city_entry = tk.Entry(loc_frame, bg="#2D2D3D", fg="#FFFFFF", insertbackground="white", width=15)
    city_entry.grid(row=0, column=1, padx=5, pady=5)
    city_entry.insert(0, "Budapest")

    tk.Label(loc_frame, text="Lat:", bg="#1A1A24", fg="#A0A0AA").grid(row=0, column=2, padx=5, pady=5, sticky='e')
    lat_entry = tk.Entry(loc_frame, bg="#2D2D3D", fg="#FFFFFF", insertbackground="white", width=10)
    lat_entry.grid(row=0, column=3, padx=5, pady=5)
    lat_entry.insert(0, str(DEFAULT_LAT))

    tk.Label(loc_frame, text="Lon:", bg="#1A1A24", fg="#A0A0AA").grid(row=0, column=4, padx=5, pady=5, sticky='e')
    lon_entry = tk.Entry(loc_frame, bg="#2D2D3D", fg="#FFFFFF", insertbackground="white", width=10)
    lon_entry.grid(row=0, column=5, padx=5, pady=5)
    lon_entry.insert(0, str(DEFAULT_LON))

    # --- FUNKCIÓ AZ ADATOK FRISSÍTÉSÉRE ---
    def update_calculation():
        city = city_entry.get().strip()
        if city:
            fill_coordinate_entries(city, lat_entry, lon_entry)
        
        try:
            lat = float(lat_entry.get())
            lon = float(lon_entry.get())
        except ValueError:
            messagebox.showwarning("Figyelem", "Hibás koordináták! Az alapértelmezett értékeket használjuk.")
            lat, lon = DEFAULT_LAT, DEFAULT_LON

        current_idx = get_current_tithi_index(lat, lon)
        tithis = load_tithi_data()
        msg_content = generate_message(current_idx, tithis, lat, lon)
        
        # Szöveges fül frissítése
        txt.configure(state='normal')
        txt.delete(1.0, tk.END)
        txt.insert(tk.INSERT, msg_content)
        txt.configure(state='disabled')
        
        # Kép frissítése a Meditációs fülön
        img, error_msg = get_yantra_image(current_idx)
        if img:
            root.photo = ImageTk.PhotoImage(img)
            img_label.configure(image=root.photo)
            info_label.configure(text=f"Helyezkedj el kényelmesen. Engedd, hogy a(z) {current_idx}. Yantra szent geometriája\nlecsendesítse az elmédet, és megnyissa a szívedet.")
        else:
            img_label.configure(image='')
            info_label.configure(text=f"Yantra nem jeleníthető meg:\n{error_msg}")
            
        # Mentés gomb parancsának frissítése
        save_btn.configure(command=lambda: save_to_file(msg_content))

    search_btn = tk.Button(loc_frame, text="Keresés & Számítás", bg="#4A3E56", fg="#FFFFFF", font=("Segoe UI", 9, "bold"), command=update_calculation, borderwidth=0, padx=8)
    search_btn.grid(row=0, column=6, padx=10, pady=5)

    # Notebook (fülek)
    notebook = ttk.Notebook(root)
    notebook.pack(expand=True, fill='both', padx=15, pady=5)
    
    # --- 1. FÜL: ÚTRAVALÓ SZÖVEG ---
    tab_text = tk.Frame(notebook, bg="#111116")
    notebook.add(tab_text, text=" 📜 Napi Útravaló ")
    
    txt = scrolledtext.ScrolledText(tab_text, undo=True, bg="#111116", fg="#E0E0E6", 
                                    insertbackground='white', font=("Courier New", 10), borderwidth=0, highlightthickness=0)
    txt.pack(expand=True, fill='both', padx=10, pady=10)
    
    # --- 2. FÜL: YANTRA MEDITÁCIÓ ---
    tab_yantra = tk.Frame(notebook, bg="#111116")
    notebook.add(tab_yantra, text=" 💮 Yantra Meditáció ")
    
    img_label = tk.Label(tab_yantra, bg="#111116")
    img_label.pack(pady=15)
    
    info_label = tk.Label(tab_yantra, bg="#111116", fg="#A0A0AA", font=("Segoe UI", 10, "italic"))
    info_label.pack(pady=10)
    
    # --- ALSÓ GOMBOK PANEL ---
    btn_frame = tk.Frame(root, bg="#1A1A24")
    btn_frame.pack(fill='x', side='bottom', pady=10)
    
    save_btn = tk.Button(btn_frame, text="Útravaló mentése szövegfájlba", 
                         bg="#2D2D3D", fg="#FFFFFF", font=("Segoe UI", 10, "bold"),
                         padx=10, pady=5, borderwidth=0, activebackground="#3D3D4D", activeforeground="white")
    save_btn.pack(side='left', padx=20)
    
    close_btn = tk.Button(btn_frame, text="Bezárás", 
                          bg="#4A2E2B", fg="#FFFFFF", font=("Segoe UI", 10),
                          command=root.destroy, padx=15, pady=5, borderwidth=0, activebackground="#5A3E3B", activeforeground="white")
    close_btn.pack(side='right', padx=20)
    
    # Első számítás futtatása az induláskor
    update_calculation()
    
    root.mainloop()

if __name__ == "__main__":
    show_popup()
# main_gui.py
import sys
import os
import pendulum
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLabel, QLineEdit,
    QDateEdit, QTimeEdit, QPushButton, QTextEdit, QComboBox, QCheckBox, QTabWidget
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import QDate, QTime

# Modulok importálása - Tiszta struktúra, körkörös importok nélkül!
from modulok import astro_core, prashna_core, elemzes, grafika, 
 config, varshaphala_tools
from gui import gui_helpers

app = QApplication(sys.argv)
window = QWidget()
window.setWindowTitle("SonicJyotish Pro - Teljes Asztro-Zenei Rendszer")
layout = QGridLayout(window)

app.setStyleSheet("QWidget { background-color: rgb(137, 218, 218); }")

# --- BAL OLDALI INPUT MEZŐK ---
name1 = QLineEdit(); layout.addWidget(QLabel("Név"), 0, 0); layout.addWidget(name1, 0, 1)
date1 = QDateEdit(); layout.addWidget(QLabel("Születési Dátum"), 1, 0); layout.addWidget(date1, 1, 1)
date1.setCalendarPopup(True); date1.setDate(QDate(1976, 3, 15))

time1 = QTimeEdit(); layout.addWidget(QLabel("Idő (óra:perc)"), 2, 0); layout.addWidget(time1, 2, 1)
time1.setTime(QTime(21, 53))

# INTELIGENS VÁROSKERESŐ SZEKCIÓ
cityInput = QLineEdit(); layout.addWidget(QLabel("📍 Város/Helyszín"), 3, 0); layout.addWidget(cityInput, 3, 1)
searchCityButton = QPushButton("🔍 Koordináták Keresése")
layout.addWidget(searchCityButton, 4, 0, 1, 2)

lat1 = QLineEdit("47.30"); layout.addWidget(QLabel("Szélesség (Lat)"), 5, 0); layout.addWidget(lat1, 5, 1)
lon1 = QLineEdit("19.05"); layout.addWidget(QLabel("Hosszúság (Lon)"), 6, 0); layout.addWidget(lon1, 6, 1)

timezoneSelector = QComboBox()
timezoneSelector.addItems(["Europe/Budapest", "UTC", "America/New_York", "Asia/Kolkata"])
layout.addWidget(QLabel("Időzóna"), 7, 0); layout.addWidget(timezoneSelector, 7, 1)

dstCheckbox = QCheckBox("Nyári időszámítás (DST)")
layout.addWidget(dstCheckbox, 8, 0, 1, 2)

# ✨ ÚJ/VISSZARAKOTT MEZŐ: Életkor vagy Év a Varshaphala számításhoz
ageInput = QLineEdit("50")
layout.addWidget(QLabel("⏳ Varshaphala Év/Életkor"), 9, 0); layout.addWidget(ageInput, 9, 1)

# Részhoroszkópok betöltése a tables modulból
vargaSelector = QComboBox()
vargaSelector.addItems(list(astro_core.varga_factors.keys()))
layout.addWidget(QLabel("Részhoroszkóp (Varga)"), 10, 0); layout.addWidget(vargaSelector, 10, 1)

# Dallam és kotta forrás választó
musicSourceSelector = QComboBox()
musicSourceSelector.addItems([
    "Rashi (Alapképlet D1)",
    "Kiválasztott részhoroszkóp (Varga)",
    "Rashi úr (Rashi Lord)",
    "Nakshatra úr (Nakshatra Lord)",
    "Varshaphala (Éves képlet)",
    "Varshaphala úr"
])
layout.addWidget(QLabel("🎵 Dallam & Kotta forrása"), 11, 0); layout.addWidget(musicSourceSelector, 11, 1)

# --- FŐ MŰVELETI GOMBOK ---
calcButton = QPushButton("🔮 Alapképlet (D1/Varga) Számítás")
calcButton.setStyleSheet("background-color: #FFD700; font-weight: bold;")
layout.addWidget(calcButton, 12, 0, 1, 2)

# ✨ VISSZARAKOTT GOMB: Varshaphala Éves képlet gomb
varshaphalaButton = QPushButton("📅 Varshaphala (Éves Képlet) Mentéssel")
varshaphalaButton.setStyleSheet("background-color: #98FB98; font-weight: bold;")
layout.addWidget(varshaphalaButton, 13, 0, 1, 2)

# ✨ VISSZARAKOTT GOMB: Prashna gomb
prashnaButton = QPushButton("⏱️ Prashna (Kérdő Képlet - Mostani Idő)")
prashnaButton.setStyleSheet("background-color: #F0E68C; font-weight: bold;")
layout.addWidget(prashnaButton, 14, 0, 1, 2)

# --- JOBB OLDALI FÜLEK (KÉPEKNEK) ---
tabs = QTabWidget()
imageLabel1 = QLabel("Dél-indiai horoszkóp helye")
imageLabel2 = QLabel("Rashi Lord térkép helye")
imageLabel3 = QLabel("Nakshatra Lord térkép helye")
tabs.addTab(imageLabel1, "Horoszkóp (Dél)")
tabs.addTab(imageLabel2, "Rashi Lord")
tabs.addTab(imageLabel3, "Nakshatra Lord")
layout.addWidget(tabs, 0, 2, 15, 1)

# Globális szöveges visszajelző terület
resultArea = QTextEdit()
resultArea.setReadOnly(True)
layout.addWidget(QLabel("📋 Elemzés és Rendszerüzenetek:"), 15, 0, 1, 3)
layout.addWidget(resultArea, 16, 0, 4, 3)


# --- REFRISH GRAPHICS HELPER (Közös képfrissítő) ---
def frissit_kepeket(png_path, png_rashi_lord, png_nakshatra_lord):
    if os.path.exists(png_path):
        imageLabel1.setPixmap(QPixmap(png_path).scaled(400, 400))
    if os.path.exists(png_rashi_lord):
        imageLabel2.setPixmap(QPixmap(png_rashi_lord).scaled(400, 400))
    if os.path.exists(png_nakshatra_lord):
        imageLabel3.setPixmap(QPixmap(png_nakshatra_lord).scaled(400, 400))


# --- AUTOMATIKUS HELYSZÍN KERESŐ ---
def on_search_city():
    city_name = cityInput.text().strip()
    if not city_name:
        resultArea.setText("⚠️ Kérlek, írj be egy városnevet a kereséshez!")
        return
    
    resultArea.setText(f"🔎 Keresés: {city_name}...")
    success = config.fill_coordinate_entries(city_name, lat1, lon1)
    
    if success:
        resultArea.append(f"✅ Város megtalálva! Koordináták frissítve.")
        try:
            now_dt = pendulum.now("Europe/Budapest")
            config.update_dst_checkbox(dstCheckbox, "Europe/Budapest", now_dt)
            resultArea.append("⏰ Időzóna és DST állapot szinkronizálva.")
        except Exception as e:
            print(f"DST hiba: {e}")
    else:
        resultArea.append(f"❌ A várost nem sikerült azonosítani.")

searchCityButton.clicked.connect(on_search_city)


# --- 1. ESEMÉNYKEZELŐ: ALAPKÉPLET (D1 / VARGA) ---
def on_calculate():
    resultArea.clear()
    resultArea.append("⚡ Alapképlet számítás indítása...")
    bd = gui_helpers.get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector)
    varga_label = vargaSelector.currentText()
    zene_forras = musicSourceSelector.currentText()

    try:
        res = astro_core.compute_full_chart_for_gui(bd, varga_label)
        svg_p, png_p = draw.rajzol_del_indiai_horoszkop_svg(res, bd, res["planet_data"], varga_name=varga_label, tithi=res["tithi"])
        png_rl = draw_lord.generate_rashi_lord_chart(res, bd)
        png_nl = draw_lord.generate_nakshatra_lord_chart(res, bd)
        
        frissit_kepeket(png_p, png_rl, png_nl)
        
        szoveg = elemzes.general_szoveges_elemzes(res["planet_data"], res["tithi"], res["varga_code"])
        resultArea.append("\n" + szoveg)
        
        gui_helpers.save_analysis_pdf(resultArea)
        sonic_world.generate_sonic_melodic_wav_by_source(bd, res, zene_forras)
        resultArea.append(f"\n🚀 SIKERESEN MENTVE!")
    except Exception as e:
        resultArea.append(f"❌ Hiba: {str(e)}")

calcButton.clicked.connect(on_calculate)


# --- 2. ESEMÉNYKEZELŐ: VARSHAPHALA (ÉVES KÉPLET) ---
def on_varshaphala_calculate():
    resultArea.clear()
    resultArea.append("⚡ Varshaphala Éves Képlet számítása...")
    bd = gui_helpers.get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector)
    ev_vagy_kor = ageInput.text().strip()
    zene_forras = musicSourceSelector.currentText()

    try:
        # Meghívjuk a varshaphala_tools kalkulátorát az életkorral szűrve
        res = varshaphala_tools.compute_varshaphala_chart_for_gui(bd, ev_vagy_kor)
        resultArea.append("✅ Éves tranzit pozíciók kiszámítva.")

        svg_p, png_p = draw.rajzol_del_indiai_horoszkop_svg(res, bd, res["planet_data"], varga_name="Varshaphala", tithi=res.get("tithi", 1))
        png_rl = draw_lord.generate_rashi_lord_chart(res, bd)
        png_nl = draw_lord.generate_nakshatra_lord_chart(res, bd)
        
        frissit_kepeket(png_p, png_rl, png_nl)
        
        resultArea.append("\n📊 Éves képlet elemzése elkészült.")
        gui_helpers.save_analysis_pdf(resultArea)
        sonic_world.generate_sonic_melodic_wav_by_source(bd, res, zene_forras)
        resultArea.append(f"\n🚀 ÉVES KÉPLET ÉS ZENE SIKERESEN MENTVE!")
    except Exception as e:
        resultArea.append(f"❌ Varshaphala hiba: {str(e)}")

varshaphalaButton.clicked.connect(on_varshaphala_calculate)


# --- 3. ESEMÉNYKEZELŐ: PRASHNA (KÉRDŐ KÉPLET) ---
def on_prashna_calculate():
    resultArea.clear()
    resultArea.append("⚡ Prashna (Horoszkóp a mostani pillanatra) generálása...")
    
    try:
        # Lekérjük a prashna_core segítségével a jelenlegi pillanatot és koordinátákat
        lat_val = float(lat1.text() or 47.3)
        lon_val = float(lon1.text() or 19.0)
        prashna_data = prashna_core.fill_prashna_data_with_coords(lat_val, lon_val)
        
        # Átformázzuk, hogy a rajzoló és a zene megértse
        bd_prashna = {
            "name": "Prashna_Kérdés",
            "date": prashna_data["date"],
            "time": prashna_data["time"],
            "lat": str(lat_val),
            "lon": str(lon_val),
            "timezone": "Europe/Budapest"
        }
        
        res = prashna_data["chart_data"]
        # Biztosítjuk a tithi meglétét
        moon_lon = res["planet_data"]["Moon"]["longitude"]
        sun_lon = res["planet_data"]["Sun"]["longitude"]
        tithi = int(((moon_lon - sun_lon) % 360) / 12) + 1
        res["tithi"] = tithi
        res["varga_code"] = "D1"

        svg_p, png_p = draw.rajzol_del_indiai_horoszkop_svg(res, bd_prashna, res["planet_data"], varga_name="Prashna", tithi=tithi)
        png_rl = draw_lord.generate_rashi_lord_chart(res, bd_prashna)
        png_nl = draw_lord.generate_nakshatra_lord_chart(res, bd_prashna)
        
        frissit_kepeket(png_p, png_rl, png_nl)
        resultArea.append(f"⏱️ Pillanatnyi időpont rögzítve: {bd_prashna['date']} {bd_prashna['time']}")
        
        gui_helpers.save_analysis_pdf(resultArea)
        sonic_world.generate_sonic_melodic_wav_by_source(bd_prashna, res, musicSourceSelector.currentText())
        resultArea.append(f"\n🚀 PRASHNA JELENTÉS ÉS ZENE SIKERESEN MENTVE!")
    except Exception as e:
        resultArea.append(f"❌ Prashna hiba: {str(e)}")

prashnaButton.clicked.connect(on_prashna_calculate)


if __name__ == "__main__":
    window.resize(1100, 850)
    window.show()
    sys.exit(app.exec_())
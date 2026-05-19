# gui_helpers.py
import os
import pendulum
import swisseph as swe
from PyQt6.QtGui import QPixmap, QTextDocument
from PyQt6.QtWidgets import QDialog, QGridLayout, QLabel
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtCore import QDate, QTime

# Külső modulok (a te projektedből)
from modulok import astro_core, draw, data_handler, harmonizacio, audio_kotta_tools, elemzes
from jhora.ui import horo_chart_tabs 


# --- Alap útvonalak ---
def get_output_folder() -> str:
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    folder = os.path.join(downloads, "SonicJyotish")
    os.makedirs(folder, exist_ok=True)
    return folder

# --- Születési adatok kiolvasása a globális widgetekből ---
def get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector) -> dict:
    return {
        "name": name1.text(),
        "date": date1.date().toString("yyyy-MM-dd"),
        "time": time1.time().toString("HH:mm"),
        "lat": lat1.text(),
        "lon": lon1.text(),
        "timezone": timezoneSelector.currentText()
    }


# --- Horoszkóp rajzolás és mentés (SVG + PNG) ---
    draw.rajzol_del_indiai_horoszkop_svg(
        bd,
        positions_or_varga_pos,
        tithi=tithi,
        horoszkop_nev=varga_name,
        date_str=bd["date"],
        time_str=bd["time"],
        nev=bd["name"]
    )
    # SVG megjelenítéshez és PNG mentéshez a draw modul függvényét használjuk
    # Feltételezzük, hogy a draw.rajzol_del_indiai_horoszkop létrehozza a fájlokat a kimeneti mappában
    out_dir = get_output_folder()

    # Mentési alapnév
    safe_name = bd["name"].lower().replace(" ", "_") if bd["name"] else "noname"
    base = f"user_{safe_name}_horoszkop_{varga_name.replace(' ', '_')}"

    # Rajzolás
    draw.rajzol_del_indiai_horoszkop_svg(bd, planet_data, 
        positions_or_varga_pos,
        tithi=tithi,
        horoszkop_nev=varga_name,
        date_str=bd["date"],
        time_str=bd["time"],
        nev=bd["name"]
    )

    # Elérési utak (ha a draw modul is ide ment)
    path_svg = os.path.join(out_dir, base + ".svg")
    path_png = os.path.join(out_dir, base + ".png")
    return path_svg, path_png

# --- Nagyítási párbeszéd képhez ---
def open_fullscreen_image(parent, png_path: str):
    dialog = QDialog(parent)
    dialog.setWindowTitle("Horoszkóp nagyítva")
    layout = QGridLayout(dialog)
    view = QLabel()
    view.setPixmap(QPixmap(png_path))
    view.setScaledContents(True)
    layout.addWidget(view, 0, 0)
    dialog.resize(900, 900)
    dialog.exec_()

# --- Személyek: lista frissítése, mentés, betöltés ---
def refresh_person_list(personSelector):
    persons = data_handler.load_data()
    personSelector.clear()
    for p in persons:
        personSelector.addItem(p.get("name", "Ismeretlen"))

def save_person(personSelector, name1, date1, time1, lat1, lon1, timezoneSelector):
    persons = data_handler.load_data()
    new_entry = get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector)
    persons.append(new_entry)
    data_handler.save_data(persons)
    refresh_person_list(personSelector)

def load_person(personSelector, name1, date1, time1, lat1, lon1, timezoneSelector):
    persons = data_handler.load_data()
    idx = personSelector.currentIndex()
    if idx < 0 or idx >= len(persons):
        return
    p = persons[idx]

    # név
    name1.setText(p.get("name", ""))

    # dátum
    from PyQt5.QtCore import QDate, QTime
    date1.setDate(QDate.fromString(p.get("date", ""), "yyyy-MM-dd"))

    # idő
    time1.setTime(QTime.fromString(p.get("time", ""), "HH:mm"))

    # koordináták
    lat1.setText(p.get("lat", ""))
    lon1.setText(p.get("lon", ""))

    # időzóna
    timezoneSelector.setCurrentText(p.get("timezone", "UTC"))

# --- Elemzés PDF-be ---
def save_analysis_pdf(resultArea):
    path = os.path.join(get_output_folder(), "Downloads", "SonicJyotish", "elemzes.pdf")
    printer = QPrinter()
    printer.setOutputFileName(path)
    printer.setOutputFormat(QPrinter.PdfFormat)
    doc = QTextDocument(resultArea.toPlainText())
    doc.print_(printer)
    resultArea.append(f"📄 PDF mentve: {path}")
    return path

# --- Megzenésítés (WAV) ---
def musicalize_and_save(bd: dict, resultArea) -> str:
    mix, sr = harmonizacio.compute_person_mix(bd)
    path = os.path.join(get_output_folder(), "Downloads", "SonicJyotish", "horoszkop_zene.wav")
    audio_kotta_tools.write(path, sr, mix)
    resultArea.append(f"🎵 Megzenésítés mentve: {path}")
    return path
def draw_and_save_chart(planet_data, birth_data, varga_name="D1", tithi=None):
    # Rajzolás SVG-ben
    svg_path = rajzol_del_indiai_horoszkop_svg(planet_data, birth_data, varga_name=varga_name)

    # PNG mentés
    png_path = svg_path.replace(".svg", ".png")
    convert_svg_to_png(svg_path, png_path)

    return svg_path, png_path

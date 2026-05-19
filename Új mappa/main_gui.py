import sys, os, pendulum
from PyQt6.QtWidgets import QApplication, QWidget, QGridLayout, QLabel, QLineEdit, QDateEdit, QTimeEdit, QPushButton, QTextEdit, QComboBox, QCheckBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtPrintSupport import QPrinter
from PyQt6.QtGui import QTextDocument

# Új wrapper az astro_core-ban
from jhora.ui import horo_chart_tabs
from modulok.astro_core import get_chart_data
from modulok.elemzes import generate_full_analysis
from gui import gui_helpers
from modulok.draw import rajzol_del_indiai_horoszkop_svg, rajzol_eszak_indiai_horoszkop_svg, show_horoszkop_image
from modulok import dasa_mandala
from modulok.data_handler import  load_data, save_data
from modulok.infografika_pipeline import run_pipeline
from gui.gui_helpers import get_birth_data as bd

# --- globális mezők ---
def build_main_window(planet_positions=None):
    window = QWidget()
    layout = QGridLayout(window)


    name1 = QLineEdit(); layout.addWidget(QLabel("Név"),0,0); layout.addWidget(name1,0,1)
    date1 = QDateEdit(); layout.addWidget(QLabel("Dátum"),1,0); layout.addWidget(date1,1,1)
    time1 = QTimeEdit(); layout.addWidget(QLabel("Idő"),1,2); layout.addWidget(time1,1,3)
    lat1 = QLineEdit(); lon1 = QLineEdit()  
    layout.addWidget(QLabel("Szélesség"),3,0); layout.addWidget(lat1,3,1)
    layout.addWidget(QLabel("Hosszúság"),3,2); layout.addWidget(lon1,3,3)

    timezoneSelector = QComboBox(); timezoneSelector.addItems(["Europe/Budapest","UTC","Asia/Kolkata"])
    layout.addWidget(QLabel("Időzóna"),5,0); layout.addWidget(timezoneSelector,5,1)
    dstCheckbox = QCheckBox("☀️ Nyári időszámítás"); layout.addWidget(dstCheckbox,5,2)

    vargaSelector = QComboBox()
    vargaSelector.addItems(["D1", "D9", "D10", "D12", "D60"])  # vagy bármelyik varga, amit támogatni akarsz
    layout.addWidget(QLabel("Részhoroszkóp"), 6, 0)
    layout.addWidget(vargaSelector, 6, 1, 1, 1)

    calcButton = QPushButton("Horoszkóp számítás"); layout.addWidget(calcButton,6,2)
    savePDF = QPushButton("📄 PDF mentés"); layout.addWidget(savePDF,7,1)
    readAloud = QPushButton("🔊 Felolvasás"); layout.addWidget(readAloud,7,2)
# Életkor mező a Vaarshaphala-hoz
    ageInput = QLineEdit()
    layout.addWidget(QLabel("Életkor"), 5, 4)
    layout.addWidget(ageInput, 6, 4)

# Új gombok
    prashnaButton = QPushButton("🔮 Prashna horoszkóp")
    layout.addWidget(prashnaButton, 6, 3)

    varshaphalaButton = QPushButton("☀️ Vaarshaphala (Éves horoszkóp)")
    layout.addWidget(varshaphalaButton, 7, 4)

    infografikaButton = QPushButton("📊 Infografika")
    layout.addWidget(infografikaButton, 7, 3)

    resultArea = QTextEdit(); resultArea.setReadOnly(True); layout.addWidget(resultArea,9,0,1,2)
    chartImage = QLabel(); layout.addWidget(chartImage,8,0,1,3)

# Kapcsolások
    calcButton.clicked.connect(on_calculate)
    savePDF.clicked.connect(on_save_pdf)
    readAloud.clicked.connect(on_read_aloud)
    musicButton = QPushButton("🎵 Megzenésít + ment WAV-ba"); layout.addWidget(musicButton, 7, 0)
    musicButton.clicked.connect(on_musicalize)

    saveButton = QPushButton("💾 Mentés"); layout.addWidget(saveButton, 17, 0, 1, 2)
    loadButton = QPushButton("📂 Betöltés"); layout.addWidget(loadButton, 17, 2, 1, 2)
    personSelector = QComboBox(); layout.addWidget(QLabel("Mentett személyek"), 0, 2); layout.addWidget(personSelector, 0, 3)

    saveButton.clicked.connect(on_save_person)
    loadButton.clicked.connect(on_load_person)
    init_persons()
    prashnaButton.clicked.connect(on_prashna)
    varshaphalaButton.clicked.connect(on_varshaphala)
    infografikaButton.clicked.connect(on_infografika)
    if planet_positions:
        # például kiírhatod a bolygóadatokat a resultArea-ba
        resultArea = QTextEdit()
        resultArea.setReadOnly(True)
        layout.addWidget(resultArea, 9, 0, 1, 2)
        resultArea.setText(str(planet_positions))


# --- funkciók ---
# main_gui.py (részlet)
# ... widgetek létrehozása után ...
def on_prashna():
    bd = gui_helpers.get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector)
    # aktuális időpont
    now = pendulum.now(tz=bd["timezone"])

    chart_data = get_chart_data(
        source="jhora",
        name=bd["name"],
        year=now.year, month=now.month, day=now.day,
        hour=now.hour, minute=now.minute,
        tz_str=bd["timezone"],
        lng=float(bd["lon"] or 19.0),
        lat=float(bd["lat"] or 47.0)
    )

    resultArea.setText("🔮 Prashna horoszkóp elkészült az aktuális időpontra.")
    # opcionálisan rajzolás:
    rajzol_del_indiai_horoszkop_svg(chart_data["planet_data"], bd, varga_name="Prashna")


def on_varshaphala():
    bd = gui_helpers.get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector)
    try:
        age = int(ageInput.text())
    except ValueError:
        resultArea.setText("⚠️ Adj meg érvényes életkort!")
        return

    chart_data = get_chart_data(
        source="jhora",
        name=bd["name"],
        year=bd["date"].year,
        month=bd["date"].month,
        day=bd["date"].day,
        hour=bd["time"].hour,
        minute=bd["time"].minute,
        tz_str=bd["timezone"],
        lng=float(bd["lon"] or 19.0),
        lat=float(bd["lat"] or 47.0)
    )

    sr_chart = SolarReturnChart(chart_data["subject"], year=bd["date"].year + age)
    resultArea.setText(f"☀️ Vaarshaphala horoszkóp elkészült {age} éves korra.")
    # opcionálisan rajzolás:
    rajzol_eszak_indiai_horoszkop_svg(bd, sr_chart.planets, varga_name="Varshaphala")


def on_infografika():
    bd = gui_helpers.get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector)
    run_pipeline(bd)
    resultArea.setText("📊 Infografika pipeline lefutott és elmentve.")

def on_calculate():
    bd = gui_helpers.get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector)

    chart_data = get_chart_data(
        source="jhora",
        name=bd["name"],
        year=bd["date"].year,
        month=bd["date"].month,
        day=bd["date"].day,
        hour=bd["time"].hour,
        minute=bd["time"].minute,
        tz_str=bd["timezone"],
        lng=float(bd["lon"] or 19.0),
        lat=float(bd["lat"] or 47.0)
    )

    varga_name = vargaSelector.currentText()
    if varga_name != "D1":
        varga_chart = DivisionalChart(chart_data["subject"], varga_name)
        varga_pos = varga_chart.planets
    else:
        varga_pos = chart_data["planet_data"]

    # PNG rajz
    _, chart_png = gui_helpers.draw_and_save_chart(varga_pos, bd, varga_name=varga_name, tithi=chart_data["tithi"])

    # SVG rajz + Dasa Mandala
    chart_svg = rajzol_del_indiai_horoszkop_svg(varga_pos, bd, varga_name=varga_name)
    dasa_svg = dasa_mandala.generate_dasa_mandala_svg(bd, chart_data["planet_data"])
    gui_helpers.embed_dasa_in_svg(chart_svg, dasa_svg)

    chartImage.setPixmap(QPixmap(chart_png))
    chartImage.setScaledContents(True)
    resultArea.setText(f"{varga_name} horoszkóp mentve:\nPNG: {chart_png}\nSVG: {chart_svg}")
    show_horoszkop_image(chartImage, bd, varga="D1")

def rajzol_horoszkop_svg(style, *args, **kwargs):
    if style == "south_indian":
        return rajzol_del_indiai_horoszkop_svg(*args, **kwargs)
    elif style == "north_indian":
        return rajzol_eszak_indiai_horoszkop_svg(*args, **kwargs)
    else:
        raise ValueError(f"Ismeretlen stílus: {style}")

def on_open_fullscreen():
    # Dupla kattintásra megnyitjuk nagyban
    chartImage.mouseDoubleClickEvent = lambda event: gui_helpers.open_fullscreen_image(window, chartImage.pixmap())

def on_save_pdf():
    gui_helpers.save_analysis_pdf(resultArea)

def on_read_aloud():
    import pyttsx3
    engine = pyttsx3.init()
    engine.say(resultArea.toPlainText())
    engine.runAndWait()

def on_musicalize():
    bd = gui_helpers.get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector)
    gui_helpers.musicalize_and_save(bd, resultArea)

def on_save_person():
    gui_helpers.save_person(personSelector, name1, date1, time1, lat1, lon1, timezoneSelector)

def on_load_person():
    gui_helpers.load_person(personSelector, name1, date1, time1, lat1, lon1, timezoneSelector)

def init_persons():
    gui_helpers.refresh_person_list(personSelector)
    personSelector.currentIndexChanged.connect(on_load_person)


def save_pdf():
    path = os.path.join(gui_helpers.get_output_folder(), "Downloads","SonicJyotish", "elemzes.pdf")
    printer = QPrinter(); printer.setOutputFileName(path); printer.setOutputFormat(QPrinter.PdfFormat)
    doc = QTextDocument(resultArea.toPlainText()); doc.print_(printer)
    resultArea.append(f"📄 PDF mentve: {path}")

def read_text():
    import pyttsx3
    engine = pyttsx3.init()
    engine.say(resultArea.toPlainText())
    engine.runAndWait()

def get_subject_from_json(name: str):
    # Betöltjük az összes mentett adatot
    all_data = data_helpers.load_data()
    # Megkeressük a megfelelő személyt
    for person in all_data:
        if person["name"] == name:
            args = data_helpers.load_data(person)
            return ()
    raise ValueError(f"Nincs mentett adat a névhez: {name}")

# --- kapcsolások ---


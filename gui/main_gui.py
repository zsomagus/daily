import sys, os, pendulum
from PyQt5.QtWidgets import (
    QApplication, QWidget, QGridLayout, QLabel, QLineEdit,
    QDateEdit, QTimeEdit, QPushButton, QTextEdit, QComboBox, QCheckBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QTextDocument
from PyQt5.QtCore import QTimer

from sky_skymap import generate_sky_map
from modulok.varga_ikozaeder_adapter import varga_face_map
from modulok import varshaphala_tools, prashna_core, astro_core

from gui import gui_helpers
from modulok.draw import (
    rajzol_del_indiai_horoszkop_svg,
    rajzol_eszak_indiai_horoszkop_svg,
)
from modulok.varga_adapter import get_varga_chart
from modulok.astro_core import get_chart_data  # prashna / varshaphala esetén, ha kell
from modulok.sonic_bridge import bridge_load_person,  bridge_list_persons, bridge_save_person, convert_bridge_to_gui


from modulok.tables import (
    nakshatra_data,
    tithi_dynamics,
)
app = QApplication(sys.argv)
window = QWidget()
layout = QGridLayout(window)

# --- Ikosaéder animáció ---
icosa_frames = []
icosa_dir = os.path.join(os.path.dirname(__file__), "assets", "icosa")

for i in range(60):
    path = os.path.join(icosa_dir, f"icosa_{i:03d}.png")
    if os.path.exists(path):
        icosa_frames.append(QPixmap(path))

current_frame = 0
def animate_icosa():
    global current_frame
    if icosa_frames:
        icosaLabel.setPixmap(icosa_frames[current_frame])
        icosaLabel.setScaledContents(True)
        current_frame = (current_frame + 1) % len(icosa_frames)

def jump_to_frame(face_id):
    global current_frame
    current_frame = (face_id - 1) * 3  # 3 frame / lap

timer = QTimer()
timer.timeout.connect(animate_icosa)
timer.start(80)

current_frame = 0

# 🌌 Globális stíluslap
app.setStyleSheet("""
    QWidget {
        background-color: rgb(137, 218, 218);
    }
""")

# --- globális mezők ---
name1 = QLineEdit(); layout.addWidget(QLabel("Név"), 0, 0); layout.addWidget(name1, 0, 1)
date1 = QDateEdit(); layout.addWidget(QLabel("Dátum"), 1, 0); layout.addWidget(date1, 1, 1)
time1 = QTimeEdit(); layout.addWidget(QLabel("Idő"), 1, 2); layout.addWidget(time1, 1, 3)
lat1 = QLineEdit(); lon1 = QLineEdit()
layout.addWidget(QLabel("Szélesség"), 3, 0); layout.addWidget(lat1, 3, 1)
layout.addWidget(QLabel("Hosszúság"), 3, 2); layout.addWidget(lon1, 3, 3)

timezoneSelector = QComboBox()
timezoneSelector.addItems(["Europe/Budapest", "UTC", "Asia/Kolkata"])
layout.addWidget(QLabel("Időzóna"), 5, 0); layout.addWidget(timezoneSelector, 5, 1)
dstCheckbox = QCheckBox("☀️ Nyári időszámítás"); layout.addWidget(dstCheckbox, 5, 2)

vargaSelector = QComboBox()
vargaSelector.addItems(list(varga_face_map.keys()))
layout.addWidget(QLabel("Részhoroszkóp"), 6, 0)
layout.addWidget(vargaSelector, 6, 1)

calcButton = QPushButton("Horoszkóp számítás"); layout.addWidget(calcButton, 6, 2)
savePDF = QPushButton("📄 PDF mentés"); layout.addWidget(savePDF, 7, 1)
readAloud = QPushButton("🔊 Felolvasás"); layout.addWidget(readAloud, 7, 2)

ageInput = QLineEdit()
layout.addWidget(QLabel("Életkor"), 5, 4)
layout.addWidget(ageInput, 6, 4)

prashnaButton = QPushButton("🔮 Prashna horoszkóp")
layout.addWidget(prashnaButton, 6, 3)

varshaphalaButton = QPushButton("☀️ Vaarshaphala (Éves horoszkóp)")
layout.addWidget(varshaphalaButton, 7, 4)

infografikaButton = QPushButton("📊 Infografika")
layout.addWidget(infografikaButton, 7, 3)

resultArea = QTextEdit(); resultArea.setReadOnly(True); layout.addWidget(resultArea, 9, 0, 1, 2)
chartImage = QLabel(); layout.addWidget(chartImage, 8, 0, 1, 3)

icosaLabel = QLabel()
layout.addWidget(icosaLabel, 8, 3, 1, 1)

# Mentett személyek
personSelector = QComboBox()
layout.addWidget(QLabel("Mentett személyek"), 0, 2)
layout.addWidget(personSelector, 0, 3)


skyMapButton = QPushButton("🌌 Égtérkép (csillagászati)")
layout.addWidget(skyMapButton, 8, 4)
# --- Funkciók ---
def on_sky_map():
    # születési / kérdezett adatok a GUI-ból
    bd = gui_helpers.get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector)

    # pendulum datetime → sima datetime Skyfieldnek
    dt = pendulum.datetime(
        int(bd["date"].split("-")[0]),
        int(bd["date"].split("-")[1]),
        int(bd["date"].split("-")[2]),
        int(bd["time"].split(":")[0]),
        int(bd["time"].split(":")[1]),
        tz=bd["timezone"]
    ).naive()  # timezone nélküli datetime Skyfieldnek

    lat = float(bd["lat"] or 47.0)
    lon = float(bd["lon"] or 19.0)

    planets = get_planet_positions_skyfield(dt, lat, lon)
    stars = load_bsc5_stars(limit_mag=6.5)

    out_svg = pathlib.Path(__file__).parent / "egbolt_csillagaszati.svg"
    draw_sky_svg(planets, stars, out_svg)

    resultArea.append(f"🌌 Csillagászati égtérkép elkészült: {out_svg}")


def on_prashna():
    bd = gui_helpers.get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector)
    now = pendulum.now(tz=bd["timezone"])

    chart_data = get_chart_data(
        source="jyotishganit",
        name=bd["name"],
        year=now.year, month=now.month, day=now.day,
        hour=now.hour, minute=now.minute,
        tz_str=bd["timezone"],
        lng=float(bd["lon"] or 19.0),
        lat=float(bd["lat"] or 47.0),
    )

    resultArea.setText("🔮 Prashna horoszkóp elkészült az aktuális időpontra.")
    rajzol_del_indiai_horoszkop_svg(
        chart_data["planet_data"],
        bd,
        chart_data["planet_data"],
        varga_name="Prashna",
        tithi=chart_data["tithi"],
        horoszkop_nev="Prashna",
        date_str=bd["date"],
        time_str=bd["time"],
    )


def on_varshaphala():
    from modulok.varshaphala_tools import compute_varshaphala_chart
    from modulok.draw import rajzol_del_indiai_horoszkop_svg

    bd = gui_helpers.get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector)

    # életkor mező
    age = int(ageInput.text() or 0)

    # születési idő → pendulum
    birth_dt = pendulum.datetime(
        int(bd["date"].split("-")[0]),
        int(bd["date"].split("-")[1]),
        int(bd["date"].split("-")[2]),
        int(bd["time"].split(":")[0]),
        int(bd["time"].split(":")[1]),
        tz=bd["timezone"]
    )

    # Varshaphala számítás
    result = compute_varshaphala_chart(
        birth_dt=birth_dt,
        age=age,
        lat=float(bd["lat"]),
        lon=float(bd["lon"])
    )

    chart = result["chart"]

    # Szöveg kiírása
    resultArea.setText(
        f"☀️ Varshaphala (Éves horoszkóp)\n"
        f"Dátum: {result['datetime'].to_datetime_string()}\n\n"
        f"Tithi: {result['tithi']}\n"
        f"Nakshatra: {result['nakshatra']}\n"
        f"Yoga: {result['yoga']}\n"
        f"Karana: {result['karana']}\n"
        f"Vaara: {result['vaara']}\n"
    )

    # Rajzolás
    svg_path = rajzol_del_indiai_horoszkop_svg(
        chart.planet_data,
        bd,
        chart.planet_data,
        varga_name="Varshaphala",
        tithi=result["tithi"],
        horoszkop_nev="Varshaphala",
        date_str=result["datetime"].format("YYYY-MM-DD"),
        time_str=result["datetime"].format("HH:mm"),
    )

    if os.path.exists(svg_path):
        chartImage.setPixmap(QPixmap(svg_path))
        chartImage.setScaledContents(True)

    # Elemzés + PDF
    md = generate_markdown_summary(chart)
    md += summarize_purusharthas(chart)
    pdf_path = save_analysis_pdf(md, bd["name"])
    resultArea.append(f"📄 PDF mentve: {pdf_path}")




def normalize_varga_label(label: str):
    return label.split(" ")[0]   # "D9 (Navamsha)" → "D9"

def on_calculate():
    bd = gui_helpers.get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector)
    varga_label = vargaSelector.currentText()
    varga_name = normalize_varga_label(varga_label)

    dt = pendulum.datetime(
        int(bd["date"].split("-")[0]),
        int(bd["date"].split("-")[1]),
        int(bd["date"].split("-")[2]),
        int(bd["time"].split(":")[0]),
        int(bd["time"].split(":")[1]),
        tz=bd["timezone"]
    )

    timezone_offset = dt.utcoffset().total_seconds() / 3600.0

    chart_data = get_varga_chart(
        year=dt.year, month=dt.month, day=dt.day,
        hour=dt.hour, minute=dt.minute,
        lat=float(bd["lat"]),
        lon=float(bd["lon"]),
        timezone_offset=timezone_offset,
        varga_label=varga_name
    )

    resultArea.setText(chart_data["text"])

    png_path = chart_data.get("png_path")
    if png_path and os.path.exists(png_path):
        chartImage.setPixmap(QPixmap(png_path))
        chartImage.setScaledContents(True)

    
    # ha akarod, itt beállíthatod:
    # window.current_chart = chart_data.get("chart_obj")
def on_save_pdf():
    gui_helpers.save_analysis_pdf(resultArea)


def on_read_aloud():
    import pyttsx3
    engine = pyttsx3.init()
    engine.say(resultArea.toPlainText())
    engine.runAndWait()




def on_save_person():
    bd = gui_helpers.get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector)
    bd["dst"] = dstCheckbox.isChecked()
    bridge_save_person(bd)
    init_persons()


def on_load_person():
    name = personSelector.currentText()
    bd = bridge_load_person(name)
    if bd:
        bd_gui = convert_bridge_to_gui(bd)
        gui_helpers.load_data(bd_gui, name1, date1, time1, lat1, lon1, timezoneSelector, dstCheckbox)
        personSelector.setCurrentText(name)


def init_persons():
    personSelector.clear()
    for name in bridge_list_persons():
        personSelector.addItem(name)
init_persons()

# --- AUTO LOAD LAST PERSON ---
names = bridge_list_persons()
if names:
    last = names[-1]   # utolsó mentett
    bd = bridge_load_person(last)
    if bd:
        bd_gui = convert_bridge_to_gui(bd)
        gui_helpers.load_data(bd_gui, name1, date1, time1, lat1, lon1, timezoneSelector, dstCheckbox)
        personSelector.setCurrentText(last)

# --- Kapcsolások ---

calcButton.clicked.connect(on_calculate)
savePDF.clicked.connect(on_save_pdf)
readAloud.clicked.connect(on_read_aloud)

musicButton = QPushButton("🎵 Megzenésít + ment WAV-ba")
layout.addWidget(musicButton, 7, 0)
#musicButton.clicked.connect(on_musicalize)

saveButton = QPushButton("💾 Mentés")
layout.addWidget(saveButton, 17, 0, 1, 2)
loadButton = QPushButton("📂 Betöltés")
layout.addWidget(loadButton, 17, 2, 1, 2)
saveButton.clicked.connect(on_save_person)
loadButton.clicked.connect(on_load_person)

prashnaButton.clicked.connect(on_prashna)
varshaphalaButton.clicked.connect(on_varshaphala)
skyMapButton.clicked.connect(on_sky_map)

#infografikaButton.clicked.connect(on_infografika_button_clicked)

window.setLayout(layout)
window.setWindowTitle("SonicJyotish – Egyszerű GUI")
window.show()
sys.exit(app.exec_())

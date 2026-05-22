import os
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QTextDocument
from PyQt5.QtCore import QDate, QTime



# ---------------------------------------------------------\
# Kimeneti mappa
# ---------------------------------------------------------\
def get_output_folder() -> str:
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    folder = os.path.join(downloads, "SonicJyotish")
    os.makedirs(folder, exist_ok=True)
    return folder


# ---------------------------------------------------------\
# Születési adatok kiolvasása a GUI mezőkből
# (A formátum: STRING date + STRING time)
# ---------------------------------------------------------\
def get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector) -> dict:
    return {
        \"name\": name1.text(),
        \"date\": date1.date().toString(\"yyyy-MM-dd\"),
        \"time\": time1.time().toString(\"HH:mm\"),
        \"lat\": lat1.text(),
        \"lon\": lon1.text(),
        \"timezone\": timezoneSelector.currentText(),
    }


# ---------------------------------------------------------\
# Horoszkóp rajzolás és mentés
# ---------------------------------------------------------\
def draw_and_save_horoscope(varga_pos: dict, bd: dict, planet_data: dict, varga_label: str, tithi: int) -> str:
    svg_path, png_path = draw.rajzol_del_indiai_horoszkop_svg(
        varga_pos=varga_pos,
        bd=bd,
        planet_data=planet_data,
        varga_name=varga_label,
        tithi=tithi,
        horoszkop_nev=varga_label,
        date_str=bd["date"],
        time_str=bd["time"],
    )

    return svg_path


# ---------------------------------------------------------\
# Nagyított kép megnyitása
# ---------------------------------------------------------\
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


# ---------------------------------------------------------\
# Elemzés PDF-be
# ---------------------------------------------------------\
def save_analysis_pdf(resultArea):
    path = os.path.join(get_output_folder(), "elemzes.pdf")
    printer = QPrinter()
    printer.setOutputFileName(path)
    printer.setOutputFormat(QPrinter.PdfFormat)

    doc = QTextDocument(resultArea.toPlainText())
    doc.print_(printer)

    resultArea.append(f"📄 PDF mentve: {path}")
    return path


# ---------------------------------------------------------\
# 🎵 Helye a végén: Megzenésítés és WAV generálás indítása
# ---------------------------------------------------------\
def generate_sonic_melodic_wav(bd: dict, chart_data: dict, resultArea) -> str:
    """
    Meghívja a sonic_world modul dallamgenerátorát a GUI-ból átadott 
    születési adatokkal és a kalkulált asztrológiai adatokkal.
    """
    resultArea.append("🎵 Dallamkompozíció és audio szintézis folyamatban...")
    
    try:
        # Lokális import a körkörös hivatkozások szigorú elkerülése érdekében
        from modulok import sonic_world
        
        # Lefuttatjuk a hanghullámok összefűzését és mixelését
        wav_output_path = sonic_world.generate_sonic_jyotish_melodic(bd, chart_data)
        
        resultArea.append(f"✅ Hangfájl sikeresen legenerálva ide:\n   {wav_output_path}")
        return wav_output_path
        
    except Exception as e:
        resultArea.append(f"❌ Hiba a zene generálása közben: {str(e)}")
        return ""
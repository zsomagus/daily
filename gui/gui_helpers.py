import os
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QGridLayout, QLabel
from PyQt5.QtPrintSupport import QPrinter
from PyQt5.QtGui import QTextDocument
from PyQt5.QtCore import QDate, QTime

import modulok.draw as draw



# ---------------------------------------------------------
# Kimeneti mappa
# ---------------------------------------------------------
def get_output_folder() -> str:
    downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    folder = os.path.join(downloads, "SonicJyotish")
    os.makedirs(folder, exist_ok=True)
    return folder


# ---------------------------------------------------------
# Születési adatok kiolvasása a GUI mezőkből
# (A formátum: STRING date + STRING time)
# ---------------------------------------------------------
def get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector) -> dict:
    return {
        "name": name1.text(),
        "date": date1.date().toString("yyyy-MM-dd"),
        "time": time1.time().toString("HH:mm"),
        "lat": lat1.text(),
        "lon": lon1.text(),
        "timezone": timezoneSelector.currentText(),
    }


# ---------------------------------------------------------
# Horoszkóp rajzolás és mentés
# ---------------------------------------------------------
def draw_and_save_chart(bd: dict, varga_label: str, tithi: int, planet_data: dict):
    """
    A varga_adapterből érkező planet_data-t és bd-t átadjuk a draw modulnak.
    """

    # A draw modul paramétersorrendje:
    # rajzol_del_indiai_horoszkop_svg(varga_pos, bd, planet_data, ...)
    svg_path = draw.rajzol_del_indiai_horoszkop_svg(
        planet_data,          # varga_pos (nálad ugyanaz)
        bd,                   # birth data
        planet_data,          # planet_data
        varga_name=varga_label,
        tithi=tithi,
        horoszkop_nev=varga_label,
        date_str=bd["date"],
        time_str=bd["time"],
    )

    return svg_path


# ---------------------------------------------------------
# Nagyított kép megnyitása
# ---------------------------------------------------------
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


# ---------------------------------------------------------
# Elemzés PDF-be
# ---------------------------------------------------------
def save_analysis_pdf(resultArea):
    path = os.path.join(get_output_folder(), "elemzes.pdf")
    printer = QPrinter()
    printer.setOutputFileName(path)
    printer.setOutputFormat(QPrinter.PdfFormat)

    doc = QTextDocument(resultArea.toPlainText())
    doc.print_(printer)

    resultArea.append(f"📄 PDF mentve: {path}")
    return path


# ---------------------------------------------------------
# Megzenésítés (ha később bekötöd)
# ---------------------------------------------------------
def musicalize_and_save(bd: dict, resultArea):
    resultArea.append("🎵 A hangmodul még nincs bekötve ebben a verzióban.")
    return ""

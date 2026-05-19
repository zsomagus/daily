
import os
from modulok import sonic_world
from modulok import varshaphala_tools
from  modulok import prashna_core
from modulok import astro_core
from modulok.tables import (
    nakshatra_data,
    tithi_dynamics,
)

def export_score_to_pdf_and_png(score, folder, base_name):
    pdf_path = os.path.join(folder, base_name + ".pdf")
    png_path = os.path.join(folder, base_name + ".png")

    score.write("musicxml.pdf", fp=pdf_path)
    score.write("musicxml.png", fp=png_path)

    return pdf_path, png_path
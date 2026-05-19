import os
from modulok import sonic_world
def export_score_to_pdf_and_png(score, folder, base_name):
    os.makedirs(folder, exist_ok=True)

    xml_path = os.path.join(folder, base_name + ".musicxml")
    pdf_path = os.path.join(folder, base_name + ".pdf")
    png_path = os.path.join(folder, base_name + ".png")

    # 1) Mindig mentsünk MusicXML-t (ez biztosan működik)
    score.write("musicxml", xml_path)

    # 2) PDF és PNG – csak ha MuseScore elérhető
    try:
        score.write("musicxml.pdf", pdf_path)
    except Exception as e:
        print("PDF export nem sikerült (MuseScore nincs telepítve?):", e)
        pdf_path = None

    try:
        score.write("musicxml.png", png_path)
    except Exception as e:
        print("PNG export nem sikerült (MuseScore nincs telepítve?):", e)
        png_path = None

    return xml_path, pdf_path, png_path

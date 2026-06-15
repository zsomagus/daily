# modulok/elemzes.py

import os
import re
import textwrap
from pathlib import Path

import pandas as pd
import pendulum
import pyttsx3
from markdown import markdown
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.pdfgen import canvas

from modulok.config import BASE_DIR
from modulok import astro_core
from modulok.visuals import generate_visuals_from_summary
from modulok.tables import haz_aspektusok, haz_bolygo_aspektusok
from modulok.terkep import redraw_map
# -------------------------------------------------------------------
# Alap beállítások
# -------------------------------------------------------------------

OUTPUT_DIR = os.path.expanduser("~/Letöltések/SonicJyotish")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Excel adatbázis betöltése
excel_path = BASE_DIR / "static" / "asztrológiai_adatbázis.xlsx"
jegyek_df = pd.read_excel(excel_path, sheet_name="Jegyek")
hazak_df = pd.read_excel(excel_path, sheet_name="Házak")
bolygok_df = pd.read_excel(excel_path, sheet_name="Bolygók")
nakshatra_df = pd.read_excel(excel_path, sheet_name="Nakshatra _ Pada")

# -------------------------------------------------------------------
# Segédfüggvények – adatbázis alapú szövegek
# -------------------------------------------------------------------

def get_jegy_info(jegy):
    match = jegyek_df[jegyek_df["Jegy"] == jegy]
    return match.iloc[0]["Tulajdonságok"] if not match.empty else "Ismeretlen jegy."

def get_haz_info(haz_szam):
    match = hazak_df[hazak_df["Ház száma"] == haz_szam]
    if not match.empty:
        return match.iloc[0]["Tulajdonságok"]
    return "Ismeretlen ház."

def get_bolygo_info(bolygo):
    match = bolygok_df[bolygok_df["Bolygó"] == bolygo]
    return match.iloc[0]["Tulajdonságok"] if not match.empty else "Ismeretlen bolygó."

def get_purushartha_from_pada(pada):
    # 1–4: Dharma, Artha, Kama, Moksha
    mapping = ["Dharma", "Artha", "Kama", "Moksha"]
    if 1 <= pada <= 4:
        return mapping[pada - 1]
    return "Ismeretlen"

def get_nakshatra_info(nakshatra, pada):
    match = nakshatra_df[nakshatra_df["Nakshatra"] == nakshatra]
    if not match.empty:
        col = f"{pada}. Páda ({get_purushartha_from_pada(pada)})"
        return match.iloc[0].get(col, "Hiányzó pada értelmezés.")
    return "Ismeretlen nakshatra vagy pada."

# -------------------------------------------------------------------
# Lélek Útiterve – spirituális blokk
# -------------------------------------------------------------------

def generate_souls_roadmap(chart):
    planets = chart.get("planets", {})
    houses = chart.get("houses", {})

    sun = planets.get("Sun", {})
    saturn = planets.get("Saturn", {})
    rahu = planets.get("Rahu", {})
    ketu = planets.get("Ketu", {})

    def fmt_planet(p):
        sign = p.get("sign", "ismeretlen jegy")
        deg = p.get("deg", 0)
        return f"{sign} ({deg:.1f}°)"

    md = "\n---\n\n## 🕉️ A Lélek Útiterve (The Soul's Roadmap)\n\n"

    # Nap – életcél
    md += "### ☀️ Nap – Mi a célod?\n"
    if sun:
        md += f"A Nap jelenlegi helyzete: **{fmt_planet(sun)}**. "
        md += "Ez mutatja, hol ragyogsz, hol tudsz önazonosan jelen lenni, "
        md += "és milyen minőségek mentén tudsz vezetni, alkotni, jelen lenni a világban.\n\n"
    else:
        md += "A Nap pozíciója nem elérhető ebben a képletben.\n\n"

    # Szaturnusz – lecke
    md += "### ♄ Szaturnusz – Mi a lecke?\n"
    if saturn:
        md += f"A Szaturnusz helyzete: **{fmt_planet(saturn)}**. "
        md += "Ez jelöli azokat a területeket, ahol felelősséget, kitartást és türelmet tanulsz. "
        md += "Itt lassabban érkeznek az eredmények, de amit itt felépítesz, az tartós marad.\n\n"
    else:
        md += "A Szaturnusz pozíciója nem elérhető ebben a képletben.\n\n"

    # Rahu–Ketu tengely
    md += "### ☊☋ Rahu–Ketu tengely – Múlt és jövő\n"
    if rahu and ketu:
        md += f"Rahu: **{fmt_planet(rahu)}**, Ketu: **{fmt_planet(ketu)}**. "
        md += "A Rahu jelzi, merre tart a lélek – azokat a tapasztalatokat, amelyek felé vonzódsz, "
        md += "még ha ismeretlenek is. A Ketu a hozott múlt, a korábbi életek lenyomata, "
        md += "ahol már van tapasztalat, de néha túltelítettség is.\n\n"
    else:
        md += "A Rahu–Ketu tengely adatai nem teljesek ebben a képletben.\n\n"

    # Összegzés
    md += "### 🔮 Összegzés – A jövő iránya\n"
    md += "A képlet azt mutatja, hogy a lélek útja nem véletlenszerű: "
    md += "a Nap célja, a Szaturnusz leckéi és a Rahu–Ketu tengely együtt rajzolják ki azt az irányt, "
    md += "amerre érdemes fejlődnöd. Ha a belső hívást követed, és türelemmel vállalod a tanulást, "
    md += "a sorsod egyre inkább összhangba kerül a belső igazságoddal.\n\n"

    return md

# -------------------------------------------------------------------
# Markdown elemzés generálása astro_core chartból
# -------------------------------------------------------------------

def generate_markdown_summary_from_chart(chart, meta):
    """
    chart: astro_core.generate_chart visszatérési dict
    meta:  kiegészítő adatok (név, dátum, idő, hely stb.)
    """
    planets = chart.get("planets", {})
    asc = chart.get("ascendant", {})
    tithi = chart.get("tithi", None)

    md = "# 🌠 Asztrológiai Elemzés\n\n"

    # Meta blokk
    md += f"**Név**: {meta.get('keresztnev', '')} {meta.get('vezeteknev', '')}\n\n"
    md += f"**Dátum**: {meta.get('date_str', '')}\n\n"
    md += f"**Idő**: {meta.get('time_str', '')}\n\n"
    if meta.get("place_str"):
        md += f"**Hely**: {meta.get('place_str')}\n\n"
    if tithi is not None:
        md += f"**Tithi**: {tithi}\n\n"
    md += f"**Horoszkóp típusa**: {meta.get('horoszkop_nev', 'D1')}\n\n"

    # Ascendens
    if asc:
        md += "## 🔹 Ascendens\n"
        md += f"- **Jegy**: {asc.get('sign', 'ismeretlen')}\n"
        md += f"- **Fok**: {asc.get('deg', 0):.1f}°\n\n"

    # Bolygók
    for bolygo, adat in planets.items():
        sign = adat.get("sign", "ismeretlen")
        deg = adat.get("deg", 0)
        nak = adat.get("nakshatra", None)
        pada = adat.get("pada", None)

        md += f"## 🔹 {bolygo}\n"
        md += f"- **Jegy**: {sign} ({deg:.1f}°)\n"

        # Ház – ha van
        haz = adat.get("house")
        if haz is not None:
            md += f"- **Ház**: {haz}\n"
            md += f"- **Ház jellemzői**: {get_haz_info(haz)}\n"

        # Nakshatra
        if nak and pada:
            md += f"- **Nakshatra**: {nak} – {pada}. páda ({get_purushartha_from_pada(pada)})\n"
            md += f"- **Nakshatra értelmezés**: {get_nakshatra_info(nak, pada)}\n"

        md += f"- **Bolygó tulajdonságai**: {get_bolygo_info(bolygo)}\n"
        md += f"- **Jegy jellemzői**: {get_jegy_info(sign)}\n\n"

    # Lélek Útiterve blokk
    md += generate_souls_roadmap(chart)

    # Vizuális archetípusok – promptok
    md += "\n---\n\n## 🎨 Vizuális archetípusok\n"
    md += "_Ezeket a leírásokat másold be egy képgenerátorba (pl. Midjourney, DALL·E, Stable Diffusion)._ \n\n"

    summary_text = md  # teljes szöveg alapján generálunk vizuális promptokat
    viz_prompts = generate_visuals_from_summary(summary_text, "Összkép", "Rashi", "1")
    for i, prompt in enumerate(viz_prompts, 1):
        md += f"- Kép {i}: *{prompt}*\n"

    return md

# -------------------------------------------------------------------
# PDF generálás – fejléc, lábléc, első oldali kép
# -------------------------------------------------------------------

def _draw_header_footer(c, width, height):
    # Fejléc
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.HexColor("#2E4E1F"))
    c.drawCentredString(width / 2, height - 1.5 * cm, "HINDU–VÉDIKUS")
    c.drawCentredString(width / 2, height - 2.1 * cm, "ASZTROLÓGIAI ELEMZÉS")
    c.setStrokeColor(colors.HexColor("#2E4E1F"))
    c.setLineWidth(2)
    c.line(2 * cm, height - 2.4 * cm, width - 2 * cm, height - 2.4 * cm)

    # Lábléc
    c.setFont("Helvetica", 9)
    c.setFillColor(colors.grey)
    c.drawCentredString(width / 2, 1.2 * cm, "Készítette: Mucsi Zsombor – Védikus asztrológus")

def save_analysis_pdf(md_text, meta, image_path=None):
    safe_name = re.sub(r"[^\w\-]", "_", f"{meta.get('keresztnev','')}_{meta.get('vezeteknev','')}".strip())
    filename = os.path.join(OUTPUT_DIR, f"{safe_name}_elemzes.pdf")

    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    margin_x = 2 * cm
    text_top = height - 3 * cm  # fejléc alatt
    y = text_top

    def new_page():
        nonlocal y
        c.showPage()
        _draw_header_footer(c, width, height)
        y = text_top

    # Első oldal fejléc + lábléc
    _draw_header_footer(c, width, height)

    # Ha van kép (Rashi + yantra), tegyük az első oldal jobb felső részére
    if image_path and os.path.exists(image_path):
        img_w = 8 * cm
        img_h = 8 * cm
        img_x = width - margin_x - img_w
        img_y = height - 3 * cm - img_h
        c.drawImage(image_path, img_x, img_y, width=img_w, height=img_h, preserveAspectRatio=True, anchor='nw')
        # Szöveg kezdő y kicsit lejjebb
        y = img_y - 1 * cm
    else:
        y = text_top

    # Markdown → sima szöveg sorokra tördelve
    # Egyszerű megoldás: a md_text sorait wrap-oljuk
    c.setFont("Helvetica", 11)
    c.setFillColor(colors.black)

    max_width = width - 2 * margin_x
    wrapper = textwrap.TextWrapper(width=90)

    for raw_line in md_text.split("\n"):
        # Üres sor → sortörés
        if not raw_line.strip():
            y -= 14
            if y < 2.5 * cm:
                new_page()
            continue

        for line in wrapper.wrap(raw_line):
            if y < 2.5 * cm:
                new_page()
            c.drawString(margin_x, y, line)
            y -= 14

    c.save()
    return filename

# -------------------------------------------------------------------
# Hangos felolvasás
# -------------------------------------------------------------------

def save_analysis_audio(text, meta):
    safe_name = re.sub(r"[^\w\-]", "_", f"{meta.get('keresztnev','')}_{meta.get('vezeteknev','')}".strip())
    filename = os.path.join(OUTPUT_DIR, f"{safe_name}_elemzes.wav")

    engine = pyttsx3.init()
    engine.setProperty("rate", 155)
    engine.setProperty("volume", 0.9)
    # egyszerűbb, természetesebb hangzás: mondatközi szünetekhez a szövegben is lehet pontokat, sortöréseket használni
    engine.save_to_file(text, filename)
    engine.runAndWait()
    engine = pyttsx3.init()
    
    # KIKERESSÜK A MAGYAR HANGOT A WINDOWSBÓL
    voices = engine.getProperty('voices')
    for voice in voices:
        if "hungarian" in voice.name.lower() or "hu-HU" in voice.id:
            engine.setProperty('voice', voice.id)
            break
    return filename

# -------------------------------------------------------------------
# Horoszkóp kép generálása (Rashi + yantra)
# -------------------------------------------------------------------
# -------------------------------------------------------------------
# Horoszkóp kép generálása (Rashi + yantra)
# -------------------------------------------------------------------

def generate_chart_image(chart, meta):
    

    return None

# -------------------------------------------------------------------
# Fő belépő – teljes elemzés generálása egy gombnyomásra
# -------------------------------------------------------------------

def generate_full_analysis(
    date_str: str,
    time_str: str,
    timezone_str: str,
    latitude: float,
    longitude: float,
    vezeteknev: str,
    keresztnev: str,
    varga_nev: str = "D1",
    place_str: str = "",
    is_prashna: bool = False,
):
    """
    Teljes folyamat:
    - astro_core.generate_chart hívása
    - Markdown elemzés generálása
    - PDF mentése (fejléc + lábléc + Rashi+yantra kép)
    - Hangos felolvasás mentése
    """

    # 1) Dátum/idő → datetime
    local_dt = pendulum.parse(f"{date_str}T{time_str}", tz=timezone_str)
    year, month, day = local_dt.year, local_dt.month, local_dt.day
    hour, minute = local_dt.hour, local_dt.minute

# modulok/elemzes.py -> kb. 350. sor
    # JAVÍTVA: A függvény valódi argumentumneveit (latitude, longitude) alakítjuk float-tá!
    chart = astro_core.generate_chart(
        name=f"{keresztnev} {vezeteknev}",
        year=local_dt.year,
        month=local_dt.month,
        day=local_dt.day,
        hour=local_dt.hour,
        minute=local_dt.minute,
        lat=float(latitude),   # 👈 latitude_str helyett simán latitude!
        lng=float(longitude),  # 👈 longitude_str helyett simán longitude!
    )

    # 3) Meta adatok
    meta = {
        "date_str": date_str,
        "time_str": time_str,
        "timezone_str": timezone_str,
        "latitude": latitude,
        "longitude": longitude,
        "vezeteknev": vezeteknev,
        "keresztnev": keresztnev,
        "varga_nev": varga_nev,
        "horoszkop_nev": varga_nev,
        "place_str": place_str,
        "is_prashna": is_prashna,
        "tithi": chart.get("tithi"),
    }

    # 4) Horoszkóp kép generálása (Rashi + yantra)
    image_path = generate_chart_image(chart, meta)

    # 5) Markdown elemzés
    md_text = generate_markdown_summary_from_chart(chart, meta)

    # 6) PDF mentés
    pdf_path = save_analysis_pdf(md_text, meta, image_path=image_path)

    # 7) Hangos felolvasás
    audio_path = save_analysis_audio(md_text, meta)

    return {
        "chart": chart,
        "markdown": md_text,
        "pdf_path": pdf_path,
        "audio_path": audio_path,
        "image_path": image_path,
    }
# modulok/elemzes.py

def generate_varshaphala_forecast_block(varsha_data, age: int):
    """
    Egyszerű, érthető éves előrejelzés blokk Varshaphalára.
    varsha_data: a compute_varshaphala_chart visszatérési dict-je
    """
    tithi = varsha_data.get("tithi")
    chart = varsha_data.get("chart", {})
    planets = chart.get("planets", {})

    md = "\n---\n\n## 📅 Varshaphala – Éves előrejelzés\n\n"
    md += f"**Életkor**: {age} év\n\n"

    if tithi is not None:
        md += f"- **Születésnapi Tithi**: {tithi} – ez mutatja az év alaprezgését, hangulatát.\n"

    asc = chart.get("ascendant", {})
    if asc:
        md += f"- **Varshaphala Ascendens**: {asc.get('sign','ismeretlen')} – az év fókuszterülete.\n"

    sun = planets.get("Sun", {})
    if sun:
        md += f"- **Nap helyzete az éves képletben**: {sun.get('sign','ismeretlen')} – az év fő témája, önkifejezés.\n"

    saturn = planets.get("Saturn", {})
    if saturn:
        md += f"- **Szaturnusz az éves képletben**: {saturn.get('sign','ismeretlen')} – felelősség, próbatételek területe.\n"

    rahu = planets.get("Rahu", {})
    ketu = planets.get("Ketu", {})
    if rahu and ketu:
        md += f"- **Rahu–Ketu tengely az éves képletben**: {rahu.get('sign','?')} – {ketu.get('sign','?')} – karmikus irányváltások.\n"

    md += "\nEz a Varshaphala képlet azt mutatja, hogy ebben az évben mely életterületek kerülnek fókuszba, "
    md += "hol kér tőled az élet több tudatosságot, felelősséget, és hol nyílnak új lehetőségek.\n"

    return md

    # miután megvan a chart + meta:
    map_path = redraw_map(chart, meta)
    print("Karmikus térkép:", map_path)

# Egyszerű teszt
def teszt():
    print("Elemzés modul betöltve (új, astro_core-alapú verzió).")

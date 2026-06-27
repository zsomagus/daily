import svgwrite
import os
import re
from collections import Counter
import cairosvg

# ----------------------- BETŰ MAP -----------------------
letter_map = {
    1: "AJS", 2: "BKT", 3: "CLU", 4: "DMV", 5: "ENW",
    6: "FOX", 7: "GPY", 8: "HQZ", 9: "IR"
}

char_to_num = {}
for num, chars in letter_map.items():
    for c in chars:
        char_to_num[c] = num

# ----------------------- SEGÉDFÜGGVÉNYEK -----------------------
def clean_text(text):
    text = text.upper()
    repl = {"Á":"A","É":"E","Í":"I","Ó":"O","Ö":"O","Ő":"O","Ú":"U","Ü":"U","Ű":"U"}
    for k,v in repl.items():
        text = text.replace(k,v)
    return re.sub(r'[^A-Z]', '', text)

def text_to_numbers(text):
    text = clean_text(text)
    return [char_to_num[c] for c in text if c in char_to_num]

def digits(s):
    return [int(c) for c in re.sub(r'\D', '', s) if c != '0']

def life_path(date_nums):
    total = sum(date_nums)
    while total > 9:
        total = sum(int(c) for c in str(total))
    return total

# ----------------------- SVG GENERÁLÁS -----------------------
def draw_svg(name, date, time, name_c, date_c, time_c, name_nums, date_nums, time_nums, filepath):
    dwg = svgwrite.Drawing(filepath, size=(1250, 950))

    FONT_MAIN = "Cinzel"
    FONT_SCRIPT = "Great Vibes"

    # Bal oldali körök
    start_x, start_y = 60, 60
    cell = 130

    positions = {1:(0,0),2:(1,0),3:(2,0),4:(0,1),5:(1,1),6:(2,1),7:(0,2),8:(1,2),9:(2,2)}

    # Keret és rács
    dwg.add(dwg.rect((start_x-15, start_y-15), (cell*3+30, cell*3+30), stroke="black", fill="none", stroke_width=4))
    for i in range(4):
        dwg.add(dwg.line((start_x, start_y + i*cell), (start_x+3*cell, start_y + i*cell), stroke="black", stroke_width=2))
        dwg.add(dwg.line((start_x + i*cell, start_y), (start_x + i*cell, start_y+3*cell), stroke="black", stroke_width=2))

    # Számok + körök
    for num, (x,y) in positions.items():
        cx = start_x + x*cell + cell/2
        cy = start_y + y*cell + cell/2

        dwg.add(dwg.text(str(num), insert=(cx-18, cy+18), font_size=48, font_family=FONT_MAIN, font_weight="bold"))

        # Név (fekete)
        for i in range(name_c[num]):
            dwg.add(dwg.circle((cx, cy), r=32 + i*7, stroke="black", fill="none", stroke_width=3))
        # Dátum (zöld)
        for i in range(date_c[num]):
            dwg.add(dwg.circle((cx, cy), r=24 + i*7, stroke="#2E8B57", fill="none", stroke_width=3))
        # Idő (kék)
        for i in range(time_c[num]):
            dwg.add(dwg.circle((cx, cy), r=16 + i*7, stroke="#1E90FF", fill="none", stroke_width=3))

    # Alsó címek
    labels = ["Test", "Lélek", "Szellem"]
    for i, label in enumerate(labels):
        dwg.add(dwg.text(label, insert=(start_x + i*cell + 25, start_y + 3*cell + 55),
                         font_family=FONT_SCRIPT, font_size=28))

    # Jobb oldal
    x = 520
    y = 80
    dwg.add(dwg.text(f"Név: {name}", insert=(x, y), font_family=FONT_SCRIPT, font_size=26))
    y += 35
    dwg.add(dwg.text(f"Születési dátum: {date}", insert=(x, y), font_family=FONT_SCRIPT, font_size=22))
    y += 30
    dwg.add(dwg.text(f"Idő: {time}", insert=(x, y), font_family=FONT_SCRIPT, font_size=22))

    # Legend
    ly = 190
    dwg.add(dwg.circle((x, ly), r=9, stroke="black", fill="none", stroke_width=3))
    dwg.add(dwg.text("Név (betűk)", insert=(x+25, ly+5), font_size=15))
    ly += 30
    dwg.add(dwg.circle((x, ly), r=9, stroke="#2E8B57", fill="none", stroke_width=3))
    dwg.add(dwg.text("Születési dátum", insert=(x+25, ly+5), font_size=15))
    ly += 30
    dwg.add(dwg.circle((x, ly), r=9, stroke="#1E90FF", fill="none", stroke_width=3))
    dwg.add(dwg.text("Idő", insert=(x+25, ly+5), font_size=15))

    # Betű térkép
    y = 320
    for i in range(1,10):
        dwg.add(dwg.text(f"{i}: {letter_map[i]}", insert=(x, y), font_size=15))
        y += 22

    # Számolás
    y = 520
    dwg.add(dwg.text("Számolás", insert=(60, y), font_family=FONT_SCRIPT, font_size=26))
    y += 35
    dwg.add(dwg.text("Név számai:", insert=(60, y), font_size=15))
    dwg.add(dwg.text(" ".join(map(str, name_c.elements())), insert=(60, y+25), font_size=14))
    
    y += 55
    dwg.add(dwg.text("Születési dátum számai:", insert=(60, y), font_size=15))
    dwg.add(dwg.text(" ".join(map(str, date_c.elements())), insert=(60, y+25), font_size=14))

    y += 55
    dwg.add(dwg.text("Idő számai:", insert=(60, y), font_size=15))
    dwg.add(dwg.text(" ".join(map(str, time_c.elements())), insert=(60, y+25), font_size=14))

    # Életút
    lp = life_path(list(date_c.elements()))
    y += 70
    dwg.add(dwg.text(f"Életút szám: {lp}", insert=(60, y), font_size=18, font_weight="bold"))
    if lp == 5:
        dwg.add(dwg.text("Szabadság vándora", insert=(60, y+30), font_size=17, fill="green"))

    # Elemzés (jobbra)
    y = 520
    dwg.add(dwg.text("Elemzés", insert=(520, y), font_family=FONT_SCRIPT, font_size=26))
    # ===================== AUTOMATIKUS ELEMZÉS =====================
    y += 40
    elemzesek = {
        1: "Akarat, vezetés – az 1-es életút az önálló, kezdeményező személyiséget jelképezi. Erőssége a céltudatosság, gyengesége a túlzott ego.",
        2: "Érzékenység, együttműködés – a 2-es életút a diplomatikus, empatikus lélek. Erőssége a harmónia, gyengesége a bizonytalanság.",
        3: "Kommunikáció, kreativitás – a 3-as életút a vidám, inspiráló személyiség. Erőssége az önkifejezés, gyengesége a szétszórtság.",
        4: "Stabilitás, munka – a 4-es életút a kitartó, rendszerező ember. Erőssége a megbízhatóság, gyengesége a merevség.",
        5: "Szabadság, változás – az 5-ös életút a kalandvágyó, rugalmas lélek. Erőssége az alkalmazkodás, gyengesége a nyughatatlanság.",
        6: "Szeretet, felelősség – a 6-os életút a gondoskodó, családcentrikus ember. Erőssége az odaadás, gyengesége a túlzott aggódás.",
        7: "Spiritualitás, befelé figyelés – a 7-es életút a kutató, bölcs személyiség. Erőssége az elemző gondolkodás, gyengesége az elzárkózás.",
        8: "Hatalom, anyagi világ – a 8-as életút az ambiciózus, céltudatos ember. Erőssége a vezetői képesség, gyengesége a túlzott kontroll.",
        9: "Bölcsesség, segítés – a 9-es életút az idealista, együttérző lélek. Erőssége a humanizmus, gyengesége az önfeláldozás."
    }

    def wrap_text(text, width=80):
        """Tördelés több sorba, ha hosszú az elemzés."""
        import textwrap
        return textwrap.wrap(text, width)

    # Életút-szám
    dwg.add(dwg.text(f"Életút szám ({lp}):", insert=(520, y), font_size=18, font_weight="bold"))
    y += 25
    for line in wrap_text(elemzesek.get(lp, "Nincs elemzés ehhez az életút számhoz.")):
        dwg.add(dwg.text(line, insert=(520, y), font_size=14))
        y += 20

    # Lélek-szám (névszám)
    y += 30
    nev_osszeg = sum(name_nums)
    while nev_osszeg > 9:
        nev_osszeg = sum(int(c) for c in str(nev_osszeg))
    dwg.add(dwg.text(f"Lélek-szám (névszám): {nev_osszeg}", insert=(520, y), font_size=18, font_weight="bold"))
    y += 25
    for line in wrap_text(elemzesek.get(nev_osszeg, "Nincs elemzés.")):
        dwg.add(dwg.text(line, insert=(520, y), font_size=14))
        y += 20

    # Sors-szám (születési dátum)
    y += 30
    sors = sum(date_nums)
    while sors > 9:
        sors = sum(int(c) for c in str(sors))
    dwg.add(dwg.text(f"Sors-szám: {sors}", insert=(520, y), font_size=18, font_weight="bold"))
    y += 25
    for line in wrap_text(elemzesek.get(sors, "Nincs elemzés.")):
        dwg.add(dwg.text(line, insert=(520, y), font_size=14))
        y += 20

        # ===================== KARMA-SZÁMOK =====================
    y += 40
    all_nums = set(range(1, 10))
    present_nums = set(name_c.keys()) | set(date_c.keys()) | set(time_c.keys())
    missing = sorted(list(all_nums - present_nums))

    karma_jelentes = {
        1: "Hiányzó 1 → az önbizalom, kezdeményezés és vezetői képesség fejlesztése szükséges.",
        2: "Hiányzó 2 → az együttműködés, empátia és érzékenység tanulása áll előtérben.",
        3: "Hiányzó 3 → a kommunikáció, önkifejezés és kreativitás kibontakoztatása a feladat.",
        4: "Hiányzó 4 → a fegyelem, kitartás és gyakorlati gondolkodás elsajátítása fontos.",
        5: "Hiányzó 5 → a rugalmasság, szabadság és változások elfogadása a fejlődés kulcsa.",
        6: "Hiányzó 6 → a felelősségvállalás, szeretet és családi harmónia megteremtése szükséges.",
        7: "Hiányzó 7 → a belső hit, önvizsgálat és spirituális tudás fejlesztése a cél.",
        8: "Hiányzó 8 → az anyagi világ, hatalom és önérvényesítés tudatos kezelése a feladat.",
        9: "Hiányzó 9 → az együttérzés, bölcsesség és segítőkészség kibontakoztatása szükséges."
    }

    dwg.add(dwg.text("Karma-szám(ok):", insert=(520, y), font_size=18, font_weight="bold"))
    y += 25

    if missing:
        dwg.add(dwg.text(f"Hiányzó számok: {', '.join(map(str, missing))}", insert=(520, y), font_size=14))
        y += 25
        dwg.add(dwg.text("Ezek a számok jelzik azokat a tapasztalatokat, amelyeket ebben az életben kell elsajátítani:", insert=(520, y), font_size=14))
        y += 25
        for num in missing:
            for line in wrap_text(karma_jelentes[num], width=80):
                dwg.add(dwg.text(line, insert=(520, y), font_size=14))
                y += 20
    else:
        dwg.add(dwg.text("Nincs hiányzó szám – kiegyensúlyozott numerológiai mintázat.", insert=(520, y), font_size=14))
    # ===================== TEST – LÉLEK – SZELLEM HÁROMSZÖG =====================
    y += 50
    dwg.add(dwg.text("Test – Lélek – Szellem háromszög", insert=(520, y), font_size=20, font_weight="bold"))
    y += 35

    # Háromszög értékek
    test_sum = sum(name_nums)
    while test_sum > 9:
        test_sum = sum(int(c) for c in str(test_sum))

    lelek_sum = sum(date_nums)
    while lelek_sum > 9:
        lelek_sum = sum(int(c) for c in str(lelek_sum))

    szellem_sum = sum(time_nums)
    while szellem_sum > 9:
        szellem_sum = sum(int(c) for c in str(szellem_sum))

    haromszog_elemzes = {
        1: "Erős fizikai energia, kezdeményezőkészség, vezetői dinamika.",
        2: "Érzékeny test, finom energiák, együttműködő természet.",
        3: "Kreatív testkifejezés, mozgásigény, játékosság.",
        4: "Stabil fizikum, fegyelmezett életvitel, rendszeretet.",
        5: "Rugalmas test, mozgékonyság, szabadságvágy.",
        6: "Gondoskodó energia, harmóniaigény, kiegyensúlyozottság.",
        7: "Belső fókusz, visszahúzódó energia, spirituális testérzékelés.",
        8: "Erőteljes fizikum, kitartás, anyagi stabilitásra törekvés.",
        9: "Humanitárius energia, segítőkészség, magas rezgés."
    }

    # Test
    dwg.add(dwg.text(f"Test-szám: {test_sum}", insert=(520, y), font_size=17, font_weight="bold"))
    y += 25
    for line in wrap_text(haromszog_elemzes.get(test_sum, "Nincs elemzés."), width=80):
        dwg.add(dwg.text(line, insert=(520, y), font_size=14))
        y += 20

    # Lélek
    y += 30
    dwg.add(dwg.text(f"Lélek-szám: {lelek_sum}", insert=(520, y), font_size=17, font_weight="bold"))
    y += 25
    for line in wrap_text(haromszog_elemzes.get(lelek_sum, "Nincs elemzés."), width=80):
        dwg.add(dwg.text(line, insert=(520, y), font_size=14))
        y += 20

    # Szellem
    y += 30
    dwg.add(dwg.text(f"Szellem-szám: {szellem_sum}", insert=(520, y), font_size=17, font_weight="bold"))
    y += 25
    for line in wrap_text(haromszog_elemzes.get(szellem_sum, "Nincs elemzés."), width=80):
        dwg.add(dwg.text(line, insert=(520, y), font_size=14))
        y += 20
    # ===================== TEST–LÉLEK–SZELLEM GRAFIKUS HÁROMSZÖG =====================
    y += 60
    dwg.add(dwg.text("Háromszög diagram", insert=(520, y), font_size=20, font_weight="bold"))
    y += 30

    # Háromszög középpont
    cx = 250
    cy = y + 150

    # Skála (minden szám 1–9 → 20px lépés)
    scale = 20

    # Pontok kiszámítása
    # Test → bal alsó irány
    tx = cx - test_sum * scale
    ty = cy + test_sum * scale

    # Lélek → jobb alsó irány
    lx = cx + lelek_sum * scale
    ly = cy + lelek_sum * scale

    # Szellem → felső irány
    sx = cx
    sy = cy - szellem_sum * scale

    # Háromszög vonalak
    dwg.add(dwg.line((tx, ty), (lx, ly), stroke="black", stroke_width=2))
    dwg.add(dwg.line((lx, ly), (sx, sy), stroke="black", stroke_width=2))
    dwg.add(dwg.line((sx, sy), (tx, ty), stroke="black", stroke_width=2))

    # Pontok
    dwg.add(dwg.circle((tx, ty), r=6, fill="black"))
    dwg.add(dwg.circle((lx, ly), r=6, fill="black"))
    dwg.add(dwg.circle((sx, sy), r=6, fill="black"))

    # Feliratok
    dwg.add(dwg.text("Test", insert=(tx - 40, ty + 20), font_size=14))
    dwg.add(dwg.text("Lélek", insert=(lx + 10, ly + 20), font_size=14))
    dwg.add(dwg.text("Szellem", insert=(sx - 20, sy - 15), font_size=14))

    # ===================== DOMINÁNS ENERGIA ÉS EGYENSÚLY-ELEMZÉS =====================
    y += 60
    dwg.add(dwg.text("Domináns energia és egyensúly elemzés", insert=(520, y), font_size=20, font_weight="bold"))
    y += 35

    # Domináns energia meghatározása
    energies = {"Test": test_sum, "Lélek": lelek_sum, "Szellem": szellem_sum}
    dominant = max(energies, key=energies.get)
    dwg.add(dwg.text(f"Domináns energia: {dominant} ({energies[dominant]})", insert=(520, y), font_size=17, font_weight="bold"))
    y += 25

    dominant_texts = {
        "Test": "A fizikai, cselekvő oldal dominál – erős akarat, gyakorlati érzék, megvalósító energia.",
        "Lélek": "Az érzelmi, intuitív oldal dominál – érzékenység, empátia, szabadságvágy, belső harmónia keresése.",
        "Szellem": "A mentális, spirituális oldal dominál – tudásvágy, elemző gondolkodás, belső bölcsesség."
    }

    for line in wrap_text(dominant_texts[dominant], width=80):
        dwg.add(dwg.text(line, insert=(520, y), font_size=14))
        y += 20

    # Háromszög egyensúly elemzés
    y += 30
    dwg.add(dwg.text("Háromszög egyensúly:", insert=(520, y), font_size=17, font_weight="bold"))
    y += 25

    diff = max(energies.values()) - min(energies.values())
    if diff <= 1:
        balance_text = "Harmonikus háromszög – kiegyensúlyozott Test–Lélek–Szellem energia."
    elif diff <= 3:
        balance_text = "Enyhén torz háromszög – egyik energia kissé dominál, de az összhang megvan."
    else:
        balance_text = "Torz háromszög – jelentős különbség az energiák között, fejlődési irányt jelez."

    for line in wrap_text(balance_text, width=80):
        dwg.add(dwg.text(line, insert=(520, y), font_size=14))
        y += 20

    # Automatikus lapmagasság növelés
    current_height = int(str(dwg['height']).replace('px', ''))
    if y + 200 > current_height:
        dwg['height'] = f"{y + 300}px"

    # Automatikus lapmagasság növelés
    current_height = int(str(dwg['height']).replace('px', ''))
    if sy + 200 > current_height:
        dwg['height'] = f"{sy + 250}px"

    # Automatikus lapmagasság‑növelés, ha sok szöveg van
    current_height = int(dwg['height'].replace('px', ''))
    if y + 100 > current_height:
        dwg['height'] = f"{y + 150}px"

    dwg.save()

# ----------------------- MAIN -----------------------
def main():
    print("=== Numerológia Diagram Generátor ===\n")
    name = input("Név: ").strip()
    date = input("Születési dátum (pl. 1976.03.15): ").strip()
    time = input("Születési idő (pl. 21:53): ").strip()

    name_nums = text_to_numbers(name)
    date_nums = digits(date)
    time_nums = digits(time)

    name_c = Counter(name_nums)
    date_c = Counter(date_nums)
    time_c = Counter(time_nums)

    base = os.path.join(os.path.expanduser("~"), "Downloads", "numerologia")
    os.makedirs(base, exist_ok=True)

    filename = clean_text(name.lower())
    svg_path = os.path.join(base, f"{filename}_numerologia.svg")
    pdf_path = os.path.join(base, f"{filename}_numerologia.pdf")

    draw_svg(name, date, time, name_c, date_c, time_c, name_nums, date_nums, time_nums, svg_path)
    
    try:
        cairosvg.svg2pdf(url=svg_path, write_to=pdf_path)
        print(f"\n✅ Kész! Fájlok elmentve:")
        print(f"   • {svg_path}")
        print(f"   • {pdf_path}")
    except:
        print(f"\n✅ SVG elkészült: {svg_path}")
        print("   (PDF konvertáláshoz telepítsd: sudo apt install cairo")

if __name__ == "__main__":
    main()

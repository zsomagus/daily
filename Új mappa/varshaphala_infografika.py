# modulok/varshaphala_infografika.py

import os
import svgwrite
from pathlib import Path
from graphviz import Digraph

from modulok.tables import RULERSHIP, nakshatra_data
from modulok.elemzes_core import generate_full_analysis
from modulok import varshaphala_tools
from modulok.tables import SIGN_MAP

BASE_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------
# 1) Nakshatra urak betöltése
# ---------------------------------------------------------

def load_nakshatra_rulers():
    df = nakshatra_df
    return dict(zip(df.iloc[:, 0].astype(str), df.iloc[:, 1].astype(str)))


# ---------------------------------------------------------
# 2) Markdown → pozíciók
# ---------------------------------------------------------

def parse_md(md: str):
    import re
    positions = {}

    planet_re = re.compile(
        r"## 🔹 (?P<planet>[^\n]+)\n(?P<body>.*?)(?=\n## |\Z)", re.S
    )
    field_re = re.compile(
        r"- \*\*(?P<label>[^*]+)\*\*: (?P<value>[^\n]+)"
    )

    for m in planet_re.finditer(md):
        planet = m.group("planet").strip()
        body = m.group("body")

        fields = {
            fm.group("label").strip(): fm.group("value").strip()
            for fm in field_re.finditer(body)
        }

        positions[planet] = {
            "sign": fields.get("Jegy"),
            "house": fields.get("Ház"),
            "nakshatra": fields.get("Nakshatra"),
            "pada": fields.get("Pada"),
        }

    return positions


# ---------------------------------------------------------
# 3) Varshaphala gráf
# ---------------------------------------------------------

def build_varshaphala_graph(positions, nak_rulers, varshesh, muntha):
    dot = Digraph(comment="Varshaphala Patterns", format="svg")
    dot.attr(rankdir="LR", bgcolor="#0b1220", fontname="Inter")

    def node(n, t, color):
        dot.node(
            n, n,
            shape="box" if t != "bolygó" else "circle",
            style="filled",
            color=color,
            fontcolor="white"
        )

    if muntha:
        node(f"Muntha: {muntha}", "spec", "#ffdd00")

    if varshesh:
        node(f"Varshesh: {varshesh}", "spec", "#ff8800")

    for planet, pos in positions.items():
        sign = pos.get("sign")
        nak = pos.get("nakshatra")

        node(planet, "bolygó", "#1f77b4")

        if sign:
            node(sign, "jegy", "#ff7f0e")
            dot.edge(planet, sign, label="helyezkedik", color="#9467bd")

            ruler = RULERSHIP.get(sign)
            if ruler:
                node(ruler, "bolygó", "#1f77b4")
                dot.edge(sign, ruler, label="jegy ura", color="#d62728")

        if nak:
            node(nak, "nakshatra", "#2ca02c")
            dot.edge(planet, nak, label="nakshatrában", color="#8c564b")

            nr = nak_rulers.get(nak)
            if nr:
                node(nr, "bolygó", "#1f77b4")
                dot.edge(nak, nr, label="nakshatra ura", color="#17becf")

    return dot



# ---------------------------------------------------------
# 4) Paneles Varshaphala infografika
# ---------------------------------------------------------

def render_varshaphala_panels(positions, nak_rulers, out_path, year, tithi, nakshatra, yoga, karana, vaara, varshesh, muntha):
    dwg = svgwrite.Drawing(out_path, size=("1400px", "900px"))
    dwg.add(dwg.rect(insert=(0, 0), size=("1400px", "900px"), fill="#0b1220"))

    font = {"font_family": "Inter", "fill": "#EAEFF7"}

    # Fejléc
    dwg.add(dwg.text(
        f"🌞 Varshaphala – {year}. év",
        insert=(40, 50),
        font_size=32,
        **font
    ))

    # Éves adatok
    dwg.add(dwg.text(
        f"Tithi: {tithi}   Nakshatra: {nakshatra}   Yoga: {yoga}   Karana: {karana}   Vaara: {vaara}",
        insert=(40, 90),
        font_size=20,
        **font
    ))

    dwg.add(dwg.text(
        f"Varshesh (Év ura): {varshesh}    Muntha (Éves Ascendens): {muntha}",
        insert=(40, 130),
        font_size=20,
        **font
    ))

    # Bolygó panelek
    x, y = 40, 180
    col_w, row_h = 420, 180
    i = 0

    for planet, pos in positions.items():
        px = x + (i % 3) * col_w
        py = y + (i // 3) * row_h

        dwg.add(dwg.rect(
            insert=(px, py),
            size=(col_w - 20, row_h - 20),
            rx=12,
            fill="#121a2b",
            stroke="#243a66"
        ))

        dwg.add(dwg.text(planet, insert=(px + 16, py + 32),
                         font_size=20, **font))

        lines = [
            f"Jegy: {pos.get('sign','?')} | Ház: {pos.get('house','?')}",
            f"Nakshatra: {pos.get('nakshatra','?')} | Pada: {pos.get('pada','?')}",
            f"Jegy ura: {RULERSHIP.get(pos.get('sign',''), '?')}",
            f"Nakshatra ura: {nak_rulers.get(pos.get('nakshatra',''), '?')}",
        ]

        for k, line in enumerate(lines):
            dwg.add(dwg.text(
                line,
                insert=(px + 16, py + 60 + 26 * k),
                font_size=16,
                **font
            ))

        i += 1

    dwg.save()
    return out_path


# ---------------------------------------------------------
# 5) Fő pipeline
# ---------------------------------------------------------

def run_varshaphala_infografika(varsha_data, bd):
    """
    varsha_data = compute_varshaphala_chart() eredménye
    bd = birth_data dict
    """

    chart = varsha_data["chart"]
    year = varsha_data["datetime"].year

    # Markdown → pozíciók
    md = generate_markdown_summary(chart)
    positions = parse_md(md)

    # Nakshatra urak
    nak_rulers = load_nakshatra_rulers()

    # Varshesh = év ura (Sun → jegy ura)
    sun_sign = chart.planet_data["Sun"]["sign"]
    varshesh = RULERSHIP.get(sun_sign, "?")

    # Muntha = éves Ascendens jegy
    try:
        muntha = chart.d1_chart.ascendant.sign
    except:
        muntha = "?"

    # Kimeneti mappa
    out_dir = BASE_DIR / "download" / "SonicJyotish"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Gráf
    graph = build_varshaphala_graph(
        positions,
        nak_rulers,
        varshesh,
        muntha
    )
    graph_path = str(out_dir / "varshaphala_patterns")
    graph.render(filename=graph_path, cleanup=True)

    # Panelek
    panels_svg = render_varshaphala_panels(
        positions,
        nak_rulers,
        out_path=str(out_dir / "varshaphala_panels.svg"),
        year=year,
        tithi=varsha_data["tithi"],
        nakshatra=varsha_data["nakshatra"],
        yoga=varsha_data["yoga"],
        karana=varsha_data["karana"],
        vaara=varsha_data["vaara"],
        varshesh=varshesh,
        muntha=muntha
    )

    return graph_path + ".svg", panels_svg

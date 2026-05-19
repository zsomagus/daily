# modulok/infografika_pipeline.py

import os
import re
import pandas as pd
from pathlib import Path
from graphviz import Digraph
import svgwrite

from modulok.elemzes_core import generate_full_analysis
from modulok.tables import RULERSHIP, nakshatra_data

from modulok.elemzes_utils import (
    translate_sign,
    get_planet_symbol,
    get_sign_symbol,
    get_elem_by_sign,
    get_purushartha_by_house,
)


BASE_DIR = Path(__file__).resolve().parent


# ---------------------------------------------------------
# 1) Nakshatra urak betöltése Excelből
# ---------------------------------------------------------

def load_nakshatra_rulers():
    df = nakshatra_df
    # 1. oszlop: Nakshatra neve, 2. oszlop: Ura
    return dict(zip(df.iloc[:, 0].astype(str), df.iloc[:, 1].astype(str)))


# ---------------------------------------------------------
# 2) Markdown → pozíciók kinyerése
# ---------------------------------------------------------

def parse_md(md: str):
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
# 3) Gráf építése (bolygó → jegy → ura, bolygó → nakshatra → ura)
# ---------------------------------------------------------

def build_graph(positions, nak_rulers):
    dot = Digraph(comment="Védikus mintázatok", format="svg")
    dot.attr(rankdir="LR", bgcolor="#0b1220", fontname="Inter")

    def node(n, t, color):
        dot.node(
            n, n,
            shape="box" if t != "bolygó" else "circle",
            style="filled",
            color=color,
            fontcolor="white"
        )

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
# 4) Paneles infografika (SVG)
# ---------------------------------------------------------

def render_panels(positions, nak_rulers, out_path):
    dwg = svgwrite.Drawing(out_path, size=("1200px", "800px"))
    dwg.add(dwg.rect(insert=(0, 0), size=("1200px", "800px"), fill="#0b1220"))

    font = {"font_family": "Inter", "fill": "#EAEFF7"}
    dwg.add(dwg.text("🌠 Védikus infografika – panelek",
                     insert=(40, 40), font_size=24, **font))

    x, y = 40, 60
    col_w, row_h = 380, 180
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
                         font_size=18, **font))

        lines = [
            f"Jegy: {pos.get('sign','?')} | Ház: {pos.get('house','?')}",
            f"Nakshatra: {pos.get('nakshatra','?')} | Pada: {pos.get('pada','?')}",
            f"Jegy ura: {RULERSHIP.get(pos.get('sign',''), '?')}",
            f"Nakshatra ura: {nak_rulers.get(pos.get('nakshatra',''), '?')}",
        ]

        for k, line in enumerate(lines):
            dwg.add(dwg.text(
                line,
                insert=(px + 16, py + 60 + 24 * k),
                font_size=14,
                **font
            ))

        i += 1

    dwg.save()
    return out_path


# ---------------------------------------------------------
# 5) Fő pipeline – chart → markdown → infografika
# ---------------------------------------------------------

def run_infografika(chart, bd):
    """
    chart = JyotishGanit chart objektum
    bd = birth_data dict
    """

    # Markdown elemzés generálása
    md = generate_markdown_summary(chart)

    # Pozíciók kinyerése
    positions = parse_md(md)

    # Nakshatra urak
    nak_rulers = load_nakshatra_rulers()

    # Kimeneti mappa
    out_dir = BASE_DIR / "download" / "SonicJyotish"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Gráf
    graph = build_graph(positions, nak_rulers)
    graph_path = str(out_dir / "vedikus_patterns")
    graph.render(filename=graph_path, cleanup=True)

    # Panelek
    panels_svg = render_panels(
        positions,
        nak_rulers,
        out_path=str(out_dir / "bolygo_panelek.svg")
    )

    return graph_path + ".svg", panels_svg

def build_infografika_data(chart):
    data = []
    for planet_name, pdata in chart.planet_data.items():
        english_sign = pdata["sign"]
        magyar_jegy = translate_sign(english_sign)
        jegy_szimbolum = get_sign_symbol(magyar_jegy)
        haz = pdata["house"]
        nakshatra = pdata.get("nakshatra")
        pada = pdata.get("pada")
        puru = get_purushartha_by_house(haz)
        elem = get_elem_by_sign(english_sign)

        data.append({
            "bolygo": planet_name,
            "bolygo_symbol": get_planet_symbol(planet_name),
            "jegy": magyar_jegy,
            "jegy_symbol": jegy_szimbolum,
            "haz": haz,
            "nakshatra": nakshatra,
            "pada": pada,
            "purushartha": puru,
            "elem": elem,
            # ide jöhet egy rövid összegzés is, ha akarod
        })
    return data
# modulok/infografika_svg.py



# 2–3 szavas kulcscímkék
ELEM_CIMKE = {
    "Tűz": "Impulzív teremtő erő",
    "Föld": "Gyakorlati stabil alap",
    "Levegő": "Szellemi mozgékony elme",
    "Víz": "Érzelmi mély áramlás",
}

PURU_CIMKE = {
    "Dharma": "Belső erkölcsi irány",
    "Artha": "Anyagi biztonság fókusz",
    "Kama": "Vágyak és kapcsolódás",
    "Moksha": "Szabadság és elengedés",
}


def build_infografika_data(chart):
    """A 9 bolygó összes infografika-adatát előkészíti."""
    data = []

    for planet_name, pdata in chart.planet_data.items():
        english_sign = pdata["sign"]
        magyar_jegy = translate_sign(english_sign)
        jegy_symbol = get_sign_symbol(magyar_jegy)
        haz = pdata["house"]
        nakshatra = pdata.get("nakshatra", "")
        pada = pdata.get("pada", "")
        puru = get_purushartha_by_house(haz)
        elem = get_elem_by_sign(english_sign)

        data.append({
            "bolygo": planet_name,
            "bolygo_symbol": get_planet_symbol(planet_name),
            "jegy": magyar_jegy,
            "jegy_symbol": jegy_symbol,
            "haz": haz,
            "nakshatra": nakshatra,
            "pada": pada,
            "purushartha": puru,
            "purushartha_cimke": PURU_CIMKE.get(puru, ""),
            "elem": elem,
            "elem_cimke": ELEM_CIMKE.get(elem, ""),
            "osszefoglalo": f"{planet_name} energiája a(z) {magyar_jegy} jegyben "
                            f"és a {haz}. házban aktív, "
                            f"{nakshatra} {pada}. pádájának minőségével.",
        })

    return data


def generate_infografika_svg(chart):
    """3×3 bolygó-infografika SVG generálása."""
    data = build_infografika_data(chart)

    cell_w = 400
    cell_h = 450

    svg = [
        '<svg width="1200" height="1400" viewBox="0 0 1200 1400" '
        'xmlns="http://www.w3.org/2000/svg">',
        '<rect x="0" y="0" width="1200" height="1400" fill="#020617"/>'
    ]

    for i, d in enumerate(data):
        row = i // 3
        col = i % 3
        x = col * cell_w
        y = row * cell_h

        svg.append(f'''
        <g transform="translate({x}, {y})">
            <rect x="20" y="20" width="360" height="420" rx="20" ry="20"
                  fill="#111827" stroke="#374151" stroke-width="2"/>

            <circle cx="80" cy="80" r="40" fill="#EF4444"/>
            <text x="80" y="88" text-anchor="middle"
                  font-size="32" fill="#F9FAFB">{d["bolygo_symbol"]}</text>

            <text x="140" y="70" font-size="20" fill="#F9FAFB" font-weight="bold">
                {d["bolygo"]}
            </text>

            <text x="40" y="130" font-size="14" fill="#E5E7EB">
                Jegy: {d["jegy"]} ({d["jegy_symbol"]})
            </text>

            <text x="40" y="155" font-size="14" fill="#E5E7EB">
                Ház: {d["haz"]}. ház
            </text>

            <text x="40" y="180" font-size="14" fill="#E5E7EB">
                Nakshatra: {d["nakshatra"]}, {d["pada"]}. páda
            </text>

            <text x="40" y="205" font-size="14" fill="#E5E7EB">
                Purushartha: {d["purushartha"]} – {d["purushartha_cimke"]}
            </text>

            <text x="40" y="230" font-size="14" fill="#E5E7EB">
                Elem: {d["elem"]} – {d["elem_cimke"]}
            </text>

            <text x="40" y="265" font-size="13" fill="#D1D5DB">
                <tspan x="40" dy="0">{d["osszefoglalo"]}</tspan>
            </text>
        </g>
        ''')

    svg.append("</svg>")
    return "\n".join(svg)

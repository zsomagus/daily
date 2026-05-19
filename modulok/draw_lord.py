# modulok/draw_lord.py

import svgwrite
from modulok.tables import house_positions

def rajzol_lord_chart_svg(lord_chart, filename="lord_chart.svg"):
    dwg = svgwrite.Drawing(filename, size=("1200px", "1200px"))

    # 12 ház rácsa
    for h, (x, y) in house_positions.items():
        dwg.add(dwg.rect(insert=(x*100, y*100), size=("100px", "100px"),
                         fill="white", stroke="black", stroke_width=2))

    # Bolygók elhelyezése az Ura helye szerint
    for graha, info in lord_chart.items():
        rashi = info["rashi_lord_rashi"]   # <-- EZ A LÉNYEG
        house = list(house_positions.keys())[list(house_positions.values()).index(house_positions[rashi])]
        x, y = house_positions[house]

        dwg.add(dwg.text(
            graha,
            insert=(x*100 + 50, y*100 + 50),
            text_anchor="middle",
            font_size="20px",
            fill="red"
        ))

    dwg.save()
    return filename

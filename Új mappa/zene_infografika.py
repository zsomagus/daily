# modulok/zene_infografika_svg.py

import math

METRIC_LABELS = {
    "energy": "Energia szint",
    "brightness": "Fényesség érzet",
    "tension": "Feszültség jelenlét",
    "complexity": "Zenei komplexitás",
    "rhythm_stability": "Ritmus stabilitás",
}

METRIC_KEYWORDS = {
    "energy": ("Lassú pulzáló energia", "Kiegyensúlyozott hajtás", "Intenzív hajtó erő"),
    "brightness": ("Sötét, mély tónus", "Meleg, kiegyensúlyozott", "Fényes, ragyogó hangzás"),
    "tension": ("Nyugodt, oldott tér", "Finom belső feszültség", "Erős, feszült atmoszféra"),
    "complexity": ("Letisztult, egyszerű forma", "Mérsékelt részletgazdagság", "Sűrű, komplex textúra"),
    "rhythm_stability": ("Lebegő, szabad ritmus", "Stabil, de élő pulzus", "Nagyon feszes groove"),
}


def _keyword_for_value(metric, value):
    low, mid, high = METRIC_KEYWORDS[metric]
    if value < 0.33:
        return low
    elif value < 0.66:
        return mid
    else:
        return high


def generate_zene_infografika_svg(audio_analysis):
    """
    Kördiagram / energia‑kerék SVG a zenei analízis alapján.
    """
    cx, cy = 600, 700
    base_r = 120
    max_r = 260

    metrics = ["energy", "brightness", "tension", "complexity", "rhythm_stability"]
    n = len(metrics)

    svg = [
        '<svg width="1200" height="1400" viewBox="0 0 1200 1400" '
        'xmlns="http://www.w3.org/2000/svg">',
        '<rect x="0" y="0" width="1200" height="1400" fill="#020617"/>',
        f'<text x="600" y="120" text-anchor="middle" '
        f'font-size="28" fill="#F9FAFB" font-weight="bold">Zenei energia‑térkép</text>',
        f'<text x="600" y="160" text-anchor="middle" '
        f'font-size="16" fill="#E5E7EB">{audio_analysis.get("mood_label","")}</text>',
        f'<text x="600" y="190" text-anchor="middle" '
        f'font-size="14" fill="#9CA3AF">BPM: {audio_analysis.get("bpm","?")}  •  Hangnem: {audio_analysis.get("key","?")}</text>',
    ]

    # Kör középpont
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{base_r}" fill="#020617" stroke="#374151" stroke-width="2"/>')

    # Metrikák sugarai + poligon
    points = []
    for i, m in enumerate(metrics):
        angle = (2 * math.pi / n) * i - math.pi / 2
        v = float(audio_analysis.get(m, 0.0))
        r = base_r + (max_r - base_r) * v
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        points.append((x, y))

        # sugár
        x_line = cx + max_r * math.cos(angle)
        y_line = cy + max_r * math.sin(angle)
        svg.append(f'<line x1="{cx}" y1="{cy}" x2="{x_line}" y2="{y_line}" stroke="#1F2937" stroke-width="1"/>')

        # címke
        label = METRIC_LABELS[m]
        lx = cx + (max_r + 40) * math.cos(angle)
        ly = cy + (max_r + 40) * math.sin(angle)
        svg.append(
            f'<text x="{lx}" y="{ly}" text-anchor="middle" '
            f'font-size="12" fill="#E5E7EB">{label}</text>'
        )

        # kulcsszó
        kw = _keyword_for_value(m, v)
        kw_y = ly + 16
        svg.append(
            f'<text x="{lx}" y="{kw_y}" text-anchor="middle" '
            f'font-size="11" fill="#9CA3AF">{kw}</text>'
        )

    # poligon – energia‑forma
    points_str = " ".join(f"{x},{y}" for x, y in points)
    svg.append(
        f'<polygon points="{points_str}" fill="#22C55E33" stroke="#22C55E" stroke-width="2"/>'
    )


    svg.append("</svg>")
    return "\n".join(svg)

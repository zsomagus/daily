# modulok/zene_infografika_svg.py

import math

# Ikonok (Unicode)
ICONS = {
    "melancholy": "🌙",
    "euphoria": "✨",
    "intimacy": "💗",
    "tension": "🔥",
    "brightness": "🔆",

    "density": "🌫️",
    "dynamics": "🌊",
    "rhythm_stability": "🥁",
    "harmonic_complexity": "🎼",
    "spectral_brightness": "🔔",
}

# Színek
COLORS = {
    "melancholy": "#6366F1",
    "euphoria": "#22C55E",
    "intimacy": "#EC4899",
    "tension": "#EF4444",
    "brightness": "#FACC15",

    "density": "#6EE7B7",
    "dynamics": "#3B82F6",
    "rhythm_stability": "#F97316",
    "harmonic_complexity": "#A855F7",
    "spectral_brightness": "#FDE047",
}


def generate_zene_infografika_svg(analysis):
    """
    Két-gyűrűs zenei energia-kerék SVG.
    analysis = analyze_audio_enhanced() kimenete
    """

    cx, cy = 600, 750
    inner_r = 120
    outer_r = 260

    emotional = ["melancholy", "euphoria", "intimacy", "tension", "brightness"]
    technical = ["density", "dynamics", "rhythm_stability", "harmonic_complexity", "spectral_brightness"]

    svg = [
        '<svg width="1200" height="1500" viewBox="0 0 1200 1500" xmlns="http://www.w3.org/2000/svg">',
        '<rect x="0" y="0" width="1200" height="1500" fill="#020617"/>',

        f'<text x="600" y="120" text-anchor="middle" font-size="32" fill="#F9FAFB" font-weight="bold">Zenei Energia-Kerék</text>',
        f'<text x="600" y="165" text-anchor="middle" font-size="18" fill="#E5E7EB">{analysis["mood_label"]}</text>',
        f'<text x="600" y="195" text-anchor="middle" font-size="14" fill="#9CA3AF">BPM: {analysis["bpm"]} • Hangnem: {analysis["key"]}</text>',
    ]

    # Háttérkörök
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{inner_r}" fill="#111827" stroke="#1F2937" stroke-width="2"/>')
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{outer_r}" fill="#111827" stroke="#1F2937" stroke-width="2"/>')

    # Belső gyűrű (technikai)
    for i, m in enumerate(technical):
        angle = (2 * math.pi / len(technical)) * i - math.pi / 2
        v = analysis["metrics"][m]
        r = inner_r + (outer_r - inner_r) * v * 0.5
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)

        color = COLORS[m]
        icon = ICONS[m]
        label = analysis["keywords"][m]

        # Sugár
        svg.append(f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="{color}" stroke-width="3"/>')

        # Ikon + címke
        lx = cx + (inner_r + 40) * math.cos(angle)
        ly = cy + (inner_r + 40) * math.sin(angle)
        svg.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="20" fill="{color}">{icon}</text>')
        svg.append(f'<text x="{lx}" y="{ly+20}" text-anchor="middle" font-size="11" fill="#E5E7EB">{label}</text>')

    # Külső gyűrű (érzelmi)
    for i, m in enumerate(emotional):
        angle = (2 * math.pi / len(emotional)) * i - math.pi / 2
        v = analysis["metrics"][m]
        r = inner_r + (outer_r - inner_r) * v
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)

        color = COLORS[m]
        icon = ICONS[m]
        label = analysis["keywords"][m]

        # Sugár
        svg.append(f'<line x1="{cx}" y1="{cy}" x2="{x}" y2="{y}" stroke="{color}" stroke-width="4"/>')

        # Ikon + címke
        lx = cx + (outer_r + 40) * math.cos(angle)
        ly = cy + (outer_r + 40) * math.sin(angle)
        svg.append(f'<text x="{lx}" y="{ly}" text-anchor="middle" font-size="24" fill="{color}">{icon}</text>')
        svg.append(f'<text x="{lx}" y="{ly+22}" text-anchor="middle" font-size="12" fill="#E5E7EB">{label}</text>')

    svg.append("</svg>")
    return "\n".join(svg)

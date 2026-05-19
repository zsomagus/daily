# modulok/sonic_profile_svg.py

from modulok.infografika_pipeline import generate_infografika_svg
from modulok.zene_infografika_svg import generate_zene_infografika_svg


def generate_sonic_profile_svg(chart, audio_analysis):
    """
    Összevont Sonic Profile oldal:
    - bal: horoszkóp 3×3 rács
    - jobb: zenei energia-kerék
    - alul: narratív összegzés
    """

    # 1) rész-SVG-k legenerálása
    svg_h = generate_infografika_svg(chart)
    svg_z = generate_zene_infografika_svg(audio_analysis)

    # 2) beágyazás <foreignObject>-tel
    # (minden modern SVG renderelő támogatja)
    svg = [
        '<svg width="2400" height="1600" viewBox="0 0 2400 1600" '
        'xmlns="http://www.w3.org/2000/svg">',
        '<rect x="0" y="0" width="2400" height="1600" fill="#020617"/>',

        # Bal oldal – horoszkóp
        '<foreignObject x="0" y="0" width="1200" height="1500">',
        svg_h,
        '</foreignObject>',

        # Jobb oldal – zene
        '<foreignObject x="1200" y="0" width="1200" height="1500">',
        svg_z,
        '</foreignObject>',
    ]

    # 3) Narratív összegzés
    mood = audio_analysis["mood_label"]
    key = audio_analysis["key"]
    bpm = audio_analysis["bpm"]

    summary = (
        f"A zene {key} hangnemben és {bpm} BPM-mel egy olyan érzelmi teret hoz létre, "
        f"amely rezonál a horoszkóp aktuális bolygóállásaival. "
        f"A zenei energia-kerék alapján a hangzás fő tónusa: {mood}. "
        f"A bolygók elhelyezkedése és a zenei érzelmi profil között "
        f"finom, organikus párhuzamok figyelhetők meg, amelyek "
        f"egy egyedi, személyre szabott Sonic Profile-t alkotnak."
    )

    svg.append(f'''
        <text x="1200" y="1550" text-anchor="middle"
              font-size="20" fill="#E5E7EB" font-weight="bold">
            Sonic Profile – Összegzés
        </text>

        <text x="1200" y="1580" text-anchor="middle"
              font-size="14" fill="#9CA3AF" width="2000">
            {summary}
        </text>
    ''')

    svg.append("</svg>")
    return "\n".join(svg)

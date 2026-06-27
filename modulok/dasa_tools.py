from jyotishganit.dasa import VimshottariDasa


DASA_YEARS = {
    "Ketu": 7,
    "Venus": 20,
    "Sun": 6,
    "Moon": 10,
    "Mars": 7,
    "Rahu": 18,
    "Jupiter": 16,
    "Saturn": 19,
    "Mercury": 17,
}

NAKSHATRA_ORDER = [
    "Ketu",
    "Venus",
    "Sun",
    "Moon",
    "Mars",
    "Rahu",
    "Jupiter",
    "Saturn",
    "Mercury",
]


def calculate_dasa_info(positions, start_year=None):
    """Vimshottari Dasa számítás jyotishganit segítségével."""
    from datetime import datetime

    # Hold hosszúság lekérése
    moon_lon = positions["Moon"]["longitude"]

    # jyotishganit Dasa objektum létrehozása
    dasa_calc = VimshottariDasa(moon_lon)

    # aktuális év
    current_year = start_year if start_year else datetime.now().year

    # fő ciklusok lekérése
    mahadasa = dasa_calc.get_current_dasa()
    antardasa = dasa_calc.get_current_antardasa()
    pratyantardasa = dasa_calc.get_current_pratyantardasa()

    return {
        "Mahadasa": {
            "planet": mahadasa.lord,
            "start": current_year,
            "end": round(current_year + mahadasa.remaining_years, 2)
        },
        "Antardasa": {
            "planet": antardasa.lord,
            "start": current_year,
            "end": round(current_year + antardasa.remaining_years, 2)
        },
        "Pratyantardasa": {
            "planet": pratyantardasa.lord,
            "start": current_year,
            "end": round(current_year + pratyantardasa.remaining_years, 2)
        }
    }

    return {
        "Mahadasa": mahadasa,
        "Antardasa": antardasa,
        "Pratyantardasa": pratyantardasa,
    }
# modulok/dasa_analysis.py
def generate_dasa_summary(birth_data):
    dasa = calculate_dasa_info(birth_data["planet_data"])
    md = "## 🕰️ Daśa ciklusok\n\n"
    for key, data in dasa.items():
        md += f"- **{key} – {data['planet']}**: {data['start']} → {data['end']}\n"
    return md

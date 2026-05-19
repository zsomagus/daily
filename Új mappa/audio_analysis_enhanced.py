# modulok/audio_analysis_enhanced.py

import numpy as np

# 2–3 szavas kulcscímkék minden tengelyhez
KEYWORDS = {
    "melancholy": ("Derűs nyugalom", "Finom melankólia", "Mély érzelmi tónus"),
    "euphoria": ("Visszafogott öröm", "Emelkedett hangulat", "Intenzív eufória"),
    "intimacy": ("Távoli hangzás", "Közeli melegség", "Intim jelenlét"),
    "tension": ("Oldott tér", "Finom feszültség", "Erős vibrálás"),
    "brightness": ("Sötét tónus", "Meleg fényesség", "Ragyogó hangzás"),

    "density": ("Légies textúra", "Közepes sűrűség", "Masszív rétegzettség"),
    "dynamics": ("Lágy dinamika", "Élő hullámzás", "Erőteljes kontraszt"),
    "rhythm_stability": ("Lebegő ritmus", "Stabil pulzus", "Feszes groove"),
    "harmonic_complexity": ("Egyszerű harmónia", "Gazdag akkordok", "Komplex harmónia"),
    "spectral_brightness": ("Sötét spektrum", "Kiegyensúlyozott fény", "Tiszta magasak"),
}


def _keyword(metric, value):
    low, mid, high = KEYWORDS[metric]
    if value < 0.33:
        return low
    elif value < 0.66:
        return mid
    else:
        return high


def analyze_audio_enhanced(audio_data, bpm, key):
    """
    Finomhangolt zene-analízis.
    audio_data: numpy array vagy bármilyen hullámforma
    bpm: MusicGen metaadat
    key: MusicGen metaadat
    """

    # Ha nincs valódi audio-elemzés, generálunk stabil, de változatos értékeket
    # (később beépíthető: librosa, essentia, stb.)
    rng = np.random.default_rng()

    metrics = {
        "melancholy": float(rng.uniform(0.0, 1.0)),
        "euphoria": float(rng.uniform(0.0, 1.0)),
        "intimacy": float(rng.uniform(0.0, 1.0)),
        "tension": float(rng.uniform(0.0, 1.0)),
        "brightness": float(rng.uniform(0.0, 1.0)),

        "density": float(rng.uniform(0.0, 1.0)),
        "dynamics": float(rng.uniform(0.0, 1.0)),
        "rhythm_stability": float(rng.uniform(0.0, 1.0)),
        "harmonic_complexity": float(rng.uniform(0.0, 1.0)),
        "spectral_brightness": float(rng.uniform(0.0, 1.0)),
    }

    # Kulcscímkék hozzárendelése
    keywords = {m: _keyword(m, v) for m, v in metrics.items()}

    # Összegző érzelmi címke
    mood = _build_mood_label(metrics)

    return {
        "bpm": bpm,
        "key": key,
        "metrics": metrics,
        "keywords": keywords,
        "mood_label": mood,
    }


def _build_mood_label(m):
    """
    Összegző érzelmi címke generálása.
    """
    if m["euphoria"] > 0.7 and m["brightness"] > 0.6:
        return "Fényes, felemelő hangulat"
    if m["melancholy"] > 0.7:
        return "Mély, melankolikus atmoszféra"
    if m["intimacy"] > 0.7:
        return "Közeli, bensőséges tér"
    if m["tension"] > 0.7:
        return "Feszült, vibráló energia"

    return "Kiegyensúlyozott, organikus hangzás"

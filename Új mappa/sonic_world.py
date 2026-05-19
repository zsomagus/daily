# sonic_jyotish.py

import os
import wave
from pathlib import Path

import numpy as np
import scipy.signal as sps
import soundfile as sf

from modulok.astro_core import get_chart_data
from modulok import varshaphala_tools
from  modulok import prashna_core

from modulok.music_prompt import build_music_prompt
from modulok.tables import (
    nakshatra_data,
    tithi_dynamics,
)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = os.path.expanduser("~/Letöltések/Álmaim/SonicJyotish")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Cseleszt minta betöltése ---
celeste_path = BASE_DIR / "static" / "hangok" / "cseleszt.wav"
if celeste_path.exists():
    celeste, SR = sf.read(celeste_path)
    if celeste.ndim > 1:
        celeste = celeste.mean(axis=1)
else:
    celeste = None
    SR = 44100


# ---------- Alap hullámok, timbre, dinamika ----------

def sine_wave(freq, duration, samplerate=44100):
    n = int(duration * samplerate)
    t = np.arange(n) / samplerate
    return np.sin(2 * np.pi * freq * t).astype(np.float32)


def apply_celeste_timbre(samples):
    if celeste is None:
        return samples
    out = sps.fftconvolve(samples, celeste, mode="same")
    # normalizálás
    m = np.max(np.abs(out)) or 1.0
    return (out / m).astype(np.float32)


def rahu_timbre(wave):
    # enyhe frekvenciamoduláció
    t = np.linspace(0, 1, len(wave))
    mod = np.sin(2 * np.pi * 5 * t)
    return (wave * (1 + 0.3 * mod)).astype(np.float32)


def ketu_timbre(wave):
    # enyhe high-pass jelleg
    return sps.lfilter([1, -0.9], [1], wave).astype(np.float32)


def apply_tithi_dynamics(samples, tithi, samplerate=44100):
    dyn = tithi_dynamics.get(tithi, {"amp": 1.0, "attack": 0.05})
    amp = dyn.get("amp", 1.0)
    attack = dyn.get("attack", 0.05)

    samples = samples * amp
    n_attack = int(attack * samplerate)
    if 0 < n_attack < len(samples):
        env = np.linspace(0, 1, n_attack)
        samples[:n_attack] *= env
    return samples.astype(np.float32)


def apply_rhythm(samples, rhythm, samplerate=44100):
    step = max(1, int(rhythm * samplerate))
    chunks = []
    for i in range(0, len(samples), step):
        chunk = samples[i:i + step]
        chunks.append(chunk)
        chunks.append(np.zeros_like(chunk))
    if not chunks:
        return samples
    out = np.concatenate(chunks)
    return out.astype(np.float32)


def rhythm_from_element(elem):
    return {
        "Tűz": 0.25,
        "Víz": 1.0,
        "Föld": 0.5,
        "Levegő": 0.75,
    }.get(elem, 0.5)


# ---------- Prompt-alapú módosítók ----------

def analyze_prompt_for_modifiers(text, mood, keywords, symbols):
    prompt = build_music_prompt(text, mood, keywords, symbols or [])
    p = prompt.lower()

    # tempó
    if "nyugodt" in p or "calm" in p:
        tempo_factor = 1.2
    elif "félelmetes" in p or "fear" in p:
        tempo_factor = 0.8
    elif "misztikus" in p or "mystic" in p:
        tempo_factor = 0.9
    else:
        tempo_factor = 1.0

    # hangerő
    if "boldog" in p or "happy" in p:
        volume = 1.1
    elif "zaklatott" in p or "chaotic" in p:
        volume = 0.95
    else:
        volume = 1.0

    # szólam-sűrűség (Rahu/Ketu)
    if "zavaros" in p or "chaotic" in p:
        include_rahu = include_ketu = True
    elif "nyugodt" in p or "calm" in p:
        include_rahu = include_ketu = False
    else:
        include_rahu = include_ketu = True

    return tempo_factor, volume, include_rahu, include_ketu


# ---------- 108 pāda fővonal (pāda-frekvenciákból) ----------

def generate_108_pada_main_track(nakshatra, tithi, volume):
    data = nakshatra_data.get(nakshatra)
    if not data:
        return np.zeros(1, dtype=np.float32)

    pada_freqs = data.get("pada_freqs", [])
    if not pada_freqs:
        return np.zeros(1, dtype=np.float32)

    # 108 lépés = 27× a 4 pāda
    steps = []
    for i in range(108):
        f = pada_freqs[i % len(pada_freqs)]
        s = sine_wave(f, 2.0, samplerate=SR)
        s = apply_celeste_timbre(s)
        s = apply_tithi_dynamics(s, tithi, samplerate=SR)
        s *= volume
        steps.append(s)

    return np.concatenate(steps).astype(np.float32)


# ---------- Bolygó szólamok ----------

def generate_planet_tracks(chart_data, tempo_factor, volume, include_rahu, include_ketu):
    planet_data = chart_data.get("planet_data", {})
    tithi = chart_data.get("tithi_data")
    nakshatra = chart_data.get("nakshatra_data")

    tracks = []

    for planet_name, pos in planet_data.items():
        sign = pos.get("sign")
        elem = pos.get("element") or "Tűz"  # ha van ilyen, különben default
        rhythm = rhythm_from_element(elem) * tempo_factor

        # alap frekvencia: nakshatra pāda-frekvenciák első eleme vagy fallback
        nd = nakshatra_data.get(nakshatra, {})
        pada_freqs = nd.get("pada_freqs", [220.0])
        base_freq = pada_freqs[0]

        s = sine_wave(base_freq, 2.0, samplerate=SR)
        s = apply_rhythm(s, rhythm, samplerate=SR)
        s = apply_tithi_dynamics(s, tithi, samplerate=SR)
        s *= volume

        pl = planet_name.lower()
        if pl == "rahu" and include_rahu:
            s = rahu_timbre(s)
        elif pl == "ketu" and include_ketu:
            s = ketu_timbre(s)

        tracks.append(s.astype(np.float32))

    return tracks


# ---------- Mantra szólam (egyszerű, mély alap) ----------

def generate_mantra_track(chart_data, volume):
    # ha később akarod: asc_lord alapján
    freq = 150.0
    s = sine_wave(freq, 30.0, samplerate=SR)
    s *= volume * 0.7
    return s.astype(np.float32)


# ---------- Mixelés ----------

def mix_tracks(tracks):
    if not tracks:
        return np.zeros(1, dtype=np.float32)
    max_len = max(len(t) for t in tracks)
    mix = np.zeros(max_len, dtype=np.float32)
    for t in tracks:
        mix[:len(t)] += t * 0.2
    # normalizálás
    m = np.max(np.abs(mix)) or 1.0
    return (mix / m).astype(np.float32)


# ---------- Fő generáló függvény ----------

def generate_full_audio(
    name,
    year,
    month,
    day,
    hour,
    minute,
    tz,
    lon,
    lat,
    text="",
    mood="",
    keywords="",
    symbols=None,
):
    if symbols is None:
        symbols = []

    chart_data = get_chart_data(name, year, month, day, hour, minute, tz, lon, lat)
    tithi = chart_data.get("tithi_data")
    nakshatra = chart_data.get("nakshatra_data")

    tempo_factor, volume, include_rahu, include_ketu = analyze_prompt_for_modifiers(
        text, mood, keywords, symbols
    )

    # fő 108 pāda sáv
    main_track = generate_108_pada_main_track(nakshatra, tithi, volume)

    # bolygó szólamok
    planet_tracks = generate_planet_tracks(
        chart_data, tempo_factor, volume, include_rahu, include_ketu
    )

    # mantra szólam (egyszerű, mély alap)
    mantra_track = generate_mantra_track(chart_data, volume)
    planet_tracks.append(mantra_track)

    all_tracks = [main_track] + planet_tracks
    final = mix_tracks(all_tracks)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, "sonic_jyotish.wav")

    with wave.open(output_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((final * 32767).astype(np.int16).tobytes())

    return output_path

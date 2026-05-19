# modulok/sonic_world.py

import os
import wave
from pathlib import Path

import numpy as np
import scipy.signal as sps
import soundfile as sf

from modulok.tables import (
    nakshatra_data,
    tithi_dynamics,
    mantra_map,
    ELEMENTS,
    RHYTMS
)
from modulok.varshaphala_tools import compute_varshaphala_chart
from modulok import prashna_core, astro_core
BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = os.path.expanduser("~/Letöltések/SonicJyotish")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Cseleszt minta betöltése ---
celeste_path = BASE_DIR.parent / "static" / "hangok" / "cseleszt.wav"
if celeste_path.exists():
    celeste, SR = sf.read(celeste_path)
    if celeste.ndim > 1:
        celeste = celeste.mean(axis=1)
else:
    celeste = None
    SR = 44100
    print("Celeste found:", celeste_path.exists())


# ---------- Alap hullámok, timbre, dinamika ----------

def sine_wave(freq, duration, samplerate=44100):
    n = int(duration * samplerate)
    t = np.arange(n) / samplerate
    return np.sin(2 * np.pi * freq * t).astype(np.float32)


def apply_celeste_timbre(samples):
    if celeste is None:
        return samples
    out = sps.fftconvolve(samples, celeste, mode="same")
    m = np.max(np.abs(out)) or 1.0
    return (out / m).astype(np.float32)


def rahu_timbre(wave):
    t = np.linspace(0, 1, len(wave))
    mod = np.sin(2 * np.pi * 5 * t)
    return (wave * (1 + 0.3 * mod)).astype(np.float32)


def ketu_timbre(wave):
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
        "Víz": 0.6,
        "Föld": 0.4,
        "Levegő": 0.35,
    }.get(elem, 0.4)


# ---------- Skálák, dallamok ----------

def build_pentatonic_scale(base_freq):
    ratios = [1.0, 9/8, 5/4, 3/2, 5/3]
    return [base_freq * r for r in ratios]


def melodic_step_sequence(num_steps, scale):
    idx = 0
    direction = 1
    seq = []
    for _ in range(num_steps):
        seq.append(scale[idx])
        idx += direction
        if idx >= len(scale):
            idx = len(scale) - 2
            direction = -1
        elif idx < 0:
            idx = 1
            direction = 1
    return seq


# ---------- 108 pāda fővonal – dallamos verzió ----------

def generate_108_pada_main_track(nakshatra, tithi, volume):
    data = nakshatra_data.get(nakshatra)
    if not data:
        return np.zeros(1, dtype=np.float32)

    pada_freqs = data.get("pada_freqs", [])
    if not pada_freqs:
        return np.zeros(1, dtype=np.float32)

    base_freq = pada_freqs[0]
    scale = build_pentatonic_scale(base_freq)
    melody_freqs = melodic_step_sequence(108, scale)

    steps = []
    for f in melody_freqs:
        s = sine_wave(f, 0.8, samplerate=SR)
        s = apply_celeste_timbre(s)
        s = apply_tithi_dynamics(s, tithi, samplerate=SR)
        s *= volume
        steps.append(s)

    return np.concatenate(steps).astype(np.float32)


# ---------- Bolygó motívumok – dallamos szólamok ----------

def planet_motif(freq_base, elem, duration=2.0):
    scale = build_pentatonic_scale(freq_base)

    if elem == "Tűz":
        pattern = [0, 1, 2, 4]
    elif elem == "Víz":
        pattern = [2, 1, 2, 3]
    elif elem == "Föld":
        pattern = [0, 0, 1, 0]
    elif elem == "Levegő":
        pattern = [1, 3, 2, 4]
    else:
        pattern = [0, 1, 2, 3]

    note_dur = duration / len(pattern)
    notes = []
    for idx in pattern:
        f = scale[idx % len(scale)]
        n = sine_wave(f, note_dur, samplerate=SR)
        notes.append(n)
    return np.concatenate(notes).astype(np.float32)


def generate_planet_tracks(chart_data, tempo_factor, volume, include_rahu, include_ketu):
    planet_data = chart_data.get("planet_data", {})
    tithi = chart_data.get("tithi")
    nakshatra = chart_data.get("nakshatra")

    tracks = []

    nd = nakshatra_data.get(nakshatra, {})
    pada_freqs = nd.get("pada_freqs", [220.0])
    base_freq = pada_freqs[0]

    for planet_name, pos in planet_data.items():
        elem = pos.get("element") or "Tűz"
        rhythm = rhythm_from_element(elem) * tempo_factor

        motif = planet_motif(base_freq, elem, duration=2.0)
        motif = apply_rhythm(motif, rhythm, samplerate=SR)
        motif = apply_tithi_dynamics(motif, tithi, samplerate=SR)
        motif *= volume * 0.8

        pl = planet_name.lower()
        if pl == "rahu" and include_rahu:
            motif = rahu_timbre(motif)
        elif pl == "ketu" and include_ketu:
            motif = ketu_timbre(motif)

        tracks.append(motif.astype(np.float32))

    return tracks


# ---------- Mantra szólam – több hangmagasságon ----------

def generate_mantra_track_from_files(chart_data, volume):
    asc_sign = chart_data.get("asc_sign")
    if not asc_sign:
        return np.zeros(1, dtype=np.float32)

    if asc_sign not in mantra_map:
        return np.zeros(1, dtype=np.float32)

    planet, target_freq, mantra_name = mantra_map[asc_sign]

    mantra_dir = BASE_DIR.parent / "static" / "hangok" / "mantrák"
    mantra_file = mantra_dir / f"{mantra_name}.wav"

    if not mantra_file.exists():
        print("Mantra file not found:", mantra_file)
        return np.zeros(1, dtype=np.float32)

    audio, sr = sf.read(mantra_file)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    original_freq = 200.0
    ratio = target_freq / original_freq

    new_len = int(len(audio) / ratio)
    shifted = sps.resample(audio, new_len)

    shifted = shifted.astype(np.float32)
    shifted *= volume
    return shifted


# ---------- Mixelés ----------

def mix_tracks(tracks):
    if not tracks:
        return np.zeros(1, dtype=np.float32)
    max_len = max(len(t) for t in tracks)
    mix = np.zeros(max_len, dtype=np.float32)
    for t in tracks:
        mix[:len(t)] += t * 0.25
    m = np.max(np.abs(mix)) or 1.0
    return (mix / m).astype(np.float32)


# ---------- Prompt → módosítók ----------

def analyze_prompt_for_modifiers(text, mood, keywords, symbols):
    p = (text + " " + mood + " " + (keywords or "") + " " + " ".join(symbols or [])).lower()

    if "nyugodt" in p or "calm" in p:
        tempo_factor = 1.1
    elif "félelmetes" in p or "fear" in p:
        tempo_factor = 0.85
    elif "misztikus" in p or "mystic" in p:
        tempo_factor = 0.9
    else:
        tempo_factor = 1.0

    if "boldog" in p or "happy" in p:
        volume = 1.1
    elif "zaklatott" in p or "chaotic" in p:
        volume = 0.95
    else:
        volume = 1.0

    if "zavaros" in p or "chaotic" in p:
        include_rahu = include_ketu = True
    elif "nyugodt" in p or "calm" in p:
        include_rahu = include_ketu = False
    else:
        include_rahu = include_ketu = True

    return tempo_factor, volume, include_rahu, include_ketu


# ---------- Fő generáló függvény ----------

def generate_full_audio(chart, bd, text="", mood="", keywords="", symbols=None):
    """
    chart: JyotishGanit chart objektum (ugyanaz, mint az elemzésnél)
    bd:   birth_data dict a GUI-ból (name, date, time, lat, lon, timezone)
    """

    if symbols is None:
        symbols = []

    # chart → egyszerű chart_data dict
    planet_data = chart.planet_data
    tithi = chart.panchanga.tithi
    nakshatra = chart.panchanga.nakshatra

    # Ascendens jegy (szám) – ha van ilyen mező
    try:
        asc_sign = chart.d1_chart.ascendant.sign_number
    except Exception:
        asc_sign = None

    chart_data = {
        "planet_data": planet_data,
        "tithi": tithi,
        "nakshatra": nakshatra,
        "asc_sign": asc_sign,
    }

    tempo_factor, volume, include_rahu, include_ketu = analyze_prompt_for_modifiers(
        text, mood, keywords, symbols
    )

    main_track = generate_108_pada_main_track(nakshatra, tithi, volume)
    planet_tracks = generate_planet_tracks(
        chart_data, tempo_factor, volume, include_rahu, include_ketu
    )
    mantra_track = generate_mantra_track_from_files(chart_data, volume)
    planet_tracks.append(mantra_track)

    all_tracks = [main_track] + planet_tracks
    final = mix_tracks(all_tracks)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    safe_name = bd["name"].strip().replace(" ", "_")
    output_path = os.path.join(OUTPUT_DIR, f"{safe_name}_sonic_jyotish_melodic.wav")

    with wave.open(output_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((final * 32767).astype(np.int16).tobytes())

    return output_path
def on_musicalize_varshaphala():

    bd = gui_helpers.get_birth_data(name1, date1, time1, lat1, lon1, timezoneSelector)
    age = int(ageInput.text() or 0)

    birth_dt = pendulum.datetime(
        int(bd["date"].split("-")[0]),
        int(bd["date"].split("-")[1]),
        int(bd["date"].split("-")[2]),
        int(bd["time"].split(":")[0]),
        int(bd["time"].split(":")[1]),
        tz=bd["timezone"]
    )

    result = compute_varshaphala_chart(
        birth_dt=birth_dt,
        age=age,
        lat=float(bd["lat"]),
        lon=float(bd["lon"])
    )

    wav = generate_full_audio(result["chart"], bd)
    resultArea.append(f"🎵 Varshaphala hang mentve: {wav}")

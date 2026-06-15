import os
import wave
from pathlib import Path

import numpy as np
import scipy.signal as sps
import soundfile as sf
import pendulum

from mido import Message, MidiFile, MidiTrack

from modulok.tables import (
    nakshatra_data,
    tithi_dynamics,
    mantra_map,
    ELEMENTS,
    RHYTHMS
)

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = os.path.expanduser("~/Letöltések/SonicJyotish")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Celeste minta ---
celeste_path = BASE_DIR.parent / "static" / "hangok" / "cseleszt.wav"
if celeste_path.exists():
    celeste, SR = sf.read(celeste_path)
    if celeste.ndim > 1:
        celeste = celeste.mean(axis=1)
else:
    celeste = None
    SR = 44100


# ------------------ Alap hullámok ------------------

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


def rahu_timbre(wave_data):
    t = np.linspace(0, 1, len(wave_data))
    mod = np.sin(2 * np.pi * 5 * t)
    return (wave_data * (1 + 0.3 * mod)).astype(np.float32)


def ketu_timbre(wave_data):
    return sps.lfilter([1, -0.9], [1], wave_data).astype(np.float32)


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


def rhythm_from_element(elem):
    return {
        "Tűz": 0.25,
        "Víz": 0.6,
        "Föld": 0.4,
        "Levegő": 0.35,
    }.get(elem, 0.4)


# ------------------ Skálák ------------------

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


# ------------------ 108 Pāda fővonal ------------------

def generate_108_pada_main_track(nakshatra, tithi, volume):
    data = nakshatra_data.get(nakshatra)
    if not data:
        return np.zeros(1, dtype=np.float32), []

    pada_freqs = data.get("pada_freqs", [])
    if not pada_freqs:
        return np.zeros(1, dtype=np.float32), []

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

    return np.concatenate(steps).astype(np.float32), melody_freqs


# ------------------ Bolygó motívumok ------------------

def planet_motif(freq_base, elem, duration=2.0):
    scale = build_pentatonic_scale(freq_base)

    patterns = {
        "Tűz": [0, 1, 2, 4],
        "Víz": [2, 1, 2, 3],
        "Föld": [0, 0, 1, 0],
        "Levegő": [1, 3, 2, 4],
    }
    pattern = patterns.get(elem, [0, 1, 2, 3])

    note_dur = duration / len(pattern)
    notes = []
    for idx in pattern:
        f = scale[idx % len(scale)]
        n = sine_wave(f, note_dur, samplerate=SR)
        notes.append(n)
    return np.concatenate(notes).astype(np.float32)


def generate_planet_tracks(chart_data, tempo_factor, volume, include_rahu, include_ketu, target_length_samples):
    planet_data = chart_data.get("planet_data", {})
    tithi = chart_data.get("tithi", 1)
    nakshatra = chart_data.get("nakshatra", "Ashwini")

    tracks = []

    nd = nakshatra_data.get(nakshatra, {})
    base_freq = nd.get("pada_freqs", [220.0])[0]

    for idx, (planet_name, pos) in enumerate(planet_data.items()):
        elem = pos.get("element", "Tűz")
        rhythm = rhythm_from_element(elem) * tempo_factor

        motif = planet_motif(base_freq, elem, duration=2.0)
        motif = apply_tithi_dynamics(motif, tithi, samplerate=SR)
        motif *= volume * 0.5

        if planet_name.lower() == "rahu" and include_rahu:
            motif = rahu_timbre(motif)
        elif planet_name.lower() == "ketu" and include_ketu:
            motif = ketu_timbre(motif)

        full_track = np.zeros(target_length_samples, dtype=np.float32)
        start_delay = idx * int(1.5 * SR)

        pointer = start_delay
        while pointer < target_length_samples:
            end_pos = pointer + len(motif)
            if end_pos > target_length_samples:
                full_track[pointer:] += motif[:target_length_samples - pointer]
                break
            full_track[pointer:end_pos] += motif
            pointer += len(motif) + int(rhythm * SR * 4)

        tracks.append(full_track.astype(np.float32))

    return tracks


# ------------------ Mantra track ------------------

def generate_mantra_track_from_files(chart_data, volume):
    asc_sign = chart_data.get("asc_sign")
    if not asc_sign or asc_sign not in mantra_map:
        return np.zeros(1, dtype=np.float32)

    planet, target_freq, mantra_name = mantra_map[asc_sign]

    mantra_file = BASE_DIR.parent / "static" / "hangok" / "mantrák" / f"{mantra_name}.wav"
    if not mantra_file.exists():
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


# ------------------ Mix ------------------

def mix_tracks(tracks):
    if not tracks:
        return np.zeros(1, dtype=np.float32)
    max_len = max(len(t) for t in tracks)
    mix = np.zeros(max_len, dtype=np.float32)
    for t in tracks:
        mix[:len(t)] += t * 0.25
    m = np.max(np.abs(mix)) or 1.0
    return (mix / m).astype(np.float32)


# ------------------ MIDI ------------------

def save_midi_score(freqs, output_path):
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    def freq_to_midi(freq):
        if freq <= 0:
            return 60
        return int(round(12 * np.log2(freq / 440.0) + 69))

    for f in freqs:
        note = freq_to_midi(f)
        track.append(Message("note_on", note=note, velocity=64, time=0))
        track.append(Message("note_off", note=note, velocity=64, time=400))

    mid.save(output_path)


# ------------------ Fő generáló függvény ------------------

def generate_full_audio(chart_data, birth_data, text="", mood="", keywords="", symbols=None):
    if symbols is None:
        symbols = []

    # --- ADAPTER: kompatibilis a te chart_data formátumoddal ---
    planet_data = chart_data.get("planets", chart_data.get("planet_data", {}))
    tithi = chart_data.get("tithi", 1)
    nakshatra = planet_data.get("Moon", {}).get("nakshatra", "Ashwini")
    asc_sign = chart_data.get("ascendant", {}).get("sign")

    chart = {
        "planet_data": planet_data,
        "tithi": tithi,
        "nakshatra": nakshatra,
        "asc_sign": asc_sign,
    }

    # --- Paraméterek ---
    tempo_factor = 1.0
    volume = 1.0
    include_rahu = True
    include_ketu = True

    # --- Fővonal ---
    main_track, melody_freqs = generate_108_pada_main_track(nakshatra, tithi, volume)
    main_len = len(main_track)

    # --- Bolygó sávok ---
    planet_tracks = generate_planet_tracks(
        chart, tempo_factor, volume, include_rahu, include_ketu, target_length_samples=main_len
    )

    # --- Mantra ---
    mantra_track = generate_mantra_track_from_files(chart, volume)
    planet_tracks.append(mantra_track)

    # --- Mix ---
    final = mix_tracks([main_track] + planet_tracks)

    # --- Mentés ---
    safe_name = birth_data["name"].replace(" ", "_")
    wav_path = os.path.join(OUTPUT_DIR, f"{safe_name}_sonic_jyotish.wav")
    mid_path = os.path.join(OUTPUT_DIR, f"{safe_name}_sonic_jyotish.mid")

    with wave.open(wav_path, "w") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes((final * 32767).astype(np.int16).tobytes())

    if melody_freqs:
        save_midi_score(melody_freqs, mid_path)

    return wav_path

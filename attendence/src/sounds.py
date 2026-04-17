"""
sounds.py — Pure-stdlib WAV generator for the browser audio injection system.
No external libraries required (uses only wave, math, struct, io, base64).
"""
import wave
import math
import struct
import io
import base64

SAMPLE_RATE = 44100


def _write_wav(samples: list[float]) -> bytes:
    """Convert a list of float samples [-1.0, 1.0] to raw WAV bytes (mono, 16-bit)."""
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(SAMPLE_RATE)
        packed = struct.pack(f"<{len(samples)}h", *[int(s * 32767) for s in samples])
        wf.writeframes(packed)
    return buf.getvalue()


def _envelope(i: int, total: int, attack_pct: float = 0.05, release_pct: float = 0.4) -> float:
    """Simple ADSR-style envelope: linear attack then exponential release."""
    attack_end = int(total * attack_pct)
    release_start = int(total * (1.0 - release_pct))
    if i < attack_end:
        return i / max(attack_end, 1)
    elif i >= release_start:
        progress = (i - release_start) / max(total - release_start, 1)
        return math.exp(-4.0 * progress)
    return 1.0


def _generate_default_chime(volume: float) -> bytes:
    """880 Hz sine with smooth fade-out — 0.8 seconds."""
    duration = 0.8
    freq = 880.0
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        s = math.sin(2 * math.pi * freq * t) * _envelope(i, n, 0.02, 0.5)
        samples.append(s * volume)
    return _write_wav(samples)


def _generate_soft_bell(volume: float) -> bytes:
    """523 Hz + 1046 Hz harmonic blend — 1.0 second with decay."""
    duration = 1.0
    freq1, freq2 = 523.25, 1046.5
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        env = _envelope(i, n, 0.01, 0.6)
        s = (0.6 * math.sin(2 * math.pi * freq1 * t) +
             0.4 * math.sin(2 * math.pi * freq2 * t)) * env
        samples.append(s * volume)
    return _write_wav(samples)


def _generate_digital_beep(volume: float) -> bytes:
    """1200 Hz near-square wave — short 0.3 second chirp."""
    duration = 0.3
    freq = 1200.0
    n = int(SAMPLE_RATE * duration)
    samples = []
    for i in range(n):
        t = i / SAMPLE_RATE
        # Approximate a soft square by summing odd harmonics
        s = (math.sin(2 * math.pi * freq * t) +
             0.33 * math.sin(2 * math.pi * 3 * freq * t) +
             0.2 * math.sin(2 * math.pi * 5 * freq * t)) * _envelope(i, n, 0.01, 0.3)
        samples.append(s * volume)
    return _write_wav(samples)


SOUND_MAP = {
    "Default Chime": _generate_default_chime,
    "Soft Bell": _generate_soft_bell,
    "Digital Beep": _generate_digital_beep,
}


def get_sound_b64(sound_type: str = "Default Chime", volume_pct: int = 60) -> str:
    """
    Returns a base64-encoded data URI for the requested sound type and volume.
    volume_pct: 0–100 integer.
    """
    volume = max(0.0, min(1.0, volume_pct / 100.0))
    generator = SOUND_MAP.get(sound_type, _generate_default_chime)
    wav_bytes = generator(volume)
    b64 = base64.b64encode(wav_bytes).decode("utf-8")
    return f"data:audio/wav;base64,{b64}"

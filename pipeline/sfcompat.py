"""soundfile si disponible, sinon lecture/écriture WAV 16 bits avec le module standard (tests hors-ligne)."""
try:
    import soundfile as _sf
    read, write = _sf.read, _sf.write
except ImportError:  # pragma: no cover
    import wave
    import numpy as np

    def read(path, dtype="float32"):
        with wave.open(str(path)) as w:
            sr, ch, n = w.getframerate(), w.getnchannels(), w.getnframes()
            a = np.frombuffer(w.readframes(n), dtype=np.int16).astype(dtype) / 32768
        return (a.reshape(-1, ch) if ch > 1 else a), sr

    def write(path, data, sr, subtype=None):
        a = np.asarray(data, dtype=np.float64)
        ch = 1 if a.ndim == 1 else a.shape[1]
        with wave.open(str(path), "wb") as w:
            w.setnchannels(ch); w.setsampwidth(2); w.setframerate(int(sr))
            w.writeframes((np.clip(a, -1, 1) * 32767).astype(np.int16).tobytes())

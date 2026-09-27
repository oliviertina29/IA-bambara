"""Étape MIXAGE : musique de fond (générée, libre de droits) + transitions + petits sons + voix, musique baissée sous la voix."""
import json, sys
from pathlib import Path
import numpy as np
import sfcompat as sf

SR = 44100
ROOT = Path(__file__).resolve().parent.parent


def run(ep_dir):
    ep_dir = Path(ep_dir)
    out = ep_dir / "out"
    ep = json.loads((ep_dir / "episode.json").read_text(encoding="utf-8"))
    tm = json.loads((out / "timing.json").read_text(encoding="utf-8"))
    DUR = tm["sc"][-1][1]
    N = int(SR * DUR)
    music = np.zeros(N)
    rng = np.random.default_rng(3)

    def place(buf, sig, t, g=1.0):
        i = int(t * SR)
        if i >= N or i < 0:
            return
        j = min(N, i + len(sig))
        buf[i:j] += sig[: j - i] * g

    def env(n, a=0.004, d=0.3):
        tt = np.arange(n) / SR
        e = np.exp(-tt / d)
        na = max(1, int(a * SR))
        e[:na] *= np.linspace(0, 1, na)
        return e

    def marimba(f, d=0.45):
        n = int(SR * 1.2); tt = np.arange(n) / SR
        s = np.sin(2*np.pi*f*tt) + .35*np.sin(2*np.pi*f*4*tt)*np.exp(-tt/.05) + .15*np.sin(2*np.pi*f*10*tt)*np.exp(-tt/.02)
        return s * env(n, .002, d)

    def kick():
        n = int(SR * .35); tt = np.arange(n) / SR
        f = 45 + 90 * np.exp(-tt / .04)
        return np.sin(2*np.pi*np.cumsum(f)/SR) * env(n, .001, .12)

    def noise(n, d):
        s = rng.standard_normal(n)
        return np.diff(np.concatenate([[0], s])) * env(n, .003, d) * .5

    def bass(f):
        n = int(SR * .6); tt = np.arange(n) / SR
        return (np.sin(2*np.pi*f*tt) + .2*np.sin(4*np.pi*f*tt)) * env(n, .005, .35)

    A3, C4, D4, E4, G4, A4, C5, D5 = 220, 261.63, 293.66, 329.63, 392, 440, 523.25, 587.33
    riffs = [[A4, None, C5, A4, None, E4, G4, None, A4, None, C5, D5, None, C5, A4, None],
             [G4, None, A4, G4, None, E4, D4, None, E4, None, G4, A4, None, G4, E4, None]]
    bl = [A3/2, A3/2, C4/2, G4/4]
    step = 60 / 104 / 4
    t = 0.0; bar = 0
    while t < DUR - 1:
        for k in range(16):
            tt = t + k * step
            if tt > DUR - 1: break
            if k in (0, 8): place(music, kick(), tt, .9)
            if k in (6, 11) and bar % 2: place(music, kick(), tt, .5)
            place(music, noise(int(SR*.12), .03 if k % 2 == 0 else .05), tt, .10 if k % 2 == 0 else .18)
            if k in (4, 12): place(music, noise(int(SR*.15), .05), tt, .45)
            f = riffs[bar % 2][k]
            if f and t > .3: place(music, marimba(f), tt, .20)
            if k % 4 == 0: place(music, bass(bl[k // 4]), tt, .35)
        t += 16 * step; bar += 1

    fx = np.zeros(N)
    def whoosh(t0, length=1.0):
        n = int(SR * length); s = rng.standard_normal(n); kk = np.linspace(0, 1, n)
        cut = .02 + .35 * np.sin(np.pi * kk) ** 2; y = np.zeros(n); acc = 0.0
        for i in range(n):
            acc += cut[i] * (s[i] - acc); y[i] = acc
        place(fx, y * np.sin(np.pi * kk) ** 1.5, t0 - length * .55, .9)

    def pop(t0, f=900, g=.35):
        n = int(SR * .12); tt = np.arange(n) / SR
        fr = f * (1 + 1.5 * np.exp(-tt / .015))
        place(fx, np.sin(2*np.pi*np.cumsum(fr)/SR) * env(n, .001, .035), t0, g)

    for a, _ in tm["sc"][1:]:
        whoosh(a)
    for i, (a, b) in enumerate(tm["sc"]):
        pop(a + .35, 700 + 90 * (i % 5))
        if ep["scenes"][i]["type"] == "cards":
            for c in tm["clauses"][i]:
                pop(c[0] - .15, 850)

    vo = np.zeros(N)
    for t0, f in tm["voice"]:
        a, sr = sf.read(out / f, dtype="float64")
        if a.ndim > 1: a = a.mean(1)
        x = np.interp(np.arange(int(len(a) * SR / sr)) * sr / SR, np.arange(len(a)), a)
        place(vo, x, t0)
    if np.max(np.abs(vo)) > 0:
        vo = vo / np.max(np.abs(vo)) * .95
    act = np.convolve((np.abs(vo) > .02).astype(float), np.ones(int(.25*SR)) / int(.25*SR), mode="same")
    duck = 1 - .6 * np.clip(act * 4, 0, 1)
    mv = float(ep.get("music_volume", 0.4))
    mix = music / (np.max(np.abs(music)) or 1) * mv * duck + fx / (np.max(np.abs(fx)) or 1) * .25 + vo
    fade = np.ones(N); fi = int(.3 * SR); fo = int(1.8 * SR)
    fade[:fi] = np.linspace(0, 1, fi); fade[-fo:] = np.linspace(1, 0, fo)
    mix = np.tanh(mix * fade * 1.1)
    mix = mix / np.max(np.abs(mix)) * .89
    sf.write(out / "audio.wav", np.stack([mix, mix], 1).astype(np.float32), SR, subtype="PCM_16")
    print("[mix] audio.wav", round(DUR, 1), "s", flush=True)


if __name__ == "__main__":
    run(sys.argv[1])

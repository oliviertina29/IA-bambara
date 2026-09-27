"""Contrôle rapide SANS voix : minutage estimé (≈0,4 s par mot) puis quelques images fixes dans out/preview_*.png.
Sert au contrôleur pour vérifier qu'un épisode s'affiche correctement avant de lancer la vraie production."""
import json, re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import render

ROOT = Path(__file__).resolve().parent.parent
TYPES = json.loads((ROOT / "engine" / "scene_types.json").read_text(encoding="utf-8"))


def pace_rules(r, ep):
    """Rythme rapide (episode.pace = "fast") : moins de silences, scènes plus courtes."""
    if ep.get("pace") != "fast":
        return r
    f = TYPES.get("_pace_fast", {})
    return {**r, **{k: r[k] * f.get(k, 1) for k in ("lead", "tail", "min")}}


def fake_timing(ep):
    sc, words, clauses, t = [], [], [], 0.0
    for s in ep["scenes"]:
        r = pace_rules(TYPES.get(s["type"], TYPES["robot_says"]), ep); lt = r["lead"]; cl = []; wt = []
        for line in s.get("bm", []):
            ws = [w for w in line.replace("[", "").replace("]", "").split() if not re.fullmatch(r"[!?.,:;]+", w)]
            d = 0.4 * len(ws) + 0.2
            for k in range(len(ws)): wt.append(round(t + lt + d * k / max(1, len(ws)), 3))
            cl.append([round(t + lt, 3), round(t + lt + d, 3)]); lt += d + 0.35
        L = max(r["min"], lt + r["tail"]); sc.append([round(t, 3), round(t + L, 3)]); words.append(wt); clauses.append(cl); t += L
    return {"engine": "estimation", "sc": sc, "words": words, "clauses": clauses, "voice": [], "duration": round(t, 3)}


def main(ep_dir):
    ep_dir = Path(ep_dir); out = ep_dir / "out"; out.mkdir(exist_ok=True)
    ep = json.loads((ep_dir / "episode.json").read_text(encoding="utf-8"))
    unknown = [s["type"] for s in ep["scenes"] if s["type"] not in TYPES or s["type"].startswith("_")]
    if unknown: print("⚠ types de scène inconnus :", unknown)
    tm = fake_timing(ep)
    real = (out / "timing.json").read_text(encoding="utf-8") if (out / "timing.json").exists() else None
    (out / "timing.json").write_text(json.dumps(tm), encoding="utf-8")
    try:
        ts = [round(a + (b - a) * 0.75, 1) for a, b in tm["sc"]]
        render.run(ep_dir, preview_only=ts)
        print("images :", [f"preview_{x:05.1f}.png" for x in ts], "durée estimée", tm["duration"], "s")
    finally:
        if real is not None: (out / "timing.json").write_text(real, encoding="utf-8")
        else: (out / "timing.json").unlink()


if __name__ == "__main__":
    main(sys.argv[1])

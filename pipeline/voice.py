"""Étape VOIX : transforme les répliques bambara d'un épisode en audio + calcule le minutage.

Moteurs disponibles (champ episode.voice.engine) :
  - "spark"    : MALIBA-AI/bambara-tts (Spark-TTS, 10 voix maliennes, meilleure qualité, lent sur CPU)
  - "vits"     : MALIBA-AI/malian-tts, dossier models/bambara (VITS, rapide sur CPU)
  - "auto"     : essaie spark, puis vits
  - "sherpa-sw": voix swahilie locale (uniquement pour tester le pipeline sans Hugging Face)
Les modèles MALIBA-AI sont à accès restreint : il faut un jeton HF_TOKEN (compte gratuit + conditions acceptées).
"""
import json, os, re, sys, subprocess, time
from pathlib import Path
import numpy as np
import sfcompat as sf

ROOT = Path(__file__).resolve().parent.parent
TYPES = json.loads((ROOT / "engine" / "scene_types.json").read_text(encoding="utf-8"))
DEFAULT_SAY = {"IA": "i a", "AI": "e ai"}


def log(*a):
    print("[voix]", *a, flush=True)


def clean(text, say):
    t = text.replace("[", "").replace("]", "")
    for k, v in {**DEFAULT_SAY, **say}.items():
        t = re.sub(rf"\b{re.escape(k)}\b", v, t)
    return t.strip()


# ---------------------------------------------------------------- engines
class Vits:
    name = "vits"

    def __init__(self, lang="bambara"):
        import torch
        from transformers import VitsModel, AutoTokenizer
        tok = os.environ.get("HF_TOKEN")
        mid = "MALIBA-AI/malian-tts"
        self.tok = AutoTokenizer.from_pretrained(mid, subfolder=f"models/{lang}", token=tok)
        self.model = VitsModel.from_pretrained(mid, subfolder=f"models/{lang}", token=tok).eval()
        self.sr = self.model.config.sampling_rate
        self.torch = torch
        torch.manual_seed(0)

    def say(self, text):
        inp = self.tok(text, return_tensors="pt")
        with self.torch.no_grad():
            w = self.model(**inp).waveform
        return w.squeeze().cpu().numpy().astype(np.float32)


class Spark:
    name = "spark"

    def __init__(self, speaker="Seydou"):
        from maliba_ai.tts.inference import BambaraTTSInference
        from maliba_ai.config.settings import Speakers
        self.tts = BambaraTTSInference()
        self.spk = getattr(Speakers, speaker, None) or getattr(Speakers, "Seydou")
        self.sr = 16000

    def say(self, text):
        a = self.tts.generate_speech(text=text, speaker_id=self.spk)
        return np.asarray(a, dtype=np.float32).squeeze()


class SherpaSw:
    """Voix swahilie hors-ligne (tests uniquement). Chemins via SHERPA_BIN / SHERPA_MODEL."""
    name = "sherpa-sw"

    def __init__(self):
        self.bin = os.environ["SHERPA_BIN"]
        self.mdl = os.environ["SHERPA_MODEL"]
        self.sr = 22050

    def say(self, text):
        for a, b in [("ɛ", "e"), ("ɔ", "o"), ("ɲ", "ny"), ("ŋ", "ng"), ("Ɛ", "E"), ("Ɔ", "O"), ("Ɲ", "Ny")]:
            text = text.replace(a, b)
        out = "/tmp/_sherpa.wav"
        m = self.mdl
        subprocess.run([self.bin, f"--vits-model={m}/sw_CD-lanfrica-medium.onnx", f"--vits-tokens={m}/tokens.txt",
                        f"--vits-data-dir={m}/espeak-ng-data", "--vits-length-scale=1.12", "--num-threads=2",
                        f"--output-filename={out}", text], check=True, capture_output=True)
        a, sr = sf.read(out, dtype="float32")
        self.sr = sr
        return a


def make_engine(cfg):
    eng = cfg.get("engine", "auto")
    order = {"auto": ["spark", "vits"], "spark": ["spark", "vits"], "vits": ["vits"], "sherpa-sw": ["sherpa-sw"]}.get(eng, ["vits"])
    last = None
    for e in order:
        try:
            t0 = time.time()
            if e == "spark":
                obj = Spark(cfg.get("speaker", "Seydou"))
            elif e == "vits":
                obj = Vits(cfg.get("lang", "bambara"))
            else:
                obj = SherpaSw()
            log(f"moteur '{e}' chargé en {time.time()-t0:.1f}s")
            return obj
        except Exception as ex:  # noqa
            last = ex
            log(f"moteur '{e}' indisponible : {type(ex).__name__}: {ex}")
    raise RuntimeError(f"aucun moteur de voix disponible ({last})")


def trim(a, sr, th=0.01):
    idx = np.where(np.abs(a) > th)[0]
    if not len(idx):
        return a
    return a[max(0, idx[0] - int(0.01 * sr)): idx[-1] + int(0.02 * sr)]


# ---------------------------------------------------------------- main
def run(ep_dir):
    ep_dir = Path(ep_dir)
    ep = json.loads((ep_dir / "episode.json").read_text(encoding="utf-8"))
    out = ep_dir / "out"
    (out / "voice").mkdir(parents=True, exist_ok=True)
    cfg = ep.get("voice", {})
    engine = make_engine(cfg)
    say_map = ep.get("pronounce", {})
    speed = float(cfg.get("speed", 1.0))  # >1 = plus lent (étirement léger par ré-échantillonnage)

    sc, words_all, clauses_all, voice = [], [], [], []
    t = 0.0
    for i, scene in enumerate(ep["scenes"]):
        rules = TYPES.get(scene["type"], TYPES["robot_says"])
        lt = rules["lead"]
        cl = []
        lines = [c if isinstance(c, str) else c["text"] for c in scene.get("bm", [])]
        for k, line in enumerate(lines):
            txt = clean(line, say_map)
            t0 = time.time()
            a = trim(engine.say(txt), engine.sr)
            if speed != 1.0:
                n = int(len(a) * speed)
                a = np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype(np.float32)
            f = f"voice/s{i:02d}_{k:02d}.wav"
            sf.write(out / f, a, engine.sr)
            d = len(a) / engine.sr
            log(f"scène {i} phrase {k}: {d:.2f}s audio en {time.time()-t0:.1f}s — {txt}")
            cl.append({"text": line, "t0": lt, "t1": lt + d})
            voice.append([round(t + lt, 3), f])
            lt += d + (0.5 if line.rstrip()[-1:] in "?!." else 0.3)
        voice_end = lt - (0.3 if cl else 0)
        L = max(rules["min"], voice_end + rules["tail"])
        sc.append([round(t, 3), round(t + L, 3)])
        wt = []
        for c in cl:
            ws = [w for w in c["text"].replace("[", "").replace("]", "").split() if not re.fullmatch(r"[!?.,:;]+", w)]
            tot = sum(len(w) + 1 for w in ws) or 1
            acc = 0
            for w in ws:
                wt.append(round(t + c["t0"] + (c["t1"] - c["t0"]) * acc / tot - 0.08, 3))
                acc += len(w) + 1
        words_all.append(wt)
        clauses_all.append([[round(t + c["t0"], 3), round(t + c["t1"], 3)] for c in cl])
        t += L
    timing = {"engine": engine.name, "sc": sc, "words": words_all, "clauses": clauses_all, "voice": voice, "duration": round(t, 3)}
    (out / "timing.json").write_text(json.dumps(timing, indent=1, ensure_ascii=False), encoding="utf-8")
    log(f"durée totale {t:.1f}s avec le moteur {engine.name}")
    return timing


if __name__ == "__main__":
    run(sys.argv[1])

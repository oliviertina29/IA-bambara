"""Génère la même phrase avec chaque moteur / voix pour comparer (résultats dans voice-tests/)."""
import sys, time, traceback
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice, sfcompat as sf

TEXT = "I ni ce! I ye i a tɔgɔ mɛn wa? A kɔrɔ ye mun ye? An ka i a kalan ɲɔgɔn fɛ."
out = Path("voice-tests"); out.mkdir(exist_ok=True)
lines = []
try:
    t = time.time(); v = voice.Vits(); load = time.time() - t
    t = time.time(); a = v.say(TEXT); sf.write(out / "vits_bambara.wav", a, v.sr)
    lines.append(f"vits: chargement {load:.0f}s, génération {time.time()-t:.1f}s pour {len(a)/v.sr:.1f}s d'audio")
except Exception:
    lines.append("vits: ÉCHEC\n" + traceback.format_exc()[-1500:])
for spk in ["Seydou", "Bourama", "Adama", "Modibo"]:
    try:
        t = time.time(); s = voice.Spark(spk); load = time.time() - t
        t = time.time(); a = s.say(TEXT); sf.write(out / f"spark_{spk}.wav", a, s.sr)
        lines.append(f"spark {spk}: chargement {load:.0f}s, génération {time.time()-t:.1f}s pour {len(a)/s.sr:.1f}s d'audio")
    except Exception:
        lines.append(f"spark {spk}: ÉCHEC\n" + traceback.format_exc()[-1500:])
        break
(out / "resultats.txt").write_text("\n".join(lines), encoding="utf-8")
print("\n".join(lines))

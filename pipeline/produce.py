"""Chaîne complète : voix -> mixage -> rendu. Usage : python pipeline/produce.py episodes/<slug>"""
import json, sys, time, traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import voice, mix, render  # noqa: E402


def main(ep_dir):
    ep_dir = Path(ep_dir)
    (ep_dir / "out").mkdir(exist_ok=True)
    status = {"episode": ep_dir.name, "started": time.strftime("%Y-%m-%d %H:%M:%S")}
    try:
        t = time.time(); tm = voice.run(ep_dir); status["voice_s"] = round(time.time() - t); status["engine"] = tm["engine"]
        t = time.time(); mix.run(ep_dir); status["mix_s"] = round(time.time() - t)
        t = time.time(); video = render.run(ep_dir); status["render_s"] = round(time.time() - t)
        status.update(ok=True, video="out/" + video.name, duration=tm["duration"])
    except Exception as e:  # noqa
        status.update(ok=False, error=f"{type(e).__name__}: {e}", trace=traceback.format_exc()[-3000:])
        print(status["trace"], flush=True)
    (ep_dir / "out" / "status.json").write_text(json.dumps(status, indent=1, ensure_ascii=False), encoding="utf-8")
    print("[statut]", json.dumps({k: v for k, v in status.items() if k != "trace"}, ensure_ascii=False), flush=True)
    return status["ok"]


if __name__ == "__main__":
    ok = all(main(d) for d in sys.argv[1:])
    sys.exit(0 if ok else 1)

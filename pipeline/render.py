"""Étape RENDU : anime l'épisode image par image avec le moteur HTML puis encode le MP4 (1080x1920, 30 i/s)."""
import json, subprocess, sys, time
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
FPS = 30


def run(ep_dir, preview_only=None):
    ep_dir = Path(ep_dir).resolve()
    out = ep_dir / "out"
    ep = json.loads((ep_dir / "episode.json").read_text(encoding="utf-8"))
    tm = json.loads((out / "timing.json").read_text(encoding="utf-8"))
    for i, sc in enumerate(ep["scenes"]):
        f = out / "img" / f"s{i:02d}.png"
        if f.exists():
            sc["image_file"] = f.resolve().as_uri()
    types = json.loads((ROOT / "engine" / "scene_types.json").read_text(encoding="utf-8"))
    init = f"window.EPISODE={json.dumps(ep, ensure_ascii=False)};window.TIMING={json.dumps(tm)};window.SCENE_TYPES={json.dumps(types)};"
    url = (ROOT / "engine" / "index.html").as_uri() + "?capture=1"
    dur = tm["sc"][-1][1]
    with sync_playwright() as p:
        b = p.chromium.launch(args=["--font-render-hinting=none"])
        pg = b.new_page(viewport={"width": 1080, "height": 1920})
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.add_init_script(init)
        pg.goto(url)
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        if errs:
            raise RuntimeError("erreur dans le moteur : " + "; ".join(errs))
        if preview_only is not None:  # quelques images fixes pour vérification
            for t in preview_only:
                pg.evaluate(f"render({t})")
                pg.screenshot(path=str(out / f"preview_{t:05.1f}.png"))
            b.close()
            return
        name = ep.get("slug", ep_dir.name) + ".mp4"
        ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(FPS), "-i", "-",
                               "-i", str(out / "audio.wav"), "-c:v", "libx264", "-preset", "medium", "-crf", "20",
                               "-pix_fmt", "yuv420p", "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-shortest",
                               "-movflags", "+faststart", str(out / name)], stdin=subprocess.PIPE)
        n = int(dur * FPS); t0 = time.time()
        for i in range(n):
            pg.evaluate(f"render({i / FPS})")
            ff.stdin.write(pg.screenshot(type="jpeg", quality=92))
            if i % 300 == 0:
                print(f"[rendu] image {i}/{n} ({time.time()-t0:.0f}s)", flush=True)
        b.close()
    ff.stdin.close(); ff.wait()
    if errs:
        raise RuntimeError("erreur dans le moteur : " + "; ".join(errs))
    print(f"[rendu] {name} prêt en {time.time()-t0:.0f}s", flush=True)
    return out / name


if __name__ == "__main__":
    run(sys.argv[1])

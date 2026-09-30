"""Étape IMAGES : génère une illustration réaliste par scène qui a un champ "image" (prompt en anglais).
Modèle : stabilityai/sd-turbo (rapide, tourne sur CPU en 1–2 étapes). Images dans out/img/sNN.png."""
import json, sys, time
from pathlib import Path

STYLE = ", vibrant colors, detailed, cinematic lighting, high quality photo, vertical composition"


def run(ep_dir):
    ep_dir = Path(ep_dir)
    ep = json.loads((ep_dir / "episode.json").read_text(encoding="utf-8"))
    todo = [(i, s["image"]) for i, s in enumerate(ep["scenes"]) if s.get("image")]
    if not todo:
        return 0
    import torch
    from diffusers import AutoPipelineForText2Image
    torch.set_num_threads(max(1, torch.get_num_threads()))
    t0 = time.time()
    pipe = AutoPipelineForText2Image.from_pretrained("stabilityai/sd-turbo", torch_dtype=torch.float32)
    pipe.set_progress_bar_config(disable=True)
    print(f"[images] modèle chargé en {time.time()-t0:.0f}s", flush=True)
    out = ep_dir / "out" / "img"
    out.mkdir(parents=True, exist_ok=True)
    n = 0
    for i, prompt in todo:
        t = time.time()
        g = torch.Generator().manual_seed(1000 + i)
        img = pipe(prompt=prompt + STYLE, num_inference_steps=2, guidance_scale=0.0,
                   width=512, height=768, generator=g).images[0]
        img.save(out / f"s{i:02d}.png")
        n += 1
        print(f"[images] scène {i} en {time.time()-t:.0f}s : {prompt}", flush=True)
    return n


if __name__ == "__main__":
    run(sys.argv[1])

"""Composite captured keystroke states onto one frozen base frame so only the name changes.

usage: python3 tools/capture/composite_states.py <captureDir>
Reads <id>_orig|sel|tNN.webp + meta_<id>.json from capture_states.mjs, writes assets/designs/<id>_<state>.webp
(2880x1620) plus, for Cantara, a 3x crop of the nav band (<id>_<state>.hi.webp) for the macro shot,
and assets/designs/meta.json (caret geometry in CSS px + text colour) for index.html.
"""
import glob, json, os, sys
from PIL import Image

SRC = sys.argv[1]
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "designs")

# regions in CSS px (x0, y0, x1, y1): taken from every state / only from the final state
JOBS = {
    "foodee": {"all": [(0, 374, 1920, 604)], "final": [(0, 12, 1920, 46)]},
    "cantara": {"all": [(0, 14, 1920, 62)], "final": [], "hi": (240, 0, 1040, 84)},
    "azur": {"all": [(253, 767, 1920, 974)], "final": [(0, 0, 733, 66), (253, 386, 833, 533)]},
}
meta_all = {}
for id, job in JOBS.items():
    meta = json.load(open(f"{SRC}/meta_{id}.json"))
    dpr = meta["dpr"]
    px = lambda r: tuple(int(round(v * dpr)) for v in r)
    base = Image.open(f"{SRC}/{id}_orig.webp").convert("RGB")
    names = [s[0] for s in meta["states"]]
    for n in names:
        im = Image.open(f"{SRC}/{id}_{n}.webp").convert("RGB")
        out = base.copy()
        regs = job["all"] + (job["final"] if n == names[-1] else [])
        for r in regs:
            out.paste(im.crop(px(r)), px(r)[:2])
        out.resize((2880, 1620), Image.LANCZOS).save(f"{DST}/{id}_{n}.webp", quality=92)
        if "hi" in job:
            out.crop(px(job["hi"])).save(f"{DST}/{id}_{n}.hi.webp", quality=94)
    meta_all[id] = {"color": meta["color"], "states": [[s[0], round(s[1], 1), round(s[2], 1), round(s[3], 1)] for s in meta["states"]]}
    if "hi" in job:
        meta_all[id]["hi"] = job["hi"]
    print(id, len(names), "states")
json.dump(meta_all, open(f"{DST}/meta.json", "w"), separators=(",", ":"))

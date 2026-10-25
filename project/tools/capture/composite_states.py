"""Composite captured keystroke states onto one frozen base frame so only the name changes.

usage: python3 tools/capture/composite_states.py <captureDir> [--phone] [id ...]
Reads <id>_orig|sel|tNN.webp + meta_<id>.json from capture_states.mjs, writes assets/designs/<id>_<state>.webp
(2880x1620) plus, for Cantara, a 3x crop of the nav band (<id>_<state>.hi.webp) for the macro shot,
and assets/designs/meta.json (caret geometry in CSS px + text colour) for index.html.
Naming ids processes only those and merges them into the existing meta.json (e.g. foodee_fr for fr/).
--phone: captures made with capture_states.mjs --phone (402x874 @3x) -> assets/designs-phone/ at full 1206x2622, for reel/.
"""
import glob, json, os, sys
from PIL import Image

SRC = sys.argv[1]
PHONE = "--phone" in sys.argv
DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "assets", "designs-phone" if PHONE else "designs")

# regions in CSS px (x0, y0, x1, y1): taken from every state / only from the final state
JOBS = {
    "foodee": {"all": [(0, 374, 1920, 604)], "final": [(0, 12, 1920, 46)]},
    "foodee_fr": {"all": [(0, 374, 1920, 604)], "final": [(0, 12, 1920, 46)]},
    "cantara": {"all": [(0, 14, 1920, 62)], "final": [], "hi": (240, 0, 1040, 84)},
    "azur": {"all": [(253, 767, 1920, 974)], "final": [(0, 0, 733, 66), (253, 386, 833, 533)]},
}
# mobile layouts: the name band; the dish and the "scroll down" badge stay frozen from the base frame
PHONE_JOBS = {
    "foodee": {"all": [(0, 218, 402, 328)], "final": [(0, 22, 402, 54)]},
    "foodee_fr": {"all": [(0, 218, 402, 328)], "final": [(0, 22, 402, 54)]},
    "cantara": {"all": [(60, 20, 262, 66)], "final": []},
    "azur": {"all": [(70, 16, 300, 46)], "final": [(0, 372, 402, 426), (0, 842, 402, 874)]},
}
if PHONE:
    JOBS = PHONE_JOBS
    os.makedirs(DST, exist_ok=True)
ONLY = [a for a in sys.argv[2:] if not a.startswith("--")]
meta_all = json.load(open(f"{DST}/meta.json")) if ONLY else {}
for id, job in JOBS.items():
    if ONLY and id not in ONLY or not ONLY and id == "foodee_fr":
        continue
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
        (out if PHONE else out.resize((2880, 1620), Image.LANCZOS)).save(f"{DST}/{id}_{n}.webp", quality=92)
        if "hi" in job:
            out.crop(px(job["hi"])).save(f"{DST}/{id}_{n}.hi.webp", quality=94)
    meta_all[id] = {"color": meta["color"], "states": [[s[0], round(s[1], 1), round(s[2], 1), round(s[3], 1)] for s in meta["states"]]}
    if "hi" in job:
        meta_all[id]["hi"] = job["hi"]
    print(id, len(names), "states")
json.dump(meta_all, open(f"{DST}/meta.json", "w"), separators=(",", ":"))

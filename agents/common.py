"""Fungsi bersama: muat/simpan data, skor, dan proyeksi harga (sama dengan dashboard)."""
import json, math, os, datetime as dt
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
def p(*a): return os.path.join(ROOT, *a)
def load(path, default=None):
    try:
        with open(p(path), encoding="utf-8") as f: return json.load(f)
    except FileNotFoundError: return default
def save(path, obj):
    os.makedirs(os.path.dirname(p(path)), exist_ok=True)
    with open(p(path), "w", encoding="utf-8") as f: json.dump(obj, f, ensure_ascii=False, indent=1)
def today(): return dt.date.today().isoformat()
CFG = lambda: load("config/hotspots.json")
SET = lambda: load("config/settings.json", {})

STAGEW = [0, .2, .45, .85, 1, .6]
DEFW = {"katalis": 35, "celah": 35, "aktivitas": 15, "zonasi": 15, "risiko": 35}

def hotspots(cfg):
    """Ubah struktur array ringkas menjadi dict per titik."""
    out = []
    for prov in cfg["PROV"]:
        for a in prov["h"]:
            out.append({"id": a[0], "nama": a[1], "lokasi": a[2], "lat": a[3], "lon": a[4],
                        "zonasi": a[5], "aktivitas": a[6], "harga": a[7], "risiko": a[8],
                        "kat": [{"jenis": k[0], "nama": k[1], "tahap": k[2], "dampak": k[3], "cat": k[4]} for k in a[9]],
                        "note": a[10], "prov": prov["nama"], "prov_id": prov["id"], "prio": prov["prio"]})
    return out

def comp(h):
    ks = sorted((k["dampak"] * STAGEW[k["tahap"]] for k in h["kat"]), reverse=True)
    K = min(1, ((ks[0] if ks else 0) + .35 * sum(ks[1:])) / 5)
    return {"katalis": K, "celah": 1 - (h["harga"] - 1) / 4, "aktivitas": (h["aktivitas"] - 1) / 4,
            "zonasi": (h["zonasi"] - 1) / 4, "risk": (h["risiko"] - 1) / 4}

def score(h, w=DEFW, prio=True):
    c = comp(h); sw = w["katalis"] + w["celah"] + w["aktivitas"] + w["zonasi"]
    s = 100 * (w["katalis"] * c["katalis"] + w["celah"] * c["celah"] + w["aktivitas"] * c["aktivitas"] + w["zonasi"] * c["zonasi"]) / sw
    s *= 1 - (w["risiko"] / 100) * c["risk"]
    if prio: s += 8 if h["prio"] == 2 else 3 if h["prio"] == 1 else 0
    return max(0, min(100, round(s)))

def kategori(s): return "Panas" if s >= 70 else "Hangat" if s >= 55 else "Pantau" if s >= 40 else "Dingin"

def projeksi(h, cfg):
    up, sisa = cfg["UPLIFT"], cfg["SISA"]
    us = sorted((up[k["jenis"]] * k["dampak"] / 5 * sisa[k["tahap"]] for k in h["kat"]), reverse=True)
    tot = (us[0] if us else 0) + .4 * sum(us[1:])
    c = comp(h); g = tot * (.5 + .5 * c["celah"]); r = c["risk"]
    return {"kons": g * .4 * (1 - r * .5), "dasar": g * (1 - r * .3), "opt": g * 1.6}

def harga_tip(hid, cfg):
    x = cfg["HARGA"].get(hid)
    if not x: return None
    return x.get("tip") or round(math.sqrt(x["min"] * x["max"]))

"""Agen harga: membaca halaman pencarian iklan tanah, mengekstrak harga per m², lalu menghitung rentang pasar.

Hasil disimpan di data/price_obs.json (riwayat) dan, bila sampel cukup, memperbarui HARGA di config/hotspots.json.
Harga iklan adalah harga penawaran, bukan transaksi. Periksa syarat penggunaan tiap portal sebelum mengaktifkan.
"""
import re, time, statistics, requests
from bs4 import BeautifulSoup
from common import load, save, today, CFG, SET

UA = {"User-Agent": "Mozilla/5.0 (LandRadar research bot; contact: set-your-email@example.com)"}
NUM = r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?)"

def _num(s):
    s = s.strip()
    if re.fullmatch(r"\d{1,3}(\.\d{3})+", s): return float(s.replace(".", ""))
    if re.fullmatch(r"\d{1,3}(,\d{3})+", s): return float(s.replace(",", ""))
    return float(s.replace(",", "."))

MULT = {"miliar": 1e9, "milyar": 1e9, "m": 1e9, "juta": 1e6, "jt": 1e6, "ribu": 1e3, "rb": 1e3, "k": 1e3, "": 1}

def extract_prices(text):
    """Kembalikan daftar harga Rp/m² yang disebut eksplisit di teks iklan."""
    t = text.lower().replace("\u00b2", "2").replace("m²", "m2")
    hits = []  # (posisi, nilai)
    for m in re.finditer(r"(?:rp\.?\s*)?" + NUM + r"\s*(juta|jt|miliar|milyar)\s*(?:/|per)\s*(?:are|100\s*m2)", t):
        hits.append((m.start(), _num(m.group(1)) * MULT[m.group(2)] / 100))
    for m in re.finditer(r"(?:rp\.?\s*)?" + NUM + r"\s*(juta|jt|ribu|rb|k)?\s*(?:/|per)\s*(?:m2|meter|mtr|m\b)", t):
        hits.append((m.start(), _num(m.group(1)) * MULT[m.group(2) or ""]))
    for m in re.finditer(r"per\s*(?:meter|m2)\s*:?\s*rp\.?\s*" + NUM + r"\s*(juta|jt|ribu|rb)?", t):
        hits.append((m.start(), _num(m.group(1)) * MULT[m.group(2) or ""]))
    hits.sort()
    out, last = [], {}
    for pos, v in hits:  # satu iklan sering menyebut harga yang sama dua kali (per are dan per m²)
        key = round(v, -3)
        if key in last and pos - last[key] < 120: continue
        last[key] = pos; out.append(v)
    return [v for v in out if 5_000 <= v <= 150_000_000]

def summarize(vals):
    vals = sorted(vals)
    if len(vals) >= 8:  # buang pencilan dengan IQR
        q1, q3 = vals[len(vals)//4], vals[(3*len(vals))//4]; iqr = q3 - q1
        vals = [v for v in vals if q1 - 1.5*iqr <= v <= q3 + 1.5*iqr]
    pct = lambda q: vals[min(len(vals)-1, int(q*(len(vals)-1)))]
    return {"n": len(vals), "p10": pct(.1), "median": statistics.median(vals), "p90": pct(.9)}

def fetch_text(url):
    r = requests.get(url, headers=UA, timeout=30)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser").get_text(" ")

def run():
    cfg, st = CFG(), SET()
    obs = load("data/price_obs.json", {})
    changes = []
    for hid, urls in st.get("price_sources", {}).items():
        if hid.startswith("_"): continue
        vals, errs = [], []
        for u in urls:
            try: vals += extract_prices(fetch_text(u))
            except Exception as e: errs.append(f"{u}: {e}")
            time.sleep(st.get("request_delay_seconds", 4))
        if errs: print(f"[harga] {hid} gagal sebagian: {errs}")
        if len(vals) < st.get("price_min_samples", 5):
            print(f"[harga] {hid}: sampel {len(vals)}, belum cukup"); continue
        s = summarize(vals); s["tgl"] = today()
        hist = obs.setdefault(hid, []); prev = hist[-1] if hist else None
        hist.append(s); obs[hid] = hist[-60:]
        old = cfg["HARGA"].get(hid, {})
        cfg["HARGA"][hid] = {"min": round(s["p10"]), "tip": round(s["median"]), "max": round(s["p90"]),
                             "ket": f"Median dari {s['n']} harga iklan yang menyebut harga per m² atau per are",
                             "src": "Agen harga (portal iklan)", "tgl": today(), **({"ket_awal": old["ket"]} if old.get("ket") and "ket_awal" not in old else {})}
        base = prev["median"] if prev else old.get("tip")
        if base:
            ch = (s["median"] - base) / base * 100
            if abs(ch) >= st.get("price_change_alert_pct", 10):
                changes.append({"id": hid, "teks": f"Median harga iklan {hid} {'naik' if ch>0 else 'turun'} {abs(ch):.0f}% menjadi Rp{s['median']/1e6:.2f} jt/m²", "tgl": today()})
        print(f"[harga] {hid}: n={s['n']} median=Rp{s['median']:,.0f}/m²")
    save("data/price_obs.json", obs); save("config/hotspots.json", cfg)
    return changes

if __name__ == "__main__": print(run())

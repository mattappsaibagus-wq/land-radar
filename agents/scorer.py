"""Agen skor: hitung ulang skor dan proyeksi, bandingkan dengan snapshot sebelumnya, lalu tulis docs/data.js."""
import json, datetime as dt
from common import load, save, today, CFG, SET, hotspots, score, kategori, projeksi, harga_tip

def run(extra_alerts):
    cfg, st = CFG(), SET()
    prev = load("data/snapshot.json", {})
    snap, alerts = {}, list(extra_alerts)
    for h in hotspots(cfg):
        s = score(h); pr = projeksi(h, cfg); t = harga_tip(h["id"], cfg)
        snap[h["id"]] = {"skor": s, "kategori": kategori(s), "harga_tip": t, "potensi_dasar": round(pr["dasar"], 3),
                         "tahap": {k["nama"]: k["tahap"] for k in h["kat"]}}
        o = prev.get(h["id"])
        if not o: continue
        if o["kategori"] != kategori(s):
            alerts.append({"id": h["id"], "tgl": today(), "teks": f"{h['nama']} ({h['prov']}) pindah dari {o['kategori']} ke {kategori(s)}, skor {o['skor']} ke {s}"})
        elif abs(s - o["skor"]) >= st.get("score_change_alert_points", 5):
            alerts.append({"id": h["id"], "tgl": today(), "teks": f"Skor {h['nama']} berubah {o['skor']} ke {s}"})
    top = sorted(hotspots(cfg), key=lambda h: -score(h))[:5]
    old_hist = load("data/alerts.json", [])
    hist = (alerts + old_hist)[:200]
    save("data/snapshot.json", snap); save("data/alerts.json", hist)
    updated = dt.datetime.utcnow().strftime("%d %b %Y %H:%M UTC")
    js = "".join(f"const {k}={json.dumps(cfg[k], ensure_ascii=False)};\n" for k in ["TAHAP", "JENIS", "PULAU", "PROV", "HARGA", "UPLIFT", "SISA"])
    js += f"const ALERTS={json.dumps(hist[:30], ensure_ascii=False)};\nconst UPDATED={json.dumps(updated)};\n"
    with open(__import__('common').p("docs", "data.js"), "w", encoding="utf-8") as f: f.write(js)
    print("[skor] 5 teratas:", ", ".join(f"{h['nama']} {score(h)}" for h in top))
    return alerts

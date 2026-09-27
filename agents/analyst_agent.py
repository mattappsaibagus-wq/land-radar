"""Agen analis: Claude membaca berita baru per titik dan menilai apakah tahap katalis berubah atau muncul katalis baru.

Tanpa ANTHROPIC_API_KEY agen ini dilewati. Perubahan tahap hanya diterapkan otomatis bila
settings.auto_apply_stage_changes = true dan tingkat keyakinan Claude "tinggi"; selain itu hanya menjadi usulan.
"""
import os, json, re
from common import load, save, today, CFG, SET, hotspots

PROMPT = """Anda analis infrastruktur dan pasar tanah Indonesia. Nilai berita berikut untuk satu titik pantauan.
Tahap katalis: 1 Wacana, 2 Rencana resmi (PSN/RPJMN/RTRW), 3 Penlok/pembebasan lahan, 4 Konstruksi, 5 Beroperasi.
Hanya gunakan informasi di judul dan ringkasan berita. Jika tidak jelas, katakan tidak ada perubahan.

TITIK: {titik}
BERITA:
{berita}

Balas hanya JSON:
{{"perubahan":[{{"katalis":"nama persis dari daftar atau nama katalis baru","tahap_baru":1-5,"keyakinan":"tinggi|sedang|rendah","bukti":"judul berita pendukung"}}],
"sinyal":"positif|negatif|netral","ringkasan":"1 kalimat Bahasa Indonesia"}}"""

def ask(client, model, text):
    msg = client.messages.create(model=model, max_tokens=800, messages=[{"role": "user", "content": text}])
    raw = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
    raw = re.sub(r"```(?:json)?|```", "", raw).strip()
    return json.loads(raw[raw.find("{"): raw.rfind("}") + 1])

def run(news):
    if not news: return []
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key: print("[analis] ANTHROPIC_API_KEY tidak ada, dilewati"); return []
    import anthropic
    client = anthropic.Anthropic(api_key=key); st = SET(); cfg = CFG()
    by_id = {h["id"]: h for h in hotspots(cfg)}
    alerts, log = [], load("data/analyst_log.json", [])
    for hid, items in news.items():
        h = by_id.get(hid)
        if not h: continue
        titik = {"nama": h["nama"], "provinsi": h["prov"], "katalis": [{"nama": k["nama"], "tahap": k["tahap"]} for k in h["kat"]]}
        berita = "\n".join(f"- {i['judul']} ({i['tgl']}): {i['ringkas']}" for i in items)
        try: r = ask(client, st.get("claude_model", "claude-sonnet-5"), PROMPT.format(titik=json.dumps(titik, ensure_ascii=False), berita=berita))
        except Exception as e: print("[analis] gagal", hid, e); continue
        log.append({"id": hid, "tgl": today(), **r})
        for ch in r.get("perubahan", []):
            k = next((k for k in h["kat"] if k["nama"] == ch.get("katalis")), None)
            tb = ch.get("tahap_baru")
            if not isinstance(tb, int) or not 1 <= tb <= 5: continue
            if k and tb != k["tahap"]:
                applied = st.get("auto_apply_stage_changes") and ch.get("keyakinan") == "tinggi"
                if applied: _apply(cfg, hid, k["nama"], tb)
                alerts.append({"id": hid, "tgl": today(), "teks": f"{h['nama']}: {k['nama']} {'berubah' if applied else 'kemungkinan berubah'} ke tahap {tb} ({ch.get('keyakinan')}). {ch.get('bukti','')}"})
            elif not k:
                alerts.append({"id": hid, "tgl": today(), "teks": f"{h['nama']}: kemungkinan katalis baru \"{ch.get('katalis')}\" tahap {tb}. {ch.get('bukti','')}"})
        if r.get("sinyal") in ("positif", "negatif"):
            alerts.append({"id": hid, "tgl": today(), "teks": f"{h['nama']} ({r['sinyal']}): {r.get('ringkasan','')}"})
    save("data/analyst_log.json", log[-500:]); save("config/hotspots.json", cfg)
    return alerts

def _apply(cfg, hid, kname, tahap):
    for prov in cfg["PROV"]:
        for a in prov["h"]:
            if a[0] == hid:
                for k in a[9]:
                    if k[1] == kname: k[2] = tahap

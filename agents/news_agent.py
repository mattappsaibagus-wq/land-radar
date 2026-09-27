"""Agen berita: mencari berita terbaru per katalis lewat Google News RSS, menyimpan yang belum pernah dilihat."""
import time, urllib.parse, feedparser, datetime as dt
from common import load, save, CFG, SET, hotspots

def feed_url(q):
    return "https://news.google.com/rss/search?" + urllib.parse.urlencode({"q": f"{q} when:30d", "hl": "id", "gl": "ID", "ceid": "ID:id"})

def queries(h):
    qs = [f"\"{k['nama'].split('(')[0].strip()}\"" for k in h["kat"] if k["tahap"] < 5]
    qs.append(f"\"{h['nama']}\" tanah OR lahan OR investasi")
    return qs[:4]

def run():
    st = SET(); seen = set(load("data/news_seen.json", [])); cutoff = dt.datetime.utcnow() - dt.timedelta(days=st.get("news_lookback_days", 14))
    fresh = {}
    for h in hotspots(CFG()):
        items = []
        for q in queries(h):
            try: f = feedparser.parse(feed_url(q))
            except Exception as e: print("[berita] gagal", q, e); continue
            for e in f.entries:
                key = e.get("id") or e.get("link")
                pub = e.get("published_parsed")
                if key in seen or (pub and dt.datetime(*pub[:6]) < cutoff): continue
                seen.add(key)
                items.append({"judul": e.get("title", ""), "ringkas": e.get("summary", "")[:400], "link": e.get("link"), "tgl": e.get("published", "")})
            time.sleep(1)
        if items: fresh[h["id"]] = items[: st.get("news_max_items_per_hotspot", 8)]
    save("data/news_seen.json", sorted(seen)[-5000:]); save("data/news_latest.json", fresh)
    print(f"[berita] {sum(len(v) for v in fresh.values())} berita baru di {len(fresh)} titik")
    return fresh

if __name__ == "__main__": run()

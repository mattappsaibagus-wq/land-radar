"""Orkestrator Land Radar: harga -> berita -> analis (Claude) -> skor."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "agents"))
import price_agent, news_agent, analyst_agent, scorer

def main():
    only = set(sys.argv[1:])  # contoh: python run_all.py skor
    alerts = []
    if not only or "harga" in only:
        try: alerts += price_agent.run()
        except Exception as e: print("[harga] error:", e)
    news = {}
    if not only or "berita" in only:
        try: news = news_agent.run()
        except Exception as e: print("[berita] error:", e)
        try: alerts += analyst_agent.run(news)
        except Exception as e: print("[analis] error:", e)
    scorer.run(alerts)  # peringatan tampil di dashboard

if __name__ == "__main__": main()

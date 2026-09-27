"""Kirim peringatan ke Telegram bila TELEGRAM_BOT_TOKEN dan TELEGRAM_CHAT_ID tersedia."""
import os, requests
def send(alerts, url=None):
    tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not alerts: return
    text = "Land Radar: " + str(len(alerts)) + " perubahan\n\n" + "\n".join("• " + a["teks"] for a in alerts[:25])
    if url: text += f"\n\nDashboard: {url}"
    if not (tok and chat): print(text); return
    for i in range(0, len(text), 3900):
        requests.post(f"https://api.telegram.org/bot{tok}/sendMessage", json={"chat_id": chat, "text": text[i:i+3900], "disable_web_page_preview": True}, timeout=20)

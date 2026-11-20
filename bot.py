import json, os, re, sys, datetime
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT = os.environ.get("CHANNEL", "@Jizzaxfermerlari")
API = f"https://api.telegram.org/bot{TOKEN}"
TZ = datetime.timezone(datetime.timedelta(hours=5))  # Toshkent
MAX_PER_RUN = 2

def load(p, default):
    try:
        return json.load(open(p, encoding="utf-8"))
    except FileNotFoundError:
        return default

schedule = load("schedule.json", [])
sent = load("sent.json", [])
now = datetime.datetime.now(TZ)
changed = False
count = 0

def call(method, **kw):
    files = kw.pop("files", None)
    r = requests.post(f"{API}/{method}", data=kw, files=files, timeout=60)
    ok = r.status_code == 200 and r.json().get("ok")
    if not ok:
        print("Telegram xatosi:", r.status_code, r.text[:300])
    return ok

for e in schedule:
    if e["id"] in sent or count >= MAX_PER_RUN:
        continue
    when = datetime.datetime.strptime(e["when"], "%Y-%m-%d %H:%M").replace(tzinfo=TZ)
    if when > now:
        continue
    text = e["text"]
    if re.search(r"\[[^\]]*\]|\{[A-Z_]+\}", text):
        print("O'tkazib yuborildi (to'ldirilmagan joy bor):", e["id"])
        continue
    ok = False
    img = e.get("image")
    if img and os.path.exists(img):
        with open(img, "rb") as f:
            if len(text) <= 1024:
                ok = call("sendPhoto", chat_id=CHAT, caption=text, files={"photo": f})
            else:
                ok = call("sendPhoto", chat_id=CHAT, files={"photo": f})
                if ok:
                    ok = call("sendMessage", chat_id=CHAT, text=text)
    else:
        print("Rasm topilmadi, faqat matn:", e["id"])
        ok = call("sendMessage", chat_id=CHAT, text=text)
    if ok:
        sent.append(e["id"])
        changed = True
        count += 1
        print("Yuborildi:", e["id"])

if changed:
    json.dump(sent, open("sent.json", "w"), indent=1)

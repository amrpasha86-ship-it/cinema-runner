"""Send a seat-change alert as a poster-background card.

Usage (no secrets in args): TELEGRAM_TOKEN=... CHAT_ID=... python seat_alert.py request.json
request.json keys: movie, place, date, time, hall, regular, previous, premium (text),
poster_url + poster_for (title the poster belongs to; must match movie or the poster is ignored), url (optional booking link), test (bool).
"""
import html
import json
import os
import sys
import tempfile

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cardimage  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0"}


def _norm(t):
    import re
    return re.sub(r"[^a-z0-9\u0600-\u06ff]+", " ", (t or "").lower()).strip()


def poster_matches(movie, poster_for):
    """True only when the poster's own title matches the alert's movie (wrong film is worse than none)."""
    a, b = _norm(movie), _norm(poster_for)
    return bool(a) and bool(b) and (a == b or a in b or b in a)


def main(path):
    req = json.load(open(path, encoding="utf-8"))
    dry = bool(os.environ.get("DRY_RUN"))
    token, chat = os.environ.get("TELEGRAM_TOKEN", ""), os.environ.get("CHAT_ID", "")
    movie = req["movie"] + (" (TEST)" if req.get("test") else "")
    rows = [("pin", req["place"]), ("cal", req["date"]),
            ("clock", "%s  \u00b7  %s" % (req["time"], req["hall"]))]
    reg = "%s \u0645\u0642\u0639\u062f \u0639\u0627\u062f\u064a \u0645\u062a\u0627\u062d" % req["regular"]
    if req.get("previous") is not None:
        reg += " (\u0643\u0627\u0646\u062a %s)" % req["previous"]
    rows.append(("seat", reg))
    if req.get("premium"):
        rows.append(("star", "Premium: %s" % req["premium"]))
    badge = "\u062a\u063a\u064a\u0651\u0631 \u0641\u064a \u0627\u0644\u0645\u0642\u0627\u0639\u062f"
    with tempfile.TemporaryDirectory() as tmp:
        pp = None
        if req.get("poster_url") and poster_matches(req["movie"], req.get("poster_for")):
            r = requests.get(req["poster_url"], headers=UA, timeout=20)
            if r.status_code == 200 and 0 < len(r.content) < 10 * 1024 * 1024:
                pp = os.path.join(tmp, "p.jpg")
                open(pp, "wb").write(r.content)
        out = os.path.join(tmp, "c.png")
        ok = cardimage.render_png(out, badge, "#4FC3F7", movie, rows, pp,
                                  brand="SEAT WATCH")
        if ok and os.environ.get("CARD_OUT"):
            import shutil
            shutil.copy(out, os.environ["CARD_OUT"])
        cap = "\u200f\U0001FA91 <b>%s</b>\n\u200f%s \u00b7 %s\n\u200f%s" % (
            html.escape(badge), html.escape(req["place"]), html.escape(req["date"]),
            html.escape(reg))
        if req.get("url"):
            cap += '\n\u200f<a href="%s">\u0627\u0641\u062a\u062d \u0627\u0644\u062d\u062c\u0632</a>' % html.escape(req["url"], quote=True)
        if dry:
            print("dry run", "image" if ok else "text-only fallback")
            return
        base = "https://api.telegram.org/bot%s/" % token
        if ok:
            r = requests.post(base + "sendPhoto", data={"chat_id": chat, "caption": cap, "parse_mode": "HTML"},
                              files={"photo": ("card.png", open(out, "rb").read())}, timeout=40)
        else:
            r = requests.post(base + "sendMessage", data={"chat_id": chat, "text": cap, "parse_mode": "HTML",
                                                         "disable_web_page_preview": "true"}, timeout=25)
        j = r.json()
        print("sent" if j.get("ok") else "failed", "image" if ok else "text", "message_id", j.get("result", {}).get("message_id"))


if __name__ == "__main__":
    main(sys.argv[1])

"""Compose a poster-background alert image (HTML rendered by headless Chrome).

render_png(...) returns True when a PNG was written, False on any problem, so
callers can fall back to the plain card. Generic: holds no tokens or user data.
"""
import html
import os
import shutil
import subprocess
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")
W, H = 1080, 1350

ICONS = {
    "pin": '<path d="M12 2a7 7 0 0 0-7 7c0 5 7 13 7 13s7-8 7-13a7 7 0 0 0-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z"/>',
    "cal": '<path d="M7 2v2H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-2V2h-2v2H9V2H7zm-2 8h14v10H5V10z"/>',
    "clock": '<path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20zm1 5v5.4l4 2.4-1 1.7-5-3V7h2z"/>',
    "hall": '<path d="M3 5h18a1 1 0 0 1 1 1v9a1 1 0 0 1-1 1H3a1 1 0 0 1-1-1V6a1 1 0 0 1 1-1zm4 13h10v2H7v-2z"/>',
    "seat": '<path d="M6 3h12a2 2 0 0 1 2 2v7h1v6h-2v3h-2v-3H7v3H5v-3H3v-6h1V5a2 2 0 0 1 2-2z"/>',
    "star": '<path d="M12 2l3 6.6 7.2.8-5.4 4.9 1.5 7.1L12 17.7 5.7 21.4l1.5-7.1L1.8 9.4 9 8.6z"/>',
}


def _row(icon, text):
    return ('<div class="row"><svg viewBox="0 0 24 24" width="40" height="40">%s</svg>'
            '<span>%s</span></div>' % (ICONS.get(icon, ICONS["star"]), html.escape(str(text))))


def build_html(badge, accent, movie, rows, poster_url, footer, brand, wide=False):
    f = "file://" + FONTS
    bg = ('background-image:url("%s");' % poster_url) if poster_url else ""
    rows_html = "".join(_row(i, t) for i, t in rows)
    foot = '<div class="foot">%s</div>' % html.escape(footer) if footer else ""
    size = 84 if len(movie) <= 22 else (68 if len(movie) <= 34 else 54)
    return """<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:L;src:url("%(f)s/NotoSans-Regular.ttf");font-weight:400}
@font-face{font-family:L;src:url("%(f)s/NotoSans-Bold.ttf");font-weight:700}
@font-face{font-family:A;src:url("%(f)s/NotoSansArabic-Regular.ttf");font-weight:400}
@font-face{font-family:A;src:url("%(f)s/NotoSansArabic-Bold.ttf");font-weight:700}
*{box-sizing:border-box;margin:0;padding:0}
html,body{width:%(W)dpx;height:%(H)dpx;overflow:hidden;background:#0a0c14}
body{font-family:A,L,sans-serif;color:#fff;position:relative}
.bg{position:absolute;inset:0;%(bg)s%(bgpos)sbackground-color:#161a2b}
.shade{position:absolute;inset:0;background:linear-gradient(180deg,rgba(8,10,20,.55) 0%%,rgba(8,10,20,0) 22%%,rgba(8,10,20,0) 38%%,rgba(8,10,20,.82) 62%%,rgba(8,10,20,.97) 100%%)}
.top{position:absolute;top:44px;left:48px;right:48px;display:flex;justify-content:space-between;align-items:center}
.brand{font-family:L;font-weight:700;letter-spacing:6px;font-size:26px;opacity:.92;text-shadow:0 2px 12px #000}
.badge{background:%(accent)s;color:#0a0c14;font-weight:700;font-size:38px;padding:12px 30px;border-radius:40px;box-shadow:0 6px 24px rgba(0,0,0,.45)}
.panel{position:absolute;left:44px;right:44px;bottom:44px;padding:44px 48px 40px;border-radius:44px;background:rgba(12,15,28,.80);border:2px solid rgba(255,255,255,.16);box-shadow:0 20px 60px rgba(0,0,0,.55)}
.title{font-family:L,A,sans-serif;font-weight:700;font-size:%(size)dpx;line-height:1.08;margin-bottom:10px;direction:ltr;text-align:right;text-shadow:0 3px 18px rgba(0,0,0,.6)}
.bar{width:120px;height:8px;border-radius:6px;background:%(accent)s;margin:6px 0 26px auto}
.row{display:flex;align-items:center;gap:20px;font-size:40px;font-weight:700;margin:14px 0;direction:rtl}
.row svg{fill:%(accent)s;flex:none}
.row span{unicode-bidi:plaintext;flex:1;text-align:right}
.foot{margin-top:24px;font-size:28px;font-weight:400;opacity:.8;text-align:right;direction:rtl}
</style></head><body>
<div class="bg"></div><div class="shade"></div>
<div class="top"><div class="brand">%(brand)s</div><div class="badge">%(badge)s</div></div>
<div class="panel"><div class="title">%(movie)s</div><div class="bar"></div>%(rows)s%(foot)s</div>
</body></html>""" % dict(f=f, W=W, H=H, bg=bg, bgpos=('background-size:auto 72%;background-repeat:no-repeat;background-position:right top;' if wide else 'background-size:cover;background-position:center top;'), accent=accent, size=size,
                          brand=html.escape(brand), badge=html.escape(badge),
                          movie=html.escape(movie), rows=rows_html, foot=foot)


def _dims(path):
    try:
        d = open(path, "rb").read(400000)
        if d[:8] == b"\x89PNG\r\n\x1a\n":
            return int.from_bytes(d[16:20], "big"), int.from_bytes(d[20:24], "big")
        i = 2
        while i < len(d) - 9:
            if d[i] != 0xFF:
                i += 1
                continue
            m = d[i + 1]
            if 0xC0 <= m <= 0xCF and m not in (0xC4, 0xC8, 0xCC):
                return int.from_bytes(d[i + 7:i + 9], "big"), int.from_bytes(d[i + 5:i + 7], "big")
            i += 2 + int.from_bytes(d[i + 2:i + 4], "big")
    except Exception:
        pass
    return None


def _wide(p):
    d = _dims(p) if p else None
    return bool(d and d[0] > 1.3 * d[1])


def render_png(out_path, badge, accent, movie, rows, poster_path=None,
               footer="", brand="VOX RADAR  EGYPT"):
    try:
        chrome = (shutil.which("google-chrome") or shutil.which("chromium")
                  or shutil.which("chromium-browser"))
        if not chrome:
            return False
        poster_url = ("file://" + os.path.abspath(poster_path)) if poster_path else ""
        with tempfile.TemporaryDirectory() as tmp:
            page = os.path.join(tmp, "card.html")
            with open(page, "w", encoding="utf-8") as fh:
                fh.write(build_html(badge, accent, movie, rows, poster_url, footer, brand, wide=_wide(poster_path)))
            cmd = [chrome, "--headless=new", "--no-sandbox", "--disable-gpu",
                   "--hide-scrollbars", "--force-device-scale-factor=1",
                   "--allow-file-access-from-files",
                   "--window-size=%d,%d" % (W, H), "--virtual-time-budget=4000",
                   "--screenshot=" + out_path, "file://" + page]
            subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=40, check=False)
        return os.path.exists(out_path) and os.path.getsize(out_path) > 20000
    except Exception:
        return False

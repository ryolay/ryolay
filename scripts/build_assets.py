#!/usr/bin/env python3
"""Build the SVG assets of the GitHub profile README.

Run from the repo root:  python3 scripts/build_assets.py

Every card follows the viewer's light or dark preference through
@media (prefers-color-scheme), so one file serves both GitHub themes.
Animations stop when the viewer asks for reduced motion.
"""
import base64
import random
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"
SRC = ASSETS / "src"

FONT = "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif"
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
RED_A, RED_B = "#ff5a4e", "#e11d48"

# Theme tokens shared by every theme-aware asset.
THEME_CSS = f"""
  .bg {{ fill: #ffffff; }}
  .bd {{ stroke: #d0d7de; }}
  .fg {{ fill: #1f2328; }}
  .mu {{ fill: #59636e; }}
  .chip {{ fill: #f6f8fa; stroke: #d0d7de; }}
  .ink {{ fill: #1f2328; }}
  .tile {{ fill: #f6f8fa; stroke: #d8dee4; }}
  .soft {{ fill: #eef1f5; }}
  text {{ font-family: {FONT}; }}
  @media (prefers-color-scheme: dark) {{
    .bg {{ fill: #0d1117; }}
    .bd {{ stroke: #30363d; }}
    .fg {{ fill: #e6edf3; }}
    .mu {{ fill: #9198a1; }}
    .chip {{ fill: #161b22; stroke: #30363d; }}
    .ink {{ fill: #e6edf3; }}
    .tile {{ fill: #161b22; stroke: #262c36; }}
    .soft {{ fill: #1b2230; }}
  }}
  @media (prefers-reduced-motion: reduce) {{
    * {{ animation: none !important; }}
  }}
"""


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text_width(s: str, size: float, weight: int = 400, spacing: float = 0.0) -> float:
    """Rough width of a string in a system sans font; used only to size pills and chips."""
    narrow, wide = set("iljtfrI.,:;'|!() "), set("mwMW@")
    w = 0.0
    for ch in s:
        if ch in narrow:
            f = 0.30
        elif ch in wide:
            f = 0.86
        elif ch.isupper() or ch.isdigit():
            f = 0.66
        else:
            f = 0.55
        w += f * size + spacing
    return w * (1.06 if weight >= 600 else 1.0)


def png_uri(name: str) -> str:
    return "data:image/png;base64," + base64.b64encode((SRC / name).read_bytes()).decode()


def svg_doc(w: int, h: int, title: str, body: str, css: str = "", theme: bool = True) -> str:
    style = (THEME_CSS if theme else f"text {{ font-family: {FONT}; }}\n  @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}") + css
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}">\n'
        f"<title>{esc(title)}</title>\n<style>{style}</style>\n{body}\n</svg>\n"
    )


def write(rel: str, content: str) -> None:
    path = ASSETS / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    print(f"{rel:28s} {len(content):>7,d} bytes")


def chips(x: float, y: float, labels, accent_last: bool = False, size: float = 12) -> str:
    out, h = [], size * 2
    for i, label in enumerate(labels):
        w = text_width(label, size, 600) + 22
        accent = accent_last and i == len(labels) - 1
        if accent:
            out.append(f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{h}" rx="{h/2}" fill="{RED_A}" fill-opacity="0.12" stroke="{RED_A}" stroke-opacity="0.45"/>')
            out.append(f'<text x="{x + w/2:.1f}" y="{y + h/2 + size*0.36:.1f}" text-anchor="middle" font-size="{size}" font-weight="600" fill="{RED_B}" class="acc">{esc(label)}</text>')
        else:
            out.append(f'<rect x="{x}" y="{y}" width="{w:.0f}" height="{h}" rx="{h/2}" class="chip"/>')
            out.append(f'<text x="{x + w/2:.1f}" y="{y + h/2 + size*0.36:.1f}" text-anchor="middle" font-size="{size}" font-weight="600" class="mu">{esc(label)}</text>')
        x += w + 8
    return "\n".join(out)


def card_frame(w: int, h: int, glow: str, gid: str) -> str:
    return f"""<defs>
  <radialGradient id="{gid}" cx="1" cy="0" r="1">
    <stop offset="0" stop-color="{glow}" stop-opacity="0.20"/>
    <stop offset="0.55" stop-color="{glow}" stop-opacity="0"/>
  </radialGradient>
  <clipPath id="clip"><rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="18"/></clipPath>
</defs>
<g clip-path="url(#clip)">
  <rect width="{w}" height="{h}" class="bg"/>
  <rect width="{w}" height="{h}" fill="url(#{gid})"/>
  <rect x="0" y="0" width="{w}" height="3" fill="{glow}" fill-opacity="0.9"/>
</g>
<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="18" fill="none" class="bd"/>"""


# ---------------------------------------------------------------- hero banner
def build_hero() -> None:
    W, H = 1200, 320
    N, M = 25, 7
    X0, Y0 = 925, 72
    rng = random.Random(1201)  # Geneva postcode: the pattern stays stable between builds

    reserved = set()
    for fx, fy in [(0, 0), (N - 7, 0), (0, N - 7)]:
        for i in range(-1, 8):
            for j in range(-1, 8):
                reserved.add((fx + i, fy + j))
    for i in range(9, 16):
        for j in range(9, 16):
            reserved.add((i, j))

    mods = []
    for i in range(N):
        for j in range(N):
            if (i, j) in reserved or rng.random() >= 0.47:
                continue
            op = 0.35 + 0.5 * rng.random()
            cls = ""
            if rng.random() < 0.28:
                cls = f' class="tw" style="animation-delay:-{rng.random()*5:.2f}s"'
            mods.append(f'<rect x="{X0+i*M+0.6:.1f}" y="{Y0+j*M+0.6:.1f}" width="{M-1.2:.1f}" height="{M-1.2:.1f}" rx="1.2" fill="#e2e8f0" fill-opacity="{op:.2f}"{cls}/>')

    finders = []
    for fx, fy in [(0, 0), (N - 7, 0), (0, N - 7)]:
        x, y = X0 + fx * M, Y0 + fy * M
        finders.append(f'<rect x="{x+M/2}" y="{y+M/2}" width="{6*M}" height="{6*M}" rx="7" fill="none" stroke="#f8fafc" stroke-width="{M}"/>')
        finders.append(f'<rect x="{x+2*M}" y="{y+2*M}" width="{3*M}" height="{3*M}" rx="3" fill="url(#accent)"/>')

    cx, cy, S = X0 + N * M / 2, Y0 + N * M / 2, 44
    cross = (
        f'<rect x="{cx-S/2-4}" y="{cy-S/2-4}" width="{S+8}" height="{S+8}" rx="6" fill="#0d1117"/>'
        f'<rect x="{cx-S/2}" y="{cy-S/2}" width="{S}" height="{S}" rx="4" fill="#da291c"/>'
        f'<rect x="{cx-4.5}" y="{cy-14}" width="9" height="28" fill="#ffffff"/>'
        f'<rect x="{cx-14}" y="{cy-4.5}" width="28" height="9" fill="#ffffff"/>'
    )
    size = N * M

    phrases = ["SaaS products.", "iOS and Android apps.", "open-source tools.", "the infrastructure behind them."]
    rot = []
    for k, p in enumerate(phrases):
        delay = 0 if k == 0 else 3 * k - 12
        # Shift every phrase by -1.2s so a frozen first frame shows phrase 1 in place.
        rot.append(
            f'<text x="58" y="182" font-size="27" font-weight="600" class="r" style="animation-delay:{delay - 1.2:.1f}s{";opacity:1" if k == 0 else ""}">'
            f'<tspan fill="transparent">I build </tspan><tspan fill="url(#accent)">{esc(p)}</tspan></text>'
        )

    pill_text = "BASED IN GENEVA, SWITZERLAND"
    pill_w = text_width(pill_text, 13, 600, 1.6) + 48

    css = f"""
  @keyframes tw {{ 0%, 100% {{ opacity: .22; }} 50% {{ opacity: 1; }} }}
  .tw {{ animation: tw 4.5s ease-in-out infinite; }}
  @keyframes scan {{ 0% {{ transform: translateY(0); }} 100% {{ transform: translateY({size}px); }} }}
  .scan {{ animation: scan 2.8s ease-in-out infinite alternate; }}
  @keyframes rot {{
    0% {{ opacity: 0; transform: translateY(16px); }}
    5% {{ opacity: 1; transform: translateY(0); }}
    20% {{ opacity: 1; transform: translateY(0); }}
    25% {{ opacity: 0; transform: translateY(-16px); }}
    100% {{ opacity: 0; transform: translateY(-16px); }}
  }}
  .r {{ opacity: 0; animation: rot 12s cubic-bezier(.2,.7,.2,1) infinite; }}
  @keyframes ping {{ 0% {{ transform: scale(1); opacity: .75; }} 100% {{ transform: scale(3.2); opacity: 0; }} }}
  .ping {{ transform-box: fill-box; transform-origin: center; animation: ping 1.8s ease-out infinite; }}
  @keyframes shine {{ 0% {{ transform: translateX(-400px); }} 100% {{ transform: translateX(1600px); }} }}
  .shine {{ animation: shine 5s linear infinite; }}
  @keyframes breathe {{ 0%, 100% {{ opacity: .65; }} 50% {{ opacity: 1; }} }}
  .glow {{ animation: breathe 6s ease-in-out infinite; }}
  @keyframes caret {{ 0%, 49% {{ opacity: 1; }} 50%, 100% {{ opacity: 0; }} }}
"""
    body = f"""<defs>
  <linearGradient id="background" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#0b0f17"/><stop offset="1" stop-color="#1c2230"/>
  </linearGradient>
  <linearGradient id="accent" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{RED_A}"/><stop offset="1" stop-color="#ff2d6f"/>
  </linearGradient>
  <linearGradient id="name" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#ffffff"/><stop offset="1" stop-color="#c9d1dc"/>
  </linearGradient>
  <linearGradient id="beam" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{RED_A}" stop-opacity="0"/><stop offset="1" stop-color="{RED_A}" stop-opacity="0.35"/>
  </linearGradient>
  <linearGradient id="shineg" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="#ffffff" stop-opacity="0"/><stop offset="0.5" stop-color="#ffffff" stop-opacity="0.85"/><stop offset="1" stop-color="#ffffff" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="glow">
    <stop offset="0" stop-color="#ef4444" stop-opacity="0.20"/><stop offset="1" stop-color="#ef4444" stop-opacity="0"/>
  </radialGradient>
  <pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">
    <circle cx="2" cy="2" r="1" fill="#94a3b8" fill-opacity="0.13"/>
  </pattern>
  <clipPath id="bounds"><rect width="{W}" height="{H}" rx="18"/></clipPath>
  <clipPath id="qr"><rect x="{X0-8}" y="{Y0-8}" width="{size+16}" height="{size+16}" rx="8"/></clipPath>
</defs>
<g clip-path="url(#bounds)">
  <rect width="{W}" height="{H}" fill="url(#background)"/>
  <rect width="{W}" height="{H}" fill="url(#dots)"/>
  <ellipse class="glow" cx="1012" cy="160" rx="310" ry="260" fill="url(#glow)"/>
  <path d="M858 0V{H}" stroke="#94a3b8" stroke-opacity="0.28" stroke-dasharray="6 7"/>
  <g>{''.join(mods)}{''.join(finders)}</g>
  <g clip-path="url(#qr)">
    <g class="scan">
      <rect x="{X0-8}" y="{Y0-36}" width="{size+16}" height="34" fill="url(#beam)"/>
      <rect x="{X0-8}" y="{Y0-3}" width="{size+16}" height="3" rx="1.5" fill="{RED_A}"/>
    </g>
  </g>
  {cross}
  <text x="1012" y="284" text-anchor="middle" fill="#64748b" font-family="{MONO}" font-size="12" letter-spacing="2">QR-BILL · CH</text>

  <rect x="56" y="34" width="{pill_w:.0f}" height="30" rx="15" fill="#ffffff" fill-opacity="0.05" stroke="#ffffff" stroke-opacity="0.12"/>
  <circle cx="75" cy="49" r="4.5" fill="{RED_A}" class="ping"/>
  <circle cx="75" cy="49" r="4.5" fill="{RED_A}"/>
  <text x="90" y="53.5" fill="#cbd5e1" font-size="13" font-weight="600" letter-spacing="1.6">{pill_text}</text>

  <text x="56" y="134" fill="url(#name)" font-size="56" font-weight="800" letter-spacing="-1.4">Christian Da Silva Perez</text>
  <text x="58" y="182" fill="#e2e8f0" font-size="27" font-weight="600">I build </text>
  {''.join(rot)}
  <text x="58" y="224" fill="#94a3b8" font-size="20">Full-stack developer · Founder · Open-source maker</text>
  <text x="58" y="276" fill="#7c8799" font-size="13" letter-spacing="1.6">TYPESCRIPT · REACT · NODE.JS · POSTGRESQL · KUBERNETES · SWIFT</text>

  <rect y="{H-4}" width="{W}" height="4" fill="url(#accent)"/>
  <rect class="shine" x="0" y="{H-4}" width="260" height="4" fill="url(#shineg)" fill-opacity="0.7"/>
</g>"""
    write("hero.svg", svg_doc(W, H, "Christian Da Silva Perez: full-stack developer and founder, based in Geneva. I build SaaS products, iOS and Android apps, open-source tools and the infrastructure behind them.", body, css, theme=False))


# ---------------------------------------------------------------- buttons
def build_buttons() -> None:
    icons = {
        "linkedin": '<path fill="#ffffff" transform="translate(18 11) scale(0.75)" d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>',
        "email": '<g transform="translate(17 10)" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="3" width="18" height="14" rx="2.5"/><path d="m19 5.5-7.6 5.3a2.4 2.4 0 0 1-2.8 0L1 5.5"/></g>',
        "website": '<g transform="translate(17 10)" fill="none" stroke="#ffffff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="10" cy="10" r="9"/><path d="M10 1a13 13 0 0 0 0 18 13 13 0 0 0 0-18M1 10h18"/></g>',
    }
    specs = [
        ("linkedin", "LinkedIn", "#0A66C2", "#0a4f99"),
        ("email", "Email me", RED_A, RED_B),
        ("website", "tobill.ch", "#2b3240", "#1a1f29"),
    ]
    for key, label, c1, c2 in specs:
        h = 42
        w = int(52 + text_width(label, 15, 600) + 22)
        body = f"""<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>
<rect width="{w}" height="{h}" rx="{h/2}" fill="url(#g)"/>
<rect x="0.5" y="0.5" width="{w-1}" height="{h-1}" rx="{(h-1)/2}" fill="none" stroke="#ffffff" stroke-opacity="0.16"/>
{icons[key]}
<text x="48" y="26.5" font-size="15" font-weight="600" fill="#ffffff">{esc(label)}</text>"""
        write(f"buttons/{key}.svg", svg_doc(w, h, label, body, theme=False))


# ---------------------------------------------------------------- project cards
def build_tobill_card() -> None:
    W, H = 840, 250
    logo = png_uri("tobill.png")
    css = f"""
  .paper {{ fill: #ffffff; stroke: #d0d7de; }}
  .paper2 {{ fill: #eef1f5; }}
  .line {{ fill: #d8dee4; }}
  .dark {{ fill: #1f2328; }}
  .acc {{ fill: {RED_B}; }}
  @media (prefers-color-scheme: dark) {{
    .paper {{ fill: #f8fafc; stroke: #f8fafc; }}
    .paper2 {{ fill: #2a3242; }}
    .acc {{ fill: {RED_A}; }}
  }}
  @keyframes stamp {{
    0%, 12% {{ opacity: 0; transform: scale(1.8) rotate(-14deg); }}
    18% {{ opacity: 1; transform: scale(0.94) rotate(-14deg); }}
    22%, 86% {{ opacity: 1; transform: scale(1) rotate(-14deg); }}
    94%, 100% {{ opacity: 0; transform: scale(1) rotate(-14deg); }}
  }}
  .stamp {{ transform-box: fill-box; transform-origin: center; transform: rotate(-14deg); animation: stamp 7s ease-out infinite; }}
  @keyframes float {{ 0%, 100% {{ transform: translateY(0); }} 50% {{ transform: translateY(-6px); }} }}
  .float {{ animation: float 6s ease-in-out infinite; }}
"""
    qr = []
    rng = random.Random(7)
    for i in range(11):
        for j in range(11):
            if (i < 3 and j < 3) or (i > 7 and j < 3) or (i < 3 and j > 7):
                continue
            if rng.random() < 0.5:
                qr.append(f'<rect x="{i*4}" y="{j*4}" width="3.4" height="3.4" class="dark"/>')
    finder = ''.join(f'<rect x="{fx*4+0.8}" y="{fy*4+0.8}" width="10.4" height="10.4" fill="none" stroke="#1f2328" stroke-width="1.6"/><rect x="{fx*4+3.6}" y="{fy*4+3.6}" width="4.8" height="4.8" class="dark"/>' for fx, fy in [(0, 0), (8, 0), (0, 8)])
    invoice = f"""<g transform="translate(598 34) rotate(-5)">
  <g class="float">
    <rect x="16" y="12" width="196" height="196" rx="10" class="paper2"/>
    <rect x="0" y="0" width="196" height="196" rx="10" class="paper"/>
    <rect x="16" y="16" width="38" height="12" rx="3" fill="#da291c"/>
    <rect x="128" y="16" width="52" height="5" rx="2.5" class="line"/>
    <rect x="140" y="25" width="40" height="5" rx="2.5" class="line"/>
    <text x="16" y="50" font-size="9" font-weight="700" letter-spacing="1.4" fill="#59636e">INVOICE</text>
    <rect x="16" y="60" width="96" height="5" rx="2.5" class="line"/><rect x="150" y="60" width="30" height="5" rx="2.5" class="line"/>
    <rect x="16" y="72" width="78" height="5" rx="2.5" class="line"/><rect x="156" y="72" width="24" height="5" rx="2.5" class="line"/>
    <rect x="16" y="84" width="88" height="5" rx="2.5" class="line"/><rect x="152" y="84" width="28" height="5" rx="2.5" class="line"/>
    <text x="180" y="108" text-anchor="end" font-size="11" font-weight="700" fill="#1f2328">CHF 1’280.00</text>
    <path d="M6 122H190" stroke="#8c959f" stroke-dasharray="3 3"/>
    <g transform="translate(16 134)">{''.join(qr)}{finder}
      <rect x="16" y="16" width="12" height="12" fill="#ffffff"/><rect x="17.5" y="17.5" width="9" height="9" fill="#da291c"/>
      <rect x="21.2" y="19" width="1.6" height="6" fill="#fff"/><rect x="19" y="21.2" width="6" height="1.6" fill="#fff"/>
    </g>
    <rect x="72" y="138" width="70" height="5" rx="2.5" class="line"/>
    <rect x="72" y="150" width="54" height="5" rx="2.5" class="line"/>
    <rect x="72" y="162" width="62" height="5" rx="2.5" class="line"/>
    <g class="stamp">
      <rect x="104" y="30" width="76" height="30" rx="5" fill="#ffffff" fill-opacity="0.6" stroke="#1a7f37" stroke-width="2.5"/>
      <text x="142" y="51" text-anchor="middle" font-size="16" font-weight="800" letter-spacing="2.5" fill="#1a7f37">PAID</text>
    </g>
  </g>
</g>"""
    body = f"""{card_frame(W, H, '#ef4444', 'glow')}
<rect x="32" y="32" width="64" height="64" rx="16" fill="#ffffff" stroke="#d0d7de"/>
<image href="{logo}" x="38" y="38" width="52" height="52"/>
<text x="114" y="52" font-size="11.5" font-weight="700" letter-spacing="1.5" class="mu">FEATURED · SAAS</text>
<text x="113" y="86" font-size="30" font-weight="800" letter-spacing="-0.6" class="fg">To Bill</text>
<text x="32" y="134" font-size="17.5" font-weight="600" class="fg">Invoicing and accounting for Swiss SMEs.</text>
<text x="32" y="162" font-size="15" class="mu">Web, iOS and Android apps, designed, built and run end to end.</text>
{chips(32, 192, ["Web app", "iOS & Android", "Made in Geneva", "tobill.ch ↗"], accent_last=True)}
{invoice}"""
    write("cards/tobill.svg", svg_doc(W, H, "To Bill: invoicing and accounting for Swiss SMEs. Web, iOS and Android apps, designed, built and run end to end.", body, css))


def build_tack_card() -> None:
    W, H = 412, 278
    icon = png_uri("tack.png")
    css = """
  @keyframes float { 0%, 100% { transform: translateY(0) rotate(4deg); } 50% { transform: translateY(-5px) rotate(4deg); } }
  .note { transform-box: fill-box; transform-origin: center; transform: rotate(4deg); animation: float 5s ease-in-out infinite; }
  @keyframes tick { 0%, 30% { stroke-dashoffset: 12; } 45%, 100% { stroke-dashoffset: 0; } }
  .tick { stroke-dasharray: 12; animation: tick 5s ease-out infinite; }
"""
    note = """<g transform="translate(316 24)"><g class="note">
  <rect width="70" height="64" rx="9" fill="#ffb340" fill-opacity="0.16" stroke="#ff9f0a" stroke-opacity="0.55"/>
  <rect x="10" y="12" width="9" height="9" rx="2.5" fill="#ff9f0a"/><path class="tick" d="M12 16.6l2 2 3.5-4" fill="none" stroke="#fff" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
  <rect x="24" y="14" width="34" height="5" rx="2.5" fill="#ff9f0a" fill-opacity="0.55"/>
  <rect x="10" y="28" width="9" height="9" rx="2.5" fill="none" stroke="#ff9f0a" stroke-width="1.4"/><rect x="24" y="30" width="28" height="5" rx="2.5" fill="#ff9f0a" fill-opacity="0.35"/>
  <rect x="10" y="44" width="9" height="9" rx="2.5" fill="none" stroke="#ff9f0a" stroke-width="1.4"/><rect x="24" y="46" width="36" height="5" rx="2.5" fill="#ff9f0a" fill-opacity="0.35"/>
</g></g>"""
    desc = ["Pin a thought from the macOS menu bar with", "one shortcut, even over full-screen apps.", "Checklists, reminders, tags and Markdown."]
    lines = "\n".join(f'<text x="26" y="{146 + 21*i}" font-size="14" class="mu">{esc(t)}</text>' for i, t in enumerate(desc))
    body = f"""{card_frame(W, H, '#ff9f0a', 'glow')}
<image href="{icon}" x="22" y="22" width="60" height="60"/>
<text x="94" y="46" font-size="11" font-weight="700" letter-spacing="1.5" class="mu">MACOS APP</text>
<text x="93" y="76" font-size="26" font-weight="800" letter-spacing="-0.5" class="fg">Tack</text>
<text x="26" y="118" font-size="16" font-weight="600" class="fg">A quick alternative to Notes.</text>
{lines}
{chips(26, 222, ["Swift", "SwiftUI", "MIT", "No telemetry"])}
{note}"""
    write("cards/tack.svg", svg_doc(W, H, "Tack: a quick alternative to Notes. A macOS menu bar app for checklists, reminders, tags and Markdown. Open source.", body, css))


def build_nebula_card() -> None:
    W, H = 412, 278
    css = """
  @keyframes pulse { 0%, 100% { opacity: .35; } 50% { opacity: 1; } }
  .p { animation: pulse 2.4s ease-in-out infinite; }
  @keyframes draw { 0% { stroke-dashoffset: 120; } 40%, 100% { stroke-dashoffset: 0; } }
  .branch { stroke-dasharray: 120; animation: draw 4s ease-out infinite; }
"""
    icon = """<g transform="translate(22 22)">
  <defs><linearGradient id="neb" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#7c3aed"/><stop offset="1" stop-color="#db2777"/></linearGradient></defs>
  <rect width="60" height="60" rx="15" fill="url(#neb)"/>
  <g fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round"><path d="M22 14v32"/><path d="M22 36c0-10 16-6 16-16"/></g>
  <circle cx="22" cy="14" r="4.5" fill="#fff"/><circle cx="22" cy="46" r="4.5" fill="#fff"/><circle cx="38" cy="18" r="4.5" fill="#fff"/>
</g>"""
    graph = """<g transform="translate(322 22)" fill="none" stroke-width="2.4" stroke-linecap="round">
  <path d="M12 0V66" stroke="#a78bfa"/>
  <path class="branch" d="M12 12c0 14 24 8 24 24v30" stroke="#f472b6"/>
  <path class="branch" d="M36 30c0 12 24 6 24 22" stroke="#c084fc" style="animation-delay:-1.3s"/>
  <g stroke="none">
    <circle cx="12" cy="8" r="5" fill="#a78bfa" class="p"/>
    <circle cx="12" cy="40" r="5" fill="#a78bfa" class="p" style="animation-delay:-.6s"/>
    <circle cx="36" cy="38" r="5" fill="#f472b6" class="p" style="animation-delay:-1.2s"/>
    <circle cx="60" cy="54" r="5" fill="#c084fc" class="p" style="animation-delay:-1.8s"/>
  </g>
</g>"""
    desc = ["A fast Git client for macOS, Windows and", "Linux: commit graph, merge conflicts, pull", "requests, issues and an integrated terminal."]
    lines = "\n".join(f'<text x="26" y="{146 + 21*i}" font-size="14" class="mu">{esc(t)}</text>' for i, t in enumerate(desc))
    body = f"""{card_frame(W, H, '#a855f7', 'glow')}
{icon}
<text x="94" y="46" font-size="11" font-weight="700" letter-spacing="1.5" class="mu">GIT CLIENT</text>
<text x="93" y="76" font-size="26" font-weight="800" letter-spacing="-0.5" class="fg">Nebula</text>
<text x="26" y="118" font-size="16" font-weight="600" class="fg">A free alternative to GitKraken.</text>
{lines}
{chips(26, 222, ["Electron", "Mac · Win · Linux", "MIT"])}
{graph}"""
    write("cards/nebula.svg", svg_doc(W, H, "Nebula: a free, open-source alternative to GitKraken. A fast Git client for macOS, Windows and Linux.", body, css))


# ---------------------------------------------------------------- principles
def build_principles() -> None:
    W, TW, TH, GAP = 840, 414, 112, 12
    H = TH * 2 + GAP
    ic = {
        "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/><path d="m9 12 2 2 4-4"/>',
        "terminal": '<path d="m4 17 6-6-6-6"/><path d="M12 19h8"/>',
        "book": '<path d="M2 4h6a4 4 0 0 1 4 4v13a3 3 0 0 0-3-3H2z"/><path d="M22 4h-6a4 4 0 0 0-4 4v13a3 3 0 0 1 3-3h7z"/>',
        "layers": '<path d="m12 2 10 5-10 5L2 7z"/><path d="m2 17 10 5 10-5"/><path d="m2 12 10 5 10-5"/>',
    }
    items = [
        ("shield", "Correct before pretty", ["Money, law and personal data: I get the", "rules right before I polish the screens."]),
        ("terminal", "Run it, don't just compile it", ["Every change runs against a real stack", "before it ships. A type check is not proof."]),
        ("book", "Docs ship with the product", ["A visible change lands together with its", "user guide, never later."]),
        ("layers", "Own the whole stack", ["From the database schema and the jobs", "to the mobile builds and Kubernetes."]),
    ]
    tiles = []
    for k, (icon, title, desc) in enumerate(items):
        x, y = (k % 2) * (TW + GAP), (k // 2) * (TH + GAP)
        lines = "".join(f'<text x="{x+76}" y="{y+68+20*i}" font-size="13.5" class="mu">{esc(t)}</text>' for i, t in enumerate(desc))
        tiles.append(f"""<g class="t" style="animation-delay:{k*0.08:.2f}s">
  <rect x="{x+0.5}" y="{y+0.5}" width="{TW-1}" height="{TH-1}" rx="16" class="tile"/>
  <rect x="{x+20}" y="{y+22}" width="40" height="40" rx="11" fill="{RED_A}" fill-opacity="0.12"/>
  <g transform="translate({x+28} {y+30})" fill="none" stroke="{RED_A}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{ic[icon]}</g>
  <text x="{x+76}" y="{y+42}" font-size="16" font-weight="700" class="fg">{esc(title)}</text>
  {lines}
</g>""")
    css = """
"""
    alt = "How I work. " + " ".join(f"{t}: {' '.join(d)}" for _, t, d in items)
    write("principles.svg", svg_doc(W, H, alt, "\n".join(tiles), css))


# ---------------------------------------------------------------- toolkit grid
def build_toolkit() -> None:
    stack = [
        ("typescript", "TypeScript"), ("react", "React"), ("nodedotjs", "Node.js"), ("fastify", "Fastify"),
        ("postgresql", "PostgreSQL"), ("prisma", "Prisma"), ("redis", "Redis"), ("nextdotjs", "Next.js"),
        ("vite", "Vite"), ("tailwindcss", "Tailwind"), ("expo", "Expo"), ("swift", "Swift"),
        ("electron", "Electron"), ("docker", "Docker"), ("kubernetes", "Kubernetes"), ("githubactions", "Actions"),
    ]
    cols, gap = 8, 10
    W = 840
    tw = (W - gap * (cols - 1)) / cols
    th = 92
    H = int(th * 2 + gap)
    tiles = []
    for k, (slug, label) in enumerate(stack):
        raw = (SRC / "simple-icons" / f"{slug}.svg").read_text()
        d = re.search(r' d="([^"]+)"', raw).group(1)
        color = re.search(r'fill="(#[0-9A-Fa-f]{6})"', raw).group(1)
        r, g, b = (int(color[i:i + 2], 16) / 255 for i in (1, 3, 5))
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        fill = 'class="ink"' if lum < 0.25 else f'fill="{color}"'
        x, y = (k % cols) * (tw + gap), (k // cols) * (th + gap)
        tiles.append(f"""<g class="t" style="animation-delay:{k*0.04:.2f}s">
  <rect x="{x+0.5:.1f}" y="{y+0.5}" width="{tw-1:.1f}" height="{th-1}" rx="14" class="tile"/>
  <path {fill} transform="translate({x + tw/2 - 16:.1f} {y+16}) scale(1.3333)" d="{d}"/>
  <text x="{x + tw/2:.1f}" y="{y+76}" text-anchor="middle" font-size="12" font-weight="600" class="mu">{esc(label)}</text>
</g>""")
    css = """
"""
    alt = "Toolkit: " + ", ".join(l for _, l in stack)
    write("toolkit.svg", svg_doc(W, H, alt, "\n".join(tiles), css))


if __name__ == "__main__":
    build_hero()
    build_buttons()
    build_tobill_card()
    build_tack_card()
    build_nebula_card()
    build_principles()
    build_toolkit()

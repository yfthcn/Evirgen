#!/usr/bin/env python3
"""Generate Chrome Web Store assets for Evirgen (screenshots + promo tiles)."""
import io
import cairosvg
from PIL import Image

OUT = "/home/claude/evirgen/store"

# palette
BG = "#0d1420"
RAISED = "#131c2b"
LINE = "#22304a"
TEXT = "#cbd5e1"
DIM = "#64748b"
AMBER = "#f5a623"
AMBER_DIM = "#b45309"
DANGER = "#ef4444"
MONO = "DejaVu Sans Mono, monospace"
SANS = "DejaVu Sans, sans-serif"


def popup_svg(x=0, y=0, scale=1.0):
    """The Evirgen popup, replicated from popup.css, as an SVG group (320x412 logical)."""
    g = f'<g transform="translate({x},{y}) scale({scale})">'
    # frame
    g += f'<rect x="0" y="0" width="320" height="412" rx="10" fill="{BG}" stroke="{LINE}" stroke-width="1.5"/>'
    # header
    g += f'<line x1="0" y1="40" x2="320" y2="40" stroke="{LINE}"/>'
    g += f'<text x="14" y="26" font-family="{MONO}" font-size="13" fill="{AMBER}">&#8635;</text>'
    g += f'<text x="34" y="25" font-family="{MONO}" font-size="12" letter-spacing="2.2" fill="{AMBER}">EV&#304;RGEN</text>'
    g += f'<rect x="246" y="11" width="60" height="19" rx="4" fill="{RAISED}" stroke="{LINE}"/>'
    g += f'<text x="256" y="24" font-family="{MONO}" font-size="10" fill="{DIM}">English</text>'
    # toggle row
    g += f'<text x="14" y="63" font-family="{SANS}" font-size="13" font-weight="600" fill="{TEXT}">Auto refresh</text>'
    g += f'<rect x="268" y="50" width="38" height="20" rx="10" fill="{AMBER_DIM}"/>'
    g += f'<circle cx="296" cy="60" r="7" fill="#fffbeb"/>'
    # countdown (fake glow: layered text)
    g += f'<text x="160" y="122" font-family="{MONO}" font-size="40" font-weight="bold" fill="{AMBER}" opacity="0.25" text-anchor="middle" letter-spacing="1.5" transform="translate(0,1)">04:37</text>'
    g += f'<text x="160" y="122" font-family="{MONO}" font-size="40" font-weight="bold" fill="{AMBER}" text-anchor="middle" letter-spacing="1.5">04:37</text>'
    # interval label
    g += f'<text x="14" y="152" font-family="{MONO}" font-size="9" letter-spacing="1.4" fill="{DIM}">INTERVAL</text>'
    # presets
    labels = ["5 min", "10 min", "15 min", "20 min"]
    for i, lab in enumerate(labels):
        px = 14 + i * 75
        sel = i == 0
        stroke = AMBER if sel else LINE
        fill_t = AMBER if sel else TEXT
        sw = 2 if sel else 1
        g += f'<rect x="{px}" y="160" width="69" height="32" rx="6" fill="{RAISED}" stroke="{stroke}" stroke-width="{sw}"/>'
        g += f'<text x="{px + 34.5}" y="180" font-family="{MONO}" font-size="11" fill="{fill_t}" text-anchor="middle">{lab}</text>'
    # custom row
    g += f'<rect x="14" y="202" width="130" height="30" rx="6" fill="{RAISED}" stroke="{LINE}"/>'
    g += f'<text x="24" y="221" font-family="{MONO}" font-size="12" fill="{TEXT}">30</text>'
    g += f'<rect x="150" y="202" width="58" height="30" rx="6" fill="{RAISED}" stroke="{LINE}"/>'
    g += f'<text x="160" y="221" font-family="{MONO}" font-size="11" fill="{TEXT}">min &#9662;</text>'
    g += f'<rect x="214" y="202" width="92" height="30" rx="6" fill="{AMBER_DIM}"/>'
    g += f'<text x="260" y="221" font-family="{SANS}" font-size="11" font-weight="600" fill="#fffbeb" text-anchor="middle">Apply</text>'
    # hard reload checkbox
    g += f'<rect x="14" y="244" width="12" height="12" rx="2" fill="{RAISED}" stroke="{LINE}"/>'
    g += f'<text x="34" y="254" font-family="{SANS}" font-size="11" fill="{DIM}">Hard reload (bypass cache)</text>'
    # divider + active timers
    g += f'<line x1="14" y1="270" x2="306" y2="270" stroke="{LINE}"/>'
    g += f'<text x="14" y="288" font-family="{MONO}" font-size="9" letter-spacing="1.4" fill="{DIM}">ACTIVE TIMERS</text>'
    rows = [("Grafana — Node Overview", "5 min", True), ("BT Service Status", "30 sec", False)]
    for i, (title, iv, cur) in enumerate(rows):
        ry = 306 + i * 24
        col = AMBER if cur else TEXT
        g += f'<text x="14" y="{ry}" font-family="{SANS}" font-size="11" fill="{col}">{title}</text>'
        g += f'<text x="222" y="{ry}" font-family="{MONO}" font-size="10" fill="{DIM}" text-anchor="end">{iv}</text>'
        g += f'<rect x="264" y="{ry - 12}" width="42" height="17" rx="4" fill="none" stroke="{LINE}"/>'
        g += f'<text x="285" y="{ry}" font-family="{MONO}" font-size="9" fill="{DIM}" text-anchor="middle">OFF</text>'
    # stop all
    g += f'<rect x="14" y="348" width="292" height="28" rx="6" fill="none" stroke="{DANGER}" stroke-width="1.2"/>'
    g += f'<text x="160" y="366" font-family="{SANS}" font-size="11" font-weight="600" fill="{DANGER}" text-anchor="middle">Stop all timers</text>'
    # footer
    g += f'<line x1="0" y1="386" x2="320" y2="386" stroke="{LINE}"/>'
    g += f'<text x="14" y="403" font-family="{MONO}" font-size="9" fill="{DIM}">v1.1.1</text>'
    g += f'<text x="306" y="403" font-family="{MONO}" font-size="9" fill="{DIM}" text-anchor="end">kaktusdev.net / github</text>'
    g += "</g>"
    return g


def refresh_glyph(cx, cy, r, sw, color=AMBER):
    """Circular-arrow brand glyph."""
    import math
    a0 = math.radians(-60)
    x0, y0 = cx + r * math.cos(a0), cy + r * math.sin(a0)
    x1, y1 = cx + r * math.cos(math.radians(210)), cy + r * math.sin(math.radians(210))
    ah = r * 0.55
    tang = a0 - math.pi / 2
    p1 = (x0 + ah * math.cos(tang), y0 + ah * math.sin(tang))
    p2 = (x0 + ah * 0.7 * math.cos(a0), y0 + ah * 0.7 * math.sin(a0))
    p3 = (x0 - ah * 0.7 * math.cos(a0), y0 - ah * 0.7 * math.sin(a0))
    d = (
        f'<path d="M {x0:.1f} {y0:.1f} A {r} {r} 0 1 0 {x1:.1f} {y1:.1f}" '
        f'fill="none" stroke="{color}" stroke-width="{sw}" stroke-linecap="round"/>'
        f'<polygon points="{p1[0]:.1f},{p1[1]:.1f} {p2[0]:.1f},{p2[1]:.1f} {p3[0]:.1f},{p3[1]:.1f}" fill="{color}"/>'
    )
    return d


def backdrop(w, h):
    return (
        f'<rect width="{w}" height="{h}" fill="{BG}"/>'
        f'<radialGradient id="glow" cx="0.85" cy="0.15" r="0.9">'
        f'<stop offset="0" stop-color="{AMBER}" stop-opacity="0.07"/>'
        f'<stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></radialGradient>'
        f'<rect width="{w}" height="{h}" fill="url(#glow)"/>'
    )


def bullet(x, y, text, sub=None):
    s = f'<circle cx="{x}" cy="{y - 5}" r="3.5" fill="{AMBER}"/>'
    s += f'<text x="{x + 18}" y="{y}" font-family="{SANS}" font-size="21" fill="{TEXT}">{text}</text>'
    if sub:
        s += f'<text x="{x + 18}" y="{y + 26}" font-family="{SANS}" font-size="15" fill="{DIM}">{sub}</text>'
    return s


def render(svg_body, w, h, path):
    doc = f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{svg_body}</svg>'
    png = cairosvg.svg2png(bytestring=doc.encode(), output_width=w, output_height=h)
    img = Image.open(io.BytesIO(png)).convert("RGBA")
    flat = Image.new("RGB", img.size, (13, 20, 32))  # flatten: 24-bit, no alpha
    flat.paste(img, mask=img.split()[3])
    flat.save(path, "PNG")
    print(path)


# ---------- screenshot 1: hero ----------
s = backdrop(1280, 800)
s += refresh_glyph(120, 120, 34, 9)
s += f'<text x="180" y="134" font-family="{MONO}" font-size="34" letter-spacing="8" fill="{AMBER}">EV&#304;RGEN</text>'
s += f'<text x="90" y="250" font-family="{SANS}" font-size="46" font-weight="bold" fill="{TEXT}">Auto refresh, per tab.</text>'
s += f'<text x="90" y="300" font-family="{SANS}" font-size="22" fill="{DIM}">Each tab gets its own interval, countdown and switch.</text>'
s += bullet(94, 380, "Presets or any custom interval")
s += bullet(94, 440, "Live countdown on badge and popup")
s += bullet(94, 500, "Hard reload to bypass cache")
s += bullet(94, 560, "One button to stop everything")
s += f'<text x="90" y="680" font-family="{MONO}" font-size="16" fill="{DIM}">kaktusdev.net</text>'
s += popup_svg(770, 100, 1.46)
render(s, 1280, 800, f"{OUT}/screenshot-1-hero.png")

# ---------- screenshot 2: intervals ----------
s = backdrop(1280, 800)
s += f'<text x="90" y="150" font-family="{SANS}" font-size="42" font-weight="bold" fill="{TEXT}">Pick a preset. Or type your own.</text>'
s += f'<text x="90" y="200" font-family="{SANS}" font-size="21" fill="{DIM}">5 / 10 / 15 / 20 minutes one tap away &#8212; anything else in seconds or minutes.</text>'
# enlarged preset chips
for i, lab in enumerate(["5 min", "10 min", "15 min", "20 min"]):
    px = 90 + i * 150
    sel = i == 1
    stroke = AMBER if sel else LINE
    fill_t = AMBER if sel else TEXT
    s += f'<rect x="{px}" y="270" width="132" height="62" rx="10" fill="{RAISED}" stroke="{stroke}" stroke-width="{3 if sel else 1.5}"/>'
    s += f'<text x="{px + 66}" y="308" font-family="{MONO}" font-size="21" fill="{fill_t}" text-anchor="middle">{lab}</text>'
# enlarged custom row
s += f'<rect x="90" y="380" width="260" height="60" rx="10" fill="{RAISED}" stroke="{LINE}" stroke-width="1.5"/>'
s += f'<text x="112" y="418" font-family="{MONO}" font-size="23" fill="{TEXT}">45</text>'
s += f'<rect x="366" y="380" width="120" height="60" rx="10" fill="{RAISED}" stroke="{LINE}" stroke-width="1.5"/>'
s += f'<text x="388" y="418" font-family="{MONO}" font-size="21" fill="{TEXT}">sec &#9662;</text>'
s += f'<rect x="502" y="380" width="170" height="60" rx="10" fill="{AMBER_DIM}"/>'
s += f'<text x="587" y="418" font-family="{SANS}" font-size="21" font-weight="600" fill="#fffbeb" text-anchor="middle">Apply</text>'
s += f'<text x="90" y="510" font-family="{SANS}" font-size="17" fill="{DIM}">Minimum interval 5 seconds &#183; countdown badge on the icon</text>'
# big countdown motif
s += f'<text x="90" y="660" font-family="{MONO}" font-size="96" font-weight="bold" fill="{AMBER}" opacity="0.9" letter-spacing="4">00:45</text>'
s += f'<text x="480" y="660" font-family="{SANS}" font-size="19" fill="{DIM}">next refresh</text>'
s += popup_svg(800, 180, 1.35)
render(s, 1280, 800, f"{OUT}/screenshot-2-intervals.png")

# ---------- screenshot 3: control ----------
s = backdrop(1280, 800)
s += f'<text x="90" y="150" font-family="{SANS}" font-size="42" font-weight="bold" fill="{TEXT}">Every timer in one list.</text>'
s += f'<text x="90" y="200" font-family="{SANS}" font-size="21" fill="{DIM}">See all refreshing tabs, switch any of them off &#8212; or stop everything at once.</text>'
# enlarged active list card
s += f'<rect x="90" y="260" width="620" height="300" rx="14" fill="{RAISED}" stroke="{LINE}" stroke-width="1.5"/>'
s += f'<text x="120" y="304" font-family="{MONO}" font-size="14" letter-spacing="2" fill="{DIM}">ACTIVE TIMERS</text>'
rows = [("Grafana &#8212; Node Overview", "5 min"), ("BT Service Status", "30 sec"), ("VeloCloud Orchestrator", "2 min")]
for i, (title, iv) in enumerate(rows):
    ry = 350 + i * 48
    s += f'<text x="120" y="{ry}" font-family="{SANS}" font-size="19" fill="{TEXT}">{title}</text>'
    s += f'<text x="560" y="{ry}" font-family="{MONO}" font-size="16" fill="{DIM}" text-anchor="end">{iv}</text>'
    s += f'<rect x="590" y="{ry - 20}" width="66" height="28" rx="6" fill="none" stroke="{LINE}"/>'
    s += f'<text x="623" y="{ry - 1}" font-family="{MONO}" font-size="13" fill="{DIM}" text-anchor="middle">OFF</text>'
s += f'<rect x="120" y="496" width="536" height="42" rx="8" fill="none" stroke="{DANGER}" stroke-width="2"/>'
s += f'<text x="388" y="523" font-family="{SANS}" font-size="17" font-weight="600" fill="{DANGER}" text-anchor="middle">Stop all timers</text>'
s += f'<text x="90" y="640" font-family="{SANS}" font-size="17" fill="{DIM}">Timers are per-tab: close the tab and its timer is gone. Nothing lingers.</text>'
s += popup_svg(800, 180, 1.35)
render(s, 1280, 800, f"{OUT}/screenshot-3-control.png")

# ---------- screenshot 4: light by design ----------
s = backdrop(1280, 800)
s += f'<text x="90" y="150" font-family="{SANS}" font-size="42" font-weight="bold" fill="{TEXT}">Light by design.</text>'
s += f'<text x="90" y="200" font-family="{SANS}" font-size="21" fill="{DIM}">Built so your browser never feels it running.</text>'
cards = [
    ("&#9679; SLEEPING BACKGROUND", "The background worker stays asleep.",
     "It only wakes for settings changes and a", "handful of badge updates per cycle."),
    ("&#9679; PRECISE TIMING", "Worker-based timers stay accurate",
     "even in throttled background tabs &#8212;", "dashboards refresh on time."),
    ("&#9679; NOTHING STORED", "No accounts, no tracking, no telemetry.",
     "Settings live in session storage and", "vanish when the tab closes."),
]
for i, (tag, l1, l2, l3) in enumerate(cards):
    cx = 90 + i * 380
    s += f'<rect x="{cx}" y="260" width="340" height="300" rx="14" fill="{RAISED}" stroke="{LINE}" stroke-width="1.5"/>'
    s += f'<text x="{cx + 28}" y="316" font-family="{MONO}" font-size="14" letter-spacing="1.5" fill="{AMBER}">{tag}</text>'
    s += f'<text x="{cx + 28}" y="372" font-family="{SANS}" font-size="17" fill="{TEXT}">{l1}</text>'
    s += f'<text x="{cx + 28}" y="402" font-family="{SANS}" font-size="17" fill="{TEXT}">{l2}</text>'
    s += f'<text x="{cx + 28}" y="432" font-family="{SANS}" font-size="17" fill="{TEXT}">{l3}</text>'
s += f'<text x="90" y="660" font-family="{MONO}" font-size="16" fill="{DIM}">Zero dependencies &#183; vanilla JavaScript &#183; open build</text>'
s += f'<text x="90" y="700" font-family="{MONO}" font-size="16" fill="{DIM}">kaktusdev.net / github.com/yfthcn</text>'
render(s, 1280, 800, f"{OUT}/screenshot-4-light.png")

# ---------- small promo tile 440x280 ----------
s = f'<rect width="440" height="280" fill="{BG}"/>'
s += (f'<radialGradient id="g2" cx="0.5" cy="0.35" r="0.8">'
      f'<stop offset="0" stop-color="{AMBER}" stop-opacity="0.10"/>'
      f'<stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></radialGradient>'
      f'<rect width="440" height="280" fill="url(#g2)"/>')
s += refresh_glyph(220, 95, 38, 10)
s += f'<text x="220" y="188" font-family="{MONO}" font-size="30" letter-spacing="7" fill="{AMBER}" text-anchor="middle">EV&#304;RGEN</text>'
s += f'<text x="220" y="222" font-family="{SANS}" font-size="15" fill="{TEXT}" text-anchor="middle">Per-tab auto refresh with countdown</text>'
s += f'<text x="220" y="252" font-family="{MONO}" font-size="11" fill="{DIM}" text-anchor="middle">kaktusdev.net</text>'
render(s, 440, 280, f"{OUT}/small-promo-440x280.png")

# ---------- marquee promo tile 1400x560 ----------
s = f'<rect width="1400" height="560" fill="{BG}"/>'
s += (f'<radialGradient id="g3" cx="0.25" cy="0.4" r="0.9">'
      f'<stop offset="0" stop-color="{AMBER}" stop-opacity="0.08"/>'
      f'<stop offset="1" stop-color="{AMBER}" stop-opacity="0"/></radialGradient>'
      f'<rect width="1400" height="560" fill="url(#g3)"/>')
s += refresh_glyph(190, 250, 72, 18)
s += f'<text x="320" y="250" font-family="{MONO}" font-size="72" letter-spacing="16" fill="{AMBER}">EV&#304;RGEN</text>'
s += f'<text x="322" y="322" font-family="{SANS}" font-size="28" fill="{TEXT}">Per-tab auto refresh. Zero background load.</text>'
s += f'<text x="322" y="372" font-family="{SANS}" font-size="20" fill="{DIM}">Presets &#183; custom intervals &#183; live countdown &#183; hard reload &#183; stop-all</text>'
s += f'<text x="322" y="450" font-family="{MONO}" font-size="17" fill="{DIM}">kaktusdev.net / github.com/yfthcn</text>'
# ghosted countdown motif right side
s += f'<text x="1330" y="380" font-family="{MONO}" font-size="170" font-weight="bold" fill="{AMBER}" opacity="0.14" text-anchor="end" letter-spacing="6">04:37</text>'
render(s, 1400, 560, f"{OUT}/marquee-promo-1400x560.png")

print("done")

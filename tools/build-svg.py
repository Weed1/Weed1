# Generator SVG profile GitHub "Adventurer's Ledger v2" (terang + gelap, beranimasi).
# Teks diukur pakai metrik font asli supaya wrap dan posisi tepat,
# lalu font di-subset dan ditanam (woff2 base64) karena GitHub tidak memuat font eksternal di <img>.
# Jalankan: pip install fonttools==4.60.1 brotli==1.1.0 && python build-svg.py  -> hasil di out/
import base64, io, math, os, urllib.request
from xml.sax.saxutils import escape
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer
from fontTools import subset

OUT = "out"
os.makedirs(OUT, exist_ok=True)
os.makedirs("fonts", exist_ok=True)

SRC = {
    "Cinzel.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/cinzel/Cinzel%5Bwght%5D.ttf",
    "EBGaramond.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/ebgaramond/EBGaramond%5Bwght%5D.ttf",
    "EBGaramond-Italic.ttf": "https://raw.githubusercontent.com/google/fonts/main/ofl/ebgaramond/EBGaramond-Italic%5Bwght%5D.ttf",
}
for name, url in SRC.items():
    p = os.path.join("fonts", name)
    if not os.path.exists(p):
        urllib.request.urlretrieve(url, p)

FACES = {
    ("LCinzel", 500, "normal"): ("Cinzel.ttf", 500),
    ("LCinzel", 700, "normal"): ("Cinzel.ttf", 700),
    ("LGaramond", 400, "normal"): ("EBGaramond.ttf", 400),
    ("LGaramond", 600, "normal"): ("EBGaramond.ttf", 600),
    ("LGaramond", 400, "italic"): ("EBGaramond-Italic.ttf", 400),
}
STATIC = {}
for key, (fn, w) in FACES.items():
    STATIC[key] = instancer.instantiateVariableFont(TTFont(os.path.join("fonts", fn)), {"wght": w})

CZ5, CZ7 = ("LCinzel", 500, "normal"), ("LCinzel", 700, "normal")
G4, G6, GI = ("LGaramond", 400, "normal"), ("LGaramond", 600, "normal"), ("LGaramond", 400, "italic")

# palet dari style.md (terang) dan artboard "Ledger v2 Gelap" di Claude Design
THEMES = {
    "light": dict(
        accent="#2f7a4f", link="#2a6b44", bg="#e7eae5", surface="#f4f6f2", raised="#f7f8f5",
        hero="#dbe1d9", column="#dde2db", qtint="#dcebe0", chip="#e9ede7", trophy="#e4ece5",
        border="#c9d0c8", bsoft="#cdd4cc", bstrong="#a9b3aa", rule="#bfc7be", track="#c4ccc3",
        strong="#121815", text="#1f2622", body="#3a423c", soft="#48514a", muted="#555e57",
        planned="#6b746d", active="#6f7d2e", avatar="#f4f6f2", shadow="rgba(30,40,34,.06)",
        btn_fill="#2f7a4f", btn_stroke="#2f7a4f", btn_ink="#ffffff", ghost_fill="#f4f6f2", ghost_ink="#1f2622",
        mount1="#d2d9d0", mount2="#c8d0c6", moon="#f4f6f2", spark="#2f7a4f",
    ),
    "dark": dict(
        accent="#5f9e6e", link="#7fbf8e", bg="#131815", surface="#1a201c", raised="#222924",
        hero="#1c231f", column="#1a201c", qtint="#1f2a23", chip="#222924", trophy="#222924",
        border="#2f3732", bsoft="#343d37", bstrong="#3a433c", rule="#353d37", track="#2a312c",
        strong="#eef0eb", text="#d9dcd6", body="#c3c8c1", soft="#b4bbb2", muted="#9aa39b",
        planned="#9aa39b", active="#c9d4a0", avatar="#262d28", shadow="rgba(0,0,0,.25)",
        btn_fill="#23362a", btn_stroke="#5f9e6e", btn_ink="#e6e9e3", ghost_fill="#1a201c", ghost_ink="#d9dcd6",
        mount1="#222a25", mount2="#273029", moon="#d9dcd6", spark="#6fbf7f",
    ),
}

# animasi dimatikan untuk pengunjung yang memilih kurangi gerak
BASE_CSS = ("@keyframes fadeUp{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}"
            ".fu{animation:fadeUp .8s ease-out both}"
            "@keyframes twinkle{0%,100%{opacity:.15}50%{opacity:.9}}"
            ".tw{animation:twinkle 3.6s ease-in-out infinite}"
            "@keyframes pulse{0%,100%{opacity:.25}50%{opacity:.8}}"
            ".pl{animation:pulse 4s ease-in-out infinite}"
            "@keyframes sweep{from{transform:translateX(-80px)}to{transform:translateX(280px)}}"
            ".sw{animation:sweep 2.8s ease-in-out infinite}"
            "@media (prefers-reduced-motion:reduce){*{animation:none!important}}")


def width(s, face, size, ls=0.0):
    f = STATIC[face]
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    w = 0
    for ch in s:
        g = cmap.get(ord(ch))
        if g is None:
            raise SystemExit(f"glyph hilang {ch!r} di {face}")
        w += hmtx[g][0]
    return w * size / upm + ls * max(len(s) - 1, 0)


def wrap(s, face, size, maxw):
    lines, cur = [], ""
    for word in s.split():
        t = (cur + " " + word).strip()
        if cur and width(t, face, size) > maxw:
            lines.append(cur)
            cur = word
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def spark(x, y, r, fill, delay):
    # kilau 4 sudut (debu giok seperti di web)
    d = f"M{x} {y-r}Q{x} {y} {x+r} {y}Q{x} {y} {x} {y+r}Q{x} {y} {x-r} {y}Q{x} {y} {x} {y-r}z"
    return f'<path class="tw" style="animation-delay:{delay}s" d="{d}" fill="{fill}"/>'


class Svg:
    def __init__(self, w, title):
        self.w, self.title, self.parts, self.used, self.css = w, title, [], {}, BASE_CSS

    def note(self, face, s):
        self.used.setdefault(face, set()).update(s)

    def add(self, x):
        self.parts.append(x)

    def text(self, x, y, s, face, size, fill, ls=0, anchor="start"):
        self.note(face, s)
        fam, wt, st = face
        a = f' text-anchor="{anchor}"' if anchor != "start" else ""
        l = f' letter-spacing="{ls}"' if ls else ""
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-weight="{wt}" font-style="{st}" '
                 f'font-size="{size}" fill="{fill}"{l}{a}>{escape(s)}</text>')

    def rich(self, x, y, runs, size):
        out = []
        for s, face, fill in runs:
            self.note(face, s)
            fam, wt, st = face
            out.append(f'<tspan font-family="{fam}" font-weight="{wt}" font-style="{st}" fill="{fill}">{escape(s)}</tspan>')
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" xml:space="preserve">{"".join(out)}</text>')

    def group(self, cls="fu", delay=0.0):
        self.add(f'<g class="{cls}" style="animation-delay:{delay:.2f}s">')

    def end(self):
        self.add("</g>")

    def save(self, name, h):
        css = [self.css]
        for face, chars in self.used.items():
            fam, wt, st = face
            buf = io.BytesIO()
            STATIC[face].save(buf)
            buf.seek(0)
            sub = TTFont(buf)
            opts = subset.Options()
            opts.flavor = "woff2"
            opts.layout_features = ["kern", "liga"]
            opts.name_IDs = []
            opts.notdef_outline = True
            ss = subset.Subsetter(opts)
            ss.populate(text="".join(sorted(chars)) + " ")
            ss.subset(sub)
            ob = io.BytesIO()
            sub.flavor = "woff2"
            sub.save(ob)
            b64 = base64.b64encode(ob.getvalue()).decode()
            css.append(f"@font-face{{font-family:'{fam}';font-weight:{wt};font-style:{st};"
                       f"src:url(data:font/woff2;base64,{b64}) format('woff2')}}")
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{h:.0f}" '
               f'viewBox="0 0 {self.w} {h:.0f}" role="img" aria-label="{escape(self.title)}">'
               f'<title>{escape(self.title)}</title><style>{"".join(css)}</style>'
               + "".join(self.parts) + "</svg>")
        with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(svg)
        print(f"{name}: {len(svg)//1024} KB, tinggi {h:.0f}")


W = 880


def hero(t, sfx):
    C = THEMES[t]
    s = Svg(W, "Hail, traveller. I am Yam, Network Warden of Batam.")
    x0, maxw = 252, W - 252 - 40
    y = 78
    s.group(delay=0.1)
    s.text(x0, y, "THE ADVENTURER'S LEDGER", CZ5, 12, C["accent"], ls=2.9)
    y += 48
    s.text(x0, y, "Hail, traveller.", CZ7, 44, C["strong"])
    s.end()
    y += 38
    s.group(delay=0.35)
    s.rich(x0, y, [("I am ", GI, C["soft"]), ("Yam", G6, C["strong"]),
                   (" (@Weed1), Network Warden of Batam.", GI, C["soft"])], 21)
    y += 34
    bio = ("Day to day I serve in the Network Operation Center: watching the paths, "
           "diagnosing outages, and keeping routers and switches loyal to their orders.")
    for line in wrap(bio, G4, 17, maxw):
        s.text(x0, y, line, G4, 17, C["body"])
        y += 25
    y += 6
    s.text(x0, y, "Batam, Indonesia  ·  Guild: PT. Filltech Antar Nusa  ·  yanurfillah.com", G4, 15, C["muted"])
    s.end()
    y += 40
    s.group(delay=0.6)
    s.text(x0, y, "TONGUES", CZ5, 11, C["muted"], ls=1.5)
    cy = y + 18 + 36
    tongues = [("ID", "INDONESIA", "Native", 100), ("EN", "ENGLISH", "Good", 70), ("DE", "DEUTSCH", "B1 · Goethe", 60)]
    for i, (ab, name, lvl, val) in enumerate(tongues):
        cx = x0 + 36 + i * 196
        r = 32
        circ = 2 * math.pi * r
        ln = circ * val / 100
        # ring terisi pelan sekali saat gambar dimuat
        s.css += (f"@keyframes ring{i}{{from{{stroke-dashoffset:{ln:.2f}}}to{{stroke-dashoffset:0}}}}"
                  f".ring{i}{{animation:ring{i} 1.6s {0.8 + i*0.25:.2f}s cubic-bezier(.2,.7,.2,1) both}}")
        s.add(f'<circle cx="{cx}" cy="{cy}" r="36" fill="{C["surface"]}"/>')
        s.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{C["track"]}" stroke-width="8"/>')
        s.add(f'<circle class="ring{i}" cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{C["accent"]}" stroke-width="8" '
              f'stroke-dasharray="{ln:.2f} {circ:.2f}" transform="rotate(-90 {cx} {cy})"/>')
        s.add(f'<circle cx="{cx}" cy="{cy}" r="28" fill="{C["hero"] if t == "dark" else C["surface"]}"/>')
        s.text(cx, cy + 6, ab, CZ7, 17, C["accent"], anchor="middle")
        s.text(cx + 50, cy - 3, name, CZ7, 13, C["strong"], ls=1.3)
        s.text(cx + 50, cy + 18, lvl, G4, 15, C["muted"])
    s.end()
    h = cy + 36 + 96  # ruang ekstra untuk siluet pegunungan di bawah
    ax, ay = 124, 172
    # latar: panel, bulan, pegunungan (dipotong mengikuti sudut panel), kilau
    deco = [f'<defs><clipPath id="panel"><rect width="{W}" height="{h:.0f}" rx="12"/></clipPath></defs>',
            f'<rect x="0.5" y="0.5" width="{W-1}" height="{h-1:.0f}" rx="12" fill="{C["hero"]}"/>',
            f'<g clip-path="url(#panel)">',
            f'<circle cx="826" cy="54" r="20" fill="{C["moon"]}" opacity="{0.9 if t == "light" else 0.75}"/>',
            f'<circle cx="834" cy="48" r="17" fill="{C["hero"]}"/>']
    base = h
    m1 = (f'M0 {base} L0 {base-58} L70 {base-84} L150 {base-52} L230 {base-96} L320 {base-60} L400 {base-80} '
          f'L470 {base-48} L560 {base-92} L640 {base-58} L720 {base-86} L800 {base-54} L880 {base-78} L880 {base} Z')
    m2 = (f'M0 {base} L0 {base-30} L90 {base-50} L180 {base-26} L270 {base-46} L360 {base-22} L450 {base-44} '
          f'L540 {base-24} L630 {base-48} L720 {base-28} L810 {base-42} L880 {base-30} L880 {base} Z')
    deco.append(f'<path d="{m1}" fill="{C["mount1"]}"/>')
    # benteng kecil di punggung bukit
    kx, ky = 560, base - 92
    deco.append(f'<path d="M{kx-14} {ky+6} v-20 h5 v5 h4 v-5 h5 v5 h4 v-5 h5 v20 z M{kx-3} {ky-14} v-14 h6 v14 z" fill="{C["mount1"]}"/>')
    deco.append(f'<path d="{m2}" fill="{C["mount2"]}"/>')
    for i, (sx, sy, r) in enumerate([(40, 42, 5), (214, 58, 4), (28, 300, 4), (222, 296, 5), (742, 30, 4),
                                     (862, 112, 4), (690, 22, 3), (470, 34, 3), (860, 300, 4)]):
        deco.append(spark(sx, sy, r, C["spark"], round(i * 0.45, 2)))
    deco.append("</g>")
    deco.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="{h-1:.0f}" rx="12" fill="none" stroke="{C["border"]}"/>')
    # avatar dengan cincin giok yang berdenyut pelan
    deco.append(f'<circle class="pl" cx="{ax}" cy="{ay}" r="95" fill="none" stroke="{C["accent"]}" stroke-width="2"/>')
    deco.append(f'<circle cx="{ax}" cy="{ay}" r="89" fill="none" stroke="{C["bstrong"]}"/>')
    deco.append(f'<circle cx="{ax}" cy="{ay}" r="79.5" fill="{C["avatar"]}" stroke="{C["accent"]}" stroke-width="3"/>')
    s.parts[0:0] = deco
    s.text(ax, ay + 24, "Y", CZ5, 68, C["accent"], anchor="middle")
    s.save(f"hero-{sfx}.svg", h)


def button(t, sfx, name, label, primary):
    C = THEMES[t]
    tw = width(label, CZ5, 13, 1.3)
    w = int(tw + 44 + 0.5)
    s = Svg(w, label.title())
    if primary:
        s.add(f'<rect x="0.5" y="0.5" width="{w-1}" height="43" rx="6" fill="{C["btn_fill"]}" stroke="{C["btn_stroke"]}"/>')
        fill = C["btn_ink"]
    else:
        s.add(f'<rect x="0.5" y="0.5" width="{w-1}" height="43" rx="6" fill="{C["ghost_fill"]}" stroke="{C["bstrong"]}"/>')
        fill = C["ghost_ink"]
    s.text(22, 27, label, CZ5, 13, fill, ls=1.3)
    s.save(f"{name}-{sfx}.svg", 44)


def main_quest(t, sfx):
    C = THEMES[t]
    s = Svg(W, "Main Quest: Network Operation Center at PT. Filltech Antar Nusa, since January 2025.")
    px, right_w = 32, 200
    maxw = W - px * 2 - right_w - 28
    y = 52
    sx, sy, R, r = px + 7, y - 5, 7, 3
    pts = []
    for k in range(10):
        rad = R if k % 2 == 0 else r
        a = math.pi / 2 + k * math.pi / 5
        pts.append(f"{sx + rad*math.cos(a):.2f},{sy - rad*math.sin(a):.2f}")
    s.group(delay=0.1)
    s.add(f'<polygon points="{" ".join(pts)}" fill="{C["accent"]}"/>')
    s.text(px + 20, y, "MAIN QUEST", CZ5, 12, C["accent"], ls=2.9)
    y += 42
    s.text(px, y, "Network Operation Center", CZ7, 28, C["strong"])
    y += 32
    desc = ("Network Warden at PT. Filltech Antar Nusa. Watching network availability, "
            "resolving incidents, and tending routers, switches, VLANs and BGP.")
    for line in wrap(desc, G4, 17, maxw):
        s.text(px, y, line, G4, 17, C["body"])
        y += 25
    s.end()
    h = y - 25 + 34
    rx, ry = W - px - right_w, 60
    s.group(delay=0.35)
    s.text(rx, ry, "STATUS", CZ5, 11, C["muted"], ls=1.5)
    # garis status "di perjalanan" dengan kilau yang terus bergerak
    s.add(f'<defs><clipPath id="bar"><rect x="{rx}" y="{ry+12}" width="{right_w}" height="3" rx="1.5"/></clipPath>'
          f'<linearGradient id="glow"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
          f'<stop offset=".5" stop-color="#fff" stop-opacity=".75"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient></defs>')
    s.add(f'<rect x="{rx}" y="{ry+12}" width="{right_w}" height="3" rx="1.5" fill="{C["active"]}"/>')
    s.add(f'<g clip-path="url(#bar)"><rect class="sw" x="{rx}" y="{ry+12}" width="60" height="3" fill="url(#glow)"/></g>')
    s.text(rx, ry + 42, "ON THE ROAD", CZ7, 15, C["active"], ls=1.8)
    s.text(rx, ry + 66, "January 2025 to present", G4, 15, C["muted"])
    s.end()
    h = max(h, ry + 66 + 34)
    s.parts.insert(0, f'<rect x="0.5" y="0.5" width="{W-1}" height="{h-1:.0f}" rx="12" fill="{C["qtint"]}" stroke="{C["accent"]}"/>')
    s.save(f"main-quest-{sfx}.svg", h)


def board(t, sfx):
    C = THEMES[t]
    s = Svg(W, "The Quest Board: rumours, quests on the road, and legends.")
    pad = 24
    s.text(pad, 52, "The Quest Board", CZ7, 24, C["strong"])
    tw = width("The Quest Board", CZ7, 24)
    s.add(f'<rect x="{pad+tw+16:.1f}" y="44" width="{W-pad*2-tw-16:.1f}" height="1" fill="{C["rule"]}"/>')
    top, gap = 76, 20
    cw = (W - pad * 2 - gap * 2) / 3
    cols = [
        ("RUMOURS", "planned", C["planned"], [
            ("Vorreon Digital", "Founding my own company: PT Vorreon Digital Nusantara.", "Company · planned"),
        ]),
        ("ON THE ROAD", "in progress", C["active"], [
            ("Goethe B1", "German tongue to level B1. The trial is taken; the scroll of results is on its way.", "Deutsch · 2026"),
            ("yanurfillah.com", "My own quest board, served by nginx and a tiny Python counter in Docker.", "Website · Docker"),
        ]),
        ("LEGENDS", "completed", C["accent"], [
            ("MikroTik MTCINE", "Certified Inter-Networking Engineer, sealed September 2025.", "MikroTik · valid to 2028"),
            ("LKS · IT Network", "Student skills competition in IT Network and System Administration.", "January 2024 to November 2025"),
            ("Catatan", "Field notes: DNS, DHCP and static IP on RHEL, Windows Server Core, Cisco, Ansible.", "Repository · public"),
        ]),
    ]
    inner = cw - 36
    tmax = inner - 32
    col_rects, heights = [], []
    n = 0
    for i, (title, sub, color, cards) in enumerate(cols):
        x = pad + i * (cw + gap)
        y = top + 18 + 15
        s.text(x + 18, y, title, CZ7, 15, color, ls=1.8)
        s.text(x + cw - 18, y, sub, G4, 14, C["muted"], anchor="end")
        y += 18
        if not cards:
            lines = wrap("No rumours on the board yet. New quests will be posted here.", GI, 16, tmax)
            ch = 16 + len(lines) * 21 + 10
            s.group(delay=0.2)
            s.add(f'<rect x="{x+18:.1f}" y="{y:.1f}" width="{inner:.1f}" height="{ch}" rx="8" fill="none" '
                  f'stroke="{C["bstrong"]}" stroke-dasharray="4 4"/>')
            ty = y + 16 + 15
            for line in lines:
                s.text(x + 34, ty, line, GI, 16, C["muted"])
                ty += 21
            s.end()
            y += ch + 12
        else:
            for name, desc, meta in cards:
                lines = wrap(desc, G4, 16, tmax)
                ch = 3 + 14 + 16 + 8 + len(lines) * 21 + 4 + 14 + 14
                # kartu muncul bergantian
                s.group(delay=0.25 + n * 0.12)
                n += 1
                s.add(f'<rect x="{x+18:.1f}" y="{y+1:.1f}" width="{inner:.1f}" height="{ch}" rx="8" fill="{C["shadow"]}"/>'
                      f'<rect x="{x+18.5:.1f}" y="{y+0.5:.1f}" width="{inner-1:.1f}" height="{ch-1}" rx="8" '
                      f'fill="{C["raised"]}" stroke="{C["bsoft"]}"/>'
                      f'<path d="M{x+18:.1f} {y+8:.1f}a8 8 0 0 1 8 -8h{inner-16:.1f}a8 8 0 0 1 8 8v-5h-{inner:.1f}z" fill="{color}"/>')
                ty = y + 3 + 14 + 14
                s.text(x + 34, ty, name, CZ7, 16, C["link"])
                ty += 8 + 16
                for line in lines:
                    s.text(x + 34, ty, line, G4, 16, C["body"])
                    ty += 21
                ty += 2
                s.text(x + 34, ty, meta, G4, 14, C["muted"])
                s.end()
                y += ch + 12
        heights.append(y - 12 + 18)
        col_rects.append(x)
    colh = max(heights) - top
    h = top + colh + pad
    pre = [f'<rect x="0.5" y="0.5" width="{W-1}" height="{h-1:.0f}" rx="12" fill="{C["bg"]}" stroke="{C["border"]}"/>']
    for x in col_rects:
        pre.append(f'<rect x="{x+0.5:.1f}" y="{top+0.5}" width="{cw-1:.1f}" height="{colh-1:.0f}" rx="12" '
                   f'fill="{C["column"]}" stroke="{C["border"]}"/>')
    s.parts[0:0] = pre
    s.save(f"quest-board-{sfx}.svg", h)


def duo(t, sfx):
    C = THEMES[t]
    s = Svg(W, "Trophies: MTCNA, MTCRE, LKS, MTCINE. Satchel of tools and skills.")
    gap, pad = 24, 24
    cw = (W - gap) / 2
    s.text(pad, 40, "TROPHIES", CZ7, 16, C["strong"], ls=1.9)
    trophies = [("I", "MTCNA", "2022"), ("II", "MTCRE", "2023"), ("III", "LKS", "2024 – 2025"), ("IV", "MTCINE", "2025")]
    tw = (cw - pad * 2) / 4
    ty = 64
    for i, (num, name, yr) in enumerate(trophies):
        cx = pad + tw * i + tw / 2
        x = cx - 30
        s.group(delay=0.15 + i * 0.15)
        s.add(f'<polygon points="{x},{ty} {x+60},{ty} {x+60},{ty+42} {cx},{ty+70} {x},{ty+42}" fill="{C["accent"]}"/>')
        s.add(f'<polygon points="{x+5},{ty+3} {x+55},{ty+3} {x+55},{ty+39} {cx},{ty+63} {x+5},{ty+39}" fill="{C["trophy"]}"/>')
        s.text(cx, ty + 36, num, CZ7, 18, C["accent"], anchor="middle")
        s.text(cx, ty + 96, name, G6, 15, C["strong"], anchor="middle")
        s.text(cx, ty + 115, yr, G4, 14, C["muted"], anchor="middle")
        s.end()
    left_h = ty + 115 + 26
    x0 = cw + gap
    s.text(x0 + pad, 40, "SATCHEL", CZ7, 16, C["strong"], ls=1.9)
    chips = ["MikroTik RouterOS", "BGP", "OSPF", "VLAN", "FTTH · OLT / ONT", "Proxmox VE", "Docker", "Nginx",
             "Debian", "RHEL", "Windows Server", "Bash", "PowerShell", "Ansible", "Cisco IOS"]
    cx, cy = x0 + pad, 60
    maxx = x0 + cw - pad
    for i, c in enumerate(chips):
        w = width(c, G4, 16) + 28
        if cx + w > maxx:
            cx, cy = x0 + pad, cy + 32 + 8
        s.group(delay=0.2 + i * 0.05)
        s.add(f'<rect x="{cx+0.5:.1f}" y="{cy+0.5}" width="{w-1:.1f}" height="31" rx="6" fill="{C["chip"]}" stroke="{C["bstrong"] if t == "dark" else C["track"]}"/>')
        s.text(cx + 14, cy + 21, c, G4, 16, C["text"])
        s.end()
        cx += w + 8
    right_h = cy + 32 + 24
    h = max(left_h, right_h)
    s.parts[0:0] = [f'<rect x="{x+0.5:.1f}" y="0.5" width="{cw-1:.1f}" height="{h-1:.0f}" rx="12" '
                    f'fill="{C["surface"]}" stroke="{C["border"]}"/>' for x in (0, x0)]
    s.save(f"trophies-satchel-{sfx}.svg", h)


for t in THEMES:
    hero(t, t)
    button(t, t, "btn-party", "JOIN MY PARTY", True)
    button(t, t, "btn-raven", "SEND A RAVEN", False)
    button(t, t, "btn-board", "VISIT MY QUEST BOARD", False)
    main_quest(t, t)
    board(t, t)
    duo(t, t)

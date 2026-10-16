# Generator SVG profile GitHub "Adventurer's Ledger v2 Light".
# Teks diukur pakai metrik font asli supaya wrap dan posisi tepat,
# lalu font di-subset dan ditanam (woff2 base64) karena GitHub tidak memuat font eksternal di <img>.
import base64, io, os, urllib.request
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

# (family, weight, style) -> file + wght
FACES = {
    ("LCinzel", 500, "normal"): ("Cinzel.ttf", 500),
    ("LCinzel", 700, "normal"): ("Cinzel.ttf", 700),
    ("LGaramond", 400, "normal"): ("EBGaramond.ttf", 400),
    ("LGaramond", 600, "normal"): ("EBGaramond.ttf", 600),
    ("LGaramond", 400, "italic"): ("EBGaramond-Italic.ttf", 400),
}
STATIC = {}
for key, (fn, w) in FACES.items():
    f = TTFont(os.path.join("fonts", fn))
    STATIC[key] = instancer.instantiateVariableFont(f, {"wght": w})

CZ5, CZ7 = ("LCinzel", 500, "normal"), ("LCinzel", 700, "normal")
G4, G6, GI = ("LGaramond", 400, "normal"), ("LGaramond", 600, "normal"), ("LGaramond", 400, "italic")

C = dict(
    accent="#2f7a4f", ink="#ffffff", link="#2a6b44", bg="#e7eae5", surface="#f4f6f2",
    raised="#f7f8f5", hero="#dbe1d9", column="#dde2db", qtint="#dcebe0", chip="#e9ede7",
    trophy="#e4ece5", border="#c9d0c8", bsoft="#cdd4cc", bstrong="#a9b3aa", rule="#bfc7be",
    track="#c4ccc3", strong="#121815", text="#1f2622", body="#3a423c", soft="#48514a",
    muted="#555e57", planned="#6b746d", active="#6f7d2e",
)


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


class Svg:
    def __init__(self, w, title):
        self.w, self.title, self.parts, self.used = w, title, [], {}

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
        # runs: [(teks, face, warna)] dalam satu baris
        out = []
        for s, face, fill in runs:
            self.note(face, s)
            fam, wt, st = face
            out.append(f'<tspan font-family="{fam}" font-weight="{wt}" font-style="{st}" fill="{fill}">{escape(s)}</tspan>')
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" xml:space="preserve">{"".join(out)}</text>')

    def save(self, name, h):
        css = []
        for face, chars in self.used.items():
            fam, wt, st = face
            ft = STATIC[face]
            buf = io.BytesIO()
            ft.save(buf)
            buf.seek(0)
            sub = TTFont(buf)
            opts = subset.Options()
            opts.flavor = "woff2"
            opts.layout_features = ["kern", "liga"]
            opts.name_IDs = []
            opts.notdef_outline = True
            s = subset.Subsetter(opts)
            s.populate(text="".join(sorted(chars)) + " ")
            s.subset(sub)
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

# ---------- hero ----------
def hero():
    s = Svg(W, "Hail, traveller. I am Yam, Network Warden of Batam.")
    x0, maxw = 252, W - 252 - 40
    y = 78
    body = []
    s.text(x0, y, "THE ADVENTURER'S LEDGER", CZ5, 12, C["accent"], ls=2.9)
    y += 48
    s.text(x0, y, "Hail, traveller.", CZ7, 44, C["strong"])
    y += 38
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
    y += 40
    s.text(x0, y, "TONGUES", CZ5, 11, C["muted"], ls=1.5)
    cy = y + 18 + 36
    tongues = [("ID", "INDONESIA", "Native", 100), ("EN", "ENGLISH", "Good", 70), ("DE", "DEUTSCH", "B1 · Goethe", 60)]
    for i, (ab, name, lvl, val) in enumerate(tongues):
        cx = x0 + 36 + i * 196
        r = 32
        circ = 2 * 3.14159265 * r
        s.add(f'<circle cx="{cx}" cy="{cy}" r="36" fill="{C["surface"]}"/>')
        s.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{C["track"]}" stroke-width="8"/>')
        s.add(f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{C["accent"]}" stroke-width="8" '
              f'stroke-dasharray="{circ*val/100:.2f} {circ:.2f}" transform="rotate(-90 {cx} {cy})"/>')
        s.add(f'<circle cx="{cx}" cy="{cy}" r="28" fill="{C["surface"]}"/>')
        s.text(cx, cy + 6, ab, CZ7, 17, C["accent"], anchor="middle")
        s.text(cx + 50, cy - 3, name, CZ7, 13, C["strong"], ls=1.3)
        s.text(cx + 50, cy + 18, lvl, G4, 15, C["muted"])
    h = cy + 36 + 40
    # avatar
    ax, ay = 124, 172
    s.parts.insert(0, f'<rect x="0.5" y="0.5" width="{W-1}" height="{h-1:.0f}" rx="12" fill="{C["hero"]}" stroke="{C["border"]}"/>'
                      f'<circle cx="{ax}" cy="{ay}" r="89" fill="none" stroke="{C["bstrong"]}"/>'
                      f'<circle cx="{ax}" cy="{ay}" r="79.5" fill="{C["surface"]}" stroke="{C["accent"]}" stroke-width="3"/>')
    s.text(ax, ay + 24, "Y", CZ5, 68, C["accent"], anchor="middle")
    s.save("hero.svg", h)


# ---------- tombol ----------
def button(name, label, primary):
    tw = width(label, CZ5, 13, 1.3)
    w = int(tw + 44 + 0.5)
    s = Svg(w, label.title())
    if primary:
        s.add(f'<rect width="{w}" height="44" rx="6" fill="{C["accent"]}"/>')
        fill = C["ink"]
    else:
        s.add(f'<rect x="0.5" y="0.5" width="{w-1}" height="43" rx="6" fill="{C["surface"]}" stroke="{C["bstrong"]}"/>')
        fill = C["text"]
    s.text(22, 27, label, CZ5, 13, fill, ls=1.3)
    s.save(name, 44)


# ---------- main quest ----------
def main_quest():
    s = Svg(W, "Main Quest: Network Operation Center at PT. Filltech Antar Nusa, since January 2025.")
    px = 32
    right_w = 200
    maxw = W - px * 2 - right_w - 28
    y = 52
    # bintang garis tipis (pengganti glyph ★ yang tidak ada di Cinzel)
    sx, sy, R, r = px + 7, y - 5, 7, 3
    import math
    pts = []
    for k in range(10):
        rad = R if k % 2 == 0 else r
        a = math.pi / 2 + k * math.pi / 5
        pts.append(f"{sx + rad*math.cos(a):.2f},{sy - rad*math.sin(a):.2f}")
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
    h = y - 25 + 34
    rx = W - px - right_w
    ry = 60
    s.text(rx, ry, "STATUS", CZ5, 11, C["muted"], ls=1.5)
    s.add(f'<rect x="{rx}" y="{ry+12}" width="{right_w}" height="3" rx="1.5" fill="{C["active"]}"/>')
    s.text(rx, ry + 42, "ON THE ROAD", CZ7, 15, C["active"], ls=1.8)
    s.text(rx, ry + 66, "January 2025 to present", G4, 15, C["muted"])
    h = max(h, ry + 66 + 34)
    s.parts.insert(0, f'<rect x="0.5" y="0.5" width="{W-1}" height="{h-1:.0f}" rx="12" fill="{C["qtint"]}" stroke="{C["accent"]}"/>')
    s.save("main-quest.svg", h)


# ---------- quest board ----------
def board():
    s = Svg(W, "The Quest Board: rumours, quests on the road, and legends.")
    pad = 24
    s.text(pad, 52, "The Quest Board", CZ7, 24, C["strong"])
    tw = width("The Quest Board", CZ7, 24)
    s.add(f'<rect x="{pad+tw+16:.1f}" y="44" width="{W-pad*2-tw-16:.1f}" height="1" fill="{C["rule"]}"/>')
    top = 76
    gap = 20
    cw = (W - pad * 2 - gap * 2) / 3
    cols = [
        ("RUMOURS", "planned", C["planned"], None),
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
    col_parts, heights = [], []
    for i, (title, sub, color, cards) in enumerate(cols):
        x = pad + i * (cw + gap)
        parts = []
        y = top + 18 + 15
        s.text(x + 18, y, title, CZ7, 15, color, ls=1.8)
        s.text(x + cw - 18, y, sub, G4, 14, C["muted"], anchor="end")
        y += 18
        if not cards:
            lines = wrap("No rumours on the board yet. New quests will be posted here.", GI, 16, tmax)
            ch = 16 + len(lines) * 21 + 10
            parts.append(f'<rect x="{x+18:.1f}" y="{y:.1f}" width="{inner:.1f}" height="{ch}" rx="8" fill="none" '
                         f'stroke="{C["bstrong"]}" stroke-dasharray="4 4"/>')
            ty = y + 16 + 15
            for line in lines:
                s.text(x + 34, ty, line, GI, 16, C["muted"])
                ty += 21
            y += ch + 12
        else:
            for name, desc, meta in cards:
                lines = wrap(desc, G4, 16, tmax)
                ch = 3 + 14 + 16 + 8 + len(lines) * 21 + 4 + 14 + 14
                parts.append(f'<rect x="{x+18:.1f}" y="{y+1:.1f}" width="{inner:.1f}" height="{ch}" rx="8" fill="rgba(30,40,34,.06)"/>'
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
                y += ch + 12
        heights.append(y - 12 + 18)
        col_parts.append((x, parts))
    colh = max(heights) - top
    for x, parts in col_parts:
        s.parts.insert(0, "".join(parts))
        s.parts.insert(0, f'<rect x="{x+0.5:.1f}" y="{top+0.5}" width="{cw-1:.1f}" height="{colh-1:.0f}" rx="12" '
                          f'fill="{C["column"]}" stroke="{C["border"]}"/>')
    h = top + colh + pad
    s.parts.insert(0, f'<rect x="0.5" y="0.5" width="{W-1}" height="{h-1:.0f}" rx="12" fill="{C["bg"]}" stroke="{C["border"]}"/>')
    s.save("quest-board.svg", h)


# ---------- trophies + satchel ----------
def duo():
    s = Svg(W, "Trophies: MTCNA, MTCRE, LKS, MTCINE. Satchel of tools and skills.")
    gap = 24
    cw = (W - gap) / 2
    pad = 24
    # trophies
    s.text(pad, 40, "TROPHIES", CZ7, 16, C["strong"], ls=1.9)
    trophies = [("I", "MTCNA", "2022"), ("II", "MTCRE", "2023"), ("III", "LKS", "2024 – 2025"), ("IV", "MTCINE", "2025")]
    tw = (cw - pad * 2) / 4
    ty = 64
    for i, (num, name, yr) in enumerate(trophies):
        cx = pad + tw * i + tw / 2
        x = cx - 30
        s.add(f'<polygon points="{x},{ty} {x+60},{ty} {x+60},{ty+42} {cx},{ty+70} {x},{ty+42}" fill="{C["accent"]}"/>')
        s.add(f'<polygon points="{x+5},{ty+3} {x+55},{ty+3} {x+55},{ty+39} {cx},{ty+63} {x+5},{ty+39}" fill="{C["trophy"]}"/>')
        s.text(cx, ty + 36, num, CZ7, 18, C["accent"], anchor="middle")
        s.text(cx, ty + 96, name, G6, 15, C["strong"], anchor="middle")
        s.text(cx, ty + 115, yr, G4, 14, C["muted"], anchor="middle")
    left_h = ty + 115 + 26
    # satchel
    x0 = cw + gap
    s.text(x0 + pad, 40, "SATCHEL", CZ7, 16, C["strong"], ls=1.9)
    chips = ["MikroTik RouterOS", "BGP", "OSPF", "VLAN", "FTTH · OLT / ONT", "Proxmox VE", "Docker", "Nginx",
             "Debian", "RHEL", "Windows Server", "Bash", "PowerShell", "Ansible", "Cisco IOS"]
    cx, cy = x0 + pad, 60
    maxx = x0 + cw - pad
    for c in chips:
        w = width(c, G4, 16) + 28
        if cx + w > maxx:
            cx, cy = x0 + pad, cy + 32 + 8
        s.add(f'<rect x="{cx+0.5:.1f}" y="{cy+0.5}" width="{w-1:.1f}" height="31" rx="6" fill="{C["chip"]}" stroke="{C["track"]}"/>')
        s.text(cx + 14, cy + 21, c, G4, 16, C["text"])
        cx += w + 8
    right_h = cy + 32 + 24
    h = max(left_h, right_h)
    for x in (0, x0):
        s.parts.insert(0, f'<rect x="{x+0.5:.1f}" y="0.5" width="{cw-1:.1f}" height="{h-1:.0f}" rx="12" '
                          f'fill="{C["surface"]}" stroke="{C["border"]}"/>')
    s.save("trophies-satchel.svg", h)


hero()
button("btn-party.svg", "JOIN MY PARTY", True)
button("btn-raven.svg", "SEND A RAVEN", False)
button("btn-board.svg", "VISIT MY QUEST BOARD", False)
main_quest()
board()
duo()

import random
import sys

THEMES = {
    "dark": dict(bg="#0d1117", border="#30363d", text="#e6edf3", muted="#8b949e", ghost="#161b22",
                 levels=["#0e4429", "#006d32", "#26a641", "#39d353"], shine="#b6f5c0"),
    "light": dict(bg="#ffffff", border="#d0d7de", text="#1f2328", muted="#57606a", ghost="#ebedf0",
                  levels=["#9be9a8", "#40c463", "#30a14e", "#216e39"], shine="#0b3d1c"),
}
GLYPHS = {
    "k": ["1....", "1....", "1..1.", "1.1..", "11...", "1.1..", "1..1."],
    "a": [".....", ".....", ".111.", "....1", ".1111", "1...1", ".1111"],
    "y": [".....", ".....", "1...1", "1...1", ".1111", "....1", ".111."],
}
COLS, ROWS, CELL, SCALE = 96, 26, 9, 2
OX, OY = 28, 30
CYCLE = 7.0
MONO = "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
SANS = "-apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif"


def name_cells():
    word = "kakkky"
    gw = 5 * SCALE + SCALE
    x0 = (COLS - (len(word) * gw - SCALE)) // 2
    y0 = (ROWS - 7 * SCALE) // 2
    cells = []
    for i, ch in enumerate(word):
        for r, row in enumerate(GLYPHS[ch]):
            for c, v in enumerate(row):
                if v == "1":
                    for dy in range(SCALE):
                        for dx in range(SCALE):
                            cells.append((x0 + i * gw + c * SCALE + dx, y0 + r * SCALE + dy))
    return cells


def render(c, rnd):
    w, h = OX * 2 + COLS * CELL, OY + ROWS * CELL + 56
    cells = name_cells()
    min_x = min(x for x, _ in cells)
    span = max(x for x, _ in cells) - min_x
    dots = []
    for x, y in cells:
        tx, ty = OX + x * CELL, OY + y * CELL
        # 散らばった位置はグリッド上のどこか。集まる/散るタイミングをドットごとにずらす
        sx, sy = OX + rnd.randrange(COLS) * CELL, OY + rnd.randrange(ROWS) * CELL
        delay = rnd.uniform(0, .5)
        wave = .1 + (x - min_x) / span * .9
        level = rnd.choices(c["levels"], weights=[1, 2, 3, 3])[0]
        dots.append(
            f'<g class="dot" style="--dx:{sx - tx}px;--dy:{sy - ty}px;animation-delay:{delay:.2f}s">'
            f'<rect x="{tx}" y="{ty}" fill="{level}"/>'
            f'<rect class="shine" x="{tx}" y="{ty}" fill="{c["shine"]}" style="animation-delay:{delay + wave:.2f}s"/></g>')
    style = f"""
.dot rect{{width:{CELL - 2}px;height:{CELL - 2}px;rx:1.5px}}
.dot{{animation:gather {CYCLE}s cubic-bezier(.22,1,.36,1) infinite both}}
.shine{{opacity:0;animation:shine {CYCLE}s ease-in-out infinite both}}
@keyframes gather{{
  0%{{transform:translate(var(--dx),var(--dy));opacity:0}}
  6%{{opacity:.6}}
  24%,78%{{transform:translate(0,0);opacity:1}}
  92%,100%{{transform:translate(var(--dx),var(--dy));opacity:0}}
}}
@keyframes shine{{0%,34%{{opacity:0}}40%{{opacity:.9}}50%,100%{{opacity:0}}}}
.title{{font:600 20px {SANS};fill:{c["text"]}}}
.sub{{font:14px {MONO};fill:{c["muted"]}}}
@media (prefers-reduced-motion:reduce){{.dot,.shine{{animation:none}}}}
"""
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="kakkky — Web Application Engineer · Gopher">
<style>{style}</style>
<defs><pattern id="gp" x="{OX}" y="{OY}" width="{CELL}" height="{CELL}" patternUnits="userSpaceOnUse"><rect width="{CELL - 2}" height="{CELL - 2}" rx="1.5" fill="{c["ghost"]}"/></pattern></defs>
<rect x="0.5" y="0.5" width="{w - 1}" height="{h - 1}" rx="14" fill="{c["bg"]}" stroke="{c["border"]}"/>
<rect x="{OX}" y="{OY}" width="{COLS * CELL}" height="{ROWS * CELL}" fill="url(#gp)"/>
{"".join(dots)}
<text class="title" x="{OX}" y="{h - 20}">Web Application Engineer · Gopher</text>
<text class="sub" x="{w - OX}" y="{h - 22}" text-anchor="end">→ kakkky.dev</text>
</svg>
'''


out = sys.argv[1] if len(sys.argv) > 1 else "assets"
for name, theme in THEMES.items():
    open(f"{out}/header-{name}.svg", "w").write(render(theme, random.Random(7)))

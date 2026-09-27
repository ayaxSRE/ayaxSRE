import os
import sys
import math
import hashlib
import requests

WAKATIME_API_KEY = os.environ.get("WAKATIME_API_KEY")
RANGE = os.environ.get("WAKATIME_RANGE", "all_time")
OUTPUT_PATH = os.environ.get("OUTPUT_PATH", "assets/wakatime.svg")
MAX_LANGS = int(os.environ.get("MAX_LANGS", "15"))

# --- Paleta Tokyo Night ---
BG_CARD = "#1a1b26"
BORDER = "#292e42"
TITLE_COLOR = "#c0caf5"   # foreground principal
TEXT_COLOR = "#a9b1d6"    # foreground secundario, mas apagado
TRACK_COLOR = "#292e42"

# Acentos Tokyo Night
ACCENTS = [
    "#7aa2f7",  # blue
    "#bb9af7",  # purple
    "#7dcfff",  # cyan
    "#9ece6a",  # green
    "#e0af68",  # yellow/orange
    "#f7768e",  # red/pink
    "#73daca",  # teal
    "#565f89",  # comment gray-blue (para lo "otros"/menores)
]

# Asignaciones fijas para los lenguajes mas comunes, resto se resuelve por hash
LANG_COLORS = {
    "python": "#7aa2f7",
    "go": "#7dcfff",
    "typescript": "#7aa2f7",
    "javascript": "#e0af68",
    "markdown": "#565f89",
    "c++": "#f7768e",
    "java": "#e0af68",
    "yaml": "#f7768e",
    "scss": "#bb9af7",
    "html": "#e0af68",
    "css": "#bb9af7",
    "haskell": "#bb9af7",
    "lua": "#7aa2f7",
    "perl": "#565f89",
    "sh": "#9ece6a",
    "bash": "#9ece6a",
    "makefile": "#73daca",
    "docker": "#7dcfff",
    "dockerfile": "#7dcfff",
    "other": "#565f89",
    "text": "#565f89",
}

def color_for(name):
    key = name.strip().lower()
    if key in LANG_COLORS:
        return LANG_COLORS[key]
    # color estable por hash para que no todo quede gris,
    # pero siempre dentro de la paleta Tokyo Night
    idx = int(hashlib.sha1(key.encode()).hexdigest(), 16) % len(ACCENTS)
    return ACCENTS[idx]

def fetch_stats():
    if not WAKATIME_API_KEY:
        print("Falta WAKATIME_API_KEY", file=sys.stderr)
        sys.exit(1)
    url = f"https://wakatime.com/api/v1/users/current/stats/{RANGE}"
    resp = requests.get(url, auth=(WAKATIME_API_KEY, ""), timeout=30)
    resp.raise_for_status()
    return resp.json()["data"]

def build_svg(data):
    langs = data.get("languages", [])[:MAX_LANGS]
    n = len(langs)
    half = math.ceil(n / 2) if n else 0
    col1, col2 = langs[:half], langs[half:]

    width = 940
    pad = 32
    title_h = 70
    bar_h = 16
    bar_gap = 26
    row_h = 34
    rows = max(len(col1), len(col2), 1)
    height = title_h + bar_h + bar_gap + rows * row_h + pad

    col1_x = pad
    col2_x = width // 2 + 10

    total = sum(l["percent"] for l in langs) or 1
    bar_x = pad
    bar_w = width - 2 * pad

    segs = []
    cx = bar_x
    for lang in langs:
        seg_w = (lang["percent"] / total) * bar_w
        segs.append(
            f'<rect x="{cx:.1f}" y="{title_h}" width="{seg_w:.1f}" height="{bar_h}" '
            f'fill="{color_for(lang["name"])}"/>'
        )
        cx += seg_w

    def render_col(items, x):
        out = []
        for i, lang in enumerate(items):
            y = title_h + bar_h + bar_gap + i * row_h
            out.append(f'''
    <circle cx="{x + 6}" cy="{y + 8}" r="6" fill="{color_for(lang['name'])}"/>
    <text x="{x + 22}" y="{y + 13}" fill="{TEXT_COLOR}" font-size="15"
          font-family="Segoe UI, sans-serif">{lang['name']} - {lang['text']}</text>''')
        return "".join(out)

    svg = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <clipPath id="barclip">
      <rect x="{bar_x}" y="{title_h}" width="{bar_w}" height="{bar_h}" rx="{bar_h / 2}"/>
    </clipPath>
  </defs>
  <rect width="{width}" height="{height}" rx="18" fill="{BG_CARD}" stroke="{BORDER}"/>
  <text x="{pad}" y="52" fill="{TITLE_COLOR}" font-size="28" font-weight="600"
        font-family="Segoe UI, sans-serif">Wakatime Stats</text>
  <g clip-path="url(#barclip)">
    <rect x="{bar_x}" y="{title_h}" width="{bar_w}" height="{bar_h}" fill="{TRACK_COLOR}"/>
    {''.join(segs)}
  </g>
  {render_col(col1, col1_x)}
  {render_col(col2, col2_x)}
</svg>'''
    return svg

def main():
    data = fetch_stats()
    svg = build_svg(data)
    os.makedirs(os.path.dirname(OUTPUT_PATH) or ".", exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"SVG generado en {OUTPUT_PATH}")

if __name__ == "__main__":
    main()

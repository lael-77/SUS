import os, re, urllib.request

ROOT = r"c:\Users\Q\Desktop\SUS Kigali Haircut\sus-kigali-haircut"
OUT = os.path.join(ROOT, "sus", "static", "fonts")
os.makedirs(OUT, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

FAMILIES = [
    ("Fraunces", "Fraunces:opsz,wght@9..144,100..900"),
    ("Manrope", "Manrope:wght@200..800"),
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read()


blocks = []
for name, spec in FAMILIES:
    css = get("https://fonts.googleapis.com/css2?family=" + spec.replace(",", "%2C")
              + "&display=swap").decode("utf-8")
    # keep only the plain-latin subsets
    parts = re.split(r"/\*\s*([a-z0-9\-]+)\s*\*/", css)
    for i in range(1, len(parts), 2):
        subset, block = parts[i], parts[i + 1]
        if subset != "latin":
            continue
        url = re.search(r"url\((https://[^)]+\.woff2)\)", block)
        if not url:
            continue
        style = re.search(r"font-style:\s*(\w+)", block).group(1)
        weight = re.search(r"font-weight:\s*([\d ]+)", block).group(1).strip()
        src = url.group(1)
        fname = "%s-%s-%s.woff2" % (name.lower(), weight.replace(" ", "_"), style)
        with open(os.path.join(OUT, fname), "wb") as fh:
            fh.write(get(src))
        rng = re.search(r"unicode-range:\s*([^;]+);", block)
        block = re.sub(r"url\(https://[^)]+\.woff2\)\s*format\('woff2'\)",
                       "url('fonts/%s') format('woff2')" % fname, block)
        block = re.sub(r"src:\s*(local\([^)]*\)\s*,\s*)+", "src: ", block)
        block = re.sub(r"^\s*\n", "", block, flags=re.M)
        blocks.append(block.strip())
        print("saved", fname)

hdr = ("/* SUS Kigali Haircut - self-hosted webfonts (SIL Open Font License 1.1)\n"
       "   Fraunces (Undercase Type) + Manrope (Mikhail Sharanda). Downloaded from\n"
       "   the Google Fonts CDN so the site needs no third-party requests at runtime. */\n\n")
with open(os.path.join(ROOT, "sus", "static", "css", "fonts.css"), "w", encoding="utf-8") as fh:
    fh.write(hdr + "\n".join(blocks) + "\n")
print("fonts.css written", len(blocks), "faces")

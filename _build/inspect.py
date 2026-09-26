import os
from PIL import Image
ROOT = r"c:\Users\Q\Desktop\SUS Kigali Haircut\sus-kigali-haircut"
IMG = os.path.join(ROOT, "sus", "static", "img")
P = r"c:\Users\Q\Desktop\SUS Kigali Haircut\_build"

full = Image.open(os.path.join(IMG, "_logo-full-alpha.png"))
print("full size", full.size, "bbox", full.getbbox())

# what actually lives in the left 160px column?
strip = full.crop((0, 0, 160, full.height))
print("left strip alpha bbox", strip.getbbox())

prev = Image.new("RGBA", (160 * 3, full.height * 3), (40, 40, 44, 255))
big = strip.resize((160 * 3, full.height * 3), Image.NEAREST)
prev.alpha_composite(big)
prev.convert("RGB").save(os.path.join(P, "preview_pole.png"))

lg = Image.new("RGBA", (full.width + 40, full.height + 40), (120, 120, 126, 255))
lg.alpha_composite(full, (20, 20))
lg.convert("RGB").resize(((full.width + 40) // 2, (full.height + 40) // 2)).save(os.path.join(P, "preview_logo.png"))

b = Image.open(os.path.join(IMG, "icon-512.png")).resize((320, 320), Image.LANCZOS)
bb = Image.new("RGBA", (360, 360), (120, 120, 126, 255))
bb.alpha_composite(b, (20, 20))
bb.convert("RGB").save(os.path.join(P, "preview_badge.png"))
print("previews written")

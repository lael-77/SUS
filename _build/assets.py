import os
from PIL import Image, ImageDraw

ROOT = r"c:\Users\Q\Desktop\SUS Kigali Haircut\sus-kigali-haircut"
IMG = os.path.join(ROOT, "sus", "static", "img")
os.makedirs(IMG, exist_ok=True)

INK = (11, 11, 12, 255)
GOLD = (242, 199, 0, 255)

src = Image.open(os.path.join(ROOT, "SUS logo.jpeg")).convert("RGB")


def unpremultiply(im, floor=16):
    """The artwork sits on a pure-black field, so observed colour == paint * alpha.
    Invert that to recover straight-alpha RGBA (clean edges, no black halo)."""
    im = im.convert("RGB")
    w, h = im.size
    px = im.load()
    out = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    op = out.load()
    span = 255 - floor
    for y in range(h):
        for x in range(w):
            r, g, b = px[x, y]
            a = r if r > g else g
            if b > a:
                a = b
            if a <= floor:
                continue
            na = int((a - floor) * 255 / span)
            if na > 255:
                na = 255
            s = 255.0 / a
            op[x, y] = (min(255, int(r * s + 0.5)),
                        min(255, int(g * s + 0.5)),
                        min(255, int(b * s + 0.5)), na)
    return out


rgba = unpremultiply(src)
rgba.save(os.path.join(IMG, "_logo-full-alpha.png"))

# ---------- horizontal lockup (for dark backgrounds) ----------
lock = rgba.crop(rgba.getbbox())
pad = 10
canvas = Image.new("RGBA", (lock.width + pad * 2, lock.height + pad * 2), (0, 0, 0, 0))
canvas.paste(lock, (pad, pad), lock)
canvas.save(os.path.join(IMG, "logo.png"))
print("logo.png", canvas.size)

# ---------- isolate the barber pole (the only art left of x=150) ----------
strip = rgba.crop((0, 0, 150, rgba.height))
bbox = strip.getbbox()
print("pole bbox", bbox)

pole = rgba.crop(bbox)
pole.save(os.path.join(IMG, "logo-pole.png"))
print("pole", pole.size)


# ---------- square badge: the pole on the brand black, works on any background ----------
def badge(size, radius_ratio=0.16, pole_ratio=0.80, bg=INK):
    ss = size * 4
    img = Image.new("RGBA", (ss, ss), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([0, 0, ss - 1, ss - 1], radius=int(ss * radius_ratio), fill=bg)
    th = int(ss * pole_ratio)
    tw = max(1, int(pole.width * th / pole.height))
    p = pole.resize((tw, th), Image.LANCZOS)
    img.alpha_composite(p, ((ss - tw) // 2, (ss - th) // 2))
    return img.resize((size, size), Image.LANCZOS)


badge(512).save(os.path.join(IMG, "icon-512.png"))
badge(192).save(os.path.join(IMG, "icon-192.png"))
badge(180).save(os.path.join(IMG, "apple-touch-icon.png"))
badge(32).save(os.path.join(IMG, "favicon-32.png"))
badge(16).save(os.path.join(IMG, "favicon-16.png"))

ico = badge(256)
ico.save(os.path.join(IMG, "favicon.ico"), sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64)])
print("favicon.ico written")

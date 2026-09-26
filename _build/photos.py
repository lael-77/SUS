import os, urllib.request
from PIL import Image, ImageDraw

P = r"c:\Users\Q\Desktop\SUS Kigali Haircut\_build"
os.makedirs(os.path.join(P, "thumbs"), exist_ok=True)

IDS = [
    "photo-1503951914875-452162b0f3f1",
    "photo-1585747860715-2ba37e788b70",
    "photo-1622286342621-4bd786c2447c",
    "photo-1599351431202-1e0f0137899a",
    "photo-1521590832167-7bcbfaa6381f",
    "photo-1560066984-138dadb4c035",
    "photo-1580618672591-eb180b1a973f",
    "photo-1604654894610-df63bc536371",
    "photo-1522337360788-8b13dee7a37e",
    "photo-1517832606299-7ae9b720a186",
    "photo-1512690459411-b9245aed614b",
    "photo-1633681926022-84c23e8cb2d6",
]

url = ("https://images.unsplash.com/%s?w=400&h=280&fit=crop&crop=entropy&q=70&fm=jpg")
cells = []
for i, pid in enumerate(IDS):
    dst = os.path.join(P, "thumbs", "%02d.jpg" % i)
    if not os.path.exists(dst):
        req = urllib.request.Request(url % pid, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=45) as r:
            open(dst, "wb").write(r.read())
    cells.append(Image.open(dst).convert("RGB").resize((300, 210), Image.LANCZOS))
    print("ok", i, pid)

cols, rows = 4, 3
sheet = Image.new("RGB", (cols * 300, rows * 240), (20, 20, 22))
d = ImageDraw.Draw(sheet)
for i, c in enumerate(cells):
    x, y = (i % cols) * 300, (i // cols) * 240
    sheet.paste(c, (x, y + 30))
    d.text((x + 8, y + 9), "%02d" % i, fill=(255, 220, 0))
sheet.save(os.path.join(P, "contact_sheet.png"))
print("contact sheet written")

import os, urllib.request
from PIL import Image

ROOT = r"c:\Users\Q\Desktop\SUS Kigali Haircut\sus-kigali-haircut"
IMG = os.path.join(ROOT, "sus", "static", "img")
os.makedirs(IMG, exist_ok=True)

UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

# filename, unsplash id, width, height, crop focus, alt/description
SET = [
    ("hero.jpg",        "photo-1503951914875-452162b0f3f1", 2000, 1200, "faces",   "Straight-razor shave in a low-lit barbershop"),
    ("shop.jpg",        "photo-1585747860715-2ba37e788b70", 1400, 1050, "entropy", "Barbershop interior with brick walls and warm workshop lamps"),
    ("chair.jpg",       "photo-1512690459411-b9245aed614b", 1400, 1050, "entropy", "Vintage leather barber chair with brass fittings"),
    ("tools.jpg",       "photo-1517832606299-7ae9b720a186", 1400, 933,  "entropy", "Barber tools laid out on a striped cape"),
    ("salon-mono.jpg",  "photo-1560066984-138dadb4c035",    1400, 933,  "entropy", "Monochrome salon interior"),
    ("salon-bright.jpg","photo-1633681926022-84c23e8cb2d6", 1400, 933,  "entropy", "Bright modern salon interior"),
    ("fade.jpg",        "photo-1599351431202-1e0f0137899a", 1000, 1250, "faces",   "Close fade cut finished with a comb"),
    ("clipper.jpg",     "photo-1622286342621-4bd786c2447c", 1000, 1250, "faces",   "Clipper work on the back of the head"),
    ("styling.jpg",     "photo-1580618672591-eb180b1a973f", 1000, 1250, "faces",   "Blow-dry styling with a round brush"),
    ("hair.jpg",        "photo-1522337360788-8b13dee7a37e", 1000, 1250, "faces",   "Long hair braided and finished"),
    ("nails.jpg",       "photo-1604654894610-df63bc536371", 1000, 1000, "faces",   "Freshly manicured nails"),
    ("salon-pink.jpg",  "photo-1521590832167-7bcbfaa6381f", 1000, 1250, "entropy", "Salon styling stations with upholstered chairs"),
]

url = ("https://images.unsplash.com/%s?w=%d&h=%d&fit=crop&crop=%s&q=74&fm=jpg"
       "&auto=format&dpr=1")
for name, pid, w, h, crop, desc in SET:
    dst = os.path.join(IMG, name)
    try:
        rq = urllib.request.Request(url % (pid, w, h, crop), headers={"User-Agent": UA})
        data = urllib.request.urlopen(rq, timeout=60).read()
        open(dst, "wb").write(data)
        im = Image.open(dst)
        print("%-18s %-42s %s %dx%d %dKB" % (name, pid, im.format, im.width, im.height, len(data) // 1024))
    except Exception as e:
        print("FAIL", name, pid, e)

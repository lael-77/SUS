import os, re, urllib.request
from PIL import Image, ImageDraw

P = r"c:\Users\Q\Desktop\SUS Kigali Haircut\_build"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
os.makedirs(os.path.join(P, "thumbs2"), exist_ok=True)

QUERIES = ["black barber", "african barbershop", "black woman braids", "african hair salon"]
found = []
for q in QUERIES:
    try:
        req = urllib.request.Request("https://unsplash.com/s/photos/" + q.replace(" ", "-"),
                                     headers={"User-Agent": UA})
        html = urllib.request.urlopen(req, timeout=45).read().decode("utf-8", "ignore")
    except Exception as e:
        print("search fail", q, e)
        continue
    ids = re.findall(r"images\.unsplash\.com/(photo-[0-9a-f\-]{20,})", html)
    seen = []
    for i in ids:
        if i not in seen:
            seen.append(i)
    print(q, "->", len(seen))
    for i in seen[:6]:
        found.append((q, i))

print("total", len(found))
if found:
    url = "https://images.unsplash.com/%s?w=400&h=280&fit=crop&crop=entropy&q=70&fm=jpg"
    cells = []
    for n, (q, pid) in enumerate(found):
        dst = os.path.join(P, "thumbs2", "%02d.jpg" % n)
        try:
            if not os.path.exists(dst):
                rq = urllib.request.Request(url % pid, headers={"User-Agent": UA})
                open(dst, "wb").write(urllib.request.urlopen(rq, timeout=45).read())
            cells.append((n, q, Image.open(dst).convert("RGB").resize((300, 210), Image.LANCZOS)))
        except Exception as e:
            print("img fail", pid, e)
    cols = 4
    rows = (len(cells) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 300, rows * 240), (20, 20, 22))
    d = ImageDraw.Draw(sheet)
    for n, q, c in cells:
        x, y = (n % cols) * 300, (n // cols) * 240
        sheet.paste(c, (x, y + 30))
        d.text((x + 8, y + 9), "%02d %s" % (n, q), fill=(255, 220, 0))
    sheet.save(os.path.join(P, "contact_sheet2.png"))
    with open(os.path.join(P, "found_ids.txt"), "w") as fh:
        for n, (q, pid) in enumerate(found):
            fh.write("%02d %s %s\n" % (n, q, pid))
    print("sheet2 written")

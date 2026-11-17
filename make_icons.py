from PIL import Image, ImageDraw
import os
S = 1024
def grad(size):
    img = Image.new("RGB", (size, size))
    px = img.load()
    c1, c2 = (124, 58, 237), (6, 182, 212)   # violet -> cyan
    for y in range(size):
        for x in range(size):
            t = (x + y) / (2 * size - 2)
            px[x, y] = tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))
    return img
def draw_icon(size=S):
    k = size / S
    base = grad(size).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, size - 1, size - 1), int(230 * k), fill=255)
    base.putalpha(mask)
    # soft white play-circle behind arrow
    ov = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(ov)
    d.ellipse((190*k, 150*k, 834*k, 794*k), fill=(255, 255, 255, 40))
    # download arrow
    w = (255, 255, 255, 255)
    d.rounded_rectangle((462*k, 230*k, 562*k, 520*k), int(50*k), fill=w)
    d.polygon([(312*k, 480*k), (712*k, 480*k), (512*k, 700*k)], fill=w)
    # tray
    d.rounded_rectangle((250*k, 770*k, 774*k, 836*k), int(33*k), fill=w)
    d.rounded_rectangle((250*k, 730*k, 316*k, 836*k), int(33*k), fill=w)
    d.rounded_rectangle((708*k, 730*k, 774*k, 836*k), int(33*k), fill=w)
    base.alpha_composite(ov)
    return base
big = draw_icon(1024)
big.save("desktop/icon.png")
big.resize((256, 256), Image.LANCZOS).save("desktop/icon.ico", sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
res = "android/app/src/main/res"
for n, s in {"mdpi":48,"hdpi":72,"xhdpi":96,"xxhdpi":144,"xxxhdpi":192}.items():
    os.makedirs(f"{res}/mipmap-{n}", exist_ok=True)
    im = big.resize((s, s), Image.LANCZOS)
    im.save(f"{res}/mipmap-{n}/ic_launcher.png")
    im.save(f"{res}/mipmap-{n}/ic_launcher_round.png")
big.resize((512,512), Image.LANCZOS).save("icon_512.png")

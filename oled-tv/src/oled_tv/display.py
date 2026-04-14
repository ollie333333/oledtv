from PIL import Image

# ---------------- OLED FRAME CONVERTER ----------------
def to_oled(img):
    """
    Convert an RGB screenshot into 128x64 SSD1306 framebuffer (1-bit packed).
    """

    target_w, target_h = 128, 64

    # grayscale
    img = img.convert("L")

    # original size
    src_w, src_h = img.size
    src_ratio = src_w / src_h
    target_ratio = target_w / target_h

    # ---------------- PROPER ASPECT RATIO SCALING ----------------
    if src_ratio > target_ratio:
        new_w = target_w
        new_h = int(target_w / src_ratio)
    else:
        new_h = target_h
        new_w = int(target_h * src_ratio)

    img = img.resize((new_w, new_h), Image.LANCZOS)

    # ---------------- CENTER ON BLACK CANVAS ----------------
    canvas = Image.new("L", (target_w, target_h), 0)

    x_offset = (target_w - new_w) // 2
    y_offset = (target_h - new_h) // 2

    canvas.paste(img, (x_offset, y_offset))

    # ---------------- CONTRAST FIX (IMPORTANT FOR OLED) ----------------
    canvas = canvas.point(lambda p: 0 if p < 135 else 255)

    pixels = canvas.load()

    # ---------------- PACK INTO SSD1306 BUFFER ----------------
    buf = bytearray(1024)

    for page in range(8):  # 8 vertical pages
        for x in range(128):
            byte = 0

            for bit in range(8):
                y = page * 8 + bit
                if pixels[x, y]:
                    byte |= (1 << bit)

            buf[page * 128 + x] = byte

    return buf


# ---------------- OPTIONAL DEBUG TEST ----------------
if __name__ == "__main__":
    # quick test image
    img = Image.new("RGB", (200, 200), "white")
    data = to_oled(img)
    print("Frame size:", len(data))

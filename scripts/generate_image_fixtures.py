"""Generate synthetic test image fixtures for Phase 12F testing.

Strict requirement:
- Fake domains only (.example / .test)
- Fixtures:
  1. text_screenshot.png: High-contrast email screenshot with spam text and suspicious link
  2. qr_phish.png: High-resolution QR code encoding a phishing URL on .test
  3. plain_photo.jpg: Benign image with no text and no QR code
  4. corrupt.png: File with invalid magic bytes signature
  5. oversized.png: Valid PNG image exceeding 5 MB limit
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import qrcode

FIXTURES_DIR = Path(__file__).resolve().parent.parent / "tests" / "fixtures" / "images"


def generate_fixtures():
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Generating test fixtures in: {FIXTURES_DIR}")

    # 1. text_screenshot.png
    # 800x420 image with clear rendered typography
    img_text = Image.new("RGB", (850, 420), color=(255, 255, 255))
    draw = ImageDraw.Draw(img_text)
    
    try:
        font_header = ImageFont.truetype("arial.ttf", 20)
        font_body = ImageFont.truetype("arial.ttf", 18)
        font_url = ImageFont.truetype("arial.ttf", 19)
    except Exception:
        font_header = ImageFont.load_default()
        font_body = ImageFont.load_default()
        font_url = ImageFont.load_default()

    # Header bar
    draw.rectangle([(0, 0), (850, 50)], fill=(139, 30, 63))
    draw.text((25, 14), "Security Alert - Action Required", fill=(255, 255, 255), font=font_header)

    # Body lines
    lines = [
        ("URGENT NOTICE: Your account access has been restricted.", font_body, (180, 20, 20)),
        ("Unauthorized access attempts were detected from an unknown IP address.", font_body, (30, 30, 30)),
        ("Please confirm your credentials immediately to avoid permanent deletion:", font_body, (30, 30, 30)),
        ("http://security-update.example/verify-login", font_url, (0, 70, 180)),
        ("", font_body, (30, 30, 30)),
        ("If you do not verify within 24 hours, your profile will be locked.", font_body, (50, 50, 50)),
        ("Thank you, Security Protection Department", font_body, (80, 80, 80))
    ]
    y = 75
    for line_text, font, fill in lines:
        if line_text:
            draw.text((30, y), line_text, fill=fill, font=font)
        y += 36

    text_path = FIXTURES_DIR / "text_screenshot.png"
    img_text.save(text_path, "PNG")
    print(f"  [Created] {text_path.name} ({text_path.stat().st_size:,} bytes)")

    # 2. qr_phish.png
    qr_data = "http://phishing-portal.test/steal-credentials"
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    # Composite into image with title
    comp_w, comp_h = 500, 520
    qr_card = Image.new("RGB", (comp_w, comp_h), color=(250, 250, 250))
    c_draw = ImageDraw.Draw(qr_card)
    c_draw.rectangle([(0, 0), (comp_w, 40)], fill=(180, 40, 60))
    c_draw.text((20, 10), "Scan to Authenticate Identity", fill=(255, 255, 255))
    
    # Paste QR in center
    qr_w, qr_h = qr_img.size
    qr_card.paste(qr_img, ((comp_w - qr_w) // 2, 60))
    c_draw.text((50, 450), "Use your mobile camera to scan and confirm login.", fill=(50, 50, 50))

    qr_path = FIXTURES_DIR / "qr_phish.png"
    qr_card.save(qr_path, "PNG")
    print(f"  [Created] {qr_path.name} ({qr_path.stat().st_size:,} bytes)")

    # 3. plain_photo.jpg (Scenic photo with no text, no QR code)
    photo = Image.new("RGB", (400, 400), color=(135, 206, 235))
    p_draw = ImageDraw.Draw(photo)
    p_draw.ellipse([(280, 40), (360, 120)], fill=(255, 223, 0))  # sun
    p_draw.ellipse([(-50, 250), (450, 550)], fill=(34, 139, 34))  # rolling hill
    photo_path = FIXTURES_DIR / "plain_photo.jpg"
    photo.save(photo_path, "JPEG", quality=95)
    print(f"  [Created] {photo_path.name} ({photo_path.stat().st_size:,} bytes)")

    # 4. corrupt.png (Bad magic bytes)
    corrupt_path = FIXTURES_DIR / "corrupt.png"
    with open(corrupt_path, "wb") as f:
        # Invalid header: not 89 50 4E 47 0D 0A 1A 0A
        f.write(b"CORRUPT_NOT_A_REAL_PNG_DATA_HEADER\x00\x01\x02\x03\x04")
    print(f"  [Created] {corrupt_path.name} ({corrupt_path.stat().st_size:,} bytes)")

    # 5. oversized.png (Exceeds 5 MB limit)
    # Create large uncompressed raw image or pad with bytes
    oversized_path = FIXTURES_DIR / "oversized.png"
    # Create valid large PNG (~2600x2600 random noise) or pad valid PNG with metadata
    img_large = Image.new("RGB", (2200, 2200), color=(240, 240, 240))
    l_draw = ImageDraw.Draw(img_large)
    for x in range(0, 2200, 40):
        for y in range(0, 2200, 40):
            l_draw.rectangle([(x, y), (x + 35, y + 35)], fill=((x * 7) % 256, (y * 11) % 256, (x + y) % 256))
    
    # Save uncompressed PNG
    img_large.save(oversized_path, "PNG", compress_level=0)
    # Ensure it exceeds 5 * 1024 * 1024 bytes (5,242,880)
    current_size = oversized_path.stat().st_size
    if current_size < 5_300_000:
        # Append safe dummy ancillary chunk to exceed 5 MB
        with open(oversized_path, "ab") as f:
            f.write(b"\x00" * (5_300_000 - current_size))
    print(f"  [Created] {oversized_path.name} ({oversized_path.stat().st_size:,} bytes)")


if __name__ == "__main__":
    generate_fixtures()

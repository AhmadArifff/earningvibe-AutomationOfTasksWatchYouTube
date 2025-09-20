import cv2
import pytesseract
import numpy as np
import re
from PIL import Image

# Path tesseract (Windows)
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def preprocess(path):
    img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise FileNotFoundError(f"File {path} not found")
    
    # Invert → biar teks jadi hitam di atas putih (lebih gampang buat contour)
    _, th = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Hapus garis panjang pakai morfologi
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30,1))
    cleaned = cv2.morphologyEx(th, cv2.MORPH_OPEN, kernel, iterations=1)

    # Combine: teks = th - garis
    final = cv2.subtract(th, cleaned)

    return final

def segment_and_ocr(processed):
    # Cari kontur (karakter)
    contours, _ = cv2.findContours(processed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    chars = []

    for cnt in contours:
        x,y,w,h = cv2.boundingRect(cnt)
        if h > 20 and w > 5:  # filter noise kecil
            char_img = processed[y:y+h, x:x+w]
            chars.append((x, char_img))

    # Urut dari kiri ke kanan
    chars = sorted(chars, key=lambda x: x[0])

    result = ""
    for _, ch in chars:
        # Resize biar OCR lebih jelas
        ch = cv2.resize(ch, (50, 50), interpolation=cv2.INTER_CUBIC)
        pil_img = Image.fromarray(ch)

        config = "-c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 --psm 10 --oem 3"
        text = pytesseract.image_to_string(pil_img, config=config)
        text = re.sub(r'[^A-Z0-9]', '', text)  # hanya huruf/angka
        result += text

    return result

# --- Main ---
input_path = "captcha_1758067989154.png"   # captcha kamu
processed = preprocess(input_path)
cv2.imwrite("processed_clean.png", processed)
print("📂 Preprocessed image saved as processed_clean.png")

output = segment_and_ocr(processed)
print("✨ Final Captcha OCR Output:", output)

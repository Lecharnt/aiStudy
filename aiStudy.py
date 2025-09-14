import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import cv2
import numpy as np
import os

# ✅ Update this path to point directly to tesseract.exe
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\lft05\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# 📌 OCR Configuration: Optimized for text and math symbols
custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ+-*/=().% '

def preprocess_image(pil_img):
    """
    Convert a PIL image to grayscale and apply binary thresholding.
    This improves OCR accuracy by reducing noise and enhancing text.
    """
    img = np.array(pil_img)
    img = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return Image.fromarray(img)

def ocr_every_page(pdf_path, output_folder="ocr_pages"):
    """
    Perform OCR on each page of a PDF and return the extracted text.                                  
    Saves temporary page images in `output_folder`.
    """
    if not os.path.exists(pdf_path) or not pdf_path.lower().endswith(".pdf"):
        raise FileNotFoundError(f"❌ File not found or not a PDF: {pdf_path}")

    os.makedirs(output_folder, exist_ok=True)
    doc = fitz.open(pdf_path)
    all_text = ""

    for i, page in enumerate(doc):
        print(f"🖼️ OCR on Page {i + 1}")
        pix = page.get_pixmap(dpi=500)
        img_path = os.path.join(output_folder, f"page_{i + 1}.png")
        pix.save(img_path)

        pil_image = Image.open(img_path)
        clean_image = preprocess_image(pil_image)

        ocr_text = pytesseract.image_to_string(clean_image, config=custom_config)
        all_text += f"\n--- Page {i + 1} ---\n{ocr_text.strip()}\n"

    return all_text

if __name__ == "__main__":
    # 📂 Change these paths to match your setup
    pdf_path = "C:/Users/lft05/OneDrive/Documents/aiStudy/test2.pdf"
    output_file = "C:/Users/lft05/OneDrive/Documents/aiStudy/ocr_only_output.txt"

    try:
        extracted_text = ocr_every_page(pdf_path)

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(extracted_text)

        print(f"\n✅ OCR complete. Output saved to:\n{output_file}")
    except Exception as e:
        print(f"\n❌ Error: {e}")

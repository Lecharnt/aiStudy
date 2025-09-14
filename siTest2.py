# 🧠 AI Math Flashcard Generator with OCR + Gemini + GUI

import fitz  # PyMuPDF
import pytesseract
from PIL import Image, ImageTk
import cv2
import numpy as np
import requests
import time
import tkinter as tk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from io import BytesIO
import os
import re

# Tesseract setup
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\lft05\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'

# OCR configs
config_psm4 = r'--oem 3 --psm 4'
config_psm11 = r'--oem 3 --psm 11'

# Gemini API key (Use env var in production)
GEMINI_API_KEY = "AIzaSyA0JAvz2tI1l7Qecuz-TPSoCBmWn7_6cHM"
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"

class FlashCard:
    def __init__(self, question_text, answer_text):
        self.question = question_text
        self.answer = answer_text

# Image Preprocessing
def preprocess_image(pil_img):
    img = np.array(pil_img)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((2, 2), np.uint8)
    processed = cv2.dilate(thresh, kernel, iterations=1)
    processed = cv2.erode(processed, kernel, iterations=1)
    return Image.fromarray(processed)

# OCR each PDF page
def ocr_every_page(pdf_path):
    doc = fitz.open(pdf_path)
    all_text = []
    for i, page in enumerate(doc):
        try:
            vector_text = page.get_text("text")
            if vector_text.strip():
                all_text.append(vector_text.strip())
                continue
            pix = page.get_pixmap(dpi=200)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            clean_img = preprocess_image(img)
            ocr1 = pytesseract.image_to_string(clean_img, config=config_psm4)
            ocr2 = pytesseract.image_to_string(clean_img, config=config_psm11)
            score1 = sum(ocr1.count(c) for c in "+-*/=∫∑π^")
            score2 = sum(ocr2.count(c) for c in "+-*/=∫∑π^")
            final = ocr1 if score1 >= score2 else ocr2
            all_text.append(final.strip())
        except Exception as e:
            print(f"[ERROR] OCR failed on page {i + 1}: {e}")
            all_text.append("")
    return all_text

# Fix missing spacing
def insert_spaces_if_needed(text):
    lines = text.splitlines()
    fixed_lines = []
    for line in lines:
        if '\\(' in line and '\\)' in line:
            parts = []
            last_end = 0
            for match in re.finditer(r'\\\(.*?\\\)', line):
                start, end = match.span()
                before_text = line[last_end:start]
                if before_text and ' ' not in before_text and re.match(r'^[A-Za-z]+$', before_text):
                    words = re.findall(r'[A-Z][a-z]*|[a-z]+', before_text)
                    before_text = ' '.join(words)
                parts.append(before_text)
                parts.append(line[start:end])
                last_end = end
            after_text = line[last_end:]
            if after_text and ' ' not in after_text and re.match(r'^[A-Za-z]+$', after_text):
                words = re.findall(r'[A-Z][a-z]*|[a-z]+', after_text)
                after_text = ' '.join(words)
            parts.append(after_text)
            fixed_lines.append(''.join(parts))
        elif len(line) > 20 and ' ' not in line:
            if re.match(r'^[A-Za-z]+$', line):
                words = re.findall(r'[A-Z][a-z]*|[a-z]+', line)
                fixed_lines.append(' '.join(words))
            else:
                spaced = ' '.join(re.findall('.{1,10}', line))
                fixed_lines.append(spaced)
        else:
            fixed_lines.append(line)
    return '\n'.join(fixed_lines)

# Call Gemini API
def query_gemini(prompt):
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        r = requests.post(GEMINI_API_URL, headers=headers, json=payload)
        r.raise_for_status()
        return r.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        print(f"[ERROR] Gemini call failed: {e}")
        return ""

# Chunking

def chunk_text(text, max_tokens=1800):
    chunks, chunk, count = [], "", 0
    for para in text.split("\n"):
        tlen = len(para.split())
        if count + tlen > max_tokens:
            chunks.append(chunk.strip())
            chunk, count = para + "\n", tlen
        else:
            chunk += para + "\n"
            count += tlen
    if chunk.strip():
        chunks.append(chunk.strip())
    return chunks

# Generate flashcards

def generate_flashcards(ocr_pages):
    full_text = "\n".join(ocr_pages)
    chunks = chunk_text(full_text)
    flashcards = []
    for chunk_idx, chunk in enumerate(chunks):
        prompt = f"""
You are a helpful math tutor AI.

Given the following scanned math content, create 5 distinct simple practice problems related to the subject.

- Format each problem as:  
  Q: [problem statement]  
  A: [answer]  
- Use `\\(...\\)` for math expressions.  
- Use proper spacing and punctuation.  
- Do NOT write any filler text like "You have reached the end".
- Each Q:/A: pair should be on a single line.

Content to base problems on:  
{chunk}
"""

        print(f"[INFO] Generating for chunk {chunk_idx+1}...")
        res = query_gemini(prompt)
        print(f"[DEBUG] Raw response: {res[:100]}...")  # Print first 100 chars for debugging
        res = insert_spaces_if_needed(res)
        lines = res.strip().splitlines()
        print(f"[DEBUG] Found {len(lines)} lines in response")
        
        # Process lines to handle both single-line and multi-line Q/A formats
        line_idx = 0
        chunk_flashcards = 0
        while line_idx < len(lines):
            line = lines[line_idx].strip()
            
            # Case 1: Q: and A: on the same line
            if line.startswith("Q:") and "A:" in line:
                parts = line.split("A:")
                q = parts[0][2:].strip()
                a = parts[1].strip()
                flashcards.append(FlashCard(q, a))
                chunk_flashcards += 1
                print(f"[DEBUG] Found flashcard (case 1): Q: {q[:30]}...")
                line_idx += 1
            
            # Case 2: Q: on one line, A: on the next line
            elif line.startswith("Q:") and line_idx + 1 < len(lines) and lines[line_idx+1].strip().startswith("A:"):
                q = line[2:].strip()
                a = lines[line_idx+1][2:].strip()
                flashcards.append(FlashCard(q, a))
                chunk_flashcards += 1
                print(f"[DEBUG] Found flashcard (case 2): Q: {q[:30]}...")
                line_idx += 2
            
            # Case 3: Line starts with a number followed by Q:
            elif re.match(r'^\d+\)\s*Q:', line) or re.match(r'^\d+\.\s*Q:', line):
                # Extract the Q: part
                q_part = re.sub(r'^\d+\)\s*Q:|^\d+\.\s*Q:', '', line).strip()
                
                # Check if A: is on the same line
                    q = q_part
                    a = lines[i+1][2:].strip()
                    flashcards.append(FlashCard(q, a))
                    i += 1
                
                i += 1
            else:
                i += 1
                
        print(f"[INFO] Generated {len(flashcards)} flashcards from chunk {i+1}")
        time.sleep(1)
    return flashcards

# GUI

def run_gui():
    root = tk.Tk()
    root.title("📘 Math Flashcard AI Generator")
    root.geometry("1000x700")

    widgets = []
    flashcards = []
    current_index = [0]

    top_frame = tk.Frame(root)
    top_frame.pack(pady=10)

    text_frame = tk.Frame(root)
    text_frame.pack(fill=tk.BOTH, expand=True)

    question_label = tk.Label(text_frame, text="", font=("Arial", 14), wraplength=800, justify='left')
    question_label.pack(pady=20)

    answer_entry = tk.Entry(text_frame, font=("Arial", 14), width=60)
    answer_entry.pack(pady=5)

    feedback_label = tk.Label(text_frame, text="", font=("Arial", 12), fg="green")
    feedback_label.pack(pady=10)

    def show_flashcard(index):
        if 0 <= index < len(flashcards):
            question_label.config(text=flashcards[index].question)
            answer_entry.delete(0, tk.END)
            feedback_label.config(text="")
        else:
            question_label.config(text="🎉 You've reached the end!")
            answer_entry.pack_forget()
            feedback_label.pack_forget()
            next_btn.pack_forget()
            submit_btn.pack_forget()

    def check_answer():
        user_input = answer_entry.get().strip()
        correct_answer = flashcards[current_index[0]].answer
        if user_input.lower() == correct_answer.lower():
            feedback_label.config(text="✅ Correct!", fg="green")
        else:
            feedback_label.config(text=f"❌ Wrong. Answer: {correct_answer}", fg="red")

    def next_card():
        current_index[0] += 1
        show_flashcard(current_index[0])

    def select_pdf():
        file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
        if not file_path:
            return
        question_label.config(text="🔍 Running OCR...")
        root.update()
        ocr_text = ocr_every_page(file_path)
        question_label.config(text="⚙️ Generating flashcards...")
        root.update()
        nonlocal flashcards
        flashcards = generate_flashcards(ocr_text)
        current_index[0] = 0
        show_flashcard(current_index[0])

    btn_frame = tk.Frame(top_frame)
    btn_frame.pack()

    tk.Button(btn_frame, text="📂 Select PDF", command=select_pdf).pack(side=tk.LEFT, padx=5)

    submit_btn = tk.Button(btn_frame, text="✅ Check Answer", command=check_answer)
    submit_btn.pack(side=tk.LEFT, padx=5)

    next_btn = tk.Button(btn_frame, text="➡️ Next", command=next_card)
    next_btn.pack(side=tk.LEFT, padx=5)

    root.mainloop()

if __name__ == "__main__":
    run_gui()

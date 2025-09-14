import tkinter as tk
from tkinter import filedialog
from transformers import pipeline
import fitz  # PyMuPDF
from nltk.tokenize import sent_tokenize
import threading

# Load model once globally
print("[INFO] Loading model...")
question_gen = pipeline("text2text-generation", model="iarfmoose/t5-base-question-generator")

# Smart sentence-aware chunking
def split_text_smart(text, max_chars=500):
    sentences = sent_tokenize(text)
    chunks, current_chunk = [], ""
    for sent in sentences:
        if len(current_chunk) + len(sent) <= max_chars:
            current_chunk += " " + sent
        else:
            chunks.append(current_chunk.strip())
            current_chunk = sent
    if current_chunk:
        chunks.append(current_chunk.strip())
    return chunks

# Create practice questions page-by-page
def create_practice_test(pdf_path, max_pages=1000, max_questions=100):
    print("[INFO] Opening PDF...")
    doc = fitz.open(pdf_path)
    questions = []

    total_pages = min(len(doc), max_pages)
    question_count = 0

    for page_num in range(total_pages):
        if question_count >= max_questions:
            break

        page = doc[page_num]
        text = page.get_text()

        if not text.strip():
            continue

        chunks = split_text_smart(text)

        for chunk in chunks:
            if question_count >= max_questions:
                break
            input_text = "generate questions: " + chunk
            try:
                output = question_gen(input_text, max_length=64, num_return_sequences=1)[0]['generated_text']
                questions.append(f"Page {page_num+1}: {output}")
                question_count += 1
            except Exception as e:
                questions.append(f"Page {page_num+1}: [Error generating question: {e}]")

    return questions

# GUI functions
def open_pdf():
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")])
    if file_path:
        output_text.delete(1.0, tk.END)
        output_text.insert(tk.END, "[INFO] Processing PDF. Please wait...\n")
        root.update()
        threading.Thread(target=process_pdf, args=(file_path,)).start()

def process_pdf(file_path):
    questions = create_practice_test(file_path)
    display_questions(questions)

def display_questions(questions):
    output_text.delete(1.0, tk.END)
    for i, q in enumerate(questions, 1):
        output_text.insert(tk.END, f"Question {i}:\n{q}\n\n")

# Tkinter GUI setup
root = tk.Tk()
root.title("AI Study Tool")

frame = tk.Frame(root)
frame.pack(padx=10, pady=10)

open_button = tk.Button(frame, text="Open PDF", command=open_pdf)
open_button.pack()

output_text = tk.Text(frame, width=100, height=40)
output_text.pack()

root.mainloop()

import re
import time
import pytesseract
import cv2
import numpy as np
import requests
from PIL import Image
import fitz  # PyMuPDF
from datetime import datetime, timedelta

class FlashcardGenerator:
    def __init__(self):
        self.config_psm4 = r'--oem 3 --psm 4'
        self.config_psm11 = r'--oem 3 --psm 11'
        self.gemini_api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=AIzaSyA0JAvz2tI1l7Qecuz-TPSoCBmWn7_6cHM"

    def preprocess_image(self, image):
        """Enhance image for better OCR results"""
        gray = cv2.cvtColor(np.array(image), cv2.COLOR_BGR2GRAY)
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                     cv2.THRESH_BINARY, 11, 2)
        denoised = cv2.fastNlMeansDenoising(thresh, None, 10, 7, 21)
        return Image.fromarray(denoised)

    def ocr_every_page(self, pdf_path):
        """Extract text from PDF using OCR"""
        doc = fitz.open(pdf_path)
        full_text = ""
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            pix = page.get_pixmap()
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            processed_img = self.preprocess_image(img)
            text = pytesseract.image_to_string(processed_img, config=self.config_psm11)
            full_text += f"\n\nPAGE {page_num + 1}:\n{text}"
        
        doc.close()
        return full_text

    def query_gemini(self, prompt):
        """Query Gemini API for flashcard generation"""
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topP": 0.9,
                "maxOutputTokens": 2000
            }
        }
        
        try:
            response = requests.post(self.gemini_api_url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            return result['candidates'][0]['content']['parts'][0]['text']
        except Exception as e:
            print(f"Gemini API error: {e}")
            return None

    def generate_flashcards(self, text, topic="Imported"):
        """Generate flashcards from text using AI"""
        chunks = self.chunk_text(text)
        flashcards = []
        
        for chunk in chunks:
            prompt = f"""Convert this study material into 5-10 high-quality flashcards. For each concept:
            
            Q: [Clear, specific question]
            A: [Concise, accurate answer]
            
            Focus on key concepts, formulas, and relationships. For math problems, include both the question and step-by-step solution.
            
            Material:
            {chunk}
            
            Return ONLY the flashcards in this exact format:
            Q: [question]
            A: [answer]
            [blank line]
            Q: [question]
            A: [answer]"""
            
            result = self.query_gemini(prompt)
            if result:
                cards = self.parse_flashcards(result)
                for card in cards:
                    card.topic = topic
                flashcards.extend(cards)
        
        return flashcards

    def chunk_text(self, text, max_length=2000):
        """Split text into manageable chunks for API"""
        sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_length:
                current_chunk += sentence + " "
            else:
                chunks.append(current_chunk)
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks

    def parse_flashcards(self, text):
        """Parse Q/A pairs from Gemini response"""
        cards = []
        current_q = None
        
        for line in text.split('\n'):
            line = line.strip()
            if line.startswith('Q:'):
                current_q = line[2:].strip()
            elif line.startswith('A:') and current_q:
                cards.append(FlashCard(current_q, line[2:].strip()))
                current_q = None
        
        return cards
class FlashCard:
    def __init__(self, question_text, answer_text, topic="General"):
        self.id = int(time.time() * 1000)
        self.question = question_text
        self.answer = answer_text
        self.topic = topic
        self.difficulty = "medium"
        self.next_review = datetime.now().isoformat()
        self.interval = 1
        self.repetitions = 0
        self.ease_factor = 2.5

    def __repr__(self):
        return f"<FlashCard Q: {self.question[:30]}... A: {self.answer[:30]}...>"

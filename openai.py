import json
import os
import random
import re
import time
from datetime import datetime, timedelta
from io import BytesIO
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
import fitz  # PyMuPDF
import pytesseract
import cv2
import numpy as np
import requests

# Configuration
pytesseract.pytesseract.tesseract_cmd = r'C:\Users\lft05\AppData\Local\Programs\Tesseract-OCR\tesseract.exe'  # Update this path
GEMINI_API_KEY = "AIzaSyA0JAvz2tI1l7Qecuz-TPSoCBmWn7_6cHM"  # Replace with your actual key
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=AIzaSyA0JAvz2tI1l7Qecuz-TPSoCBmWn7_6cHM"

class Database:
    def __init__(self):
        self.users_file = "users.json"
        self.study_data_file = "study_data.json"
        self.flashcards_file = "flashcards.json"
        self.ensure_files_exist()
    
    def ensure_files_exist(self):
        for file in [self.users_file, self.study_data_file, self.flashcards_file]:
            if not os.path.exists(file):
                with open(file, 'w') as f:
                    json.dump({}, f)
    
    def load_data(self, filename):
        with open(filename, 'r') as f:
            return json.load(f)
    
    def save_data(self, filename, data):
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

class FlashCard:
    def __init__(self, question_text, answer_text, topic="General"):
        self.id = int(time.time() * 1000)  # Unique ID
        self.question = question_text
        self.answer = answer_text
        self.topic = topic
        self.difficulty = "medium"
        self.next_review = datetime.now().isoformat()
        self.interval = 1
        self.repetitions = 0
        self.ease_factor = 2.5

class FlashcardGenerator:
    def __init__(self):
        self.config_psm4 = r'--oem 3 --psm 4'
        self.config_psm11 = r'--oem 3 --psm 11'

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
            response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
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

class FlashcardSystem:
    def __init__(self, user_id):
        self.db = Database()
        self.user_id = user_id
        self.flashcards = self.load_flashcards()
        self.generator = FlashcardGenerator()
    
    def load_flashcards(self):
        data = self.db.load_data(self.db.flashcards_file)
        user_cards = data.get(str(self.user_id), [])
        
        # Convert dicts back to FlashCard objects
        cards = []
        for card_data in user_cards:
            card = FlashCard(card_data['question'], card_data['answer'], card_data.get('topic', 'General'))
            card.id = card_data['id']
            card.difficulty = card_data.get('difficulty', 'medium')
            card.next_review = card_data.get('next_review', datetime.now().isoformat())
            card.interval = card_data.get('interval', 1)
            card.repetitions = card_data.get('repetitions', 0)
            card.ease_factor = card_data.get('ease_factor', 2.5)
            cards.append(card)
        
        return cards
    
    def save_flashcards(self):
        data = self.db.load_data(self.db.flashcards_file)
        
        # Convert FlashCard objects to dicts
        cards_data = []
        for card in self.flashcards:
            cards_data.append({
                'id': card.id,
                'question': card.question,
                'answer': card.answer,
                'topic': card.topic,
                'difficulty': card.difficulty,
                'next_review': card.next_review,
                'interval': card.interval,
                'repetitions': card.repetitions,
                'ease_factor': card.ease_factor
            })
        
        data[str(self.user_id)] = cards_data
        self.db.save_data(self.db.flashcards_file, data)
    
    def create_flashcard(self, question, answer, topic="General"):
        new_card = FlashCard(question, answer, topic)
        self.flashcards.append(new_card)
        self.save_flashcards()
        return new_card
    
    def get_due_flashcards(self):
        due_cards = []
        now = datetime.now()
        
        for card in self.flashcards:
            review_time = datetime.fromisoformat(card.next_review)
            if review_time <= now:
                due_cards.append(card)
        
        return due_cards
    
    def update_flashcard_after_review(self, card_id, performance):
        """Performance: 0 (forgot), 1 (hard), 2 (good), 3 (easy)"""
        card = next((c for c in self.flashcards if c.id == card_id), None)
        if not card:
            return False
        
        if performance == 0:  # Forgot
            card.interval = 1
            card.repetitions = 0
        else:
            card.repetitions += 1
            
            if card.repetitions == 1:
                card.interval = 1
            elif card.repetitions == 2:
                card.interval = 6
            else:
                card.interval = card.interval * card.ease_factor
            
            if performance == 1:  # Hard
                card.ease_factor = max(1.3, card.ease_factor - 0.15)
            elif performance == 3:  # Easy
                card.ease_factor = min(2.5, card.ease_factor + 0.15)
        
        next_review = datetime.now() + timedelta(days=card.interval)
        card.next_review = next_review.isoformat()
        
        self.save_flashcards()
        return True
    
    def generate_from_pdf(self, pdf_path, topic="Imported"):
        try:
            text = self.generator.ocr_every_page(pdf_path)
            new_cards = self.generator.generate_flashcards(text, topic)
            
            for card in new_cards:
                self.flashcards.append(card)
            
            self.save_flashcards()
            return len(new_cards)
        except Exception as e:
            print(f"Error processing PDF: {e}")
            return 0

class StudyMasterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 AI Study Master")
        self.root.geometry("1200x800")
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        self.db = Database()
        self.current_user = None
        self.flashcard_system = None
        self.study_plan = None
        
        self.create_widgets()
        self.show_login_screen()
    
    def configure_styles(self):
        self.style.configure('TFrame', background='#f0f0f0')
        self.style.configure('TLabel', background='#f0f0f0', font=('Arial', 11))
        self.style.configure('TButton', font=('Arial', 10), padding=5)
        self.style.configure('Header.TLabel', font=('Arial', 14, 'bold'))
        self.style.configure('Success.TLabel', foreground='green')
        self.style.configure('Error.TLabel', foreground='red')
        self.style.map('TButton',
                      background=[('active', '#e0e0e0'), ('pressed', '#d0d0d0')])
    
    def create_widgets(self):
        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Login screen widgets
        self.login_frame = ttk.Frame(self.main_frame)
        self.register_frame = ttk.Frame(self.main_frame)
        
        # Main app widgets
        self.dashboard_frame = ttk.Frame(self.main_frame)
        self.flashcards_frame = ttk.Frame(self.main_frame)
        self.study_plan_frame = ttk.Frame(self.main_frame)
        
        # Initialize all frames
        self.init_login_screen()
        self.init_register_screen()
        self.init_dashboard()
        self.init_flashcards_screen()
        self.init_study_plan_screen()
    
    def init_login_screen(self):
        ttk.Label(self.login_frame, text="Study Master Login", style='Header.TLabel').pack(pady=20)
        
        form_frame = ttk.Frame(self.login_frame)
        form_frame.pack(pady=10)
        
        ttk.Label(form_frame, text="User ID:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.login_id_entry = ttk.Entry(form_frame)
        self.login_id_entry.grid(row=0, column=1, padx=5, pady=5)
        
        button_frame = ttk.Frame(self.login_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Login", command=self.login_user).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Register", command=self.show_register_screen).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Exit", command=self.root.quit).pack(side=tk.LEFT, padx=10)
        
        self.login_status = ttk.Label(self.login_frame, text="", style='Error.TLabel')
        self.login_status.pack(pady=10)
    
    def init_register_screen(self):
        ttk.Label(self.register_frame, text="Register New Account", style='Header.TLabel').pack(pady=20)
        
        form_frame = ttk.Frame(self.register_frame)
        form_frame.pack(pady=10)
        
        ttk.Label(form_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        self.reg_username_entry = ttk.Entry(form_frame)
        self.reg_username_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(form_frame, text="Email:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        self.reg_email_entry = ttk.Entry(form_frame)
        self.reg_email_entry.grid(row=1, column=1, padx=5, pady=5)
        
        button_frame = ttk.Frame(self.register_frame)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Register", command=self.register_user).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Back to Login", command=self.show_login_screen).pack(side=tk.LEFT, padx=10)
        
        self.reg_status = ttk.Label(self.register_frame, text="", style='Error.TLabel')
        self.reg_status.pack(pady=10)
    
    def init_dashboard(self):
        ttk.Label(self.dashboard_frame, text="Study Dashboard", style='Header.TLabel').pack(pady=20)
        
        stats_frame = ttk.Frame(self.dashboard_frame)
        stats_frame.pack(pady=20, fill=tk.X)
        
        self.due_cards_label = ttk.Label(stats_frame, text="Due Flashcards: 0")
        self.due_cards_label.pack(side=tk.LEFT, padx=20)
        
        self.upcoming_sessions_label = ttk.Label(stats_frame, text="Upcoming Sessions: 0")
        self.upcoming_sessions_label.pack(side=tk.LEFT, padx=20)
        
        button_frame = ttk.Frame(self.dashboard_frame)
        button_frame.pack(pady=30)
        
        ttk.Button(button_frame, text="Flashcards", command=self.show_flashcards_screen, width=15).pack(pady=10)
        ttk.Button(button_frame, text="Study Plan", command=self.show_study_plan_screen, width=15).pack(pady=10)
        ttk.Button(button_frame, text="Practice Tests", width=15).pack(pady=10)
        ttk.Button(button_frame, text="Logout", command=self.logout, width=15).pack(pady=10)
    
    def init_flashcards_screen(self):
        # Main flashcards screen
        ttk.Label(self.flashcards_frame, text="Flashcards", style='Header.TLabel').pack(pady=10)
        
        # Top control panel
        control_frame = ttk.Frame(self.flashcards_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="Back to Dashboard", command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Add Flashcard", command=self.add_flashcard_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Import from PDF", command=self.import_pdf_dialog).pack(side=tk.LEFT, padx=5)
        
        # Flashcard display area
        self.card_display_frame = ttk.Frame(self.flashcards_frame, relief=tk.RIDGE, borderwidth=2)
        self.card_display_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.card_question = ttk.Label(
            self.card_display_frame, 
            text="Select a flashcard to begin", 
            font=('Arial', 12), 
            wraplength=700,
            justify=tk.CENTER
        )
        self.card_question.pack(pady=50, padx=20, fill=tk.BOTH, expand=True)
        
        self.card_answer = ttk.Label(
            self.card_display_frame, 
            text="", 
            font=('Arial', 11), 
            wraplength=700,
            justify=tk.LEFT
        )
        
        # Bottom control panel
        bottom_frame = ttk.Frame(self.flashcards_frame)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        self.review_buttons_frame = ttk.Frame(bottom_frame)
        self.review_buttons_frame.pack(pady=5)
        
        ttk.Button(bottom_frame, text="Edit", command=self.edit_flashcard_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Delete", command=self.delete_flashcard).pack(side=tk.LEFT, padx=5)
        
        # Status bar
        self.flashcard_status = ttk.Label(
            self.flashcards_frame, 
            text="No flashcards loaded", 
            relief=tk.SUNKEN, 
            anchor=tk.W
        )
        self.flashcard_status.pack(fill=tk.X, pady=5)
    
    def init_study_plan_screen(self):
        ttk.Label(self.study_plan_frame, text="Study Plan", style='Header.TLabel').pack(pady=10)
        
        ttk.Button(self.study_plan_frame, text="Back to Dashboard", command=self.show_dashboard).pack(pady=10)
        
        # Will implement study plan functionality here
        ttk.Label(self.study_plan_frame, text="Study plan features coming soon!").pack(pady=50)
    
    def show_login_screen(self):
        self.hide_all_frames()
        self.login_frame.pack(fill=tk.BOTH, expand=True)
        self.login_id_entry.focus_set()
    
    def show_register_screen(self):
        self.hide_all_frames()
        self.register_frame.pack(fill=tk.BOTH, expand=True)
        self.reg_username_entry.focus_set()
    
    def show_dashboard(self):
        self.hide_all_frames()
        self.update_dashboard_stats()
        self.dashboard_frame.pack(fill=tk.BOTH, expand=True)
    
    def show_flashcards_screen(self):
        self.hide_all_frames()
        self.flashcards_frame.pack(fill=tk.BOTH, expand=True)
        self.load_flashcards_for_display()
    
    def show_study_plan_screen(self):
        self.hide_all_frames()
        self.study_plan_frame.pack(fill=tk.BOTH, expand=True)
    
    def hide_all_frames(self):
        for frame in [
            self.login_frame, 
            self.register_frame, 
            self.dashboard_frame,
            self.flashcards_frame,
            self.study_plan_frame
        ]:
            frame.pack_forget()
    
    def login_user(self):
        user_id = self.login_id_entry.get()
        users = self.db.load_data(self.db.users_file)
        
        if user_id in users:
            self.current_user = int(user_id)
            self.flashcard_system = FlashcardSystem(self.current_user)
            self.show_dashboard()
        else:
            self.login_status.config(text="User ID not found")
    
    def register_user(self):
        username = self.reg_username_entry.get().strip()
        email = self.reg_email_entry.get().strip()
        
        if not username or not email:
            self.reg_status.config(text="Please fill all fields")
            return
        
        users = self.db.load_data(self.db.users_file)
        user_id = max(map(int, users.keys())) + 1 if users else 1
        
        users[str(user_id)] = {
            'username': username,
            'email': email,
            'created_at': datetime.now().isoformat()
        }
        self.db.save_data(self.db.users_file, users)
        
        self.reg_status.config(text=f"Registration successful! Your ID is: {user_id}", style='Success.TLabel')
        self.reg_username_entry.delete(0, tk.END)
        self.reg_email_entry.delete(0, tk.END)
    
    def logout(self):
        self.current_user = None
        self.flashcard_system = None
        self.show_login_screen()
    
    def update_dashboard_stats(self):
        if not self.current_user:
            return
            
        due_cards = len(self.flashcard_system.get_due_flashcards())
        self.due_cards_label.config(text=f"Due Flashcards: {due_cards}")
        
        # Placeholder for study sessions
        self.upcoming_sessions_label.config(text="Upcoming Sessions: 0")
    
    def load_flashcards_for_display(self):
        if not self.flashcard_system:
            return
            
        self.current_card_index = 0
        self.current_card = None
        self.showing_answer = False
        
        due_cards = self.flashcard_system.get_due_flashcards()
        if due_cards:
            self.current_card = due_cards[0]
            self.display_flashcard()
        else:
            self.card_question.config(text="No flashcards due for review")
            self.card_answer.pack_forget()
            self.hide_review_buttons()
        
        self.update_flashcard_status()
    
    def display_flashcard(self):
        if not self.current_card:
            return
            
        self.card_question.config(text=self.current_card.question)
        self.card_answer.config(text=self.current_card.answer)
        
        if self.showing_answer:
            self.card_answer.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
            self.show_review_buttons()
        else:
            self.card_answer.pack_forget()
            ttk.Button(
                self.card_display_frame, 
                text="Show Answer", 
                command=self.show_answer
            ).pack(pady=20)
    
    def show_answer(self):
        self.showing_answer = True
        self.display_flashcard()
    
    def show_review_buttons(self):
        for widget in self.review_buttons_frame.winfo_children():
            widget.destroy()
        
        buttons = [
            ("❌ Forgot", 0),
            ("😓 Hard", 1),
            ("😊 Good", 2),
            ("🎯 Easy", 3)
        ]
        
        for text, rating in buttons:
            ttk.Button(
                self.review_buttons_frame,
                text=text,
                command=lambda r=rating: self.rate_flashcard(r)
            ).pack(side=tk.LEFT, padx=5)
    
    def hide_review_buttons(self):
        for widget in self.review_buttons_frame.winfo_children():
            widget.destroy()
    
    def rate_flashcard(self, rating):
        if not self.current_card:
            return
            
        self.flashcard_system.update_flashcard_after_review(self.current_card.id, rating)
        self.load_flashcards_for_display()
    
    def update_flashcard_status(self):
        if not self.flashcard_system:
            return
            
        total = len(self.flashcard_system.flashcards)
        due = len(self.flashcard_system.get_due_flashcards())
        self.flashcard_status.config(text=f"Total: {total} | Due: {due}")
    
    def add_flashcard_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add New Flashcard")
        dialog.geometry("500x300")
        
        ttk.Label(dialog, text="Question:").pack(pady=(10, 0))
        question_entry = tk.Text(dialog, height=5, width=60)
        question_entry.pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="Answer:").pack()
        answer_entry = tk.Text(dialog, height=5, width=60)
        answer_entry.pack(padx=10, pady=5)
        
        ttk.Label(dialog, text="Topic:").pack()
        topic_entry = ttk.Entry(dialog)
        topic_entry.pack(pady=5)
        topic_entry.insert(0, "General")
        
        def save_flashcard():
            question = question_entry.get("1.0", tk.END).strip()
            answer = answer_entry.get("1.0", tk.END).strip()
            topic = topic_entry.get().strip()
            
            if question and answer:
                self.flashcard_system.create_flashcard(question, answer, topic)
                self.load_flashcards_for_display()
                dialog.destroy()
            else:
                messagebox.showwarning("Missing Fields", "Please enter both question and answer")
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Save", command=save_flashcard).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        
        question_entry.focus_set()
    
    def edit_flashcard_dialog(self):
        if not self.current_card:
            return
            
        dialog = tk.Toplevel(self.root)
        dialog.title("Edit Flashcard")
        dialog.geometry("500x300")
        
        ttk.Label(dialog, text="Question:").pack(pady=(10, 0))
        question_entry = tk.Text(dialog, height=5, width=60)
        question_entry.pack(padx=10, pady=5)
        question_entry.insert("1.0", self.current_card.question)
        
        ttk.Label(dialog, text="Answer:").pack()
        answer_entry = tk.Text(dialog, height=5, width=60)
        answer_entry.pack(padx=10, pady=5)
        answer_entry.insert("1.0", self.current_card.answer)
        
        ttk.Label(dialog, text="Topic:").pack()
        topic_entry = ttk.Entry(dialog)
        topic_entry.pack(pady=5)
        topic_entry.insert(0, self.current_card.topic)
        
        def save_changes():
            self.current_card.question = question_entry.get("1.0", tk.END).strip()
            self.current_card.answer = answer_entry.get("1.0", tk.END).strip()
            self.current_card.topic = topic_entry.get().strip()
            
            self.flashcard_system.save_flashcards()
            self.display_flashcard()
            dialog.destroy()
        
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Save", command=save_changes).pack(side=tk.LEFT, padx=10)
        ttk.Button(button_frame, text="Cancel", command=dialog.destroy).pack(side=tk.LEFT, padx=10)
        
        question_entry.focus_set()
    
    def delete_flashcard(self):
        if not self.current_card:
            return
            
        if messagebox.askyesno("Confirm Delete", "Delete this flashcard?"):
            self.flashcard_system.flashcards = [
                card for card in self.flashcard_system.flashcards 
                if card.id != self.current_card.id
            ]
            self.flashcard_system.save_flashcards()
            self.load_flashcards_for_display()
    
    def import_pdf_dialog(self):
        file_path = filedialog.askopenfilename(
            title="Select PDF File",
            filetypes=[("PDF Files", "*.pdf")]
        )
        
        if not file_path:
            return
            
        topic = simpledialog.askstring(
            "Enter Topic", 
            "What topic is this PDF about?", 
            initialvalue="Imported"
        )
        
        if topic is None:  # User cancelled
            return
            
        # Show progress dialog
        progress = tk.Toplevel(self.root)
        progress.title("Processing PDF")
        progress.geometry("400x150")
        
        ttk.Label(progress, text="Processing PDF file...").pack(pady=20)
        progress_bar = ttk.Progressbar(progress, mode='indeterminate')
        progress_bar.pack(pady=10, padx=20, fill=tk.X)
        progress_bar.start()
        
        def process_pdf():
            try:
                count = self.flashcard_system.generate_from_pdf(file_path, topic)
                progress.destroy()
                messagebox.showinfo(
                    "Import Complete", 
                    f"Successfully generated {count} flashcards from the PDF"
                )
                self.load_flashcards_for_display()
            except Exception as e:
                progress.destroy()
                messagebox.showerror(
                    "Import Error", 
                    f"Failed to process PDF:\n{str(e)}"
                )
        
        # Run processing in background
        self.root.after(100, process_pdf)

if __name__ == "__main__":
    root = tk.Tk()
    app = StudyMasterApp(root)
    root.mainloop()
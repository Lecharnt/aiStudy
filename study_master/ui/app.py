import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime
import json
import os
import random
import math

# Import services and views
from models.database import Database
from services.flashcard_system import FlashcardSystem
from services.mindmap_service import MindMapService
from ui.mindmap_view import MindMapView

class StudyMasterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🧠 AI Study Master")
        self.root.geometry("1200x800")
        
        # Initialize services
        self.db = Database()
        self.current_user = None
        self.flashcard_system = None
        self.mindmap_service = None
        
        # UI styling
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        
        # Create widgets
        self.create_widgets()
        
        # Show login screen initially
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
        
        # Initialize all screens
        self.login_frame = ttk.Frame(self.main_frame)
        self.register_frame = ttk.Frame(self.main_frame)
        self.dashboard_frame = ttk.Frame(self.main_frame)
        self.flashcards_frame = ttk.Frame(self.main_frame)
        self.study_plan_frame = ttk.Frame(self.main_frame)
        self.typed_test_frame = ttk.Frame(self.main_frame)
        
        # Initialize screen components
        self.init_login_screen()
        self.init_register_screen()
        self.init_dashboard()
        self.init_flashcards_screen()
        self.init_study_plan_screen()
        self.init_typed_test_screen()
        
        # Initialize mind map view
        self.mindmap_view = MindMapView(
            self.main_frame,
            None,  # Will be set after login
            self.start_flashcard_session
        )
    
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
        ttk.Button(button_frame, text="Practice Test", command=self.show_typed_test_screen, width=15).pack(pady=10)
        ttk.Button(button_frame, text="Mind Map", command=self.show_mindmap_screen, width=15).pack(pady=10)
        ttk.Button(button_frame, text="Logout", command=self.logout, width=15).pack(pady=10)
    
    def init_flashcards_screen(self):
        ttk.Label(self.flashcards_frame, text="Flashcards", style='Header.TLabel').pack(pady=10)
        
        control_frame = ttk.Frame(self.flashcards_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(control_frame, text="Back to Dashboard", command=self.show_dashboard).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Add Flashcard", command=self.add_flashcard_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(control_frame, text="Import from PDF", command=self.import_pdf_dialog).pack(side=tk.LEFT, padx=5)
        
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
        
        bottom_frame = ttk.Frame(self.flashcards_frame)
        bottom_frame.pack(fill=tk.X, pady=10)
        
        self.review_buttons_frame = ttk.Frame(bottom_frame)
        self.review_buttons_frame.pack(pady=5)
        
        ttk.Button(bottom_frame, text="Edit", command=self.edit_flashcard_dialog).pack(side=tk.LEFT, padx=5)
        ttk.Button(bottom_frame, text="Delete", command=self.delete_flashcard).pack(side=tk.LEFT, padx=5)
        
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
        ttk.Label(self.study_plan_frame, text="Study plan features coming soon!").pack(pady=50)
    
    def init_typed_test_screen(self):
        ttk.Label(self.typed_test_frame, text="Typed Practice Test", style='Header.TLabel').pack(pady=10)
        ttk.Button(self.typed_test_frame, text="Back to Dashboard", command=self.show_dashboard).pack(pady=10)
        ttk.Label(self.typed_test_frame, text="Typed test features coming soon!").pack(pady=50)
    
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
    
    def show_typed_test_screen(self):
        self.hide_all_frames()
        self.typed_test_frame.pack(fill=tk.BOTH, expand=True)
    
    def show_mindmap_screen(self):
        self.hide_all_frames()
        self.mindmap_view.show()
    
    def hide_all_frames(self):
        for frame in [
            self.login_frame, 
            self.register_frame, 
            self.dashboard_frame,
            self.flashcards_frame,
            self.study_plan_frame,
            self.typed_test_frame
        ]:
            frame.pack_forget()
        
        self.mindmap_view.hide()
    
    def login_user(self):
        user_id = self.login_id_entry.get()
        users = self.db.load_data(self.db.users_file)
        
        if user_id in users:
            self.current_user = int(user_id)
            self.flashcard_system = FlashcardSystem(self.current_user)
            self.mindmap_service = MindMapService(self.flashcard_system)
            self.mindmap_view.service = self.mindmap_service
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
        self.mindmap_service = None
        self.show_login_screen()
    
    def update_dashboard_stats(self):
        if not self.current_user:
            return
            
        due_cards = len(self.flashcard_system.get_due_flashcards())
        self.due_cards_label.config(text=f"Due Flashcards: {due_cards}")
        
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
        # Clear the display frame completely
        for widget in self.card_display_frame.winfo_children():
            widget.destroy()
        
        if not self.current_card:
            return
            
        # Recreate question label
        self.card_question = ttk.Label(
            self.card_display_frame, 
            text=self.current_card.question, 
            font=('Arial', 12), 
            wraplength=700,
            justify=tk.CENTER
        )
        self.card_question.pack(pady=50, padx=20, fill=tk.BOTH, expand=True)
        
        if self.showing_answer:
            # Recreate answer label
            self.card_answer = ttk.Label(
                self.card_display_frame, 
                text=self.current_card.answer, 
                font=('Arial', 11), 
                wraplength=700,
                justify=tk.LEFT
            )
            self.card_answer.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
            self.show_review_buttons()
        else:
            # Create Show Answer button
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
        
        if topic is None:
            return
            
        progress = tk.Toplevel(self.root)
        progress.title("Processing PDF")
        progress.geometry("400x150")
        
        ttk.Label(progress, text="Processing PDF file...").pack(pady=20)
        progress_bar = ttk.Progressbar(progress, mode='indeterminate')
        progress_bar.pack(pady=10, padx=20, fill=tk.X)
        progress_bar.start()
        
        def process_pdf():
            try:
                text = self.flashcard_system.generator.ocr_every_page(file_path)
                new_cards = self.flashcard_system.generator.generate_flashcards(text, topic)
                
                for card in new_cards:
                    self.flashcard_system.flashcards.append(card)
                
                self.flashcard_system.save_flashcards()
                progress.destroy()
                messagebox.showinfo(
                    "Import Complete", 
                    f"Successfully generated {len(new_cards)} flashcards from the PDF"
                )
                self.load_flashcards_for_display()
            except Exception as e:
                progress.destroy()
                messagebox.showerror(
                    "Import Error", 
                    f"Failed to process PDF:\n{str(e)}"
                )
        
        self.root.after(100, process_pdf)
    
    def start_flashcard_session(self, cards):
        """Start a flashcard session with specific cards"""
        if not cards:
            messagebox.showinfo("No Cards", "No flashcards selected")
            return
        
        # Set the cards to study
        self.flashcard_system.study_session = cards
        self.show_flashcards_screen()

if __name__ == "__main__":
    root = tk.Tk()
    app = StudyMasterApp(root)
    root.mainloop()
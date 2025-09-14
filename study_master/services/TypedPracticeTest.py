import tkinter as tk
from tkinter import ttk, messagebox
from services.flashcard_system import FlashcardSystem

class TypedPracticeTest:
    def __init__(self, root, user_id,flashcards=None):
        self.root = root
        self.root.title("Typed Answer Practice Test")
        self.root.geometry("800x600")
        self.user_id = user_id
        self.flashcard_system = FlashcardSystem(user_id)
        if flashcards:
            self.flashcard_system.flashcards = flashcards
        self.test_cards = []
        self.current_card_index = 0
        self.user_answers = []
        self.setup_ui()
        self.start_new_test()

    def setup_ui(self):
        # Main container
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Question phase UI
        self.question_frame = ttk.Frame(self.main_frame)
        
        self.question_label = ttk.Label(
            self.question_frame,
            text="",
            font=('Arial', 12, 'bold'),
            wraplength=700,
            justify=tk.CENTER
        )
        self.question_label.pack(pady=20)
        
        self.answer_entry = tk.Text(
            self.question_frame,
            height=10,
            width=70,
            wrap=tk.WORD,
            font=('Arial', 11)
        )
        self.answer_entry.pack(pady=20)
        
        self.next_button = ttk.Button(
            self.question_frame,
            text="Next Question",
            command=self.next_question
        )
        self.next_button.pack(pady=10)
        
        # Review phase UI
        self.review_frame = ttk.Frame(self.main_frame)
        
        self.review_label = ttk.Label(
            self.review_frame,
            text="Review Your Answers",
            font=('Arial', 14, 'bold')
        )
        self.review_label.pack(pady=20)
        
        self.review_text = tk.Text(
            self.review_frame,
            height=20,
            width=80,
            wrap=tk.WORD,
            font=('Arial', 11),
            state=tk.DISABLED
        )
        self.review_text.pack(pady=10)
        
        self.rating_frame = ttk.Frame(self.review_frame)
        self.rating_frame.pack(pady=20)
        
        rating_buttons = [
            ("❌ Forgot", 0),
            ("😓 Hard", 1),
            ("😊 Good", 2),
            ("🎯 Easy", 3)
        ]
        
        for text, rating in rating_buttons:
            ttk.Button(
                self.rating_frame,
                text=text,
                command=lambda r=rating: self.rate_card(r)
            ).pack(side=tk.LEFT, padx=5)
        
        self.finish_button = ttk.Button(
            self.review_frame,
            text="Finish Test",
            command=self.finish_test
        )
        self.finish_button.pack(pady=10)
        
        # Start with question phase
        self.show_question_phase()

    def start_new_test(self):
        """Initialize a new practice test"""
        self.test_cards = self.flashcard_system.get_due_flashcards()
        if not self.test_cards:
            messagebox.showinfo(
                "No Flashcards Due",
                "You have no flashcards due for review right now."
            )
            self.root.destroy()
            return
        
        self.current_card_index = 0
        self.user_answers = []
        self.show_question_phase()
        self.display_current_question()

    def show_question_phase(self):
        """Show the question answering interface"""
        self.review_frame.pack_forget()
        self.question_frame.pack(fill=tk.BOTH, expand=True)

    def show_review_phase(self):
        """Show the answer review interface"""
        self.question_frame.pack_forget()
        self.review_frame.pack(fill=tk.BOTH, expand=True)
        self.display_review()

    def display_current_question(self):
        """Display the current question"""
        if self.current_card_index >= len(self.test_cards):
            self.show_review_phase()
            return
        
        card = self.test_cards[self.current_card_index]
        self.question_label.config(text=card.question)
        self.answer_entry.delete("1.0", tk.END)
        
        # Update button text for last question
        if self.current_card_index == len(self.test_cards) - 1:
            self.next_button.config(text="Finish Test")
        else:
            self.next_button.config(text="Next Question")

    def next_question(self):
        """Save answer and move to next question"""
        user_answer = self.answer_entry.get("1.0", tk.END).strip()
        if not user_answer:
            messagebox.showwarning("Empty Answer", "Please type your answer before continuing.")
            return
        
        self.user_answers.append({
            'card': self.test_cards[self.current_card_index],
            'user_answer': user_answer
        })
        
        self.current_card_index += 1
        self.display_current_question()

    def display_review(self):
        """Display all questions with user answers and correct answers"""
        self.review_text.config(state=tk.NORMAL)
        self.review_text.delete("1.0", tk.END)
        
        for i, item in enumerate(self.user_answers, 1):
            card = item['card']
            user_answer = item['user_answer']
            
            self.review_text.insert(tk.END, f"Question {i}:\n", 'bold')
            self.review_text.insert(tk.END, f"{card.question}\n\n")
            
            self.review_text.insert(tk.END, "Your answer:\n", 'bold')
            self.review_text.insert(tk.END, f"{user_answer}\n\n")
            
            self.review_text.insert(tk.END, "Correct answer:\n", 'bold')
            self.review_text.insert(tk.END, f"{card.answer}\n\n")
            self.review_text.insert(tk.END, "-"*50 + "\n\n")
        
        self.review_text.tag_config('bold', font=('Arial', 11, 'bold'))
        self.review_text.config(state=tk.DISABLED)

    def rate_card(self, rating):
        """Rate the current card based on performance"""
        if not hasattr(self, 'current_review_index'):
            self.current_review_index = 0
        
        card = self.user_answers[self.current_review_index]['card']
        self.flashcard_system.update_flashcard_after_review(card.id, rating)
        
        self.current_review_index += 1
        if self.current_review_index >= len(self.user_answers):
            self.finish_button.config(state=tk.NORMAL)

    def finish_test(self):
        """Close the test window"""
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    # Replace with actual user ID or get from user input
    user_id = 1  
    app = TypedPracticeTest(root, user_id)
    root.mainloop()
import random
import tkinter as tk
from tkinter import ttk, messagebox
from services.flashcard_system import FlashcardSystem
from models.database import Database

class PracticeTest:
    def __init__(self, root, user_id):
        self.root = root
        self.root.title("Flashcard Practice Test")
        self.root.geometry("800x600")
        
        self.user_id = user_id
        self.flashcard_system = FlashcardSystem(user_id)
        self.test_questions = []
        self.current_question_index = 0
        self.score = 0
        
        self.setup_ui()
        self.start_new_test()

    def setup_ui(self):
        # Main frame
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Question display
        self.question_label = ttk.Label(
            self.main_frame,
            text="",
            font=('Arial', 12),
            wraplength=700,
            justify=tk.CENTER
        )
        self.question_label.pack(pady=20)
        
        # Answer buttons
        self.answer_buttons = []
        for i in range(4):
            btn = ttk.Button(
                self.main_frame,
                text="",
                command=lambda idx=i: self.check_answer(idx),
                width=50
            )
            btn.pack(pady=5)
            self.answer_buttons.append(btn)
        
        # Feedback and score
        self.feedback_label = ttk.Label(
            self.main_frame,
            text="",
            font=('Arial', 11)
        )
        self.feedback_label.pack(pady=10)
        
        self.score_label = ttk.Label(
            self.main_frame,
            text="Score: 0/0",
            font=('Arial', 11)
        )
        self.score_label.pack(pady=10)
        
        # Control buttons
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(pady=20)
        
        ttk.Button(
            control_frame,
            text="New Test",
            command=self.start_new_test
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            control_frame,
            text="Exit",
            command=self.root.quit
        ).pack(side=tk.LEFT, padx=10)

    def generate_test_questions(self, num_questions=10):
        """Generate multiple choice questions from flashcards"""
        flashcards = self.flashcard_system.flashcards
        if len(flashcards) < 4:
            return None
        
        test_questions = []
        due_cards = self.flashcard_system.get_due_flashcards() or random.sample(
            flashcards, 
            min(num_questions, len(flashcards))
        )
        
        for card in due_cards[:num_questions]:
            # Get wrong answers from other flashcards
            wrong_answers = [
                c.answer for c in random.sample(
                    [c for c in flashcards if c.id != card.id],
                    min(3, len(flashcards)-1)
                )
            ]
            options = wrong_answers + [card.answer]
            random.shuffle(options)
            
            test_questions.append({
                'question': card.question,
                'answer': card.answer,
                'options': options,
                'card_id': card.id
            })
        
        return test_questions

    def start_new_test(self):
        """Initialize a new practice test"""
        self.test_questions = self.generate_test_questions()
        if not self.test_questions:
            messagebox.showwarning(
                "Not Enough Flashcards",
                "You need at least 4 flashcards to create a practice test"
            )
            return
        
        self.current_question_index = 0
        self.score = 0
        self.display_question()

    def display_question(self):
        """Show current question and options"""
        if self.current_question_index >= len(self.test_questions):
            self.show_results()
            return
        
        question = self.test_questions[self.current_question_index]
        self.question_label.config(text=question['question'])
        
        for i, btn in enumerate(self.answer_buttons):
            if i < len(question['options']):
                btn.config(text=question['options'][i], state=tk.NORMAL)
            else:
                btn.config(text="", state=tk.DISABLED)
        
        self.feedback_label.config(text="")
        self.score_label.config(text=f"Score: {self.score}/{len(self.test_questions)}")

    def check_answer(self, option_index):
        """Check if selected answer is correct"""
        question = self.test_questions[self.current_question_index]
        selected = question['options'][option_index]
        
        # Disable all buttons
        for btn in self.answer_buttons:
            btn.config(state=tk.DISABLED)
        
        if selected == question['answer']:
            self.score += 1
            self.feedback_label.config(text="Correct!", foreground="green")
        else:
            self.feedback_label.config(
                text=f"Incorrect! Correct answer: {question['answer']}",
                foreground="red"
            )
        
        # Update score and move to next question after delay
        self.score_label.config(text=f"Score: {self.score}/{len(self.test_questions)}")
        self.root.after(2000, self.next_question)

    def next_question(self):
        """Advance to next question"""
        self.current_question_index += 1
        self.display_question()

    def show_results(self):
        """Show final test results"""
        self.question_label.config(
            text=f"Test Complete!\nFinal Score: {self.score}/{len(self.test_questions)}"
        )
        
        for btn in self.answer_buttons:
            btn.pack_forget()
        
        percentage = (self.score / len(self.test_questions)) * 100
        self.feedback_label.config(
            text=f"Percentage: {percentage:.1f}%",
            font=('Arial', 12, 'bold')
        )

if __name__ == "__main__":
    root = tk.Tk()
    # Replace with actual user ID or get it from user input
    user_id = 1  
    app = PracticeTest(root, user_id)
    root.mainloop()
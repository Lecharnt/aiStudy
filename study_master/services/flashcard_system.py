from datetime import datetime, timedelta
from models.database import Database
from models.flashcard import FlashCard
from models.MindMap import MindMap
class FlashcardSystem:
    def __init__(self, user_id):
        self.db = Database()
        self.user_id = user_id
        self.flashcards = self.load_flashcards()
        self.mind_map = MindMap()
    
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

        now = datetime.now()

        # Performance 0: Forgot
        if performance == 0:
            card.interval = 0.0001  # Reset to 1 day
            card.repetitions = 0
            card.ease_factor = max(1.3, card.ease_factor - 0.2)

        else:
            card.repetitions += 1

            # Adjust ease factor
            if performance == 1:  # Hard
                card.ease_factor = max(1.3, card.ease_factor - 0.15)
            elif performance == 3:  # Easy
                card.ease_factor = min(2.5, card.ease_factor + 0.15)

            # Set next interval based on repetition
            if card.repetitions == 1:
                card.interval = 0.0021  # ~3 minutes
            elif card.repetitions == 2:
                card.interval = 0.0104  # ~15 minutes
            elif card.repetitions == 3 and performance == 3:
                card.interval = 4  # Easy after 2 reviews: 4 days
            else:
                card.interval = card.interval * card.ease_factor

            # Clamp max interval to 365 days
            card.interval = min(card.interval, 365)

        # Schedule next review
        next_review = now + timedelta(days=card.interval)
        card.next_review = next_review.isoformat()
        #print(f"[DEBUG] Card ID: {card.id} | Next Review: {card.next_review} | Interval: {card.interval:.2f} days")
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
    def create_mind_map(self, root_title):
        return self.mind_map.create_root(root_title)

    def get_current_mindmap_node(self):
        return self.mind_map.current_node

    def set_current_mindmap_node(self, node_id):
        # You'll need to implement a way to find nodes by ID
        pass
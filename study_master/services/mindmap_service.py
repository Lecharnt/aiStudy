import math
import random
from datetime import datetime
from models.flashcard import FlashCard

class MindMapNode:
    def __init__(self, title, parent=None):
        self.id = int(datetime.now().timestamp() * 1000)
        self.title = title
        self.parent = parent
        self.children = []
        self.flashcards = []
    
    def add_child(self, title):
        new_node = MindMapNode(title, parent=self)
        self.children.append(new_node)
        return new_node
    
    def add_flashcard(self, flashcard_id):
        if flashcard_id not in self.flashcards:
            self.flashcards.append(flashcard_id)
    
    def get_all_flashcards(self):
        cards = self.flashcards.copy()
        for child in self.children:
            cards.extend(child.get_all_flashcards())
        return list(set(cards))

class MindMapService:
    def __init__(self, flashcard_system):
        self.flashcard_system = flashcard_system
        self.root = None
        self.current_node = None
    
    def create_root(self, title):
        self.root = MindMapNode(title)
        self.current_node = self.root
        return self.root
    
    def get_available_flashcards(self, node):
        current_flashcards = node.get_all_flashcards()
        return [
            card for card in self.flashcard_system.flashcards
            if card.id not in current_flashcards
        ]
    
    def get_cards_for_study(self, node):
        card_ids = node.get_all_flashcards()
        return [
            card for card in self.flashcard_system.flashcards
            if card.id in card_ids
        ]
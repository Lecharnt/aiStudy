import time
class MindMapNode:
    def __init__(self, title, parent=None):
        self.id = int(time.time() * 1000)  # Unique ID
        self.title = title
        self.parent = parent
        self.children = []
        self.flashcards = []  # List of flashcard IDs
    
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
        return list(set(cards))  # Remove duplicates
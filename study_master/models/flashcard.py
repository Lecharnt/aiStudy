from datetime import datetime
import time
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
    
import json
import os

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
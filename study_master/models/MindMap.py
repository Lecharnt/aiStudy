from models.MindMapNode import MindMapNode
class MindMap:
    def __init__(self):
        self.root = None
        self.current_node = None
    
    def create_root(self, title):
        self.root = MindMapNode(title)
        self.current_node = self.root
        return self.root
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog, messagebox
from PIL import Image, ImageTk
import math

class MindMapViewer:
    def __init__(self, parent, flashcard_system):
        self.parent = parent
        self.flashcard_system = flashcard_system
        self.canvas = tk.Canvas(parent, bg="white", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Initialize zoom and pan variables
        self.zoom_level = 1.0
        self.pan_start_x = 0
        self.pan_start_y = 0
        
        # Set up event bindings
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<B1-Motion>", self.on_pan)
        self.canvas.bind("<Button-3>", self.show_context_menu)
        self.canvas.bind("<MouseWheel>", self.on_zoom)
        
        # Draw initial mind map if exists
        self.draw_mind_map()
    
    def draw_mind_map(self):
        self.canvas.delete("all")
        root = self.flashcard_system.mind_map.root
        if root:
            self.draw_node(root, 400, 300, 200)
    
    def draw_node(self, node, x, y, spread):
        # Draw the node
        node_color = "lightblue" if node == self.flashcard_system.get_current_mindmap_node() else "white"
        self.canvas.create_oval(x-50, y-30, x+50, y+30, fill=node_color, outline="black")
        self.canvas.create_text(x, y, text=node.title, width=90)
        
        # Draw connections to children
        angle_step = 2 * math.pi / len(node.children) if node.children else 0
        for i, child in enumerate(node.children):
            child_x = x + spread * math.cos(i * angle_step)
            child_y = y + spread * math.sin(i * angle_step)
            self.canvas.create_line(x, y+30, child_x, child_y-30, arrow=tk.LAST)
            self.draw_node(child, child_x, child_y, spread*0.8)
    
    def on_click(self, event):
        # Find clicked node and set as current
        pass
    
    def on_pan(self, event):
        # Implement panning logic
        pass
    
    def on_zoom(self, event):
        # Implement zooming logic
        pass
    
    def show_context_menu(self, event):
        # Create context menu for adding nodes/flashcards
        menu = tk.Menu(self.parent, tearoff=0)
        menu.add_command(label="Add Child Concept", command=self.add_child_node)
        menu.add_command(label="Add Flashcard", command=self.add_flashcard_to_node)
        menu.add_command(label="Study This Branch", command=self.study_branch)
        menu.post(event.x_root, event.y_root)
    
    def add_child_node(self):
        title = simpledialog.askstring("New Concept", "Enter concept name:")
        if title:
            current_node = self.flashcard_system.get_current_mindmap_node()
            new_node = current_node.add_child(title)
            self.draw_mind_map()
    
    def add_flashcard_to_node(self):
        # Show dialog to select/create flashcard
        pass
    
    def study_branch(self):
        current_node = self.flashcard_system.get_current_mindmap_node()
        if current_node:
            flashcard_ids = current_node.get_all_flashcards()
            # Start study session with these flashcards
            pass
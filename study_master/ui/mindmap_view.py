import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import math

class MindMapView:
    def __init__(self, parent, mindmap_service, show_flashcards_callback):
        self.parent = parent
        self.service = mindmap_service
        self.show_flashcards = show_flashcards_callback
        
        self.frame = ttk.Frame(parent)
        self.current_node = None
        
        self.setup_toolbar()
        self.setup_canvas()
        self.setup_context_menu()
    
    def setup_toolbar(self):
        toolbar = ttk.Frame(self.frame)
        toolbar.pack(fill=tk.X, pady=5)
        
        ttk.Button(
            toolbar, 
            text="New Mind Map", 
            command=self.create_new_mindmap
        ).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(
            toolbar, 
            text="Back", 
            command=self.hide
        ).pack(side=tk.RIGHT, padx=5)
    
    def setup_canvas(self):
        self.canvas = tk.Canvas(
            self.frame,
            bg="white",
            width=800,
            height=600
        )
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Event bindings
        self.canvas.bind("<Button-3>", self.show_context_menu)
    
    def setup_context_menu(self):
        self.context_menu = tk.Menu(self.parent, tearoff=0)
        self.context_menu.add_command(
            label="Add Subconcept", 
            command=self.add_subconcept
        )
        self.context_menu.add_command(
            label="Add Flashcard", 
            command=self.add_flashcard_to_node
        )
        self.context_menu.add_command(
            label="Study This Branch", 
            command=self.study_branch
        )
    
    def show(self):
        self.frame.pack(fill=tk.BOTH, expand=True)
        if not self.service.root:
            self.create_new_mindmap()
        else:
            self.draw_mind_map()
    
    def hide(self):
        self.frame.pack_forget()
    
    def create_new_mindmap(self):
        title = simpledialog.askstring("New Mind Map", "Enter the central concept:")
        if title:
            self.service.create_root(title)
            self.draw_mind_map()
    
    def draw_mind_map(self):
        self.canvas.delete("all")
        if self.service.root:
            self.draw_node(self.service.root, 400, 300, 200)
    
    def draw_node(self, node, x, y, spread):
        color = "lightblue" if node == self.current_node else "white"
        
        # Draw node
        self.canvas.create_oval(
            x-50, y-30, x+50, y+30,
            fill=color, outline="black",
            tags=("node", f"node_{node.id}")
        )
        self.canvas.create_text(
            x, y, text=node.title, width=90,
            tags=("node_text", f"node_text_{node.id}")
        )
        
        # Draw connections to children
        angle_step = 2 * math.pi / len(node.children) if node.children else 0
        for i, child in enumerate(node.children):
            child_x = x + spread * math.cos(i * angle_step)
            child_y = y + spread * math.sin(i * angle_step)
            self.canvas.create_line(
                x, y+30, child_x, child_y-30,
                arrow=tk.LAST, tags="connection"
            )
            self.draw_node(child, child_x, child_y, spread*0.8)
        
        # Bind click events
        self.canvas.tag_bind(
            f"node_{node.id}", "<Button-1>",
            lambda e, n=node: self.select_node(n)
        )
        self.canvas.tag_bind(
            f"node_text_{node.id}", "<Button-1>",
            lambda e, n=node: self.select_node(n)
        )
    
    def select_node(self, node):
        self.current_node = node
        self.draw_mind_map()
    
    def show_context_menu(self, event):
        if self.current_node:
            self.context_menu.post(event.x_root, event.y_root)
    
    def add_subconcept(self):
        if not self.current_node:
            messagebox.showerror("Error", "No node selected")
            return
        
        title = simpledialog.askstring("New Subconcept", "Enter the subconcept name:")
        if title:
            self.current_node.add_child(title)
            self.draw_mind_map()
    
    def add_flashcard_to_node(self):
        if not self.current_node:
            messagebox.showerror("Error", "No node selected")
            return
        
        available = self.service.get_available_flashcards(self.current_node)
        if not available:
            messagebox.showinfo("Info", "No flashcards available to add")
            return
        
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Flashcard")
        
        listbox = tk.Listbox(dialog, width=80, height=15)
        listbox.pack(padx=10, pady=10)
        
        for card in available:
            listbox.insert(tk.END, f"{card.question[:50]}...")
        
        def add_selected():
            selected = listbox.curselection()
            if selected:
                card = available[selected[0]]
                self.current_node.add_flashcard(card.id)
                dialog.destroy()
        
        ttk.Button(dialog, text="Add Selected", command=add_selected).pack(pady=5)
    
    def study_branch(self):
        if not self.current_node:
            messagebox.showerror("Error", "No node selected")
            return
        
        cards = self.service.get_cards_for_study(self.current_node)
        if not cards:
            messagebox.showinfo("Info", "No flashcards in this branch")
            return
        
        self.show_flashcards(cards)
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class ManageNotesScreen:
    def __init__(self, root, current_user, user_role, on_update=None):
        self.root = root
        self.current_user = current_user
        self.user_role = user_role
        self.on_update = on_update 
        self.root.title("KWH Inventory System - Manage Notes")
        
        window_width = 750
        window_height = 550
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

        list_frame = tk.LabelFrame(self.root, text="Notice Board History", padx=10, pady=10)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(list_frame, columns=("ID", "User", "Message", "Time"), show='headings')
        self.tree.heading("User", text="Posted By")
        self.tree.heading("Message", text="Note Content")
        self.tree.heading("Time", text="Date & Time")
        
        self.tree.column("User", width=120, anchor="w")
        self.tree.column("Message", width=400, anchor="w")
        self.tree.column("Time", width=150, anchor="center")

        self.tree["displaycolumns"] = ("User", "Message", "Time")
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        
        self.tree.bind("<ButtonRelease-1>", self.select_note)

        edit_frame = tk.LabelFrame(self.root, text="Edit Selected Note", padx=10, pady=10)
        edit_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.ent_message = tk.Entry(edit_frame, font=("Arial", 11))
        self.ent_message.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 10))

        tk.Button(edit_frame, text="Update Message", bg="#f39c12", fg="white", font=("Arial", 10, "bold"), command=self.update_note).pack(side=tk.RIGHT)

        btn_frame = tk.Frame(self.root, pady=5)
        btn_frame.pack(fill="x", padx=20, pady=(0, 10))

        # Only generate the Clear All button if the user is an admin
        if self.user_role == 'admin':
            tk.Button(btn_frame, text="Clear All Messages", bg="#8e44ad", fg="white", font=("Arial", 10, "bold"), width=20, command=self.clear_all_notes).pack(side=tk.LEFT)
        
        tk.Button(btn_frame, text="Delete Selected Note", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), width=20, command=self.delete_note).pack(side=tk.RIGHT)

        self.load_notes()

    def load_notes(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.ent_message.delete(0, tk.END) 
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                # Queries ASC order to display newest at bottom
                query = "SELECT note_id, username, content, strftime('%Y-%m-%d %H:%M:%S', timestamp, 'localtime') FROM Notes ORDER BY timestamp ASC"
                cursor = conn.execute(query)
                for row in cursor:
                    self.tree.insert("", "end", values=row)
            
            children = self.tree.get_children()
            if children:
                # Scroll to the bottom-most element
                self.tree.see(children[-1])

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not load notes: {e}", parent=self.root)

    def select_note(self, event):
        selected = self.tree.selection()
        if selected:
            row_data = self.tree.item(selected[0])['values']
            message_content = row_data[2] 
            self.ent_message.delete(0, tk.END)
            self.ent_message.insert(0, message_content)

    def update_note(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a note to edit.", parent=self.root)
            return
        
        row_data = self.tree.item(selected[0])['values']
        note_id = row_data[0]
        posted_by = row_data[1]
        new_content = self.ent_message.get().strip()

        if not new_content:
            messagebox.showwarning("Input Error", "Message cannot be empty.", parent=self.root)
            return

        if self.role_check(posted_by):
            if messagebox.askyesno("Confirm Update", "Are you sure you want to overwrite this message?", parent=self.root):
                try:
                    with sqlite3.connect("KWH_Inventory_System.db") as conn:
                        conn.execute("UPDATE Notes SET content = ? WHERE note_id = ?", (new_content, note_id))
                    self.load_notes()
                    if self.on_update: self.on_update()
                    messagebox.showinfo("Success", "Notice board updated!", parent=self.root)
                except sqlite3.Error as e:
                    messagebox.showerror("Error", f"Update failed: {e}", parent=self.root)

    def delete_note(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select a note to delete.", parent=self.root)
            return
        
        row_data = self.tree.item(selected[0])['values']
        note_id = row_data[0]
        posted_by = row_data[1]

        if self.role_check(posted_by):
            if messagebox.askyesno("Confirm Deletion", "Are you sure you want to delete this note?", parent=self.root):
                try:
                    with sqlite3.connect("KWH_Inventory_System.db") as conn:
                        conn.execute("DELETE FROM Notes WHERE note_id = ?", (note_id,))
                    self.load_notes()
                    if self.on_update: self.on_update()
                except sqlite3.Error as e:
                    messagebox.showerror("Error", f"Delete failed: {e}", parent=self.root)

    def clear_all_notes(self):
        # Double-check security: ensures normal users can't run this
        if self.user_role != 'admin':
            messagebox.showerror("Permission Denied", "Only administrators can clear the entire Notice Board.", parent=self.root)
            return
            
        if messagebox.askyesno("Clear All Messages", "Are you sure you want to delete ALL messages?\nThis cannot be undone.", parent=self.root):
            try:
                with sqlite3.connect("KWH_Inventory_System.db") as conn:
                    conn.execute("DELETE FROM Notes")
                
                # Triggers the visual reload, making the screen instantly blank
                self.load_notes()
                
                # Updates the main dashboard behind this window
                if self.on_update: self.on_update()
                
                # The success popup has been successfully removed from here!
                
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Failed to clear messages: {e}", parent=self.root)

    def role_check(self, author):
        # Admins can manage everything; Normal users can only manage their own notes
        if self.user_role == 'admin' or self.current_user == author:
            return True
        messagebox.showerror("Permission Denied", "You can only edit or delete your own posts.", parent=self.root)
        return False
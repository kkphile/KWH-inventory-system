import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import hashlib

class UserManagementScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("KWH Inventory System - User Management")
        
        window_width = 600
        window_height = 500
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

        # --- Auto-Migration: Safely adds 'is_active' to your database if it doesn't exist ---
        self.ensure_is_active_column()

        list_frame = tk.LabelFrame(self.root, text="System Users", padx=10, pady=10)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(list_frame, columns=("ID", "Username", "Role"), show='headings')
        self.tree.heading("Username", text="Username")
        self.tree.heading("Role", text="Access Level")
        
        self.tree.column("Username", width=250)
        self.tree.column("Role", width=150, anchor="center")
        self.tree["displaycolumns"] = ("Username", "Role")
        
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<ButtonRelease-1>", self.select_user)

        form_frame = tk.LabelFrame(self.root, text="Add / Update User", padx=10, pady=10)
        form_frame.pack(fill="x", padx=20, pady=15)

        tk.Label(form_frame, text="Username:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.ent_username = tk.Entry(form_frame, width=20)
        self.ent_username.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form_frame, text="Role:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.role_var = tk.StringVar(value="normal")
        self.combo_role = ttk.Combobox(form_frame, textvariable=self.role_var, values=("admin", "normal"), state="readonly", width=10)
        self.combo_role.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(form_frame, text="Password:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.ent_password = tk.Entry(form_frame, show="*", width=20)
        self.ent_password.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Label(form_frame, text="(Leave blank to update without changing password)", font=("Arial", 8, "italic")).grid(row=1, column=2, columnspan=2)

        btn_frame = tk.Frame(form_frame)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)

        tk.Button(btn_frame, text="Add New", bg="#2ecc71", fg="white", width=12, command=self.add_user).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Update", bg="#3498db", fg="white", width=12, command=self.update_user).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Delete", bg="#e74c3c", fg="white", width=12, command=self.delete_user).pack(side=tk.LEFT, padx=5)

        self.selected_user_id = None
        self.load_users()

    def ensure_is_active_column(self):
        """Automatically checks the database and adds the is_active column safely."""
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(Users)")
                columns = [info[1] for info in cursor.fetchall()]
                if 'is_active' not in columns:
                    conn.execute("ALTER TABLE Users ADD COLUMN is_active INTEGER DEFAULT 1")
        except Exception as e:
            print(f"Migration error: {e}")

    def clear_form(self):
        self.ent_username.delete(0, tk.END)
        self.ent_password.delete(0, tk.END)
        self.role_var.set("normal")
        self.selected_user_id = None

    def load_users(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                # Only load users that are active (is_active = 1)
                cursor = conn.execute("SELECT user_id, username, role FROM Users WHERE is_active = 1 ORDER BY username ASC")
                for row in cursor:
                    self.tree.insert("", "end", values=row)
        except sqlite3.Error as e: 
            messagebox.showerror("Error", f"Could not load users: {e}", parent=self.root)

    def select_user(self, event):
        selected = self.tree.selection()
        if selected:
            row = self.tree.item(selected[0])['values']
            self.selected_user_id = row[0]
            self.ent_username.delete(0, tk.END)
            self.ent_username.insert(0, row[1])
            self.role_var.set(row[2])
            self.ent_password.delete(0, tk.END)

    def hash_pw(self, pw):
        return hashlib.sha256(pw.encode()).hexdigest()

    def add_user(self):
        uname = self.ent_username.get().strip()
        pw = self.ent_password.get().strip()
        role = self.role_var.get()
        if not uname or not pw:
            messagebox.showwarning("Error", "Username and Password required for new users.", parent=self.root)
            return

        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                # Check if user previously existed before trying to insert
                cursor = conn.execute("SELECT user_id, is_active FROM Users WHERE username=?", (uname,))
                existing_user = cursor.fetchone()

                if existing_user:
                    if existing_user[1] == 1:
                        messagebox.showerror("Error", "Username already exists.", parent=self.root)
                        return
                    else:
                        # Resurrect a soft-deleted user instead of creating a duplicate row
                        conn.execute("UPDATE Users SET password_hash=?, role=?, is_active=1 WHERE user_id=?", 
                                     (self.hash_pw(pw), role, existing_user[0]))
                        messagebox.showinfo("Success", f"Previously deleted user '{uname}' has been restored and updated.", parent=self.root)
                else:
                    # Insert a brand new user
                    conn.execute("INSERT INTO Users (username, password_hash, role, is_active) VALUES (?, ?, ?, 1)", 
                                 (uname, self.hash_pw(pw), role))
                    messagebox.showinfo("Success", f"User '{uname}' added.", parent=self.root)
            
            self.load_users()
            self.clear_form()
            
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Database error: {e}", parent=self.root)

    def update_user(self):
        if not self.selected_user_id: return
        uname = self.ent_username.get().strip()
        pw = self.ent_password.get().strip()
        role = self.role_var.get()
        
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                if pw:
                    conn.execute("UPDATE Users SET username = ?, password_hash = ?, role = ? WHERE user_id = ?", 
                                 (uname, self.hash_pw(pw), role, self.selected_user_id))
                else:
                    conn.execute("UPDATE Users SET username = ?, role = ? WHERE user_id = ?", 
                                 (uname, role, self.selected_user_id))
            self.load_users()
            self.clear_form()
            messagebox.showinfo("Success", "User updated.", parent=self.root)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Update failed: {e}", parent=self.root)

    def delete_user(self):
        if not self.selected_user_id: return
        
        # Prevent deleting the main admin account 
        if self.ent_username.get().strip() == 'admin':
            messagebox.showwarning("Warning", "Cannot delete the default 'admin' account.", parent=self.root)
            return

        if messagebox.askyesno("Confirm", "Delete this user?", parent=self.root):
            try:
                with sqlite3.connect("KWH_Inventory_System.db") as conn:
                    # --- THE FIX: Soft Delete updates is_active to 0 instead of DROP ---
                    conn.execute("UPDATE Users SET is_active = 0 WHERE user_id = ?", (self.selected_user_id,))
                
                self.load_users()
                self.clear_form()
                messagebox.showinfo("Success", "User deleted successfully.", parent=self.root)
            except sqlite3.Error as e:
                messagebox.showerror("Error", f"Delete failed: {e}", parent=self.root)
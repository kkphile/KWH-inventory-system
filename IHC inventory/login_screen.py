import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib

class LoginScreen:
    def __init__(self, root):
        self.root = root
        
        # --- NEW: Load Custom Settings from Database ---
        self.theme_color = "#34495e"
        self.system_title = "KWH Inventory System"
        self.load_settings()

        self.root.title(f"{self.system_title} - Login")
        
        window_width = 400
        window_height = 350
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.root.configure(bg="#ecf0f1")

        # --- UPDATED: Apply Theme Color and Title to Header ---
        header_frame = tk.Frame(self.root, bg=self.theme_color, pady=20)
        header_frame.pack(fill="x")
        
        tk.Label(header_frame, text=self.system_title, font=("Arial", 16, "bold"), bg=self.theme_color, fg="white").pack()
        tk.Label(header_frame, text="Please log in to continue", font=("Arial", 10), bg=self.theme_color, fg="white").pack()

        # Login Form Elements
        form_frame = tk.Frame(self.root, bg="#ecf0f1", pady=20)
        form_frame.pack()

        tk.Label(form_frame, text="Username:", font=("Arial", 11, "bold"), bg="#ecf0f1").grid(row=0, column=0, pady=10, sticky="e")
        self.ent_username = tk.Entry(form_frame, font=("Arial", 11), width=20)
        self.ent_username.grid(row=0, column=1, pady=10, padx=10)

        tk.Label(form_frame, text="Password:", font=("Arial", 11, "bold"), bg="#ecf0f1").grid(row=1, column=0, pady=10, sticky="e")
        self.ent_password = tk.Entry(form_frame, font=("Arial", 11), width=20, show="*")
        self.ent_password.grid(row=1, column=1, pady=10, padx=10)
        self.ent_password.bind("<Return>", lambda e: self.login())

        # --- UPDATED: Apply Theme Color to Login Button ---
        tk.Button(self.root, text="Login", font=("Arial", 12, "bold"), bg=self.theme_color, fg="white", width=15, cursor="hand2", command=self.login).pack(pady=10)

    def load_settings(self):
        """Fetches the customizable title and theme color from the database."""
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                cursor = conn.execute("SELECT setting_key, setting_value FROM Settings")
                for row in cursor:
                    if row[0] == 'theme_color':
                        self.theme_color = row[1]
                    elif row[0] == 'system_title':
                        self.system_title = row[1]
        except Exception:
            pass

    def hash_pw(self, pw):
        return hashlib.sha256(pw.encode()).hexdigest()

    def login(self):
        uname = self.ent_username.get().strip()
        pw = self.ent_password.get().strip()
        
        if not uname or not pw:
            messagebox.showwarning("Input Error", "Username and password cannot be empty.", parent=self.root)
            return

        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                cursor = conn.execute("SELECT user_id, username, role FROM Users WHERE username=? AND password_hash=? AND is_active=1", (uname, self.hash_pw(pw)))
                user = cursor.fetchone()
                
                if user:
                    self.root.destroy()
                    from dashboard import MainDashboard
                    dash_root = tk.Tk()
                    MainDashboard(dash_root, user_id=user[0], username=user[1], role=user[2])
                    dash_root.mainloop()
                else:
                    messagebox.showerror("Login Failed", "Invalid username or password, or account is disabled.", parent=self.root)
        except Exception as e:
            messagebox.showerror("Database Error", f"Failed to connect to database: {e}", parent=self.root)
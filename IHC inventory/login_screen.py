import tkinter as tk
from tkinter import messagebox
import sqlite3
import hashlib
from dashboard import MainDashboard

class LoginScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("KWH Inventory System - Login")
        
        window_width = 450
        window_height = 320
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.root.configure(bg="#f4f7f6")

        tk.Label(self.root, text="KWH Inventory System", font=("Arial", 22, "bold"), 
                 bg="#f4f7f6", fg="#2C3E50").pack(pady=25)

        tk.Label(self.root, text="Username:", bg="#f4f7f6", font=("Arial", 10)).pack()
        self.ent_username = tk.Entry(self.root, width=30, font=("Arial", 11))
        self.ent_username.pack(pady=5)
        self.ent_username.focus()

        tk.Label(self.root, text="Password:", bg="#f4f7f6", font=("Arial", 10)).pack()
        self.ent_password = tk.Entry(self.root, width=30, show="*", font=("Arial", 11))
        self.ent_password.pack(pady=5)
        
        self.ent_password.bind("<Return>", lambda e: self.attempt_login())

        tk.Button(self.root, text="Login", width=15, bg="#2C3E50", fg="white", 
                  font=("Arial", 11, "bold"), cursor="hand2",
                  command=self.attempt_login).pack(pady=25)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def attempt_login(self):
        username = self.ent_username.get().strip()
        password = self.ent_password.get().strip()
        
        if not username or not password:
            messagebox.showwarning("Input Error", "Please enter both username and password.", parent=self.root)
            return

        hashed_pw = self.hash_password(password)

        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                cursor = conn.cursor()
                query = "SELECT user_id, username, role FROM Users WHERE username = ? AND password_hash = ?"
                cursor.execute(query, (username, hashed_pw))
                user = cursor.fetchone()

                if user:
                    user_id, uname, role = user
                    self.root.destroy()
                    dashboard_root = tk.Tk()
                    MainDashboard(dashboard_root, user_id, uname, role)
                    dashboard_root.mainloop()
                else:
                    messagebox.showerror("Login Failed", "Invalid username or password.", parent=self.root)
        
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not connect to database: {e}", parent=self.root)
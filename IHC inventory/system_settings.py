import tkinter as tk
from tkinter import ttk, colorchooser, messagebox
import sqlite3

class SystemSettingsScreen:
    def __init__(self, root, on_update=None):
        self.root = root
        self.on_update = on_update
        self.root.title("System Settings")
        
        window_width = 600
        window_height = 300
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

        self.settings = self.load_settings()

        frame = tk.LabelFrame(self.root, text="Customize System Appearance", padx=20, pady=20)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- Row 0: System Title ---
        tk.Label(frame, text="System Title:").grid(row=0, column=0, pady=10, sticky="e")
        self.ent_title = tk.Entry(frame, width=25)
        self.ent_title.insert(0, self.settings.get('system_title', 'KWH Inventory System'))
        self.ent_title.grid(row=0, column=1, pady=10, padx=10)
        
        tk.Button(frame, text="Restore Default Title", bg="#95a5a6", fg="white", font=("Arial", 9, "bold"), cursor="hand2", command=self.restore_default_title).grid(row=0, column=2, padx=10)

        # --- Row 1: Menu Button Color ---
        tk.Label(frame, text="Menu Button Color:").grid(row=1, column=0, pady=10, sticky="e")
        self.btn_color = tk.Button(frame, text="Choose Color", bg=self.settings.get('theme_color', '#34495e'), fg="white", width=20, cursor="hand2", command=self.choose_color)
        self.btn_color.grid(row=1, column=1, pady=10, padx=10, sticky="w")
        
        tk.Button(frame, text="Restore Default Color", bg="#95a5a6", fg="white", font=("Arial", 9, "bold"), cursor="hand2", command=self.restore_default_color).grid(row=1, column=2, padx=10)

        # --- Row 2: Save Button ---
        btn_frame = tk.Frame(frame)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=30)
        tk.Button(btn_frame, text="Save & Apply Settings", bg="#3498db", fg="white", font=("Arial", 11, "bold"), cursor="hand2", width=20, command=self.save_settings).pack()

    def load_settings(self):
        settings = {}
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                cursor = conn.execute("SELECT setting_key, setting_value FROM Settings")
                for row in cursor:
                    settings[row[0]] = row[1]
        except Exception: 
            pass
        return settings

    def choose_color(self):
        color_code = colorchooser.askcolor(parent=self.root, title="Choose Menu Button Color", initialcolor=self.settings.get('theme_color', '#34495e'))[1]
        if color_code:
            self.btn_color.config(bg=color_code)
            self.settings['theme_color'] = color_code

    def restore_default_title(self):
        self.ent_title.delete(0, tk.END)
        self.ent_title.insert(0, "KWH Inventory System")

    def restore_default_color(self):
        self.btn_color.config(bg="#34495e")
        self.settings['theme_color'] = "#34495e"

    def save_settings(self):
        new_title = self.ent_title.get().strip()
        new_color = self.settings.get('theme_color', '#34495e')

        if not new_title:
            messagebox.showwarning("Error", "Title cannot be empty.", parent=self.root)
            return

        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                conn.execute("UPDATE Settings SET setting_value=? WHERE setting_key='system_title'", (new_title,))
                conn.execute("UPDATE Settings SET setting_value=? WHERE setting_key='theme_color'", (new_color,))
            
            messagebox.showinfo("Success", "Settings saved and applied successfully!", parent=self.root)
            
            # This triggers the `apply_live_theme` function back on the dashboard!
            if self.on_update:
                self.on_update()
            self.root.destroy()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}", parent=self.root)
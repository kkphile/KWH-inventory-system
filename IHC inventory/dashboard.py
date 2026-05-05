import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import datetime

class MainDashboard:
    def __init__(self, root, user_id, username, role):
        self.root = root
        self.user_id = user_id
        self.username = username
        self.role = role
        
        self.ensure_settings_table()
        self.settings = self.load_settings()
        self.button_color = self.settings.get('theme_color', '#34495e')
        self.system_title = self.settings.get('system_title', 'KWH Inventory System')

        self.root.title(f"{self.system_title} - Dashboard ({self.role.upper()})")
        
        window_width = 1100
        window_height = 700
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.root.configure(bg="#ecf0f1")

        self.open_windows = {}
        self.sync_id = None 
        self.menu_buttons = [] 

        self.header_frame = tk.Frame(self.root, bg=self.button_color, pady=15)
        self.header_frame.pack(fill="x")
        
        self.title_label = tk.Label(self.header_frame, text=self.system_title, font=("Arial", 24, "bold"), bg=self.button_color, fg="white")
        self.title_label.pack(side=tk.LEFT, padx=(20, 10))
        
        self.welcome_label = tk.Label(self.header_frame, text=f"Welcome, {self.username}", font=("Arial", 12, "italic"), bg=self.button_color, fg="white")
        self.welcome_label.pack(side=tk.LEFT, pady=(10, 0))
        
        self.btn_header_frame = tk.Frame(self.header_frame, bg=self.button_color)
        self.btn_header_frame.pack(side=tk.RIGHT, padx=20)
        
        tk.Button(self.btn_header_frame, text="Logout", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), cursor="hand2", command=self.logout).pack(side=tk.LEFT, padx=5)

        content_frame = tk.Frame(self.root, bg="#ecf0f1")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        menu_frame = tk.Frame(content_frame, bg="#ecf0f1")
        menu_frame.pack(side=tk.LEFT, fill="y", padx=(0, 20))

        self.create_menu_button(menu_frame, "📤 Scan Out-Stock", self.open_out_stock)
        self.create_menu_button(menu_frame, "📋 Product Catalog", self.open_catalog)
        self.create_menu_button(menu_frame, "🔒 Audit Logs", self.open_audit)

        if self.role == 'admin':
            self.create_menu_button(menu_frame, "📥 Batch In-Stock", self.open_in_stock)
            self.create_menu_button(menu_frame, "📦 Inventory View", self.open_inventory)
            self.create_menu_button(menu_frame, "👥 Manage Users", self.open_users)
            self.create_menu_button(menu_frame, "⚙️ System Settings", self.open_system_settings)

        right_frame = tk.Frame(content_frame, bg="#ecf0f1")
        right_frame.pack(side=tk.LEFT, fill="both", expand=True)

        alert_frame = tk.LabelFrame(right_frame, text="⚠️ Low Stock Alerts", font=("Arial", 14, "bold"), bg="#ecf0f1", fg="#c0392b")
        alert_frame.pack(side=tk.TOP, fill="both", expand=True, pady=(0, 10))

        alert_tree_container = tk.Frame(alert_frame, bg="#ecf0f1")
        alert_tree_container.pack(fill="both", expand=True, padx=10, pady=10)

        self.alert_tree = ttk.Treeview(alert_tree_container, columns=("Product", "Category", "Current Stock", "Threshold"), show="headings")
        self.alert_tree.heading("Product", text="Product Name")
        self.alert_tree.heading("Category", text="Category")
        self.alert_tree.heading("Current Stock", text="Current Stock")
        self.alert_tree.heading("Threshold", text="Min. Threshold")
        self.alert_tree.column("Current Stock", width=100, anchor="center")
        self.alert_tree.column("Threshold", width=100, anchor="center")
        
        alert_scroll = ttk.Scrollbar(alert_tree_container, orient=tk.VERTICAL, command=self.alert_tree.yview)
        self.alert_tree.configure(yscrollcommand=alert_scroll.set)
        
        self.alert_tree.pack(side=tk.LEFT, fill="both", expand=True)
        alert_scroll.pack(side=tk.RIGHT, fill="y")
        self.alert_tree.tag_configure('low_stock_danger', foreground='red')

        notice_frame = tk.LabelFrame(right_frame, text="📢 Lab Notice Board", font=("Arial", 14, "bold"), bg="#ecf0f1", fg="#2980b9")
        notice_frame.pack(side=tk.BOTTOM, fill="x")

        notice_btn_frame = tk.Frame(notice_frame, bg="#ecf0f1")
        notice_btn_frame.pack(fill="x", padx=10, pady=(5, 0))
        tk.Button(notice_btn_frame, text="⚙️ Manage/Edit", font=("Arial", 9, "bold"), bg="#bdc3c7", fg="#2c3e50", cursor="hand2", command=self.open_notes).pack(side=tk.RIGHT)

        notice_tree_container = tk.Frame(notice_frame, bg="#ecf0f1")
        notice_tree_container.pack(fill="both", expand=True, padx=10, pady=(5, 5))

        self.notice_tree = ttk.Treeview(notice_tree_container, columns=("User", "Message", "Time"), show="headings", height=5)
        self.notice_tree.heading("User", text="Posted By")
        self.notice_tree.heading("Message", text="Announcement")
        self.notice_tree.heading("Time", text="Date & Time")
        self.notice_tree.column("User", width=120)
        self.notice_tree.column("Message", width=500)
        self.notice_tree.column("Time", width=150, anchor="center")
        
        notice_scroll = ttk.Scrollbar(notice_tree_container, orient=tk.VERTICAL, command=self.notice_tree.yview)
        self.notice_tree.configure(yscrollcommand=notice_scroll.set)

        self.notice_tree.pack(side=tk.LEFT, fill="both", expand=True)
        notice_scroll.pack(side=tk.RIGHT, fill="y")

        chat_frame = tk.Frame(notice_frame, bg="#ecf0f1")
        chat_frame.pack(fill="x", padx=10, pady=(0, 10))
        self.ent_chat = tk.Entry(chat_frame, font=("Arial", 11))
        self.ent_chat.pack(side=tk.LEFT, fill="x", expand=True, padx=(0, 10))
        self.ent_chat.bind("<Return>", lambda e: self.post_chat_message())
        tk.Button(chat_frame, text="Post", bg="#3498db", fg="white", font=("Arial", 10, "bold"), cursor="hand2", width=8, command=self.post_chat_message).pack(side=tk.RIGHT)

        self.status_var = tk.StringVar(value="System Active")
        status_bar = tk.Label(self.root, textvariable=self.status_var, bd=1, relief=tk.SUNKEN, anchor=tk.W, bg="#dfe6e9", font=("Arial", 8))
        status_bar.pack(side=tk.BOTTOM, fill="x")

        self.run_background_sync()

    def ensure_settings_table(self):
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                conn.execute('''CREATE TABLE IF NOT EXISTS Settings (
                                setting_key TEXT PRIMARY KEY,
                                setting_value TEXT)''')
                conn.execute("INSERT OR IGNORE INTO Settings (setting_key, setting_value) VALUES ('theme_color', '#34495e')")
                conn.execute("INSERT OR IGNORE INTO Settings (setting_key, setting_value) VALUES ('system_title', 'KWH Inventory System')")
        except Exception as e:
            print(f"Database setup error: {e}")

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

    def apply_live_theme(self):
        self.settings = self.load_settings()
        self.button_color = self.settings.get('theme_color', '#34495e')
        self.system_title = self.settings.get('system_title', 'KWH Inventory System')

        self.root.title(f"{self.system_title} - Dashboard ({self.role.upper()})")

        self.header_frame.config(bg=self.button_color)
        self.title_label.config(text=self.system_title, bg=self.button_color)
        self.welcome_label.config(bg=self.button_color)
        self.btn_header_frame.config(bg=self.button_color)

        for btn in self.menu_buttons:
            btn.config(bg=self.button_color)

    def refresh_all_data(self):
        self.load_alerts()
        self.load_dashboard_notes()
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.status_var.set(f"Last Live Update: {now}")

    def run_background_sync(self):
        self.refresh_all_data()
        self.sync_id = self.root.after(10000, self.run_background_sync)

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to log out?"):
            if self.sync_id:
                self.root.after_cancel(self.sync_id)
            
            self.root.destroy()
            from login_screen import LoginScreen
            login_root = tk.Tk()
            LoginScreen(login_root)
            login_root.mainloop()

    def create_menu_button(self, parent, text, command):
        btn = tk.Button(parent, text=text, font=("Arial", 14), width=20, pady=10, bg=self.button_color, fg="white", cursor="hand2", command=command)
        btn.pack(pady=5)
        self.menu_buttons.append(btn)

    def load_alerts(self):
        for i in self.alert_tree.get_children(): self.alert_tree.delete(i)
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                query = """
                    SELECT c.product_name, c.category, COUNT(i.item_id) as current_stock, c.low_stock_threshold
                    FROM Catalog c
                    LEFT JOIN Inventory i ON c.catalog_id = i.catalog_id AND i.status = 'In_Stock'
                    GROUP BY c.catalog_id
                    HAVING current_stock <= c.low_stock_threshold
                    ORDER BY current_stock ASC
                """
                cursor = conn.execute(query)
                for row in cursor:
                    if row[2] <= row[3]:
                        self.alert_tree.insert("", "end", values=row, tags=('low_stock_danger',))
                    else:
                        self.alert_tree.insert("", "end", values=row)
        except Exception as e: print(f"Alert error: {e}")

    # --- UPDATED: Fetch latest 15, reverse them, and scroll to the bottom ---
    def load_dashboard_notes(self):
        for i in self.notice_tree.get_children(): self.notice_tree.delete(i)
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                query = "SELECT username, content, strftime('%Y-%m-%d %H:%M:%S', timestamp, 'localtime') FROM Notes ORDER BY timestamp DESC LIMIT 15"
                cursor = conn.execute(query)
                rows = cursor.fetchall()
                
                # Reverse the list so the newest message displays at the bottom
                for row in reversed(rows):
                    self.notice_tree.insert("", "end", values=row)
            
            children = self.notice_tree.get_children()
            if children:
                # Scroll down to see the final (newest) element
                self.notice_tree.see(children[-1])
                
        except Exception as e: print(f"Note error: {e}")

    def post_chat_message(self):
        msg = self.ent_chat.get().strip()
        if not msg: return
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                conn.execute("INSERT INTO Notes (username, content) VALUES (?, ?)", (self.username, msg))
            self.ent_chat.delete(0, tk.END)
            self.refresh_all_data()
        except Exception as e: messagebox.showerror("Error", f"Post failed: {e}")

    def open_single_window(self, window_name, window_class, *args, **kwargs):
        if window_name in self.open_windows and self.open_windows[window_name].winfo_exists():
            self.open_windows[window_name].lift()
            self.open_windows[window_name].focus_force()
            return
        for name, win in self.open_windows.items():
            if win.winfo_exists():
                messagebox.showwarning("Action Blocked", f"Close the '{name}' module first.", parent=self.root)
                win.lift(); return

        new_win = tk.Toplevel(self.root)
        self.open_windows[window_name] = new_win
        window_class(new_win, *args, **kwargs)

    def open_catalog(self):
        from catalog_management import CatalogScreen
        self.open_single_window("Product Catalog", CatalogScreen, self.role, on_update=self.refresh_all_data)

    def open_inventory(self):
        from inventory_management import InventoryScreen
        self.open_single_window("Inventory Management", InventoryScreen, self.role, self.user_id, on_update=self.refresh_all_data)

    def open_in_stock(self):
        from batch_in_stock import BatchInStockScreen
        self.open_single_window("Batch In-Stock", BatchInStockScreen, self.user_id, on_update=self.refresh_all_data)

    def open_out_stock(self):
        from out_stock import OutStockScreen
        self.open_single_window("Scan Out-Stock", OutStockScreen, self.user_id, on_update=self.refresh_all_data)

    def open_notes(self):
        from manage_notes import ManageNotesScreen
        self.open_single_window("Notice Board", ManageNotesScreen, self.username, self.role, on_update=self.refresh_all_data)

    def open_audit(self):
        from audit_log import AuditLogScreen
        self.open_single_window("Audit Logs", AuditLogScreen)

    def open_users(self):
        from user_management import UserManagementScreen
        self.open_single_window("Manage Users", UserManagementScreen)

    def on_settings_updated(self):
        self.apply_live_theme()
        self.refresh_all_data()

    def open_system_settings(self):
        from system_settings import SystemSettingsScreen
        self.open_single_window("System Settings", SystemSettingsScreen, on_update=self.on_settings_updated)
import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3

class MainDashboard:
    def __init__(self, root, user_id, username, role):
        self.root = root
        self.user_id = user_id
        self.username = username
        self.role = role
        
        self.root.title(f"KWH Inventory System - Dashboard ({self.role.upper()})")
        
        # Centered Window
        window_width = 1100
        window_height = 700
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")
        self.root.configure(bg="#ecf0f1")

        # --- Top Header ---
        header_frame = tk.Frame(self.root, bg="#2C3E50", pady=15)
        header_frame.pack(fill="x")
        tk.Label(header_frame, text=f"Welcome, {self.username}!", font=("Arial", 20, "bold"), bg="#2C3E50", fg="white").pack(side=tk.LEFT, padx=20)
        tk.Button(header_frame, text="Logout", bg="#e74c3c", fg="white", font=("Arial", 12, "bold"), cursor="hand2", command=self.logout).pack(side=tk.RIGHT, padx=20)

        # --- Main Content Area ---
        content_frame = tk.Frame(self.root, bg="#ecf0f1")
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- Left Menu ---
        menu_frame = tk.Frame(content_frame, bg="#ecf0f1")
        menu_frame.pack(side=tk.LEFT, fill="y", padx=(0, 20))

        # 1. EVERYONE sees these buttons:
        self.create_menu_button(menu_frame, "📤 Scan Out-Stock", self.open_out_stock)
        self.create_menu_button(menu_frame, "📋 Product Catalog", self.open_catalog)
        self.create_menu_button(menu_frame, "🔒 Audit Logs", self.open_audit)

        # 2. ONLY ADMINS see these buttons:
        if self.role == 'admin':
            self.create_menu_button(menu_frame, "📥 Batch In-Stock", self.open_in_stock)
            self.create_menu_button(menu_frame, "📦 Inventory View", self.open_inventory)
            self.create_menu_button(menu_frame, "👥 Manage Users", self.open_users)

        # --- Right Area (Split Layout) ---
        right_frame = tk.Frame(content_frame, bg="#ecf0f1")
        right_frame.pack(side=tk.LEFT, fill="both", expand=True)

        # Top Right: Low Stock Alerts
        alert_frame = tk.LabelFrame(right_frame, text="⚠️ Low Stock Alerts", font=("Arial", 14, "bold"), bg="#ecf0f1", fg="#c0392b")
        alert_frame.pack(side=tk.TOP, fill="both", expand=True, pady=(0, 10))

        self.alert_tree = ttk.Treeview(alert_frame, columns=("Product", "Category", "Current Stock", "Threshold"), show="headings")
        self.alert_tree.heading("Product", text="Product Name")
        self.alert_tree.heading("Category", text="Category")
        self.alert_tree.heading("Current Stock", text="Current Stock")
        self.alert_tree.heading("Threshold", text="Min. Threshold")
        
        self.alert_tree.column("Current Stock", width=100, anchor="center")
        self.alert_tree.column("Threshold", width=100, anchor="center")
        self.alert_tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Bottom Right: Notice Board
        notice_frame = tk.LabelFrame(right_frame, text="📢 Lab Notice Board", font=("Arial", 14, "bold"), bg="#ecf0f1", fg="#2980b9")
        notice_frame.pack(side=tk.BOTTOM, fill="x")

        btn_frame = tk.Frame(notice_frame, bg="#ecf0f1")
        btn_frame.pack(fill="x", padx=10, pady=(5, 0))
        tk.Button(btn_frame, text="⚙️ Manage", font=("Arial", 9, "bold"), bg="#bdc3c7", fg="#2c3e50", cursor="hand2", command=self.open_notes).pack(side=tk.RIGHT)

        self.notice_tree = ttk.Treeview(notice_frame, columns=("User", "Message", "Time"), show="headings", height=6)
        self.notice_tree.heading("User", text="Posted By")
        self.notice_tree.heading("Message", text="Announcement")
        self.notice_tree.heading("Time", text="Date & Time")
        
        self.notice_tree.column("User", width=120)
        self.notice_tree.column("Message", width=500)
        self.notice_tree.column("Time", width=150, anchor="center")
        self.notice_tree.pack(fill="x", padx=10, pady=(0, 10))

        # Load data into both tables
        self.load_alerts()
        self.load_dashboard_notes()

    def create_menu_button(self, parent, text, command):
        tk.Button(parent, text=text, font=("Arial", 14), width=20, pady=10, bg="#34495e", fg="white", cursor="hand2", command=command).pack(pady=5)

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
                    self.alert_tree.insert("", "end", values=row)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load alerts: {e}", parent=self.root)

    def load_dashboard_notes(self):
        for i in self.notice_tree.get_children(): self.notice_tree.delete(i)
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                query = "SELECT username, content, strftime('%Y-%m-%d %H:%M:%S', timestamp, 'localtime') FROM Notes ORDER BY timestamp DESC LIMIT 15"
                cursor = conn.execute(query)
                for row in cursor:
                    self.notice_tree.insert("", "end", values=row)
        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load notices: {e}", parent=self.root)

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to log out?", parent=self.root):
            self.root.destroy()
            from login_screen import LoginScreen
            login_root = tk.Tk()
            LoginScreen(login_root)
            login_root.mainloop()

    # --- Navigation Helpers ---
    def open_catalog(self):
        from catalog_management import CatalogScreen
        CatalogScreen(tk.Toplevel(self.root), self.role)

    def open_inventory(self):
        from inventory_management import InventoryScreen
        InventoryScreen(tk.Toplevel(self.root), self.role)

    def open_in_stock(self):
        from batch_in_stock import BatchInStockScreen
        BatchInStockScreen(tk.Toplevel(self.root), self.user_id)

    def open_out_stock(self):
        from out_stock import OutStockScreen
        OutStockScreen(tk.Toplevel(self.root), self.user_id)

    def open_notes(self):
        from manage_notes import ManageNotesScreen
        ManageNotesScreen(tk.Toplevel(self.root), self.username, self.role)

    def open_audit(self):
        from audit_log import AuditLogScreen
        AuditLogScreen(tk.Toplevel(self.root))

    def open_users(self):
        from user_management import UserManagementScreen
        UserManagementScreen(tk.Toplevel(self.root))
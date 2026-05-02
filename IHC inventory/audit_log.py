import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime

class AuditLogScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("KWH Inventory System - Audit Logs")
        self.root.geometry("1100x650") # Expanded for the 2-row control panel

        # --- Clean 2-Row Filter Panel ---
        filter_frame = tk.LabelFrame(self.root, text="Search & Filter", padx=10, pady=10)
        filter_frame.pack(fill="x", padx=20, pady=10)

        # ROW 1: Action, Category, Product
        tk.Label(filter_frame, text="Action:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.filter_act_var = tk.StringVar()
        self.combo_filter_act = ttk.Combobox(filter_frame, textvariable=self.filter_act_var, state="readonly", width=15)
        self.combo_filter_act.grid(row=0, column=1, padx=5, pady=5)
        self.combo_filter_act.bind("<<ComboboxSelected>>", lambda e: self.load_logs())

        tk.Label(filter_frame, text="Category:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.filter_cat_var = tk.StringVar()
        self.combo_filter_cat = ttk.Combobox(filter_frame, textvariable=self.filter_cat_var, state="readonly", width=18)
        self.combo_filter_cat.grid(row=0, column=3, padx=5, pady=5)
        self.combo_filter_cat.bind("<<ComboboxSelected>>", lambda e: self.load_logs())

        tk.Label(filter_frame, text="Product:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.filter_prod_var = tk.StringVar()
        self.combo_filter_prod = ttk.Combobox(filter_frame, textvariable=self.filter_prod_var, state="readonly", width=22)
        self.combo_filter_prod.grid(row=0, column=5, padx=5, pady=5)
        self.combo_filter_prod.bind("<<ComboboxSelected>>", lambda e: self.load_logs())

        # ROW 2: Barcode Search, Dates, Buttons
        tk.Label(filter_frame, text="Barcode:").grid(row=1, column=0, padx=5, pady=5, sticky="e")
        self.ent_search = tk.Entry(filter_frame, width=18)
        self.ent_search.grid(row=1, column=1, padx=5, pady=5)
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_logs())

        tk.Label(filter_frame, text="From (YYYY-MM-DD):").grid(row=1, column=2, padx=5, pady=5, sticky="e")
        self.ent_start = tk.Entry(filter_frame, width=12)
        self.ent_start.grid(row=1, column=3, padx=5, pady=5)

        tk.Label(filter_frame, text="To Date:").grid(row=1, column=4, padx=5, pady=5, sticky="e")
        self.ent_end = tk.Entry(filter_frame, width=12)
        self.ent_end.grid(row=1, column=5, padx=5, pady=5, sticky="w")

        btn_frame = tk.Frame(filter_frame)
        btn_frame.grid(row=1, column=6, padx=10, sticky="w")
        tk.Button(btn_frame, text="Search Dates", bg="#3498db", fg="white", font=("Arial", 9, "bold"), cursor="hand2", command=self.load_logs).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Clear", bg="#95a5a6", fg="white", font=("Arial", 9, "bold"), cursor="hand2", command=self.clear_filters).pack(side=tk.LEFT, padx=5)

        # --- Table Section ---
        frame = tk.LabelFrame(self.root, text="System Action History", padx=10, pady=10)
        frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self.tree = ttk.Treeview(frame, columns=("LogID", "Barcode", "Product", "User", "Action", "Timestamp"), show='headings')
        self.tree.heading("Barcode", text="Barcode")
        self.tree.heading("Product", text="Product Name")
        self.tree.heading("User", text="Performed By")
        self.tree.heading("Action", text="Action Taken")
        self.tree.heading("Timestamp", text="Date & Time")
        
        self.tree["displaycolumns"] = ("Barcode", "Product", "User", "Action", "Timestamp")
        
        self.tree.column("Barcode", width=120)
        self.tree.column("Product", width=220)
        self.tree.column("User", width=100)
        self.tree.column("Action", width=100)
        self.tree.column("Timestamp", width=150)

        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")

        self.load_dropdowns()

    def validate_date(self, date_text):
        try:
            datetime.datetime.strptime(date_text, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def clear_filters(self):
        self.combo_filter_act.set("All Actions")
        self.combo_filter_cat.set("All Categories")
        self.combo_filter_prod.set("All Products")
        self.ent_search.delete(0, tk.END)
        self.ent_start.delete(0, tk.END)
        self.ent_end.delete(0, tk.END)
        self.load_logs()

    def load_dropdowns(self):
        core_actions = ["In_Stock", "Consumed", "Discarded", "Manual Edit"]
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                # Actions
                c_act = conn.execute("SELECT DISTINCT action FROM AuditLog WHERE action IS NOT NULL ORDER BY action ASC")
                db_actions = [row[0] for row in c_act]
                for act in db_actions:
                    if act not in core_actions: core_actions.append(act)
                
                # Categories & Products
                c_cat = conn.execute("SELECT DISTINCT category FROM Catalog WHERE category != '' ORDER BY category ASC")
                c_prod = conn.execute("SELECT DISTINCT product_name FROM Catalog ORDER BY product_name ASC")
                
                self.combo_filter_cat['values'] = ["All Categories"] + [row[0] for row in c_cat]
                self.combo_filter_prod['values'] = ["All Products"] + [row[0] for row in c_prod]

        except Exception:
            pass 
            
        self.combo_filter_act['values'] = ["All Actions"] + core_actions
        
        self.combo_filter_act.set("All Actions")
        self.combo_filter_cat.set("All Categories")
        self.combo_filter_prod.set("All Products")
        self.load_logs()

    def load_logs(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        
        f_act = self.filter_act_var.get()
        f_cat = self.filter_cat_var.get()
        f_prod = self.filter_prod_var.get()
        f_search = self.ent_search.get().strip().lower()
        start_date = self.ent_start.get().strip()
        end_date = self.ent_end.get().strip()

        if start_date and not self.validate_date(start_date):
            messagebox.showwarning("Format Error", "From Date must be in YYYY-MM-DD format.", parent=self.root)
            return
        if end_date and not self.validate_date(end_date):
            messagebox.showwarning("Format Error", "To Date must be in YYYY-MM-DD format.", parent=self.root)
            return

        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                query = """
                    SELECT a.log_id, a.barcode, COALESCE(c.product_name, 'Unknown/Deleted'), u.username, a.action, strftime('%Y-%m-%d %H:%M:%S', a.timestamp, 'localtime')
                    FROM AuditLog a
                    LEFT JOIN Users u ON a.user_id = u.user_id
                    LEFT JOIN Inventory i ON a.item_id = i.item_id
                    LEFT JOIN Catalog c ON i.catalog_id = c.catalog_id
                    WHERE 1=1
                """
                params = []

                if f_act and f_act != "All Actions":
                    query += " AND a.action = ?"
                    params.append(f_act)

                if f_cat and f_cat != "All Categories":
                    query += " AND c.category = ?"
                    params.append(f_cat)

                if f_prod and f_prod != "All Products":
                    query += " AND c.product_name = ?"
                    params.append(f_prod)

                if f_search:
                    query += " AND LOWER(a.barcode) LIKE ?"
                    params.append(f"%{f_search}%")

                if start_date:
                    query += " AND date(a.timestamp, 'localtime') >= ?"
                    params.append(start_date)

                if end_date:
                    query += " AND date(a.timestamp, 'localtime') <= ?"
                    params.append(end_date)

                query += " ORDER BY a.timestamp DESC"

                cursor = conn.execute(query, params)
                for row in cursor:
                    self.tree.insert("", "end", values=row)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load audit logs: {e}", parent=self.root)
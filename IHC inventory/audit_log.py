import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime

class AuditLogScreen:
    def __init__(self, root):
        self.root = root
        self.root.title("KWH Inventory System - Audit Logs")
        self.root.geometry("1100x650") 

        filter_frame = tk.LabelFrame(self.root, text="Search & Filter", padx=10, pady=10)
        filter_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(filter_frame, text="Action:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
        self.filter_act_var = tk.StringVar()
        self.combo_filter_act = ttk.Combobox(filter_frame, textvariable=self.filter_act_var, state="readonly", width=15)
        self.combo_filter_act.grid(row=0, column=1, padx=5, pady=5)
        self.combo_filter_act.bind("<<ComboboxSelected>>", lambda e: self.load_logs())

        tk.Label(filter_frame, text="Category:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
        self.filter_cat_var = tk.StringVar()
        self.combo_filter_cat = ttk.Combobox(filter_frame, textvariable=self.filter_cat_var, width=18, postcommand=self.click_drop_cat)
        self.combo_filter_cat.grid(row=0, column=3, padx=5, pady=5)
        self.combo_filter_cat.bind("<<ComboboxSelected>>", self.on_category_select)
        self.combo_filter_cat.bind("<KeyRelease>", self.on_category_select)

        tk.Label(filter_frame, text="Product:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
        self.filter_prod_var = tk.StringVar()
        self.combo_filter_prod = ttk.Combobox(filter_frame, textvariable=self.filter_prod_var, width=22, postcommand=self.click_drop_prod)
        self.combo_filter_prod.grid(row=0, column=5, padx=5, pady=5)
        self.combo_filter_prod.bind("<<ComboboxSelected>>", self.on_product_type)
        self.combo_filter_prod.bind("<KeyRelease>", self.on_product_type)

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

        self.cat_listbox = tk.Listbox(self.root, font=("Arial", 10), bg="#fdfdfe", selectbackground="#3498db", relief=tk.SOLID, bd=1)
        self.prod_listbox = tk.Listbox(self.root, font=("Arial", 10), bg="#fdfdfe", selectbackground="#3498db", relief=tk.SOLID, bd=1)
        
        self.cat_listbox.bind("<ButtonRelease-1>", lambda e: self.apply_selection(self.combo_filter_cat, self.cat_listbox, self.on_category_select))
        self.prod_listbox.bind("<ButtonRelease-1>", lambda e: self.apply_selection(self.combo_filter_prod, self.prod_listbox, self.on_product_type))
        
        self.combo_filter_cat.bind("<FocusOut>", lambda e: self.cat_listbox.after(150, self.cat_listbox.place_forget))
        self.combo_filter_prod.bind("<FocusOut>", lambda e: self.prod_listbox.after(150, self.prod_listbox.place_forget))

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

    # --- THE FIX: Smart Dropdown Listener ---
    def click_drop_cat(self):
        selected_prod = self.filter_prod_var.get().strip()
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                if selected_prod and selected_prod != "All Products":
                    exact_match = conn.execute("SELECT category FROM Catalog WHERE product_name = ?", (selected_prod,)).fetchone()
                    if exact_match:
                        self.combo_filter_cat['values'] = ["All Categories", exact_match[0]]
                        return 

                c = conn.execute("SELECT DISTINCT category FROM Catalog WHERE category != '' ORDER BY category ASC")
                self.combo_filter_cat['values'] = ["All Categories"] + [row[0] for row in c]
        except: pass

    def click_drop_prod(self):
        selected_cat = self.filter_cat_var.get().strip()
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                if selected_cat == "All Categories" or not selected_cat:
                    c = conn.execute("SELECT DISTINCT product_name FROM Catalog ORDER BY product_name ASC")
                else:
                    c = conn.execute("SELECT DISTINCT product_name FROM Catalog WHERE category LIKE ? ORDER BY product_name ASC", (f"%{selected_cat}%",))
                self.combo_filter_prod['values'] = ["All Products"] + [row[0] for row in c]
        except: pass

    def validate_date(self, date_text):
        try:
            datetime.datetime.strptime(date_text, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def load_dropdowns(self):
        core_actions = ["In_Stock", "Consumed", "Discarded", "Manual Edit", "Deleted"]
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                c_act = conn.execute("SELECT DISTINCT action FROM AuditLog WHERE action IS NOT NULL ORDER BY action ASC")
                db_actions = [row[0] for row in c_act]
                for act in db_actions:
                    if act not in core_actions: core_actions.append(act)
        except Exception:
            pass 
            
        self.combo_filter_act['values'] = ["All Actions"] + core_actions
        self.combo_filter_act.set("All Actions")
        self.clear_filters()

    def apply_selection(self, combobox, listbox, callback):
        if listbox.curselection():
            combobox.set(listbox.get(listbox.curselection()))
            listbox.place_forget()
            callback()

    def update_floating_listbox(self, combobox, listbox, var, event):
        if not event or not hasattr(event, 'keysym') or event.keysym in ("Up", "Down", "Left", "Right", "Tab", "Return", "Escape"): 
            listbox.place_forget()
            return
        
        typed = var.get().strip()
        vals = combobox['values']
        
        exact_match = any(str(v).lower() == typed.lower() for v in vals)
        
        if typed and vals and not exact_match:
            listbox.delete(0, tk.END)
            for v in vals: listbox.insert(tk.END, v)
            
            x = combobox.winfo_rootx() - self.root.winfo_rootx()
            y = combobox.winfo_rooty() - self.root.winfo_rooty() + combobox.winfo_height()
            listbox.place(x=x, y=y, width=combobox.winfo_width(), height=min(120, len(vals)*20))
            listbox.lift()
        else:
            listbox.place_forget()

    def on_category_select(self, event=None):
        if event and hasattr(event, 'keysym') and event.keysym in ("Up", "Down", "Left", "Right", "Tab", "Return", "Escape"):
            return
            
        selected_cat = self.filter_cat_var.get().strip()
        
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                c_all_cat = conn.execute("SELECT DISTINCT category FROM Catalog WHERE category != '' ORDER BY category ASC")
                all_cats = [row[0] for row in c_all_cat]
                
                new_cat_values = ["All Categories"] + all_cats
                if selected_cat and selected_cat != "All Categories":
                    new_cat_values = ["All Categories"] + [c for c in all_cats if selected_cat.lower() in c.lower()]
                
                self.combo_filter_cat['values'] = new_cat_values

                if selected_cat == "All Categories" or not selected_cat:
                    c_prod = conn.execute("SELECT DISTINCT product_name FROM Catalog ORDER BY product_name ASC")
                else:
                    c_prod = conn.execute("SELECT DISTINCT product_name FROM Catalog WHERE category LIKE ? ORDER BY product_name ASC", (f"%{selected_cat}%",))
                
                self.combo_filter_prod['values'] = ["All Products"] + [row[0] for row in c_prod]
                
                if event and not hasattr(event, 'keysym'): 
                    self.combo_filter_prod.set("All Products")
        except Exception: 
            pass
            
        self.load_logs()
        self.update_floating_listbox(self.combo_filter_cat, self.cat_listbox, self.filter_cat_var, event)

    def on_product_type(self, event=None):
        if event and hasattr(event, 'keysym') and event.keysym in ("Up", "Down", "Left", "Right", "Tab", "Return", "Escape"):
            return
            
        selected_prod = self.filter_prod_var.get().strip()
        selected_cat = self.filter_cat_var.get().strip()
        
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                exact_match = conn.execute("SELECT category FROM Catalog WHERE product_name = ?", (selected_prod,)).fetchone()
                
                if exact_match:
                    self.combo_filter_cat.set(exact_match[0])
                    selected_cat = exact_match[0] 
                    self.combo_filter_cat['values'] = ["All Categories", exact_match[0]]
                else:
                    c_all_cat = conn.execute("SELECT DISTINCT category FROM Catalog WHERE category != '' ORDER BY category ASC")
                    self.combo_filter_cat['values'] = ["All Categories"] + [row[0] for row in c_all_cat]

                if selected_cat == "All Categories" or not selected_cat:
                    c_prod = conn.execute("SELECT DISTINCT product_name FROM Catalog ORDER BY product_name ASC")
                else:
                    c_prod = conn.execute("SELECT DISTINCT product_name FROM Catalog WHERE category LIKE ? ORDER BY product_name ASC", (f"%{selected_cat}%",))
                
                valid_prods = [row[0] for row in c_prod]
                new_prod_values = ["All Products"] + valid_prods
                
                if selected_prod and selected_prod != "All Products":
                    new_prod_values = ["All Products"] + [p for p in valid_prods if selected_prod.lower() in p.lower()]
                    
                self.combo_filter_prod['values'] = new_prod_values
        except Exception:
            pass
            
        self.load_logs()
        self.update_floating_listbox(self.combo_filter_prod, self.prod_listbox, self.filter_prod_var, event)

    def clear_filters(self):
        self.combo_filter_act.set("All Actions")
        self.combo_filter_cat.set("All Categories")
        self.combo_filter_prod.set("All Products")
        self.ent_search.delete(0, tk.END)
        self.ent_start.delete(0, tk.END)
        self.ent_end.delete(0, tk.END)
        self.cat_listbox.place_forget()
        self.prod_listbox.place_forget()
        self.on_category_select()

    def load_logs(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        
        f_act = self.filter_act_var.get().strip()
        f_cat = self.filter_cat_var.get().strip()
        f_prod = self.filter_prod_var.get().strip()
        f_search = self.ent_search.get().strip().lower()
        start_date = self.ent_start.get().strip()
        end_date = self.ent_end.get().strip()

        if start_date and not self.validate_date(start_date):
            return
        if end_date and not self.validate_date(end_date):
            return

        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                query = """
                    SELECT a.log_id, a.barcode, COALESCE(c.product_name, 'Unknown/Deleted'), u.username, a.action, a.timestamp
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
                    query += " AND c.category LIKE ?"
                    params.append(f"%{f_cat}%")
                if f_prod and f_prod != "All Products":
                    query += " AND c.product_name LIKE ?"
                    params.append(f"%{f_prod}%")
                if f_search:
                    query += " AND LOWER(a.barcode) LIKE ?"
                    params.append(f"%{f_search}%")
                if start_date:
                    query += " AND date(a.timestamp) >= ?"
                    params.append(start_date)
                if end_date:
                    query += " AND date(a.timestamp) <= ?"
                    params.append(end_date)

                query += " ORDER BY a.timestamp DESC"

                cursor = conn.execute(query, params)
                for row in cursor:
                    self.tree.insert("", "end", values=row)
                    
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load audit logs: {e}", parent=self.root)
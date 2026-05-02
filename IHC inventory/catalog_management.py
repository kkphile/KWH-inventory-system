import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class CatalogScreen:
    # 1. ADDED on_update to receive the signal
    def __init__(self, root, role, on_update=None):
        self.root = root
        self.role = role
        self.on_update = on_update # Save the callback
        self.root.title("KWH Inventory System - Catalog Management")
        
        window_width = 850
        window_height = 650
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        center_x = int(screen_width / 2 - window_width / 2)
        center_y = int(screen_height / 2 - window_height / 2)
        self.root.geometry(f"{window_width}x{window_height}+{center_x}+{center_y}")

        self.sort_states = {
            "ID": 0, "Name": 0, "Category": 0, "Stock": 0, "Threshold": 0
        }
        self.original_view_data = [] 
        
        self.header_names = {
            "ID": "ID", "Name": "Product Name", "Category": "Category",
            "Stock": "Current Stock", "Threshold": "Alert Threshold"
        }

        # --- Filter Section ---
        filter_frame = tk.Frame(self.root, pady=10, padx=20)
        filter_frame.pack(fill="x")
        
        tk.Label(filter_frame, text="Category:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.filter_cat_var = tk.StringVar()
        self.combo_filter_cat = ttk.Combobox(filter_frame, textvariable=self.filter_cat_var, state="readonly", width=15)
        self.combo_filter_cat.pack(side=tk.LEFT, padx=(5, 15))
        self.combo_filter_cat.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        
        tk.Label(filter_frame, text="Product:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.filter_prod_var = tk.StringVar()
        self.combo_filter_prod = ttk.Combobox(filter_frame, textvariable=self.filter_prod_var, state="readonly", width=20)
        self.combo_filter_prod.pack(side=tk.LEFT, padx=(5, 15))
        self.combo_filter_prod.bind("<<ComboboxSelected>>", lambda e: self.load_data())
        
        tk.Button(filter_frame, text="Clear Filters", bg="#95a5a6", fg="white", cursor="hand2", command=self.clear_filters).pack(side=tk.LEFT, padx=10)

        # --- Top Section: Product List ---
        list_frame = tk.LabelFrame(self.root, text="Product Catalog & Stock Levels", padx=10, pady=10)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        self.tree = ttk.Treeview(list_frame, columns=("ID", "Name", "Category", "Stock", "Threshold"), show='headings')
        
        for col in self.tree["columns"]:
            self.tree.heading(col, text=self.header_names[col], command=lambda c=col: self.cycle_sort(c))
        
        self.tree.column("Stock", width=100, anchor="center")
        self.tree.column("Threshold", width=120, anchor="center")
        
        if self.role == 'admin':
            self.tree["displaycolumns"] = ("Name", "Category", "Stock", "Threshold")
        else:
            self.tree["displaycolumns"] = ("Name", "Category", "Stock")
            
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<ButtonRelease-1>", self.select_item)

        # --- Bottom Section: Management Form ---
        if self.role == 'admin':
            form_frame = tk.LabelFrame(self.root, text="Manage Product Details", padx=10, pady=10)
            form_frame.pack(fill="x", padx=20, pady=15)

            tk.Label(form_frame, text="Product Name:").grid(row=0, column=0, padx=5, pady=5)
            self.ent_name = tk.Entry(form_frame, width=25)
            self.ent_name.grid(row=0, column=1, padx=5, pady=5)

            tk.Label(form_frame, text="Category:").grid(row=0, column=2, padx=5, pady=5)
            self.cat_var = tk.StringVar()
            self.combo_cat = ttk.Combobox(form_frame, textvariable=self.cat_var, width=18)
            self.combo_cat.grid(row=0, column=3, padx=5, pady=5)

            tk.Label(form_frame, text="Min Threshold:").grid(row=0, column=4, padx=5, pady=5)
            self.ent_thresh = tk.Entry(form_frame, width=10)
            self.ent_thresh.insert(0, "0") 
            self.ent_thresh.grid(row=0, column=5, padx=5, pady=5)

            btn_frame = tk.Frame(form_frame)
            btn_frame.grid(row=1, column=0, columnspan=6, pady=15)

            tk.Button(btn_frame, text="Add New Item", bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), width=15, command=self.add_product).pack(side=tk.LEFT, padx=10)
            tk.Button(btn_frame, text="Update Details", bg="#f39c12", fg="white", font=("Arial", 10, "bold"), width=15, command=self.update_product).pack(side=tk.LEFT, padx=10)
            tk.Button(btn_frame, text="Delete Product", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), width=15, command=self.delete_product).pack(side=tk.LEFT, padx=10)

        self.load_filters()
        self.load_data()

    def load_filters(self):
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                c_cat = conn.execute("SELECT DISTINCT category FROM Catalog WHERE category != '' ORDER BY category ASC")
                categories = [row[0] for row in c_cat]
                
                c_prod = conn.execute("SELECT DISTINCT product_name FROM Catalog ORDER BY product_name ASC")
                products = [row[0] for row in c_prod]

                if self.role == 'admin':
                    self.combo_cat['values'] = categories
                
                self.combo_filter_cat['values'] = ["All Categories"] + categories
                self.combo_filter_prod['values'] = ["All Products"] + products
                
                if not self.filter_cat_var.get(): self.combo_filter_cat.set("All Categories")
                if not self.filter_prod_var.get(): self.combo_filter_prod.set("All Products")
        except Exception:
            pass

    def clear_filters(self):
        self.combo_filter_cat.set("All Categories")
        self.combo_filter_prod.set("All Products")
        self.load_data()

    def clear_form(self, keep_category=False):
        if self.role != 'admin': return
        self.ent_name.delete(0, tk.END)
        if not keep_category:
            self.combo_cat.set('')
        self.ent_thresh.delete(0, tk.END)
        self.ent_thresh.insert(0, "0")

    def load_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.original_view_data = [] 
        
        filter_cat = self.filter_cat_var.get()
        filter_prod = self.filter_prod_var.get()
        
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                query = """
                    SELECT c.catalog_id, c.product_name, c.category, COUNT(i.item_id), c.low_stock_threshold 
                    FROM Catalog c
                    LEFT JOIN Inventory i ON c.catalog_id = i.catalog_id AND i.status = 'In_Stock'
                    WHERE 1=1
                """
                params = []
                
                if filter_cat and filter_cat != "All Categories":
                    query += " AND c.category = ?"
                    params.append(filter_cat)
                    
                if filter_prod and filter_prod != "All Products":
                    query += " AND c.product_name = ?"
                    params.append(filter_prod)
                    
                query += " GROUP BY c.catalog_id ORDER BY c.product_name ASC"
                
                cursor = conn.execute(query, params)
                for row in cursor: 
                    self.tree.insert("", "end", values=row)
                    self.original_view_data.append(row) 
                    
            for c in self.sort_states:
                self.sort_states[c] = 0
                self.tree.heading(c, text=self.header_names[c])
                
        except Exception as e: 
            messagebox.showerror("Error", f"Could not load catalog: {e}", parent=self.root)

    def cycle_sort(self, col):
        current_state = self.sort_states.get(col, 0)
        next_state = (current_state + 1) % 3
        
        for c in self.sort_states:
            self.sort_states[c] = 0
            self.tree.heading(c, text=self.header_names.get(c, c))
            
        self.sort_states[col] = next_state
        base_text = self.header_names.get(col, col)
        
        if next_state == 0:
            self.tree.heading(col, text=base_text)
            for i in self.tree.get_children(): self.tree.delete(i)
            for row in self.original_view_data:
                self.tree.insert("", "end", values=row)
                
        elif next_state == 1:
            self.tree.heading(col, text=f"{base_text} ▲")
            self.sort_tree_data(col, reverse=False)
            
        elif next_state == 2:
            self.tree.heading(col, text=f"{base_text} ▼")
            self.sort_tree_data(col, reverse=True)

    def sort_tree_data(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        
        def convert_to_number_if_possible(val):
            try:
                return float(val)
            except ValueError:
                return str(val).lower()
                
        l.sort(key=lambda t: convert_to_number_if_possible(t[0]), reverse=reverse)
        
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

    def select_item(self, event):
        if self.role != 'admin': return
        
        selected = self.tree.selection()
        if selected:
            row = self.tree.item(selected[0])['values']
            self.ent_name.delete(0, tk.END); self.ent_name.insert(0, row[1])
            self.combo_cat.set(row[2])
            self.ent_thresh.delete(0, tk.END); self.ent_thresh.insert(0, str(row[4]))

    def add_product(self):
        if self.role != 'admin': return
        name = self.ent_name.get().strip()
        cat = self.combo_cat.get().strip()
        raw_thresh = self.ent_thresh.get().strip()
        
        try:
            thresh = int(raw_thresh) if raw_thresh else 0
        except ValueError:
            thresh = 0
        
        if not name or not cat:
            messagebox.showwarning("Input Error", "Please provide both Name and Category.", parent=self.root)
            return
            
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                conn.execute("INSERT INTO Catalog (product_name, category, low_stock_threshold) VALUES (?, ?, ?)", (name, cat, thresh))
            
            self.load_filters()
            self.load_data()
            self.clear_form(keep_category=True)
            
            # 2. TRIGGER DASHBOARD REFRESH
            if self.on_update: self.on_update()
            
            self.ent_name.focus()
            messagebox.showinfo("Success", f"Product '{name}' added.", parent=self.root)
        except sqlite3.IntegrityError:
            messagebox.showerror("Duplicate Entry", "This product name already exists.", parent=self.root)

    def update_product(self):
        if self.role != 'admin': return
        selected = self.tree.selection()
        if not selected: return
        
        cat_id = self.tree.item(selected[0])['values'][0]
        raw_thresh = self.ent_thresh.get().strip()
        
        try:
            thresh = int(raw_thresh) if raw_thresh else 0
        except ValueError:
            thresh = 0
        
        warning_msg = "Overwrite this product's details?\n\nNOTE: Changing the name or category will retroactively alter how this item appears in past Audit Logs.\n\nProceed with update?"
        if messagebox.askyesno("Confirm Update", warning_msg, parent=self.root):
            try:
                with sqlite3.connect("KWH_Inventory_System.db") as conn:
                    conn.execute("UPDATE Catalog SET product_name=?, category=?, low_stock_threshold=? WHERE catalog_id=?", 
                                 (self.ent_name.get(), self.combo_cat.get().strip(), thresh, cat_id))
                self.load_filters()
                self.load_data()
                self.clear_form(keep_category=False)
                
                # 3. TRIGGER DASHBOARD REFRESH
                if self.on_update: self.on_update()
                
                messagebox.showinfo("Success", "Catalog entry updated.", parent=self.root)
            except Exception as e: 
                messagebox.showerror("Update Failed", str(e), parent=self.root)

    def delete_product(self):
        if self.role != 'admin': return
        selected = self.tree.selection()
        if not selected: return
        
        cat_id = self.tree.item(selected[0])['values'][0]
        
        warning_msg = "Permanently remove this product?\n\nCRITICAL WARNING: If this item has ever been received or consumed, deleting it will leave 'ghost' records in your historical Audit Logs.\n\nAre you absolutely sure?"
        if messagebox.askyesno("Confirm Deletion", warning_msg, icon='warning', parent=self.root):
            try:
                with sqlite3.connect("KWH_Inventory_System.db") as conn:
                    conn.execute("DELETE FROM Catalog WHERE catalog_id=?", (cat_id,))
                self.load_filters()
                self.load_data()
                self.clear_form(keep_category=False)
                
                # 4. TRIGGER DASHBOARD REFRESH
                if self.on_update: self.on_update()
                
            except Exception as e: 
                messagebox.showerror("Deletion Error", "Cannot delete product if items are in stock.", parent=self.root)
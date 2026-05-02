import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime

class InventoryScreen:
    # 1. Added on_update=None to the parameters
    def __init__(self, root, role, on_update=None):
        self.root = root
        self.role = role
        self.on_update = on_update # 2. Save the callback
        
        self.root.title("KWH Inventory System - Inventory Management")
        self.root.geometry("1100x650")

        # --- Sorting Tracking ---
        self.sort_states = {
            "Barcode": 0, "Product": 0, "Lot": 0, "Expiry": 0, "Status": 0
        }
        self.original_view_data = [] 

        # --- Filter Section ---
        filter_frame = tk.Frame(self.root, pady=10, padx=20)
        filter_frame.pack(fill="x")

        tk.Label(filter_frame, text="Category:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.filter_cat_var = tk.StringVar()
        self.combo_filter_cat = ttk.Combobox(filter_frame, textvariable=self.filter_cat_var, state="readonly", width=15)
        self.combo_filter_cat.pack(side=tk.LEFT, padx=(5, 10))
        self.combo_filter_cat.bind("<<ComboboxSelected>>", lambda e: self.load_data())

        tk.Label(filter_frame, text="Product:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.filter_prod_var = tk.StringVar()
        self.combo_filter_prod = ttk.Combobox(filter_frame, textvariable=self.filter_prod_var, state="readonly", width=20)
        self.combo_filter_prod.pack(side=tk.LEFT, padx=(5, 10))
        self.combo_filter_prod.bind("<<ComboboxSelected>>", lambda e: self.load_data())

        tk.Label(filter_frame, text="Barcode Search:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.ent_search = tk.Entry(filter_frame, width=15)
        self.ent_search.pack(side=tk.LEFT, padx=(5, 15))
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_data())

        tk.Button(filter_frame, text="Clear Filters", bg="#95a5a6", fg="white", cursor="hand2", command=self.clear_filters).pack(side=tk.LEFT)

        # --- Table Section ---
        list_frame = tk.LabelFrame(self.root, text="Current Physical Stock & History", padx=10, pady=10)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)

        self.tree = ttk.Treeview(list_frame, columns=("ID", "Barcode", "Product", "Lot", "Expiry", "Status"), show='headings')
        
        for col in self.tree["columns"][1:]: 
            self.tree.heading(col, text=col, command=lambda c=col: self.cycle_sort(c))
        
        self.tree["displaycolumns"] = ("Barcode", "Product", "Lot", "Expiry", "Status")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<ButtonRelease-1>", self.select_item)

        # --- Bottom Section: Management Form ---
        if self.role == 'admin':
            form_frame = tk.LabelFrame(self.root, text="Edit Specific Item", padx=10, pady=10)
            form_frame.pack(fill="x", padx=20, pady=15)

            tk.Label(form_frame, text="Barcode:").grid(row=0, column=0, padx=5, pady=5)
            self.ent_barcode_edit = tk.Entry(form_frame, width=18)
            self.ent_barcode_edit.grid(row=0, column=1, padx=5, pady=5)

            tk.Label(form_frame, text="Lot Number:").grid(row=0, column=2, padx=5, pady=5)
            self.ent_lot = tk.Entry(form_frame, width=15)
            self.ent_lot.grid(row=0, column=3, padx=5, pady=5)

            tk.Label(form_frame, text="Expiry (YYYY-MM-DD):").grid(row=0, column=4, padx=5, pady=5)
            self.ent_exp = tk.Entry(form_frame, width=15)
            self.ent_exp.grid(row=0, column=5, padx=5, pady=5)

            tk.Label(form_frame, text="Status:").grid(row=0, column=6, padx=5, pady=5)
            self.status_var = tk.StringVar()
            self.combo_status = ttk.Combobox(form_frame, textvariable=self.status_var, state="readonly", width=12)
            self.combo_status['values'] = ("In_Stock", "Consumed", "Discarded")
            self.combo_status.grid(row=0, column=7, padx=5, pady=5)

            btn_frame = tk.Frame(form_frame)
            btn_frame.grid(row=1, column=0, columnspan=8, pady=10)

            tk.Button(btn_frame, text="Update Item", bg="#f39c12", fg="white", font=("Arial", 10, "bold"), command=self.update_item, width=15).pack(side=tk.LEFT, padx=10)
            tk.Button(btn_frame, text="Delete Item", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), command=self.delete_item, width=15).pack(side=tk.LEFT, padx=10)

        self.load_filters()
        self.load_data()

    def validate_date(self, date_text):
        try:
            datetime.datetime.strptime(date_text, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def load_filters(self):
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                c_cat = conn.execute("SELECT DISTINCT category FROM Catalog WHERE category != '' ORDER BY category ASC")
                self.combo_filter_cat['values'] = ["All Categories"] + [row[0] for row in c_cat]
                
                c_prod = conn.execute("SELECT DISTINCT product_name FROM Catalog ORDER BY product_name ASC")
                self.combo_filter_prod['values'] = ["All Products"] + [row[0] for row in c_prod]
                
                self.combo_filter_cat.set("All Categories")
                self.combo_filter_prod.set("All Products")
        except Exception:
            pass

    def clear_filters(self):
        self.combo_filter_cat.set("All Categories")
        self.combo_filter_prod.set("All Products")
        self.ent_search.delete(0, tk.END)
        self.load_data()

    def load_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.original_view_data = [] 
        
        filter_cat = self.filter_cat_var.get()
        filter_prod = self.filter_prod_var.get()
        search_text = self.ent_search.get().strip().lower()

        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                query = """SELECT i.item_id, i.barcode, c.product_name, i.lot_number, 
                           strftime('%Y-%m-%d', i.expiry_date), i.status 
                           FROM Inventory i JOIN Catalog c ON i.catalog_id = c.catalog_id 
                           WHERE 1=1"""
                params = []

                if filter_cat and filter_cat != "All Categories":
                    query += " AND c.category = ?"
                    params.append(filter_cat)
                    
                if filter_prod and filter_prod != "All Products":
                    query += " AND c.product_name = ?"
                    params.append(filter_prod)
                
                if search_text:
                    query += " AND LOWER(i.barcode) LIKE ?"
                    params.append(f"%{search_text}%")

                query += " ORDER BY i.status DESC, i.expiry_date ASC"
                
                for row in conn.execute(query, params): 
                    self.tree.insert("", "end", values=row)
                    self.original_view_data.append(row) 
                    
            for c in self.sort_states:
                self.sort_states[c] = 0
                self.tree.heading(c, text=c)

        except Exception as e: 
            messagebox.showerror("Error", str(e), parent=self.root)

    def cycle_sort(self, col):
        current_state = self.sort_states[col]
        next_state = (current_state + 1) % 3
        
        for c in self.sort_states:
            self.sort_states[c] = 0
            self.tree.heading(c, text=c)
            
        self.sort_states[col] = next_state
        
        if next_state == 0:
            self.tree.heading(col, text=col)
            for i in self.tree.get_children(): self.tree.delete(i)
            for row in self.original_view_data:
                self.tree.insert("", "end", values=row)
                
        elif next_state == 1:
            self.tree.heading(col, text=f"{col} ▲")
            self.sort_tree_data(col, reverse=False)
            
        elif next_state == 2:
            self.tree.heading(col, text=f"{col} ▼")
            self.sort_tree_data(col, reverse=True)

    def sort_tree_data(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            self.tree.move(k, '', index)

    def select_item(self, event):
        if self.role != 'admin': return
        sel = self.tree.selection()
        if sel:
            row = self.tree.item(sel[0])['values']
            
            self.ent_barcode_edit.delete(0, tk.END)
            self.ent_barcode_edit.insert(0, row[1])
            
            self.ent_lot.delete(0, tk.END)
            self.ent_lot.insert(0, row[3])
            
            self.ent_exp.delete(0, tk.END)
            self.ent_exp.insert(0, row[4])
            
            self.combo_status.set(row[5])

    def update_item(self):
        sel = self.tree.selection()
        if not sel: return
        row_data = self.tree.item(sel[0])['values']
        
        item_id = row_data[0]
        old_barcode = row_data[1]
        old_status = row_data[5]
        
        new_barcode = self.ent_barcode_edit.get().strip()
        new_lot = self.ent_lot.get().strip()
        new_exp = self.ent_exp.get().strip()
        new_status = self.combo_status.get().strip()
        
        if not new_barcode:
            messagebox.showwarning("Input Error", "Barcode cannot be empty.", parent=self.root)
            return

        if not self.validate_date(new_exp) or not new_status:
            messagebox.showwarning("Error", "Invalid Date or Status.", parent=self.root)
            return
            
        audit_action = new_status if new_status != old_status else "Manual Edit"
        
        warning_message = "Update this item's details?"
        if old_barcode != new_barcode:
            warning_message += "\n\nWARNING: You are changing the barcode. This will alter the item's identity in the database."
            
        if messagebox.askyesno("Confirm Update", warning_message, parent=self.root):
            try:
                with sqlite3.connect("KWH_Inventory_System.db") as conn:
                    conn.execute("UPDATE Inventory SET barcode=?, lot_number=?, expiry_date=?, status=? WHERE item_id=?", 
                                 (new_barcode, new_lot, new_exp, new_status, item_id))
                    
                    conn.execute("INSERT INTO AuditLog (item_id, barcode, action) VALUES (?, ?, ?)", 
                                 (item_id, new_barcode, audit_action))
                                 
                self.load_data()
                
                self.ent_barcode_edit.delete(0, tk.END)
                self.ent_lot.delete(0, tk.END)
                self.ent_exp.delete(0, tk.END)
                self.combo_status.set('')
                
                # 3. TRIGGER INSTANT UPDATE 
                if self.on_update: self.on_update()
                
                messagebox.showinfo("Updated", "Item successfully updated.", parent=self.root)
            except Exception as e: 
                messagebox.showerror("Error", str(e), parent=self.root)

    def delete_item(self):
        sel = self.tree.selection()
        if not sel: return
        item_id = self.tree.item(sel[0])['values'][0]
        if messagebox.askyesno("Confirm Delete", "Remove this item entirely?", icon='warning', parent=self.root):
            try:
                with sqlite3.connect("KWH_Inventory_System.db") as conn:
                    conn.execute("DELETE FROM Inventory WHERE item_id=?", (item_id,))
                self.load_data()
                
                self.ent_barcode_edit.delete(0, tk.END)
                self.ent_lot.delete(0, tk.END)
                self.ent_exp.delete(0, tk.END)
                self.combo_status.set('')
                
                # 4. TRIGGER INSTANT UPDATE
                if self.on_update: self.on_update()
                
            except Exception as e: 
                messagebox.showerror("Error", str(e), parent=self.root)
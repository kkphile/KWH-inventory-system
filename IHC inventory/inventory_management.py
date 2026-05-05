import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
import re
from utils import is_valid_date

class InventoryScreen:
    def __init__(self, root, role, user_id=None, on_update=None):
        self.root = root
        self.role = role
        self.user_id = user_id if user_id else 1
        self.on_update = on_update
        
        self.root.title("KWH Inventory System - Inventory Management")
        self.root.geometry("1100x650")
        self.sort_states = {"Barcode": 0, "Product": 0, "Lot": 0, "Expiry Date": 0, "Received Date": 0, "Status": 0}
        self.original_view_data = [] 

        filter_frame = tk.Frame(self.root, pady=10, padx=20)
        filter_frame.pack(fill="x")
        
        tk.Label(filter_frame, text="Category:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.filter_cat_var = tk.StringVar()
        self.combo_filter_cat = ttk.Combobox(filter_frame, textvariable=self.filter_cat_var, width=15, postcommand=self.click_drop_cat)
        self.combo_filter_cat.pack(side=tk.LEFT, padx=(5, 10))
        self.combo_filter_cat.bind("<<ComboboxSelected>>", self.on_category_select)
        self.combo_filter_cat.bind("<KeyRelease>", self.on_category_select)
        
        tk.Label(filter_frame, text="Product:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.filter_prod_var = tk.StringVar()
        self.combo_filter_prod = ttk.Combobox(filter_frame, textvariable=self.filter_prod_var, width=20, postcommand=self.click_drop_prod)
        self.combo_filter_prod.pack(side=tk.LEFT, padx=(5, 10))
        self.combo_filter_prod.bind("<<ComboboxSelected>>", self.on_product_type)
        self.combo_filter_prod.bind("<KeyRelease>", self.on_product_type)
        
        tk.Label(filter_frame, text="Barcode Search:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.ent_search = tk.Entry(filter_frame, width=15)
        self.ent_search.pack(side=tk.LEFT, padx=(5, 15))
        self.ent_search.bind("<KeyRelease>", lambda e: self.load_data())
        
        tk.Button(filter_frame, text="Clear Filters", bg="#95a5a6", fg="white", cursor="hand2", command=self.clear_filters).pack(side=tk.LEFT)
        
        self.cat_listbox = tk.Listbox(self.root, font=("Arial", 10), bg="#fdfdfe", selectbackground="#3498db", relief=tk.SOLID, bd=1)
        self.prod_listbox = tk.Listbox(self.root, font=("Arial", 10), bg="#fdfdfe", selectbackground="#3498db", relief=tk.SOLID, bd=1)
        
        self.cat_listbox.bind("<ButtonRelease-1>", lambda e: self.apply_selection(self.combo_filter_cat, self.cat_listbox, self.on_category_select))
        self.prod_listbox.bind("<ButtonRelease-1>", lambda e: self.apply_selection(self.combo_filter_prod, self.prod_listbox, self.on_product_type))
        
        self.combo_filter_cat.bind("<FocusOut>", lambda e: self.cat_listbox.after(150, self.cat_listbox.place_forget))
        self.combo_filter_prod.bind("<FocusOut>", lambda e: self.prod_listbox.after(150, self.prod_listbox.place_forget))
        
        list_frame = tk.LabelFrame(self.root, text="Current Physical Stock & History", padx=10, pady=10)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        self.tree = ttk.Treeview(list_frame, columns=("ID", "Barcode", "Product", "Lot", "Expiry Date", "Received Date", "Status"), show='headings')
        for col in self.tree["columns"][1:]: 
            self.tree.heading(col, text=col, command=lambda c=col: self.cycle_sort(c))
            
        self.tree.column("Barcode", width=120, anchor="center")
        self.tree.column("Product", width=120, anchor="center") 
        self.tree.column("Lot", width=120, anchor="center")
        self.tree.column("Expiry Date", width=120, anchor="center")
        self.tree.column("Received Date", width=120, anchor="center")
        self.tree.column("Status", width=100, anchor="center")
        
        self.tree["displaycolumns"] = ("Barcode", "Product", "Lot", "Expiry Date", "Received Date", "Status")
        
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")
        
        self.tree.bind("<ButtonRelease-1>", self.select_item)
        
        if self.role == 'admin':
            self.edit_prod_listbox = tk.Listbox(self.root, font=("Arial", 10), bg="#fdfdfe", selectbackground="#3498db", relief=tk.SOLID, bd=1)
            self.edit_prod_listbox.bind("<ButtonRelease-1>", lambda e: self.apply_selection(self.combo_edit_prod, self.edit_prod_listbox))
            
            form_frame = tk.LabelFrame(self.root, text="Edit Specific Item", padx=10, pady=10)
            form_frame.pack(fill="x", padx=20, pady=15)
            
            tk.Label(form_frame, text="Barcode:").grid(row=0, column=0, padx=5, pady=5, sticky="e")
            self.ent_barcode_edit = tk.Entry(form_frame, width=18)
            self.ent_barcode_edit.grid(row=0, column=1, padx=5, pady=5)
            
            tk.Label(form_frame, text="Product:").grid(row=0, column=2, padx=5, pady=5, sticky="e")
            self.combo_edit_prod = ttk.Combobox(form_frame, width=22, postcommand=self.click_drop_edit_prod) 
            self.combo_edit_prod.grid(row=0, column=3, padx=5, pady=5)
            self.combo_edit_prod.bind("<<ComboboxSelected>>", self.on_edit_product_type)
            self.combo_edit_prod.bind("<KeyRelease>", self.on_edit_product_type)
            self.combo_edit_prod.bind("<FocusOut>", lambda e: self.edit_prod_listbox.after(150, self.edit_prod_listbox.place_forget))
            
            tk.Label(form_frame, text="Lot Number:").grid(row=0, column=4, padx=5, pady=5, sticky="e")
            self.ent_lot = tk.Entry(form_frame, width=15)
            self.ent_lot.grid(row=0, column=5, padx=5, pady=5)
            
            tk.Label(form_frame, text="Expiry Date (YYYY-MM-DD):").grid(row=1, column=0, padx=5, pady=5, sticky="e")
            self.ent_exp = tk.Entry(form_frame, width=15)
            self.ent_exp.grid(row=1, column=1, padx=5, pady=5, sticky="w")
            
            tk.Label(form_frame, text="Received Date (YYYY-MM-DD):").grid(row=1, column=2, padx=5, pady=5, sticky="e")
            self.ent_recv = tk.Entry(form_frame, width=15)
            self.ent_recv.grid(row=1, column=3, padx=5, pady=5, sticky="w")
            
            tk.Label(form_frame, text="Status:").grid(row=1, column=4, padx=5, pady=5, sticky="e")
            self.status_var = tk.StringVar()
            self.combo_status = ttk.Combobox(form_frame, textvariable=self.status_var, state="readonly", width=13)
            self.combo_status['values'] = ("In_Stock", "Consumed", "Discarded")
            self.combo_status.grid(row=1, column=5, padx=5, pady=5)
            
            btn_frame = tk.Frame(form_frame)
            btn_frame.grid(row=2, column=0, columnspan=6, pady=10)
            
            tk.Button(btn_frame, text="Update Item", bg="#f39c12", fg="white", font=("Arial", 10, "bold"), command=self.update_item, width=15).pack(side=tk.LEFT, padx=10)
            tk.Button(btn_frame, text="Delete Item", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), command=self.delete_item, width=15).pack(side=tk.LEFT, padx=10)
            
        self.clear_filters()

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

    def click_drop_edit_prod(self):
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                c = conn.execute("SELECT DISTINCT product_name FROM Catalog ORDER BY product_name ASC")
                self.combo_edit_prod['values'] = [row[0] for row in c]
        except: pass

    def apply_selection(self, combobox, listbox, callback=None):
        if listbox.curselection():
            combobox.set(listbox.get(listbox.curselection()))
            listbox.place_forget()
            if callback:
                callback()

    def update_floating_listbox(self, combobox, listbox, event):
        if not event or not hasattr(event, 'keysym') or event.keysym in ("Up", "Down", "Left", "Right", "Tab", "Return", "Escape"): 
            listbox.place_forget()
            return
        
        typed = combobox.get().strip()
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
        
        self.load_data()
        self.update_floating_listbox(self.combo_filter_cat, self.cat_listbox, event)

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
                    
                    if selected_prod == "All Products" or not selected_prod:
                        self.combo_filter_cat.set("All Categories")
                        selected_cat = "All Categories"
                        
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
        
        self.load_data()
        self.update_floating_listbox(self.combo_filter_prod, self.prod_listbox, event)

    def on_edit_product_type(self, event=None):
        if event and hasattr(event, 'keysym') and event.keysym in ("Up", "Down", "Left", "Right", "Tab", "Return", "Escape"):
            return
        
        typed = self.combo_edit_prod.get().strip()
        
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                c_all_prods = conn.execute("SELECT DISTINCT product_name FROM Catalog ORDER BY product_name ASC")
                all_prods = [row[0] for row in c_all_prods]
                
                if not typed:
                    self.combo_edit_prod['values'] = all_prods
                else:
                    self.combo_edit_prod['values'] = [p for p in all_prods if typed.lower() in p.lower()]
        except Exception:
            pass
        
        self.update_floating_listbox(self.combo_edit_prod, self.edit_prod_listbox, event)

    def clear_filters(self):
        self.combo_filter_cat.set("All Categories")
        self.combo_filter_prod.set("All Products")
        self.ent_search.delete(0, tk.END)
        self.cat_listbox.place_forget()
        self.prod_listbox.place_forget()
        if hasattr(self, 'edit_prod_listbox'):
            self.edit_prod_listbox.place_forget()
        self.on_category_select()

    def load_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)
        self.original_view_data = [] 

        f_cat = self.filter_cat_var.get().strip()
        f_prod = self.filter_prod_var.get().strip()
        s_txt = self.ent_search.get().strip().lower()

        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                if self.role == 'admin' and hasattr(self, 'combo_edit_prod'):
                    c_all_prods = conn.execute("SELECT DISTINCT product_name FROM Catalog ORDER BY product_name ASC")
                    self.combo_edit_prod['values'] = [row[0] for row in c_all_prods]

                query = """SELECT i.item_id, i.barcode, c.product_name, i.lot_number,
                            strftime('%Y-%m-%d', i.expiry_date), strftime('%Y-%m-%d', i.received_date), i.status
                            FROM Inventory i JOIN Catalog c ON i.catalog_id = c.catalog_id
                            WHERE 1=1"""
                params = []
                
                if f_cat and f_cat != "All Categories":
                    query += " AND c.category LIKE ?"
                    params.append(f"%{f_cat}%")
                if f_prod and f_prod != "All Products":
                    query += " AND c.product_name LIKE ?"
                    params.append(f"%{f_prod}%")
                if s_txt:
                    query += " AND LOWER(i.barcode) LIKE ?"
                    params.append(f"%{s_txt}%")
                    
                query += " ORDER BY i.status DESC, i.expiry_date ASC"
                
                for row in conn.execute(query, params): 
                    self.tree.insert("", "end", values=row)
                    self.original_view_data.append(row)
                    
            for c in self.sort_states:
                self.sort_states[c] = 0
                self.tree.heading(c, text=c)
                
        except Exception as e: messagebox.showerror("Error", str(e), parent=self.root)

    def cycle_sort(self, col):
        curr = self.sort_states[col]
        nxt = (curr + 1) % 3
        
        for c in self.sort_states:
            self.sort_states[c] = 0
            self.tree.heading(c, text=c)
            
        self.sort_states[col] = nxt
        
        if nxt == 0:
            self.tree.heading(col, text=col)
            for i in self.tree.get_children(): self.tree.delete(i)
            for row in self.original_view_data: self.tree.insert("", "end", values=row)
        elif nxt == 1:
            self.tree.heading(col, text=f"{col} ▲")
            self.sort_tree_data(col, reverse=False)
        elif nxt == 2:
            self.tree.heading(col, text=f"{col} ▼")
            self.sort_tree_data(col, reverse=True)

    def sort_tree_data(self, col, reverse):
        l = [(self.tree.set(k, col), k) for k in self.tree.get_children('')]
        
        def natural_sort_key(item):
            val = item[0]
            return [int(text) if text.isdigit() else text.lower() for text in re.split('([0-9]+)', str(val))]
            
        l.sort(key=natural_sort_key, reverse=reverse)
        
        for index, (val, k) in enumerate(l): 
            self.tree.move(k, '', index)

    def select_item(self, event):
        if self.role != 'admin': return
        sel = self.tree.selection()
        if sel:
            row = self.tree.item(sel[0])['values']
            self.ent_barcode_edit.delete(0, tk.END); self.ent_barcode_edit.insert(0, row[1])
            self.combo_edit_prod.set(row[2]) 
            self.ent_lot.delete(0, tk.END); self.ent_lot.insert(0, row[3])
            self.ent_exp.delete(0, tk.END); self.ent_exp.insert(0, row[4])
            self.ent_recv.delete(0, tk.END); self.ent_recv.insert(0, row[5]) 
            self.combo_status.set(row[6])

    def update_item(self):
        sel = self.tree.selection()
        if not sel: return
        
        row_data = self.tree.item(sel[0])['values']
        item_id = int(row_data[0])
        old_barcode = str(row_data[1]).strip()
        old_prod = str(row_data[2]).strip()
        old_lot = str(row_data[3]).strip()
        old_exp = str(row_data[4]).strip()
        old_recv = str(row_data[5]).strip()
        old_status = str(row_data[6]).strip()
        
        new_barcode = self.ent_barcode_edit.get().strip()
        new_prod = self.combo_edit_prod.get().strip()
        new_lot = self.ent_lot.get().strip()
        new_status = self.combo_status.get().strip()
        
        raw_exp = self.ent_exp.get().strip()
        raw_recv = self.ent_recv.get().strip()
        
        # Format the dates
        new_exp = is_valid_date(raw_exp, self.root)
        new_recv = is_valid_date(raw_recv, self.root)
        
        if not new_barcode or not new_prod:
            messagebox.showwarning("Input Error", "Barcode and Product cannot be empty.", parent=self.root)
            return

        if not new_status:
            messagebox.showwarning("Error", "Status cannot be empty.", parent=self.root)
            return
            
        if new_exp is False or new_recv is False:
            return
            
        status_changed = (new_status != old_status)
        details_changed = (new_barcode != old_barcode) or (new_lot != old_lot) or (new_exp != old_exp) or (new_recv != old_recv) or (new_prod != old_prod)
        
        actions_to_log = []
        if details_changed: actions_to_log.append("Manual Edit")
        if status_changed: actions_to_log.append(new_status)
        if not actions_to_log: actions_to_log.append("Manual Edit")
            
        warning_msg = "Update this item's details?"
        if messagebox.askyesno("Confirm Update", warning_msg, parent=self.root):
            try:
                timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                with sqlite3.connect("KWH_Inventory_System.db") as conn:
                    cat_res = conn.execute("SELECT catalog_id FROM Catalog WHERE product_name=?", (new_prod,)).fetchone()
                    if not cat_res:
                        messagebox.showwarning("Error", "Selected product does not exist in the Catalog.", parent=self.root)
                        return
                    new_cat_id = cat_res[0]
                    
                    # Passing the new nicely formatted dates to the database
                    conn.execute("UPDATE Inventory SET barcode=?, catalog_id=?, lot_number=?, expiry_date=?, received_date=?, status=? WHERE item_id=?",
                                  (new_barcode, new_cat_id, new_lot, new_exp, new_recv, new_status, item_id))
                    
                    for action in actions_to_log:
                        conn.execute("INSERT INTO AuditLog (item_id, barcode, user_id, action, timestamp) VALUES (?, ?, ?, ?, ?)",
                                      (item_id, new_barcode, self.user_id, action, timestamp_str))
                                  
                self.load_data()
                self.ent_barcode_edit.delete(0, tk.END)
                self.combo_edit_prod.set('')
                self.ent_lot.delete(0, tk.END)
                self.ent_exp.delete(0, tk.END)
                self.ent_recv.delete(0, tk.END) 
                self.combo_status.set('')
                
                if self.on_update: self.on_update()
                messagebox.showinfo("Updated", "Item successfully updated.", parent=self.root)
            except Exception as e: messagebox.showerror("Error", str(e), parent=self.root)

    def delete_item(self):
        sel = self.tree.selection()
        if not sel: return
        row_data = self.tree.item(sel[0])['values']
        
        item_id = int(row_data[0])
        barcode_val = str(row_data[1]).strip()
        
        if messagebox.askyesno("Confirm Delete", "Remove this item entirely?", icon='warning', parent=self.root):
            try:
                timestamp_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                with sqlite3.connect("KWH_Inventory_System.db") as conn:
                    conn.execute("DELETE FROM Inventory WHERE item_id=?", (item_id,))
                    conn.execute("INSERT INTO AuditLog (item_id, barcode, user_id, action, timestamp) VALUES (?, ?, ?, 'Deleted', ?)",
                                  (item_id, barcode_val, self.user_id, timestamp_str))
                                  
                self.load_data()
                self.ent_barcode_edit.delete(0, tk.END)
                self.combo_edit_prod.set('')
                self.ent_lot.delete(0, tk.END)
                self.ent_exp.delete(0, tk.END)
                self.ent_recv.delete(0, tk.END)
                self.combo_status.set('')
                
                if self.on_update: self.on_update()
            except Exception as e: messagebox.showerror("Error", str(e), parent=self.root)
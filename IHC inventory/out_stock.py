import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime
from utils import is_valid_date

class OutStockScreen:
    def __init__(self, root, user_id, on_update=None):
        self.root = root
        self.user_id = user_id
        self.on_update = on_update 
        
        self.root.title("KWH Inventory System - Scan Out")
        self.root.geometry("900x750")

        # --- Frame 1: General Details ---
        setup_frame = tk.LabelFrame(self.root, text="Step 1: General Details (Applies to both methods)", padx=20, pady=10)
        setup_frame.pack(fill="x", padx=20, pady=(15, 5))

        tk.Label(setup_frame, text="Out-Stock Date:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, pady=5)
        self.ent_date = tk.Entry(setup_frame, width=20)
        self.ent_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.ent_date.pack(side=tk.LEFT, padx=15, pady=5)

        # --- Frame 2: Rapid Scan Out ---
        scan_frame = tk.LabelFrame(self.root, text="Step 2 (Method A): Rapid Barcode Scan", padx=20, pady=10)
        scan_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(scan_frame, text="Scan Barcode:", font=("Arial", 10, "bold")).pack(side=tk.LEFT, pady=5)
        self.ent_barcode = tk.Entry(scan_frame, width=25, font=("Arial", 12))
        self.ent_barcode.pack(side=tk.LEFT, padx=15, pady=5)
        self.ent_barcode.focus() 
        self.ent_barcode.bind("<Return>", lambda e: self.consume_item_via_scan())
        
        tk.Button(scan_frame, text="Consume by Scan", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), command=self.consume_item_via_scan).pack(side=tk.LEFT, padx=10)

        # --- Frame 3: Manual List ---
        list_frame = tk.LabelFrame(self.root, text="Step 2 (Method B): Manual Selection from Inventory", padx=10, pady=10)
        list_frame.pack(fill="both", expand=True, padx=20, pady=(5, 20))

        filter_frame = tk.Frame(list_frame)
        filter_frame.pack(fill="x", pady=(0, 10))

        tk.Label(filter_frame, text="Category:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.filter_cat_var = tk.StringVar()
        self.combo_filter_cat = ttk.Combobox(filter_frame, textvariable=self.filter_cat_var, width=15, postcommand=self.click_drop_cat)
        self.combo_filter_cat.pack(side=tk.LEFT, padx=(5, 15))
        self.combo_filter_cat.bind("<<ComboboxSelected>>", self.on_category_select)
        self.combo_filter_cat.bind("<KeyRelease>", self.on_category_select)
        
        tk.Label(filter_frame, text="Product:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.filter_prod_var = tk.StringVar()
        self.combo_filter_prod = ttk.Combobox(filter_frame, textvariable=self.filter_prod_var, width=20, postcommand=self.click_drop_prod)
        self.combo_filter_prod.pack(side=tk.LEFT, padx=(5, 15))
        self.combo_filter_prod.bind("<<ComboboxSelected>>", self.on_product_type)
        self.combo_filter_prod.bind("<KeyRelease>", self.on_product_type)

        tk.Button(filter_frame, text="Clear Filters", bg="#95a5a6", fg="white", cursor="hand2", command=self.clear_filters).pack(side=tk.LEFT, padx=10)
        tk.Button(filter_frame, text="Consume Selected Item", bg="#f39c12", fg="white", font=("Arial", 10, "bold"), cursor="hand2", command=self.consume_item_via_list).pack(side=tk.RIGHT, padx=10)

        # Floating Listboxes for Filters
        self.cat_listbox = tk.Listbox(self.root, font=("Arial", 10), bg="#fdfdfe", selectbackground="#3498db", relief=tk.SOLID, bd=1)
        self.prod_listbox = tk.Listbox(self.root, font=("Arial", 10), bg="#fdfdfe", selectbackground="#3498db", relief=tk.SOLID, bd=1)
        
        self.cat_listbox.bind("<ButtonRelease-1>", lambda e: self.apply_selection(self.combo_filter_cat, self.cat_listbox, self.on_category_select))
        self.prod_listbox.bind("<ButtonRelease-1>", lambda e: self.apply_selection(self.combo_filter_prod, self.prod_listbox, self.on_product_type))
        
        self.combo_filter_cat.bind("<FocusOut>", lambda e: self.cat_listbox.after(150, self.cat_listbox.place_forget))
        self.combo_filter_prod.bind("<FocusOut>", lambda e: self.prod_listbox.after(150, self.prod_listbox.place_forget))

        # Treeview setup
        self.tree = ttk.Treeview(list_frame, columns=("ID", "Barcode", "Product", "Lot", "Expiry Date", "Received Date"), show='headings')
        
        self.tree["displaycolumns"] = ("Barcode", "Product", "Lot", "Expiry Date", "Received Date")

        self.tree.heading("Barcode", text="Barcode")
        self.tree.heading("Product", text="Product")
        self.tree.heading("Lot", text="Lot Number")
        self.tree.heading("Expiry Date", text="Expiry Date")
        self.tree.heading("Received Date", text="Received Date")

        self.tree.column("Barcode", width=120, anchor="center")
        self.tree.column("Product", width=200, anchor="w")
        self.tree.column("Lot", width=100, anchor="center")
        self.tree.column("Expiry Date", width=100, anchor="center")
        self.tree.column("Received Date", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill="both", expand=True)
        scrollbar.pack(side=tk.RIGHT, fill="y")

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
        except Exception: pass
        
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
        except Exception: pass
        
        self.load_data()
        self.update_floating_listbox(self.combo_filter_prod, self.prod_listbox, event)

    def clear_filters(self):
        self.combo_filter_cat.set("All Categories")
        self.combo_filter_prod.set("All Products")
        self.cat_listbox.place_forget()
        self.prod_listbox.place_forget()
        self.on_category_select()

    def load_data(self):
        for i in self.tree.get_children(): self.tree.delete(i)

        f_cat = self.filter_cat_var.get().strip()
        f_prod = self.filter_prod_var.get().strip()

        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                query = """SELECT i.item_id, i.barcode, c.product_name, i.lot_number,
                            IFNULL(strftime('%Y-%m-%d', i.expiry_date), i.expiry_date),
                            IFNULL(strftime('%Y-%m-%d', i.received_date), i.received_date)
                            FROM Inventory i JOIN Catalog c ON i.catalog_id = c.catalog_id
                            WHERE i.status = 'In_Stock'"""
                params = []
                
                if f_cat and f_cat != "All Categories":
                    query += " AND c.category LIKE ?"
                    params.append(f"%{f_cat}%")
                if f_prod and f_prod != "All Products":
                    query += " AND c.product_name LIKE ?"
                    params.append(f"%{f_prod}%")
                    
                # --- THE FIX: Changed default sort to received_date ascending ---
                query += " ORDER BY i.received_date ASC"
                
                for row in conn.execute(query, params): 
                    self.tree.insert("", "end", values=row)
                    
        except Exception as e: 
            messagebox.showerror("Error", str(e), parent=self.root)

    def check_and_consume(self, item_id, barcode_val, catalog_id):
        raw_out_date = self.ent_date.get().strip()
        out_date = is_valid_date(raw_out_date, self.root)

        if not out_date: 
            return

        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT item_id, lot_number, expiry_date, barcode 
                    FROM Inventory WHERE catalog_id=? AND status='In_Stock'
                """, (catalog_id,))
                rows = cursor.fetchall()

                parsed_items = []
                for r in rows:
                    exp_val = str(r[2]).strip()
                    try:
                        dt = datetime.datetime.strptime(exp_val, '%Y-%m-%d').date()
                    except:
                        dt = datetime.date(2099, 1, 1) 
                    parsed_items.append({'id': r[0], 'lot': r[1], 'dt': dt, 'exp': exp_val, 'barcode': r[3]})

                if not parsed_items:
                    messagebox.showwarning("Out of Stock", "No items currently in-stock for this product.", parent=self.root)
                    return

                parsed_items.sort(key=lambda x: x['dt'])
                oldest_item = parsed_items[0]
                selected_item = next((p for p in parsed_items if p['id'] == item_id), None)

                if not selected_item:
                    messagebox.showerror("Error", "Selected item is no longer marked as 'In_Stock'.", parent=self.root)
                    return

                # FEFO Check
                if selected_item['dt'] > oldest_item['dt']:
                    warn_msg = (f"  FEFO ALERT!  \n\nYou are consuming: Lot {selected_item['lot']} (Exp: {selected_item['exp']})\n"
                               f"Older stock exists: Lot {oldest_item['lot']} (Exp: {oldest_item['exp']})\n\n"
                               f"Do you want to bypass the older stock?")
                    if not messagebox.askyesno("Confirm Override", warn_msg, icon='warning', parent=self.root):
                        self.ent_barcode.delete(0, tk.END)
                        return

                timestamp = f"{out_date} {datetime.datetime.now().strftime('%H:%M:%S')}"

                cursor.execute("UPDATE Inventory SET status='Consumed' WHERE item_id=?", (selected_item['id'],))
                cursor.execute("INSERT INTO AuditLog (item_id, barcode, user_id, action, timestamp) VALUES (?, ?, ?, 'Consumed', ?)",
                                (selected_item['id'], barcode_val, self.user_id, timestamp))
                
                cursor.execute("SELECT product_name FROM Catalog WHERE catalog_id=?", (catalog_id,))
                product_name = cursor.fetchone()[0]
                
                conn.commit()
            
            if self.on_update: 
                self.on_update()
                
            self.load_data() 
            
            success_msg = f"Successfully consumed!\n\nProduct: {product_name}\nLot Number: {selected_item['lot']}"
            messagebox.showinfo("Success", success_msg, parent=self.root)
            
            self.ent_barcode.delete(0, tk.END)
            self.ent_barcode.focus()

        except Exception as e:
            messagebox.showerror("System Error", str(e), parent=self.root)

    def consume_item_via_scan(self):
        barcode_input = self.ent_barcode.get().strip()
        if not barcode_input: return 

        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT status FROM Inventory WHERE barcode=?", (barcode_input,))
                status_results = cursor.fetchall()
                
                if not status_results:
                    messagebox.showerror("Error", "Barcode not found in database.", parent=self.root)
                    return
                    
                statuses = [row[0] for row in status_results]
                
                if 'Flagged' in statuses and 'In_Stock' not in statuses:
                    messagebox.showerror(
                        "Quarantine Alert", 
                        "🛑 This item is currently FLAGGED! 🛑\n\nIt cannot be consumed. Please set it aside for administrator review.", 
                        parent=self.root
                    )
                    self.ent_barcode.delete(0, tk.END)
                    return

                cursor.execute("SELECT item_id, catalog_id FROM Inventory WHERE barcode=? AND status='In_Stock' ORDER BY expiry_date ASC LIMIT 1", (barcode_input,))
                res = cursor.fetchone()
                
                if not res:
                    messagebox.showerror("Error", "Barcode is not currently In-Stock.", parent=self.root)
                    return
                    
                item_id, catalog_id = res[0], res[1]
                
            self.check_and_consume(item_id, barcode_input, catalog_id)
            
        except Exception as e:
            messagebox.showerror("System Error", str(e), parent=self.root)

    def consume_item_via_list(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Error", "Please select an item from the list.", parent=self.root)
            return
            
        row_data = self.tree.item(selected[0])['values']
        item_id = int(row_data[0])
        barcode_val = str(row_data[1]).strip()

        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT catalog_id FROM Inventory WHERE item_id=?", (item_id,))
                res = cursor.fetchone()
                
                if not res:
                    messagebox.showerror("Error", "Item not found in database.", parent=self.root)
                    return
                    
                catalog_id = res[0]
                
            self.check_and_consume(item_id, barcode_val, catalog_id)
            
        except Exception as e:
            messagebox.showerror("System Error", str(e), parent=self.root)
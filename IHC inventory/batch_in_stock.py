import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime

class BatchInStockScreen:
    def __init__(self, root, user_id, on_update=None):
        self.root = root
        self.user_id = user_id
        self.on_update = on_update 
        self.root.title("KWH Inventory System - Stock In")
        self.root.geometry("500x500")

        frame = tk.LabelFrame(self.root, text="Rapid Scan In-Stock", padx=20, pady=20)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(frame, text="1. Set Batch Details:", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
        tk.Label(frame, text="Product:").grid(row=1, column=0, pady=5, sticky="e")
        
        self.cat_var = tk.StringVar()
        # --- THE FIX: Postcommand added here too ---
        self.cb_product = ttk.Combobox(frame, textvariable=self.cat_var, width=28, postcommand=self.click_drop_prod) 
        self.cb_product.grid(row=1, column=1, pady=5)
        
        self.cb_product.bind("<<ComboboxSelected>>", self.on_product_type)
        self.cb_product.bind("<KeyRelease>", self.on_product_type)

        self.prod_listbox = tk.Listbox(self.root, font=("Arial", 10), bg="#fdfdfe", selectbackground="#3498db", relief=tk.SOLID, bd=1)
        self.prod_listbox.bind("<ButtonRelease-1>", lambda e: self.apply_selection())
        self.cb_product.bind("<FocusOut>", lambda e: self.prod_listbox.after(150, self.prod_listbox.place_forget))

        self.cat_map = {}
        self.all_products = [] 
        self.load_products()

        tk.Label(frame, text="Lot Number:").grid(row=2, column=0, pady=5, sticky="e")
        self.ent_lot = tk.Entry(frame, width=31)
        self.ent_lot.grid(row=2, column=1, pady=5)

        tk.Label(frame, text="Expiry Date (YYYY-MM-DD):").grid(row=3, column=0, pady=5, sticky="e")
        self.ent_exp = tk.Entry(frame, width=31)
        self.ent_exp.grid(row=3, column=1, pady=5)

        tk.Label(frame, text="Received Date:").grid(row=4, column=0, pady=5, sticky="e")
        self.ent_recv = tk.Entry(frame, width=31)
        self.ent_recv.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.ent_recv.grid(row=4, column=1, pady=5)

        tk.Label(frame, text="Quantity (Per Scan):").grid(row=5, column=0, pady=5, sticky="e")
        self.ent_qty = tk.Entry(frame, width=31)
        self.ent_qty.insert(0, "1")
        self.ent_qty.grid(row=5, column=1, pady=5)

        ttk.Separator(frame, orient='horizontal').grid(row=6, column=0, columnspan=2, sticky='ew', pady=15)
        tk.Label(frame, text="2. Scan Barcode:", font=("Arial", 11, "bold")).grid(row=7, column=0, columnspan=2, pady=(0, 5), sticky="w")
        
        self.ent_barcode = tk.Entry(frame, width=30, font=("Arial", 14))
        self.ent_barcode.grid(row=8, column=0, columnspan=2, pady=5)
        self.ent_barcode.focus()
        self.ent_barcode.bind("<Return>", lambda e: self.receive_item())

        tk.Button(frame, text="Add", bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), command=self.receive_item).grid(row=9, column=0, columnspan=2, pady=15)

    def load_products(self):
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                for row in conn.execute("SELECT catalog_id, product_name FROM Catalog ORDER BY product_name"):
                    self.cat_map[row[1]] = row[0]
            self.all_products = list(self.cat_map.keys())
            self.cb_product['values'] = self.all_products
        except Exception as e: messagebox.showerror("Error", str(e))

    def click_drop_prod(self):
        self.cb_product['values'] = self.all_products

    def apply_selection(self):
        if self.prod_listbox.curselection():
            self.cat_var.set(self.prod_listbox.get(self.prod_listbox.curselection()))
            self.prod_listbox.place_forget()

    def update_floating_listbox(self, event):
        if not event or not hasattr(event, 'keysym') or event.keysym in ("Up", "Down", "Left", "Right", "Tab", "Return", "Escape"): 
            self.prod_listbox.place_forget()
            return
        
        typed = self.cat_var.get().strip()
        vals = self.cb_product['values']
        
        exact_match = any(str(v).lower() == typed.lower() for v in vals)
        
        if typed and vals and not exact_match:
            self.prod_listbox.delete(0, tk.END)
            for v in vals: self.prod_listbox.insert(tk.END, v)
            
            x = self.cb_product.winfo_rootx() - self.root.winfo_rootx()
            y = self.cb_product.winfo_rooty() - self.root.winfo_rooty() + self.cb_product.winfo_height()
            self.prod_listbox.place(x=x, y=y, width=self.cb_product.winfo_width(), height=min(120, len(vals)*20))
            self.prod_listbox.lift()
        else:
            self.prod_listbox.place_forget()

    def on_product_type(self, event=None):
        if event and hasattr(event, 'keysym') and event.keysym in ("Up", "Down", "Left", "Right", "Tab", "Return", "Escape"):
            return
            
        typed = self.cat_var.get().strip()
        
        if not typed:
            self.cb_product['values'] = self.all_products
        else:
            filtered_prods = [p for p in self.all_products if typed.lower() in p.lower()]
            self.cb_product['values'] = filtered_prods

        self.update_floating_listbox(event)

    def validate_date(self, date_text):
        try:
            datetime.datetime.strptime(date_text, '%Y-%m-%d')
            return True
        except ValueError: return False

    def receive_item(self):
        barcode = self.ent_barcode.get().strip()
        prod = self.cb_product.get().strip()
        lot = self.ent_lot.get().strip()
        exp = self.ent_exp.get().strip()
        recv = self.ent_recv.get().strip()
        raw_qty = self.ent_qty.get().strip()

        if not barcode: return
        
        if prod not in self.cat_map:
            messagebox.showwarning("Invalid Product", "Please select a valid product from the list.")
            self.ent_barcode.delete(0, tk.END)
            return

        if not all([prod, lot, exp, recv, raw_qty]):
            messagebox.showwarning("Setup Error", "Fill all Batch Details.")
            self.ent_barcode.delete(0, tk.END)
            return

        if not self.validate_date(exp) or not self.validate_date(recv):
            messagebox.showwarning("Date Error", "Use YYYY-MM-DD.")
            self.ent_barcode.delete(0, tk.END)
            return

        try:
            qty = int(raw_qty)
            if qty <= 0: raise ValueError
            cat_id = self.cat_map[prod]
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                cursor = conn.cursor()
                for _ in range(qty):
                    cursor.execute("INSERT INTO Inventory (barcode, catalog_id, lot_number, expiry_date, received_date, status) VALUES (?, ?, ?, ?, ?, 'In_Stock')", 
                                   (barcode, cat_id, lot, exp, recv))
                    item_id = cursor.lastrowid
                    cursor.execute("INSERT INTO AuditLog (item_id, barcode, user_id, action, timestamp) VALUES (?, ?, ?, 'In_Stock', ?)", 
                                   (item_id, barcode, self.user_id, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            if self.on_update: self.on_update()
            
            if qty == 1:
                success_msg = f"Successfully added 1 item.\n\nProduct: {prod}\nLot Number: {lot}"
            else:
                success_msg = f"Successfully added {qty} items!\n\nProduct: {prod}\nLot Number: {lot}"
                
            messagebox.showinfo("Success", success_msg)
            
            self.ent_barcode.delete(0, tk.END)
            self.ent_barcode.focus()
            
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.ent_barcode.delete(0, tk.END)
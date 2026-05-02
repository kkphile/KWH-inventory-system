import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime

class BatchInStockScreen:
    def __init__(self, root, user_id):
        self.root = root
        self.user_id = user_id
        self.root.title("KWH Inventory System - Receive Stock")
        self.root.geometry("500x500")

        frame = tk.LabelFrame(self.root, text="Rapid Scan In-Stock", padx=20, pady=20)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- STEP 1: SETUP (These fields stay "sticky" between scans) ---
        tk.Label(frame, text="1. Set Batch Details:", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        tk.Label(frame, text="Product:").grid(row=1, column=0, pady=5, sticky="e")
        self.cat_var = tk.StringVar()
        self.cb_product = ttk.Combobox(frame, textvariable=self.cat_var, state="readonly", width=28)
        self.cb_product.grid(row=1, column=1, pady=5)
        self.cat_map = {}
        self.load_products()

        tk.Label(frame, text="Lot Number:").grid(row=2, column=0, pady=5, sticky="e")
        self.ent_lot = tk.Entry(frame, width=31)
        self.ent_lot.grid(row=2, column=1, pady=5)

        tk.Label(frame, text="Expiry (YYYY-MM-DD):").grid(row=3, column=0, pady=5, sticky="e")
        self.ent_exp = tk.Entry(frame, width=31)
        self.ent_exp.grid(row=3, column=1, pady=5)

        tk.Label(frame, text="Received Date:").grid(row=4, column=0, pady=5, sticky="e")
        self.ent_recv = tk.Entry(frame, width=31)
        self.ent_recv.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.ent_recv.grid(row=4, column=1, pady=5)

        tk.Label(frame, text="Quantity (Per Scan):").grid(row=5, column=0, pady=5, sticky="e")
        self.ent_qty = tk.Entry(frame, width=31)
        self.ent_qty.insert(0, "1") # Defaults to 1 for one-by-one rapid scanning
        self.ent_qty.grid(row=5, column=1, pady=5)

        # --- DIVIDER ---
        ttk.Separator(frame, orient='horizontal').grid(row=6, column=0, columnspan=2, sticky='ew', pady=15)

        # --- STEP 2: TRIGGER ---
        tk.Label(frame, text="2. Scan Barcode:", font=("Arial", 11, "bold")).grid(row=7, column=0, columnspan=2, pady=(0, 5), sticky="w")
        
        self.ent_barcode = tk.Entry(frame, width=30, font=("Arial", 14))
        self.ent_barcode.grid(row=8, column=0, columnspan=2, pady=5)
        
        # Cursor automatically waits here for immediate scanning
        self.ent_barcode.focus()

        # The scanner triggers the receive_item function automatically via the Enter key
        self.ent_barcode.bind("<Return>", lambda e: self.receive_item())

        # Cleaned up button text
        tk.Button(frame, text="Add", bg="#2ecc71", fg="white", font=("Arial", 10, "bold"), command=self.receive_item).grid(row=9, column=0, columnspan=2, pady=15)

    def load_products(self):
        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                for row in conn.execute("SELECT catalog_id, product_name FROM Catalog ORDER BY product_name"):
                    self.cat_map[row[1]] = row[0]
            self.cb_product['values'] = list(self.cat_map.keys())
        except Exception as e: 
            messagebox.showerror("Error", str(e), parent=self.root)

    def validate_date(self, date_text):
        try:
            datetime.datetime.strptime(date_text, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def receive_item(self):
        barcode = self.ent_barcode.get().strip()
        prod = self.cb_product.get()
        lot = self.ent_lot.get().strip()
        exp = self.ent_exp.get().strip()
        recv = self.ent_recv.get().strip()
        raw_qty = self.ent_qty.get().strip()

        if not barcode: return

        # Safety Lock: Prevents scanning if the top section isn't filled out
        if not all([prod, lot, exp, recv, raw_qty]):
            messagebox.showwarning("Setup Error", "Please fill out all Batch Details (Product, Lot, Expiry) before scanning.", parent=self.root)
            self.ent_barcode.delete(0, tk.END)
            return

        if not self.validate_date(exp) or not self.validate_date(recv):
            messagebox.showwarning("Date Format Error", "Ensure dates are YYYY-MM-DD format.", parent=self.root)
            self.ent_barcode.delete(0, tk.END)
            return

        try:
            qty = int(raw_qty)
            if qty <= 0: raise ValueError
        except ValueError:
            messagebox.showwarning("Quantity Error", "Quantity must be a number greater than 0.", parent=self.root)
            self.ent_barcode.delete(0, tk.END)
            return

        cat_id = self.cat_map[prod]

        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                cursor = conn.cursor()
                
                # Insert the new items (Duplicate blocker removed!)
                for _ in range(qty):
                    cursor.execute("INSERT INTO Inventory (barcode, catalog_id, lot_number, expiry_date, received_date, status) VALUES (?, ?, ?, ?, ?, 'In_Stock')", 
                                   (barcode, cat_id, lot, exp, recv))
                    item_id = cursor.lastrowid
                    cursor.execute("INSERT INTO AuditLog (item_id, barcode, user_id, action, timestamp) VALUES (?, ?, ?, 'In_Stock', ?)", 
                                   (item_id, barcode, self.user_id, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            
            # Show a brief success message
            messagebox.showinfo("Success", f"Added Barcode: {barcode}\n(Lot: {lot})", parent=self.root)
            
            # Instantly clear the barcode and reset the cursor for the next scan
            self.ent_barcode.delete(0, tk.END)
            self.ent_barcode.focus()
            
        except Exception as e:
            messagebox.showerror("Database Error", str(e), parent=self.root)
            self.ent_barcode.delete(0, tk.END)
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime

class OutStockScreen:
    def __init__(self, root, user_id):
        self.root = root
        self.user_id = user_id
        self.root.title("KWH Inventory System - Scan Out")
        self.root.geometry("500x320") # Resized slightly to perfectly match the In-Stock proportions

        frame = tk.LabelFrame(self.root, text="Rapid Scan Out", padx=20, pady=20)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Configure columns so inputs align perfectly like the In-Stock page
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=1)

        # --- STEP 1: SETUP ---
        tk.Label(frame, text="1. Setup Details:", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")

        tk.Label(frame, text="Out-Stock Date:").grid(row=1, column=0, pady=5, sticky="e")
        self.ent_date = tk.Entry(frame, width=31)
        self.ent_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.ent_date.grid(row=1, column=1, pady=5, sticky="w")

        # --- DIVIDER ---
        ttk.Separator(frame, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky='ew', pady=20)

        # --- STEP 2: TRIGGER ---
        tk.Label(frame, text="2. Scan Barcode:", font=("Arial", 11, "bold")).grid(row=3, column=0, columnspan=2, pady=(0, 5), sticky="w")
        
        self.ent_barcode = tk.Entry(frame, width=30, font=("Arial", 14))
        self.ent_barcode.grid(row=4, column=0, columnspan=2, pady=5)
        
        # Cursor starts here for immediate scanning
        self.ent_barcode.focus() 

        # Scanner triggers the consume_item function automatically via the Enter key
        self.ent_barcode.bind("<Return>", lambda e: self.consume_item())

        tk.Button(frame, text="Consume", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), width=15, command=self.consume_item).grid(row=5, column=0, columnspan=2, pady=15)

    def validate_date(self, date_text):
        try:
            datetime.datetime.strptime(date_text, '%Y-%m-%d')
            return True
        except ValueError:
            return False

    def consume_item(self):
        barcode_input = self.ent_barcode.get().strip()
        out_date = self.ent_date.get().strip()

        if not barcode_input: return
        
        # Safety Lock: Validates date before processing any items
        if not self.validate_date(out_date):
            messagebox.showwarning("Date Error", "Please provide a valid YYYY-MM-DD date before scanning.", parent=self.root)
            self.ent_barcode.delete(0, tk.END)
            return

        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                cursor = conn.cursor()
                
                # Identify Product Family
                cursor.execute("SELECT catalog_id FROM Inventory WHERE barcode=?", (barcode_input,))
                res = cursor.fetchone()
                if not res:
                    messagebox.showerror("Error", "Barcode not found in inventory.", parent=self.root)
                    self.ent_barcode.delete(0, tk.END)
                    return
                cat_id = res[0]

                # Find all siblings (other lots/boxes)
                cursor.execute("""
                    SELECT i.item_id, i.lot_number, i.expiry_date, i.barcode 
                    FROM Inventory i 
                    WHERE i.catalog_id=? AND i.status='In_Stock'
                """, (cat_id,))
                rows = cursor.fetchall()

                parsed_items = []
                for r in rows:
                    exp_val = str(r[2]).strip().split()[0]
                    try:
                        dt = datetime.datetime.strptime(exp_val, '%Y-%m-%d').date()
                    except:
                        dt = datetime.date(2099, 1, 1)
                    
                    parsed_items.append({
                        'id': r[0], 'lot': str(r[1]).strip(), 'dt': dt, 'exp': exp_val, 'barcode': r[3]
                    })

                if not parsed_items:
                    messagebox.showwarning("Out of Stock", "No items in-stock for this product.", parent=self.root)
                    self.ent_barcode.delete(0, tk.END)
                    return

                # Sort by FEFO
                parsed_items.sort(key=lambda x: x['dt'])
                oldest_item = parsed_items[0]

                # Match scan to physical lot
                selected_item = None
                for p in parsed_items:
                    if p['barcode'] == barcode_input:
                        selected_item = p
                        break

                if not selected_item:
                    messagebox.showerror("Error", "Could not match scan to an In_Stock item.", parent=self.root)
                    self.ent_barcode.delete(0, tk.END)
                    return

                # FEFO Warning Logic
                if selected_item['dt'] > oldest_item['dt']:
                    warn_msg = (
                        f"🚨 FEFO ALERT! 🚨\n\n"
                        f"You scanned: Lot {selected_item['lot']} (Exp: {selected_item['exp']})\n"
                        f"BUT older stock exists: Lot {oldest_item['lot']} (Exp: {oldest_item['exp']})\n\n"
                        f"Do you want to bypass FEFO?"
                    )
                    if not messagebox.askyesno("Confirm Override", warn_msg, icon='warning', parent=self.root):
                        self.ent_barcode.delete(0, tk.END)
                        return

                # Process consumption
                timestamp = f"{out_date} {datetime.datetime.now().strftime('%H:%M:%S')}"
                cursor.execute("UPDATE Inventory SET status='Consumed' WHERE item_id=?", (selected_item['id'],))
                cursor.execute("INSERT INTO AuditLog (item_id, barcode, action, timestamp) VALUES (?, ?, 'Consumed', ?)", 
                               (selected_item['id'], selected_item['barcode'], timestamp))
                
                messagebox.showinfo("Success", f"Consumed Lot: {selected_item['lot']}", parent=self.root)
                
                # Ready for the next box
                self.ent_barcode.delete(0, tk.END)
                self.ent_barcode.focus()

        except Exception as e:
            messagebox.showerror("System Error", str(e), parent=self.root)
            self.ent_barcode.delete(0, tk.END)
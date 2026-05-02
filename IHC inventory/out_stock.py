import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
import datetime

class OutStockScreen:
    def __init__(self, root, user_id, on_update=None):
        self.root = root
        self.user_id = user_id
        self.on_update = on_update 
        
        self.root.title("KWH Inventory System - Scan Out")
        self.root.geometry("500x320")

        frame = tk.LabelFrame(self.root, text="Rapid Scan Out", padx=20, pady=20)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(frame, text="1. Setup Details:", font=("Arial", 11, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 10), sticky="w")
        tk.Label(frame, text="Out-Stock Date:").grid(row=1, column=0, pady=5, sticky="e")
        self.ent_date = tk.Entry(frame, width=31)
        self.ent_date.insert(0, datetime.date.today().strftime("%Y-%m-%d"))
        self.ent_date.grid(row=1, column=1, pady=5, sticky="w")

        ttk.Separator(frame, orient='horizontal').grid(row=2, column=0, columnspan=2, sticky='ew', pady=20)
        tk.Label(frame, text="2. Scan Barcode:", font=("Arial", 11, "bold")).grid(row=3, column=0, columnspan=2, pady=(0, 5), sticky="w")
        
        self.ent_barcode = tk.Entry(frame, width=30, font=("Arial", 14))
        self.ent_barcode.grid(row=4, column=0, columnspan=2, pady=5)
        self.ent_barcode.focus() 
        self.ent_barcode.bind("<Return>", lambda e: self.consume_item())

        tk.Button(frame, text="Consume", bg="#e74c3c", fg="white", font=("Arial", 10, "bold"), width=15, command=self.consume_item).grid(row=5, column=0, columnspan=2, pady=15)

    def validate_date(self, date_text):
        try:
            datetime.datetime.strptime(date_text, '%Y-%m-%d')
            return True
        except ValueError: return False

    def consume_item(self):
        barcode_input = self.ent_barcode.get().strip()
        out_date = self.ent_date.get().strip()

        if not barcode_input: return
        if not self.validate_date(out_date):
            messagebox.showwarning("Date Error", "Please provide a valid YYYY-MM-DD date.", parent=self.root)
            return

        try:
            with sqlite3.connect("KWH_Inventory_System.db") as conn:
                cursor = conn.cursor()
                
                cursor.execute("SELECT catalog_id FROM Inventory WHERE barcode=?", (barcode_input,))
                res = cursor.fetchone()
                if not res:
                    messagebox.showerror("Error", "Barcode not found in inventory.", parent=self.root)
                    return
                cat_id = res[0]

                cursor.execute("""
                    SELECT item_id, lot_number, expiry_date, barcode 
                    FROM Inventory WHERE catalog_id=? AND status='In_Stock'
                """, (cat_id,))
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

                selected_item = next((p for p in parsed_items if p['barcode'] == barcode_input), None)

                if not selected_item:
                    messagebox.showerror("Error", "This specific barcode is not marked as 'In_Stock'.", parent=self.root)
                    return

                if selected_item['dt'] > oldest_item['dt']:
                    warn_msg = (f"🚨 FEFO ALERT! 🚨\n\nYou scanned: Lot {selected_item['lot']} (Exp: {selected_item['exp']})\n"
                               f"Older stock exists: Lot {oldest_item['lot']} (Exp: {oldest_item['exp']})\n\n"
                               f"Do you want to bypass the older stock?")
                    if not messagebox.askyesno("Confirm Override", warn_msg, icon='warning', parent=self.root):
                        self.ent_barcode.delete(0, tk.END)
                        return

                timestamp = f"{out_date} {datetime.datetime.now().strftime('%H:%M:%S')}"
                cursor.execute("UPDATE Inventory SET status='Consumed' WHERE item_id=?", (selected_item['id'],))
                cursor.execute("INSERT INTO AuditLog (item_id, barcode, user_id, action, timestamp) VALUES (?, ?, ?, 'Consumed', ?)", 
                               (selected_item['id'], barcode_input, self.user_id, timestamp))
                
                # FIX: Force the database to save immediately before telling the dashboard to refresh
                conn.commit()
                
            # Now that it is officially saved, tell the dashboard to update!
            if self.on_update: 
                self.on_update()
            
            messagebox.showinfo("Success", f"Consumed Lot: {selected_item['lot']}", parent=self.root)
            self.ent_barcode.delete(0, tk.END)
            self.ent_barcode.focus()

        except Exception as e:
            messagebox.showerror("System Error", str(e), parent=self.root)

import sqlite3
import csv
import datetime
import os

def import_from_csv(csv_filename):
    if not os.path.exists(csv_filename):
        print(f"Error: Could not find {csv_filename}. Please ensure it is in the same folder.")
        return

    admin_user_id = 1 

    try:
        with sqlite3.connect("KWH_Inventory_System.db") as conn:
            cursor = conn.cursor()
            
            with open(csv_filename, mode='r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                
                success_count = 0
                
                for row in reader:
                    prod_name = row.get('Product Name', '').strip()
                    category = row.get('Category', '').strip()
                    threshold = row.get('Low Stock Threshold', '0').strip()
                    barcode = row.get('Barcode', '').strip()
                    lot = row.get('Lot Number', '').strip()
                    exp_date = row.get('Expiry Date', '').strip()
                    recv_date = row.get('Received Date', '').strip()
                    
                    # --- NEW: Grab the Quantity (Defaults to 1 if blank or missing) ---
                    qty_str = row.get('Quantity', '1').strip()
                    try:
                        quantity = int(qty_str)
                    except ValueError:
                        quantity = 1 # Fallback to 1 if they typed text instead of a number

                    if not prod_name or not barcode:
                        continue

                    # 1. Handle the Catalog
                    cursor.execute("SELECT catalog_id FROM Catalog WHERE product_name=?", (prod_name,))
                    cat_result = cursor.fetchone()
                    
                    if cat_result:
                        catalog_id = cat_result[0]
                    else:
                        cursor.execute("INSERT INTO Catalog (product_name, category, low_stock_threshold) VALUES (?, ?, ?)",
                                       (prod_name, category, int(threshold) if threshold.isdigit() else 0))
                        catalog_id = cursor.lastrowid

                    # --- NEW: Loop based on the Quantity ---
                    for _ in range(quantity):
                        # 2. Insert into Inventory
                        cursor.execute("""
                            INSERT INTO Inventory (barcode, catalog_id, lot_number, expiry_date, received_date, status) 
                            VALUES (?, ?, ?, ?, ?, 'In_Stock')
                        """, (barcode, catalog_id, lot, exp_date, recv_date))
                        
                        item_id = cursor.lastrowid
                        
                        # 3. Add to Audit Log
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute("""
                            INSERT INTO AuditLog (item_id, barcode, user_id, action, timestamp) 
                            VALUES (?, ?, ?, 'Legacy Import', ?)
                        """, (item_id, barcode, admin_user_id, timestamp))

                        success_count += 1

            conn.commit()
            print(f"✅ Migration Complete! Successfully imported {success_count} total physical items.")

    except Exception as e:
        print(f"❌ An error occurred during import: {e}")

if __name__ == "__main__":
    print("Starting Data Migration...")
    import_from_csv("old_records.csv")
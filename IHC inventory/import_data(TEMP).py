import sqlite3
import csv
import datetime
import os

def format_import_date(date_text):
    """
    Silently checks and formats a date string for bulk imports.
    Understands multiple formats and translates them to standard YYYY-MM-DD.
    Returns the padded string, "/" if empty, or False if invalid.
    """
    cleaned_date = date_text.strip()
    if not cleaned_date:
        return "/" # Replace empty date fields with a slash

    # A list of date formats we want the script to understand
    accepted_formats = [
        "%d/%m/%Y",  # Matches your CSV: 15/6/2026 or 15/06/2026
        "%Y-%m-%d",  # Standard format: 2026-06-15
        "%m/%d/%Y"   # US format (just in case!): 6/15/2026
    ]

    for fmt in accepted_formats:
        try:
            parsed_date = datetime.datetime.strptime(cleaned_date, fmt)
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            continue
            
    return False 

def import_data():
    db_path = "KWH_Inventory_System.db"
    csv_path = "old_records.csv"

    if not os.path.exists(csv_path):
        print(f"Error: Cannot find {csv_path}. Please make sure it is in the same folder.")
        return

    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            with open(csv_path, 'r', encoding='utf-8-sig') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):
                    
                    barcode = row.get('Barcode', '').strip()
                    product_name = row.get('Product', '').strip()
                    category = row.get('Category', '').strip()
                    
                    # Handle empty Lot Numbers
                    lot = row.get('Lot', '').strip()
                    if not lot:
                        lot = "/"
                    
                    raw_expiry = row.get('Expiry Date', '').strip()
                    raw_received = row.get('Received Date', '').strip()
                    
                    raw_qty = row.get('Quantity', '1').strip()
                    try:
                        quantity = int(raw_qty)
                    except ValueError:
                        quantity = 1 
                    
                    if not barcode or not product_name:
                        print(f"Skipping row {row_num}: Missing Barcode or Product Name.")
                        continue
                        
                    # Format dates or replace with "/" if empty
                    expiry = format_import_date(raw_expiry)
                    received = format_import_date(raw_received)
                    
                    if expiry is False or received is False:
                        print(f"Skipping row {row_num}: Invalid date format. Please use DD/MM/YYYY or YYYY-MM-DD.")
                        continue
                        
                    cursor.execute("SELECT catalog_id FROM Catalog WHERE product_name = ?", (product_name,))
                    cat_result = cursor.fetchone()
                    
                    if cat_result:
                        catalog_id = cat_result[0] 
                    else:
                        cursor.execute("INSERT INTO Catalog (product_name, category, low_stock_threshold) VALUES (?, ?, ?)", 
                                       (product_name, category, 0))
                        catalog_id = cursor.lastrowid
                        
                    for _ in range(quantity):
                        cursor.execute("""
                            INSERT INTO Inventory (barcode, catalog_id, lot_number, expiry_date, received_date, status)
                            VALUES (?, ?, ?, ?, ?, 'In_Stock')
                        """, (barcode, catalog_id, lot, expiry, received))
                        
                        item_id = cursor.lastrowid
                        
                        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        cursor.execute("""
                            INSERT INTO AuditLog (item_id, barcode, user_id, action, timestamp)
                            VALUES (?, ?, ?, 'Legacy Import', ?)
                        """, (item_id, barcode, 1, timestamp)) 
                    
                    print(f"Row {row_num}: Successfully imported {quantity}x of {product_name}")
                    
            print("\nData imported successfully! Your database and audit logs are fully updated.")
            
    except Exception as e:
        print(f"An error occurred during import: {e}")

if __name__ == "__main__":
    import_data()
import sqlite3
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def setup_database():
    conn = sqlite3.connect("KWH_Inventory_System.db")
    cursor = conn.cursor()

    # --- THE FIX: We added 'is_active INTEGER DEFAULT 1' to the native creation script ---
    cursor.execute('''CREATE TABLE IF NOT EXISTS Users (
                        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        role TEXT NOT NULL,
                        is_active INTEGER DEFAULT 1)''')

    # Safety Check: If the table was already created without the column, this adds it safely
    cursor.execute("PRAGMA table_info(Users)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'is_active' not in columns:
        cursor.execute("ALTER TABLE Users ADD COLUMN is_active INTEGER DEFAULT 1")

    cursor.execute('''CREATE TABLE IF NOT EXISTS Catalog (
                        catalog_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_name TEXT UNIQUE NOT NULL, 
                        category TEXT NOT NULL,
                        low_stock_threshold INTEGER DEFAULT 0)''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS Inventory (
                        item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        barcode TEXT,
                        catalog_id INTEGER,
                        lot_number TEXT,
                        expiry_date DATE,
                        received_date DATE,
                        status TEXT DEFAULT 'In_Stock', 
                        FOREIGN KEY(catalog_id) REFERENCES Catalog(catalog_id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS AuditLog (
                        log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        item_id INTEGER,
                        barcode TEXT,
                        user_id INTEGER,
                        action TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY(item_id) REFERENCES Inventory(item_id),
                        FOREIGN KEY(user_id) REFERENCES Users(user_id))''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS Notes (
                        note_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        username TEXT NOT NULL,
                        content TEXT NOT NULL,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP)''')

    # Explicitly creating the default admin with the is_active flag set to 1
    cursor.execute("INSERT OR IGNORE INTO Users (username, password_hash, role, is_active) VALUES (?, ?, ?, 1)",
                    ('admin', hash_password('password123'), 'admin'))

    conn.commit()
    conn.close()
    print("KWH_Inventory_System database initialized successfully.")

if __name__ == "__main__":
    setup_database()
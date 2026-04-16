import sqlite3

def init_db():
    print("[*] Initializing Smart Router database schema...")
    conn = sqlite3.connect('router.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            mac_address TEXT PRIMARY KEY,
            ip_address TEXT,
            vendor TEXT,
            custom_name TEXT,
            device_type TEXT,
            threshold INTEGER DEFAULT 500,
            is_throttled INTEGER DEFAULT 0,
            throttle_lift_time TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS firewall_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            src_ip TEXT NOT NULL,
            dest_ip TEXT NOT NULL,
            dest_port TEXT NOT NULL,
            description TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
import sqlite3

def init_db():
    conn = sqlite3.connect('router_data.db')
    c = conn.cursor()
    
    # Create the devices table
    c.execute('''
        CREATE TABLE IF NOT EXISTS devices (
            ip_address TEXT NOT NULL,
            mac_address TEXT PRIMARY KEY,
            vendor TEXT,
            interface TEXT,
            device_type TEXT,
            custom_name TEXT,
            description TEXT
        )
    ''')
    
    c.execute('''
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
import subprocess
import re
import sqlite3
import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from mac_vendor_lookup import MacLookup

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

mac = MacLookup()
try:
    mac.update_vendors()
except Exception as e:
    print(f"Error updating MAC vendors: {e}")

# Helpers
def get_db_connection():
    conn = sqlite3.connect('router_data.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/devices', methods=['GET'])
def get_devices():
    # Run the Address Resolution command to get the list of devices
    result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
    output = result.stdout

    # --- SUBNET CONFIGURATION ---
    SUBNET_PREFIX = "192.168.137."
    ROUTER_IP = "192.168.137.1"
    BROADCAST_IP = "192.168.137.255"
    
    devices = []
    
    for line in output.split('\n'):
        parts = line.split()
        
        # Parse the device entries
        if len(parts) >= 2 and '.' in parts[0] and '-' in parts[1]: # Basic check for IP and MAC format
            ip_address = parts[0]
            mac_address = parts[1].replace('-', ':').lower() # Normalize MAC address format
                
            # Ignore multicast and broadcast addresses
            if not ip_address.startswith(SUBNET_PREFIX):
                continue
            
            if ip_address == ROUTER_IP or ip_address == BROADCAST_IP:
                continue

            # Get the vendor name from the MAC address
            try:
                vendor = mac.lookup(mac_address)
            except Exception as e:
                vendor = "Unknown"
                print(f"Error looking up MAC address {mac_address}: {e}")
                pass
            
            devices.append({
                'ip': ip_address,
                'mac': mac_address,
                'vendor': vendor,
                'interface': ROUTER_IP,
                "device_type": "Unknown Type",
                "custom_name": "New Device",
                "description": ""
            })
    
    # Let's synch with database
    conn = get_db_connection()
    c = conn.cursor()
    enriched_devices = []
    
    for device in devices:
        c.execute('SELECT * FROM devices WHERE mac_address = ?', (device['mac'],))
        row = c.fetchone()
        
        if row is None:
            # New device, insert into database
            c.execute('''
                INSERT INTO devices (ip_address, mac_address, vendor, interface, device_type, custom_name, description)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                device['ip'], device['mac'],device['vendor'],
                device['interface'], device['device_type'], device['custom_name'],
                device['description']
            ))
            conn.commit()
            enriched_devices.append(device)
        else:
            # Known device - Update Ip 
            c.execute('''
                UPDATE devices
                SET ip_address = ?, vendor = ?, interface = ?
                WHERE mac_address = ?
            ''', (
                device['ip'], device['vendor'], device['interface'], device['mac']
            ))
            conn.commit()
            device['device_type'] = row['device_type']
            device['custom_name'] = row['custom_name']
            device['description'] = row['description']
            enriched_devices.append(device)
    
    conn.close()
    return jsonify(enriched_devices)

@app.route('/api/devices/<mac>', methods=['POST'])
def update_device(mac):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update the custom fields in the database
    cursor.execute('''
        UPDATE devices 
        SET custom_name = ?, device_type = ?, description = ?
        WHERE mac = ?
    ''', (data.get('custom_name'), data.get('device_type'), data.get('description'), mac))
    
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": "Device updated"})

# Global dictionary to track running background captures
active_captures = {}

# REPLACE "X" WITH YOUR ACTUAL TSHARK INTERFACE NUMBER
TSHARK_INTERFACE = "6" 

@app.route('/api/captures/start', methods=['POST'])
def start_capture():
    data = request.json
    mac = data.get('mac')
    ip = data.get('ip')
    capture_type = data.get('type') # 'duration' or 'packets'
    value = str(data.get('value')) # e.g., '60' seconds or '100' packets
    filename = data.get('filename', f"capture_{mac.replace(':', '')}.pcap")
    
    # Get the exact, absolute path to where app.py is located
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    CAPTURE_DIR = os.path.join(BASE_DIR, 'captures')

    # Ensure the folder exists right next to app.py
    if not os.path.exists(CAPTURE_DIR):
        os.makedirs(CAPTURE_DIR)
        
    filepath = os.path.join(CAPTURE_DIR, filename)
    
    # Prevent starting multiple captures for the same device
    if mac in active_captures:
        return jsonify({"status": "error", "message": "Capture already running for this device"}), 400

    # Build the tshark command
    TSHARK_PATH = r"C:\Program Files\Wireshark\tshark.exe"
    cmd = [TSHARK_PATH, '-i', TSHARK_INTERFACE, '-f', f"host {ip}"]
    
    if capture_type == 'duration':
        cmd.extend(['-a', f"duration:{value}"])
    elif capture_type == 'packets':
        cmd.extend(['-c', value])
        
    cmd.extend(['-w', filepath])
    
    try:
        # Popen starts the process in the background and DOES NOT block Flask
        process = subprocess.Popen(cmd)
        
        # Save the process so we can kill it later if needed
        active_captures[mac] = {
            "process": process,
            "ip": ip,
            "filename": filename,
            "start_time": time.time()
        }
        
        return jsonify({"status": "success", "message": f"Capture started for {ip}", "filename": filename})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/captures/stop', methods=['POST'])
def stop_capture():
    data = request.json
    mac = data.get('mac')
    
    if mac not in active_captures:
        return jsonify({"status": "error", "message": "No active capture found for this device"}), 404
        
    # Grab the background process and terminate it
    process = active_captures[mac]['process']
    process.terminate() 
    
    del active_captures[mac]
    return jsonify({"status": "success", "message": f"Capture terminated manually. File saved as {active_captures.get(mac, {}).get('filename', 'unknown')}"})
    
@app.route('/api/captures/status', methods=['GET'])
def capture_status():
    # Housekeeping: automatically remove captures that finished naturally
    to_remove = []
    for mac, cap_data in active_captures.items():
        if cap_data['process'].poll() is not None:
            to_remove.append(mac)
            
    for mac in to_remove:
        del active_captures[mac]
        
    # Return a list of currently running captures
    status_list = [{"mac": k, "ip": v["ip"], "filename": v["filename"]} for k, v in active_captures.items()]
    return jsonify(status_list)


@app.route('/api/firewall', methods=['GET', 'POST'])
def manage_firewall():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # I am adding new firewall rules
        data = request.json
        cursor.execute('''
            INSERT INTO firewall_rules (src_ip, dest_ip, dest_port, description)
            VALUES (?, ?, ?, ?)
        ''', (data.get('src_ip', 'ANY'), data.get('dest_ip', 'ANY'), str(data.get('dest_port', 'ANY')), data.get('description', '')))
        
        conn.commit()
        conn.close()
        return jsonify({"status": "success", "message": "Firewall rule activated."})

    else:
        # GET request: List all firewalls rules
        cursor.execute('SELECT * FROM firewall_rules')
        rules = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return jsonify(rules)



if __name__ == '__main__':
    app.run(port=5000, debug=True)
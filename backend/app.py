import subprocess
import re
from flask import Flask, jsonify
from flask_cors import CORS
from mac_vendor_lookup import MacLookup

app = Flask(__name__)
CORS(app) # Enable CORS for all routes

mac = MacLookup()
try:
    mac.update_vendors()
except Exception as e:
    print(f"Error updating MAC vendors: {e}")

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
    current_interface = None
    
    for line in output.split('\n'):
        parts = line.split()
        
        # Parse the device entries
        if len(parts) >= 2 and '.' in parts[0] and '-' in parts[1]: # Basic check for IP and MAC format
            ip_address = parts[0]
            mac_address = parts[1].replace('-', ':').lower() # Normalize MAC address format
                
            # Ignore multicast and broadcast addresses
            if not ip_address.startswith(SUBNET_PREFIX) or not ip_address == BROADCAST_IP:
                continue

            # Get the vendor name from the MAC address
            try:
                vendor = MacLookup.lookup(mac_address)
            except Exception as e:
                vendor = "Unknown"
                print(f"Error looking up MAC address {mac_address}: {e}")
                pass
            
            devices.append({
                'ip': ip_address,
                'mac': mac_address,
                'vendor': vendor,
                'interface': current_interface,
                "device_type": "Unknown Type",
                "custom_name": "New Device",
                "description": ""
            })

    return jsonify(devices)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
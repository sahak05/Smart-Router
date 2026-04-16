import pydivert
import sqlite3
import time
import threading
from alert_system import send_breach_alert

# --- GLOBAL MEMORY CACHES ---
allow_list = []
devices_cache = {}
packet_tracker = {}

DATABASE_NAME = 'router.db'

# --- DATABASE SYNC THREAD ---
def sync_database_state():
    """Runs in the background every 3 seconds to pull latest rules and thresholds."""
    global allow_list, devices_cache
    while True:
        try:
            conn = sqlite3.connect(DATABASE_NAME)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            cursor.execute("SELECT src_ip, dest_ip, dest_port FROM firewall_rules")
            allow_list = [dict(row) for row in cursor.fetchall()]
            
            cursor.execute("SELECT ip_address, threshold, is_throttled, throttle_lift_time FROM devices WHERE ip_address IS NOT NULL")
            new_cache = {}
            for row in cursor.fetchall():
                new_cache[row['ip_address']] = {
                    'threshold': row['threshold'] or 500,
                    'is_throttled': row['is_throttled'] or 0,
                    'lift_time': row['throttle_lift_time']
                }
            devices_cache = new_cache
            conn.close()
        except Exception:
            pass
        
        time.sleep(3)

# --- IPS THROTTLE TRIGGER ---
def trigger_breach(ip_address):
    """Fires when a device sends/receives too many packets."""
    print(f"\n[!!!] IPS ALERT: {ip_address} breached packet threshold! Initiating 50% bandwidth throttle...\n")
    
    lift_time = int(time.time()) + 300 
    
    try:
        conn = sqlite3.connect(DATABASE_NAME)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE devices 
            SET is_throttled = 1, throttle_lift_time = ? 
            WHERE ip_address = ?
        ''', (str(lift_time), ip_address))
        conn.commit()
        conn.close()
        
        threading.Thread(target=send_breach_alert, args=(ip_address, 500), daemon=True).start()
        
    except Exception as e:
        print(f"[-] Database Error during throttle trigger: {e}")

# --- THE KERNEL ENGINE ---
def run_firewall():
    print("[*] Smart Router IPS & Firewall Engine active...")
    print("[*] Hooked into NETWORK_FORWARD layer. Heartbeat trace active...")
    
    threading.Thread(target=sync_database_state, daemon=True).start()
    
    HOTSPOT_FILTER = "ip and ((ip.SrcAddr >= 192.168.137.2) and (ip.SrcAddr <= 192.168.137.254) or (ip.DstAddr >= 192.168.137.2) and (ip.DstAddr <= 192.168.137.254))"

    try:
        with pydivert.WinDivert(HOTSPOT_FILTER, layer=pydivert.Layer.NETWORK_FORWARD) as w:
            for packet in w:
                src_ip = packet.src_addr
                dest_ip = packet.dst_addr
                
                dest_port = "ANY"
                src_port = "ANY"
                
                if packet.tcp:
                    dest_port = str(packet.tcp.dst_port)
                    src_port = str(packet.tcp.src_port)
                elif packet.udp:
                    dest_port = str(packet.udp.dst_port)
                    src_port = str(packet.udp.src_port)
                    
                # 1. ALWAYS ALLOW DNS
                if (dest_port == "53" or src_port == "53"):
                    w.send(packet)
                    continue
                
                # 2. IDENTIFY LOCAL IP
                local_ip = None
                if src_ip.startswith("192.168.137"):
                    local_ip = src_ip
                elif dest_ip.startswith("192.168.137"):
                    local_ip = dest_ip
                
                if local_ip:
                    # 3. IPS RATE MONITORING
                    current_time = time.time()
                    
                    if local_ip not in packet_tracker:
                        packet_tracker[local_ip] = {'count': 0, 'window_start': current_time, 'alert_locked': False}
                    
                    if current_time - packet_tracker[local_ip]['window_start'] > 10:
                        packet_tracker[local_ip] = {'count': 1, 'window_start': current_time, 'alert_locked': False}
                    else:
                        packet_tracker[local_ip]['count'] += 1
                    
                    device_info = devices_cache.get(local_ip, {'threshold': 500, 'is_throttled': 0})
                    
                    if packet_tracker[local_ip]['count'] > device_info['threshold'] and device_info['is_throttled'] == 0:
                        if not packet_tracker[local_ip].get('alert_locked'):
                            packet_tracker[local_ip]['alert_locked'] = True 
                            
                            if local_ip not in devices_cache:
                                devices_cache[local_ip] = {'threshold': 500}
                            devices_cache[local_ip]['is_throttled'] = 1
                            
                            threading.Thread(target=trigger_breach, args=(local_ip,)).start()
                    
                    # 4. THROTTLE ENFORCEMENT & TRACE
                    is_dropped = False
                    if device_info['is_throttled'] == 1:
                        if int(current_time * 1000) % 2 == 0: 
                            is_dropped = True
                            # Show the destruction Logs
                            if packet_tracker[local_ip]['count'] % 50 == 0:
                                print(f"[TRACE] DESTROYED packet #{packet_tracker[local_ip]['count']} | {src_ip}:{src_port} -> {dest_ip}:{dest_port}")
                            continue 
                    
                    if packet_tracker[local_ip]['count'] % 50 == 0 and not is_dropped:
                        print(f"[TRACE] ALLOWED packet #{packet_tracker[local_ip]['count']} | {src_ip}:{src_port} -> {dest_ip}:{dest_port}")
                
                # 5. FIREWALL ALLOW-LIST LOGIC
                allowed = False
                for rule in allow_list:
                    rule_src_ip = rule['src_ip']
                    rule_dest_ip = rule['dest_ip']
                    rule_dest_port = rule['dest_port']
                    
                    outbound_match = (rule_src_ip in [src_ip, "ANY"]) and (rule_dest_ip in [dest_ip, "ANY"]) and (rule_dest_port in [dest_port, "ANY"])
                    inbound_match = (rule_src_ip in [dest_ip, "ANY"]) and (rule_dest_ip in [src_ip, "ANY"]) and (rule_dest_port in [src_port, "ANY"])
                    
                    if outbound_match or inbound_match:
                        allowed = True
                        break
                
                if allowed:
                    w.send(packet)

    except PermissionError:
        print("\n[ERROR] Permission denied: Please run this script with administrative privileges.")
    except Exception as e:
        print(f"\n[ERROR] Firewall crashed: {e}")

if __name__ == '__main__':
    run_firewall()
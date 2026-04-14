import pydivert
import sqlite3
import time

def get_allow_list():
    conn = sqlite3.connect('router_data.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT src_ip, dest_ip, dest_port FROM firewall_rules")
    rules = c.fetchall()
    conn.close()
    
    return rules

# Capturing packets leaving andentering the hotspot interface
HOTSPOT_FILTER = "ip and ((ip.SrcAddr >= 192.168.137.2) and (ip.SrcAddr <= 192.168.137.254) or (ip.DstAddr >= 192.168.137.2) and (ip.DstAddr <= 192.168.137.254))"

try:
    with pydivert.WinDivert(HOTSPOT_FILTER) as w:
        print("Firewall is running...")
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
                
            # we need to allow DNS traffic to function properly
            if (dest_port == "53" or src_port == "53"):
                w.send(packet)
                continue
            
    
            
            # Check allow rules database
            allow_list = get_allow_list()
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
                w.send(packet) # Found a matching rule
            else:
                print(f"Blocked packet: {src_ip}:{src_port} -> {dest_ip}:{dest_port}")

except PermissionError:
    print("\n[ERROR] Permission denied: Please run this script with administrative privileges.")
except Exception as e:
    print(f"\n[ERROR] Firewall crashed: {e}")
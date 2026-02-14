# utils/scanner.py
import subprocess
import platform
import socket
import concurrent.futures
import re

def get_my_ip_prefix():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()
    return ".".join(local_ip.split(".")[:-1])

def ping_device(ip):
    """
    Pings an IP. Returns the IP if successful, None if not.
    """
    # DETECT OS for PING FLAGS
    param = '-n' if platform.system().lower() == 'windows' else '-c'
    
    command = ['ping', param, '1', '-w', '500', ip]
    # Note: On Linux/Mac -w 500 might be -W 500 or -w 1 (seconds). 
    # For compatibility, usually just count is enough, but timeout helps speed.
    if platform.system().lower() != 'windows':
         # Linux ping often uses -W in seconds, or ms depending on variant. 
         # Safest is just count for basic scan.
         command = ['ping', param, '1', ip]

    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if result.returncode == 0:
        return ip
    return None

def get_mac_addresses(active_ips):
    print("\nfetching MAC addresses from ARP cache...")
    try:
        arp_result = subprocess.check_output("arp -a", shell=True).decode('cp1252', errors='ignore')
    except:
        # Fallback for linux/utf-8
        arp_result = subprocess.check_output("arp -a", shell=True).decode('utf-8', errors='ignore')

    devices = []
    
    for line in arp_result.splitlines():
        line = line.strip()
        for ip in active_ips:
            if ip + " " in line or ip + ")" in line: # Handle (192.168.1.5) format on Linux
                 mac_search = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
                 if mac_search:
                     devices.append((ip, mac_search.group(0)))
    return devices

if __name__ == "__main__":
    while(True):
        prefix = get_my_ip_prefix()
        print("Please wait (approx 10-15 seconds)...")
    
        all_ips = [f"{prefix}.{i}" for i in range(1, 255)] # Adjusted range to standard /24
        active_ips = []
    
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            results = executor.map(ping_device, all_ips)
        
        for ip in results:
            if ip:
                active_ips.append(ip)
    
        final_devices = get_mac_addresses(active_ips)
    
        for ip, mac in final_devices:
            print(f"{ip:<20} {mac}")
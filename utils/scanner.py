import subprocess
import platform
import socket
import concurrent.futures
import re

def get_my_ip_prefix():
    # Find your local IP to guess the range (e.g., 192.168.1.x)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Doesn't actually connect, just gets the route
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
    finally:
        s.close()
    # Return the first 3 parts: "192.168.1"
    return ".".join(local_ip.split(".")[:-1])

def ping_device(ip):
    """
    Pings an IP. Returns the IP if successful, None if not.
    -n 1: Send only 1 packet
    -w 500: Wait only 500ms for a reply (speeds things up)
    """
    command = ['ping', '-n', '1', '-w', '500', ip]
    
    # Run the command silently (hide output)
    result = subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    if result.returncode == 0:
        return ip
    return None

def get_mac_addresses(active_ips):
    """
    Runs 'arp -a' and filters for the IPs we found.
    """
    print("\nfetching MAC addresses from ARP cache...")
    arp_result = subprocess.check_output("arp -a", shell=True).decode('cp1252', errors='ignore') # decoding for Windows
    
    devices = []
    
    for line in arp_result.splitlines():
        # Clean up line
        line = line.strip()
        # Look for lines that contain our active IPs
        for ip in active_ips:
            # Add a space to ensure we don't match 192.168.1.10 inside 192.168.1.100
            if ip + " " in line:
                 # Regex to find the MAC address (XX-XX-XX-XX-XX-XX)
                 mac_search = re.search(r'([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})', line)
                 if mac_search:
                     devices.append((ip, mac_search.group(0)))
    return devices

# --- MAIN EXECUTION ---
if __name__ == "__main__":
    while(True):
        prefix = get_my_ip_prefix()
        #print(f"Scanning network: {prefix}.1 to {prefix}.254")
        print("Please wait (approx 10-15 seconds)...")
    
        # Generate all 254 IPs
        all_ips = [f"{prefix}.{i}" for i in range(1, 511)]
        active_ips = []
    
        # Use 50 threads to ping them all quickly
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            results = executor.map(ping_device, all_ips)
        
        # Collect the ones that replied
        for ip in results:
            if ip:
                active_ips.append(ip)
    
        # Match IPs to MAC addresses
        final_devices = get_mac_addresses(active_ips)
    
        #print("\nFound Devices:")
        #print("---------------------------------------------")
        #print(f"{'IP Address':<20} {'MAC Address'}")
        #print("---------------------------------------------")
        finds = ['44-5d-5e-41-35-0c']
        for ip, mac in final_devices:
            print(f"{ip:<20} {mac}")
            if mac in finds:
                print("FOUND!!! " + ip)
            
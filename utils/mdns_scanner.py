# -*- coding: utf-8 -*-
# utils/mdns_scanner.py
import time
import socket
import logging
import sys

# Try importing zeroconf; warn if missing
try:
    from zeroconf import ServiceBrowser, Zeroconf, ServiceListener
except ImportError:
    print("Error: 'zeroconf' library is required. Please run: pip install zeroconf")
    sys.exit(1)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger("mDNS-Scanner")

class SmartDeviceListener(ServiceListener):
    def update_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def remove_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        pass

    def add_service(self, zc: Zeroconf, type_: str, name: str) -> None:
        info = zc.get_service_info(type_, name)
        if info:
            self._print_device_info(info, type_, name)

    def _print_device_info(self, info, type_, name):
        # 1. Parse IP Address
        addresses = [socket.inet_ntoa(addr) for addr in info.addresses]
        ip = addresses[0] if addresses else "Unknown"
        
        # 2. Decode Properties (e.g., Device ID is often hidden here)
        props = {}
        for k, v in info.properties.items():
            key = k.decode('utf-8') if isinstance(k, bytes) else k
            val = v.decode('utf-8') if isinstance(v, bytes) else v
            props[key] = val

        # 3. Identify Brand based on Service Type
        brand = "Generic"
        device_id = "Unknown"
        
        if "ewelink" in type_:
            brand = "Sonoff (DIY Mode)"
            device_id = props.get('id', 'Unknown') # Sonoff broadcasts ID in properties
        elif "shelly" in type_ or "shelly" in name.lower():
            brand = "Shelly"
            device_id = name.split('.')[0] # Shelly ID is usually in the name
        elif "googlecast" in type_:
            brand = "Google Home"
            device_id = props.get('id', 'Unknown')
        elif "hap" in type_:
            brand = "HomeKit Device"

        # 4. Log the Discovery
        logger.info(f"FOUND DEVICE: {brand}")
        logger.info(f" -> Name: {name}")
        logger.info(f" -> IP:   {ip}:{info.port}")
        
        if device_id != "Unknown":
            logger.info(f" -> ID:   {device_id}")
        
        # Print full properties for debugging (helpful to find hidden keys)
        logger.debug(f" -> Raw Props: {props}")
        print("-" * 40)

def scan_network():
    zeroconf = Zeroconf()
    listener = SmartDeviceListener()
    
    # List of common Smart Home service signatures
    service_types = [
        "_ewelink._tcp.local.",   # Sonoff DIY Mode
        "_http._tcp.local.",      # Generic Web Servers (Shelly often appears here)
        "_shelly._tcp.local.",    # Specific Shelly protocol
        "_googlecast._tcp.local.",# Google Nest/Home
        "_hap._tcp.local."        # Apple HomeKit
    ]

    logger.info(f"Starting mDNS Auto-Discovery...")
    logger.info(f"Listening for: {', '.join(service_types)}")
    logger.info("Press Ctrl+C to stop scanning.\n")

    browsers = []
    for s in service_types:
        browsers.append(ServiceBrowser(zeroconf, s, listener))

    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        logger.info("Stopping scan...")
    finally:
        zeroconf.close()

if __name__ == '__main__':
    scan_network()


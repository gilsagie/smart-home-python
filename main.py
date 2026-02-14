# main.py
import logging
from core.manager import SmartHomeManager
from devices.room import Room

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

if __name__ == "__main__":
    # 1. Start the System
    manager = SmartHomeManager()
    manager.initialize()

    # --- NEW FEATURE: System Health Check ---
    health = manager.get_system_health()
    print(f"\n[System Health] Online: {health['online']} | Offline: {health['offline']} | IR: {health['stateless_ir']}")

    # 2. Control Logic (Existing)
    bedroom_names = ['Bed room switch', 'Bed room TV', 'Bed room AC', 'Lamp']
    bedroom_devices = [manager.get_device(n) for n in bedroom_names if manager.get_device(n)]

    if bedroom_devices:
        bedroom = Room("Bedroom", device_list=bedroom_devices)
        print("\n--- Room Ready ---")
        # bedroom.all.on()
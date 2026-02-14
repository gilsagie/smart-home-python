# core/manager.py
import logging
import concurrent.futures
from cloud.sonoff_client import SonoffCloudClient
from cloud.tuya_client import TuyaCloudClient
from cloud.sensibo_client import SensiboCloudClient
from utils.loader import load_devices

# Import your existing scanner tools
from utils.scanner import get_my_ip_prefix, ping_device, get_mac_addresses

logger = logging.getLogger("SmartHomeManager")

class SmartHomeManager:
    """
    The Central Brain.
    - Initializes Cloud Clients ONCE.
    - Loads devices using those clients.
    - Provides access to devices.
    - Manages system health and discovery.
    """
    def __init__(self):
        self.devices = {}
        self.categories = {}
        
        # 1. Initialize Cloud Clients
        logger.info("Initializing Cloud Clients...")
        self.sonoff = SonoffCloudClient()
        self.tuya = TuyaCloudClient()
        self.sensibo = SensiboCloudClient()

    def initialize(self):
        """
        Loads the configuration and builds the device map.
        """
        self.categories = load_devices(
            sonoff_cloud=self.sonoff,
            tuya_cloud=self.tuya,
            sensibo_cloud=self.sensibo
        )
        self.devices = self.categories.get('all', {})
        logger.info(f"System Ready. Loaded {len(self.devices)} devices.")

    def get_device(self, name):
        return self.devices.get(name)

    def get_devices_by_category(self, category):
        return self.categories.get(category, {})

    # --- ADDITION 1: PARALLEL STATE REFRESH ---
    def refresh_all(self):
        """
        Forces a state refresh for ALL devices in parallel.
        Useful if the script has been running for a while.
        """
        logger.info("Refreshing all device states...")
        
        def _refresh(device):
            # This calls the device's get_state method (LAN -> Cloud fallback)
            device.get_state()
            return device

        # Use threads to make this fast (otherwise 20 devices = 20 seconds)
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            list(executor.map(_refresh, self.devices.values()))
            
        logger.info("Refresh complete.")

    # --- ADDITION 2: SYSTEM HEALTH REPORT ---
    def get_system_health(self):
        """
        Returns a dictionary summary of the system.
        """
        total = len(self.devices)
        online = 0
        offline = 0
        
        for dev in self.devices.values():
            if dev.state == 'N/A': # Stateless devices (IR)
                continue
            
            # Check internal state cache
            if dev.state == 'OFFLINE' or dev.state is None:
                offline += 1
            else:
                online += 1
                
        return {
            "total_devices": total,
            "online": online,
            "offline": offline,
            "stateless_ir": total - (online + offline)
        }

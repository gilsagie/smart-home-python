# utils/loader.py
import yaml
import os
import concurrent.futures

from devices.sonoff import SonoffSwitch
# NEW: Import the Tuya class we created
from devices.tuya import TuyaSwitch  
from cloud.sonoff_client import SonoffCloudClient
# from cloud.tuya_client import TuyaCloudClient # Optional: Uncomment if you implemented Cloud

def load_switches():
    """
    1. Loads devices from config/switches.yaml
    2. Fetches their initial state in parallel threads
    """
    # Path setup
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    yaml_file = os.path.join(project_root, 'config', 'switches.yaml')
    
    SWITCH_DICT = {}
    
    # Initialize Cloud Clients
    # We initialize them once here and pass them down to devices
    sonoff_cloud = SonoffCloudClient() 
    # tuya_cloud = TuyaCloudClient() # Optional
    tuya_cloud = None # Placeholder if you haven't set up cloud keys yet
    
    print(f"Loading switches from {yaml_file}...")
    
    try:
        # 1. READ YAML & CREATE OBJECTS
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
            device_list = data.get('devices', [])
            
            for item in device_list:
                name = item.get('name')
                ip = item.get('ip')
                
                # Basic validation
                if not name or not ip: 
                    continue

                # Common fields
                dev_type = item.get('type', 'sonoff').lower()
                channel = item.get('channel') 
                dev_id = item.get('device_id')
                dev_key = item.get('device_key') # Used as 'deviceKey' (Sonoff) or 'LocalKey' (Tuya)
                mac = item.get('mac')
                stateless = item.get('stateless', False) # <--- NEW READ
                
                new_switch = None

                # --- SONOFF LOGIC ---
                if dev_type == 'sonoff':
                    new_switch = SonoffSwitch(
                        name=name, ip=ip, device_id=dev_id, 
                        device_key=dev_key, mac=mac, 
                        channel=channel, cloud_client=sonoff_cloud,
                        stateless=stateless # <--- PASS IT
                    )

                # --- TUYA LOGIC ---
                elif dev_type == 'tuya':
                    # Tuya devices use 'device_key' from the CSV as their 'Local Key'
                    new_switch = TuyaSwitch(
                        name=name, ip=ip, device_id=dev_id,
                        local_key=dev_key, 
                        channel=channel, 
                        cloud_client=tuya_cloud,
                        stateless=stateless # <--- PASS IT
                    )
                
                # Add to dictionary if successfully created
                if new_switch:
                    SWITCH_DICT[name] = new_switch

        # 2. FETCH INITIAL STATES (PARALLEL)
        print(f"Initializing state for {len(SWITCH_DICT)} devices (Threading)...")
        
        def _fetch_state(device):
            # This calls get_state(), which now populates device._state automatically
            return device.get_state()

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            # Run get_state() for every device at the same time
            executor.map(_fetch_state, SWITCH_DICT.values())

        print(" -> All devices initialized.")
        return SWITCH_DICT

    except FileNotFoundError:
        print(f"Error: Config file not found at {yaml_file}")
        return {}
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML file: {exc}")
        return {}
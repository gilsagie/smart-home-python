# utils/loader.py
import yaml
import os
import concurrent.futures

# Existing Device Imports
from devices.sonoff import SonoffSwitch
from devices.tuya import TuyaSwitch
# NEW Device Imports
from devices.broadlink_remote import BroadlinkRemote
from devices.television import Television

# Cloud Clients
from cloud.sonoff_client import SonoffCloudClient
from cloud.tuya_client import TuyaCloudClient 

def load_switches():
    """
    1. Loads devices from config/switches.yaml
    2. Loads commands from config/commands.yaml (for TVs)
    3. Initializes Hardware (Sonoff, Tuya, Broadlink)
    4. Initializes Virtual Devices (TVs) linked to Hardware
    5. Fetches initial state in parallel
    """
    # Path setup
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    yaml_file = os.path.join(project_root, 'config', 'switches.yaml')
    cmd_file = os.path.join(project_root, 'config', 'Bed_room_IR_commands.yaml') # <--- NEW PATH
    
    SWITCH_DICT = {}
    
    # Initialize Cloud Clients
    sonoff_cloud = SonoffCloudClient() 
    tuya_cloud = TuyaCloudClient() 
    
    print(f"Loading switches from {yaml_file}...")
    
    try:
        # Load Device Config
        with open(yaml_file, 'r') as f:
            data = yaml.safe_load(f)
            device_list = data.get('devices', [])

        # Load Command Config (Safe fail if missing)
        cmd_data = {}
        if os.path.exists(cmd_file):
            with open(cmd_file, 'r') as f:
                cmd_data = yaml.safe_load(f) or {}

        # ---------------------------------------------------------
        # PASS 1: PHYSICAL HARDWARE (Sonoff, Tuya, Broadlink)
        # ---------------------------------------------------------
        for item in device_list:
            name = item.get('name')
            # Basic validation
            if not name: continue

            dev_type = item.get('type', 'sonoff').lower()
            ip = item.get('ip')
            
            # Common fields
            channel = item.get('channel') 
            dev_id = item.get('device_id')
            dev_key = item.get('device_key') 
            mac = item.get('mac')
            stateless = item.get('stateless', False)
            
            new_switch = None

            # --- SONOFF ---
            if dev_type == 'sonoff':
                new_switch = SonoffSwitch(
                    name=name, ip=ip, device_id=dev_id, 
                    device_key=dev_key, mac=mac, 
                    channel=channel, cloud_client=sonoff_cloud,
                    stateless=stateless
                )

            # --- TUYA ---
            elif dev_type == 'tuya':
                new_switch = TuyaSwitch(
                    name=name, ip=ip, device_id=dev_id,
                    local_key=dev_key, 
                    channel=channel, 
                    cloud_client=tuya_cloud,
                    stateless=stateless
                )
            
            # --- BROADLINK (NEW) ---
            elif dev_type == 'broadlink':
                new_switch = BroadlinkRemote(
                    name=name, ip=ip, device_id=dev_id,
                    mac=mac, 
                    stateless=True # Always stateless
                )

            # Add to dictionary if created
            if new_switch:
                SWITCH_DICT[name] = new_switch

        # ---------------------------------------------------------
        # PASS 2: VIRTUAL DEVICES (Televisions)
        # ---------------------------------------------------------
        for item in device_list:
            name = item.get('name')
            dev_type = item.get('type', '').lower()

            if dev_type == 'television':
                # 1. Get commands for this specific TV name
                my_commands = cmd_data.get(name)
                if not my_commands:
                    print(f"Warning: No commands found in commands.yaml for '{name}'")
                    continue
                
                # 2. Find the linked IR Blaster name
                blaster_name = my_commands.get('IR_device')
                if not blaster_name:
                    print(f"Error: 'IR_device' key missing in commands.yaml for '{name}'")
                    continue

                # 3. Retrieve the actual Blaster Object from Pass 1
                blaster_obj = SWITCH_DICT.get(blaster_name)
                if not blaster_obj:
                    print(f"Error: Blaster '{blaster_name}' (required by {name}) not found in loaded devices.")
                    continue
                
                # 4. Clean commands (remove the config key)
                clean_cmds = {k:v for k,v in my_commands.items() if k != 'IR_device'}
                
                # 5. Create TV Object
                new_tv = Television(name, blaster_obj, clean_cmds)
                SWITCH_DICT[name] = new_tv

        # ---------------------------------------------------------
        # 3. FETCH INITIAL STATES (PARALLEL)
        # ---------------------------------------------------------
        print(f"Initializing state for {len(SWITCH_DICT)} devices (Threading)...")
        
        def _fetch_state(device):
            # Safe wrapper just in case
            try:
                return device.get_state()
            except Exception as e:
                print(f"Error fetching state for {device.name}: {e}")
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(_fetch_state, SWITCH_DICT.values())

        print(" -> All devices initialized.")
        return SWITCH_DICT

    except FileNotFoundError as e:
        print(f"Error: Config file not found: {e}")
        return {}
    except yaml.YAMLError as exc:
        print(f"Error parsing YAML file: {exc}")
        return {}
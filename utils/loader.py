# utils/loader.py
import yaml
import os
import concurrent.futures
import logging

# Device Imports
from devices.brands.sonoff import SonoffSwitch
from devices.brands.tuya import TuyaSwitch
from devices.brands.broadlink_remote import BroadlinkRemote
from devices.brands.sensibo import SensiboAC

# Appliance (Wrapper) Imports
from devices.appliances.television import Television
from devices.appliances.air_conditioner import AirConditioner
from devices.appliances.light import Light
from devices.appliances.switch import Switch
from devices.appliances.other import Other

# Cloud Clients
from cloud.sonoff_client import SonoffCloudClient
from cloud.tuya_client import TuyaCloudClient 
from cloud.sensibo_client import SensiboCloudClient

logger = logging.getLogger("DeviceLoader")

def load_devices():
    """
    1. Loads devices from config/switches.yaml
    2. Loads commands from config/commands.yaml
    3. Initializes Hardware and Virtual Devices
    4. Wraps devices based on 'category' (Light, Switch, Other)
    5. Fetches initial state in parallel
    """
    # Path setup
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    yaml_file = os.path.join(project_root, 'config', 'switches.yaml')
    cmd_file = os.path.join(project_root, 'config', 'commands.yaml')
    
    # Initialize Categorized Structure
    devices = {
        'switches': {},
        'lights': {}, 
        'tvs': {},
        'acs': {},
        'ir': {},     
        'other': {},
        'all': {} 
    }
    
    # Initialize Cloud Clients
    sonoff_cloud = SonoffCloudClient() 
    tuya_cloud = TuyaCloudClient() 
    sensibo_cloud = SensiboCloudClient()
    
    logger.info(f"Loading devices from {yaml_file}...")
    
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
        # PASS 1: PHYSICAL HARDWARE
        # ---------------------------------------------------------
        for item in device_list:
            name = item.get('name')
            if not name: continue

            dev_type = item.get('type', 'sonoff').lower()
            ip = item.get('ip')
            
            # Common fields
            channel = item.get('channel') 
            dev_id = item.get('device_id')
            dev_key = item.get('device_key') 
            mac = item.get('mac')
            stateless = item.get('stateless', False)
            
            # Capture User Category
            user_category = item.get('category')
            
            new_device = None
            default_category = 'other' 

            # --- HARDWARE CREATION ---
            
            # --- SONOFF ---
            if dev_type == 'sonoff':
                new_device = SonoffSwitch(
                    name=name, ip=ip, device_id=dev_id, 
                    device_key=dev_key, mac=mac, 
                    channel=channel, cloud_client=sonoff_cloud,
                    stateless=stateless
                )
                default_category = 'switches'

            # --- TUYA ---
            elif dev_type == 'tuya':
                new_device = TuyaSwitch(
                    name=name, ip=ip, device_id=dev_id,
                    local_key=dev_key, 
                    channel=channel, 
                    cloud_client=tuya_cloud,
                    stateless=stateless
                )
                default_category = 'switches'
            
            # --- BROADLINK (Remote/Blaster) ---
            elif dev_type == 'broadlink':
                new_device = BroadlinkRemote(
                    name=name, ip=ip, device_id=dev_id,
                    mac=mac, 
                    stateless=True
                )
                default_category = 'ir' # Default to IR

            # --- SENSIBO (Smart AC) ---
            elif dev_type == 'sensibo':
                new_device = SensiboAC(
                    name=name, 
                    device_id=dev_id, 
                    cloud_client=sensibo_cloud,
                    stateless=stateless
                )
                default_category = 'acs'

            # --- CATEGORY ROUTING & WRAPPING ---
            if new_device:
                final_device = new_device
                target_category = default_category
                
                # If the user explicitly defined a category, we obey it
                if user_category:
                    # NORMALIZATION MAP (Singular -> Plural)
                    cat_map = {
                        'light': 'lights',
                        'switch': 'switches',
                        'ac': 'acs',
                        'tv': 'tvs',
                        'ir': 'ir'
                    }
                    
                    # Get the normalized category (e.g., 'light' -> 'lights')
                    normalized_cat = cat_map.get(user_category, user_category)

                    # 1. LIGHTS -> Wrap in Light class
                    if normalized_cat == 'lights':
                        final_device = Light(name, new_device)
                        target_category = 'lights'
                    
                    # 2. SWITCHES -> Wrap in Switch class
                    elif normalized_cat == 'switches':
                        final_device = Switch(name, new_device)
                        target_category = 'switches'
                        
                    # 3. OTHER -> Wrap in Other class
                    elif normalized_cat == 'other':
                        final_device = Other(name, new_device)
                        target_category = 'other'
                        
                    # 4. Direct mapping (AC, TV, IR)
                    else:
                        target_category = normalized_cat
                        # Create new bucket if it doesn't exist (e.g. 'heaters')
                        if target_category not in devices:
                            devices[target_category] = {}

                # Register the device
                devices[target_category][name] = final_device
                devices['all'][name] = final_device

        # ---------------------------------------------------------
        # PASS 2: VIRTUAL DEVICES (Televisions, AC IR)
        # ---------------------------------------------------------
        for item in device_list:
            name = item.get('name')
            dev_type = item.get('type', '').lower()
            user_category = item.get('category')

            if dev_type in ['television', 'ac_ir']:  
                
                # 1. Get commands
                my_commands = cmd_data.get(name)
                if not my_commands:
                    logger.warning(f"No commands found for '{name}'")
                    continue
                
                # 2. Find Blaster
                blaster_name = my_commands.get('IR_device')
                blaster_obj = devices['all'].get(blaster_name)
                
                if not blaster_obj:
                    logger.error(f"Blaster '{blaster_name}' not found for {name}")
                    continue
                
                clean_cmds = {k:v for k,v in my_commands.items() if k != 'IR_device'}
                new_virtual = None
                category = 'other'

                # 3. Create Object
                if dev_type == 'television':
                    new_virtual = Television(name, blaster_obj, clean_cmds)
                    category = 'tvs'
                    
                elif dev_type == 'ac_ir':
                    new_virtual = AirConditioner(name, blaster_obj, command_dict=clean_cmds)
                    category = 'acs'
                
                # 4. Apply Category Override with Normalization
                if user_category:
                    cat_map = {'light': 'lights', 'switch': 'switches', 'ac': 'acs', 'tv': 'tvs', 'ir': 'ir'}
                    category = cat_map.get(user_category, user_category)
                    
                    if category not in devices:
                        devices[category] = {}

                if new_virtual:
                    devices[category][name] = new_virtual
                    devices['all'][name] = new_virtual
                    
        # ---------------------------------------------------------
        # 3. FETCH INITIAL STATES
        # ---------------------------------------------------------
        logger.info(f"Initializing state for {len(devices['all'])} devices...")
        
        def _fetch_state(device):
            try:
                return device.get_state()
            except Exception as e:
                logger.error(f"Error fetching state for {device.name}: {e}")
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(_fetch_state, devices['all'].values())

        logger.info("All devices initialized.")
        
        ## Return categorized dict (excluding 'all')
        #final_output = devices.copy()
        #del final_output['all']
        
        return devices

    except FileNotFoundError as e:
        logger.error(f"Config file not found: {e}")
        return {'switches': {}, 'lights': {}, 'tvs': {}, 'acs': {}, 'other': {}}
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing YAML file: {exc}")
        return {'switches': {}, 'lights': {}, 'tvs': {}, 'acs': {}, 'other': {}}
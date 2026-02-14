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
from devices.appliances.television import Television
from devices.appliances.air_conditioner import AirConditioner


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
    4. Categorizes them into functional groups (switches, tvs, acs, other)
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
        'tvs': {},
        'acs': {},
        'other': {},
        # 'all' is a temporary flat index for dependency lookups (e.g. TVs finding their Blaster)
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
            
            new_device = None
            category = 'other' # Default fallback

            # --- SONOFF ---
            if dev_type == 'sonoff':
                new_device = SonoffSwitch(
                    name=name, ip=ip, device_id=dev_id, 
                    device_key=dev_key, mac=mac, 
                    channel=channel, cloud_client=sonoff_cloud,
                    stateless=stateless
                )
                category = 'switches'

            # --- TUYA ---
            elif dev_type == 'tuya':
                new_device = TuyaSwitch(
                    name=name, ip=ip, device_id=dev_id,
                    local_key=dev_key, 
                    channel=channel, 
                    cloud_client=tuya_cloud,
                    stateless=stateless
                )
                category = 'switches'
            
            # --- BROADLINK (Remote/Blaster) ---
            elif dev_type == 'broadlink':
                new_device = BroadlinkRemote(
                    name=name, ip=ip, device_id=dev_id,
                    mac=mac, 
                    stateless=True
                )
                category = 'other'

            # --- SENSIBO (Smart AC) ---
            elif dev_type == 'sensibo':
                new_device = SensiboAC(
                    name=name, 
                    device_id=dev_id, 
                    cloud_client=sensibo_cloud,
                    stateless=stateless
                )
                category = 'acs'

            # Register device if created
            if new_device:
                devices[category][name] = new_device
                devices['all'][name] = new_device

        # ---------------------------------------------------------
        # PASS 2: VIRTUAL DEVICES (Televisions, AC IR)
        # ---------------------------------------------------------
        for item in device_list:
            name = item.get('name')
            dev_type = item.get('type', '').lower()

            if dev_type in ['television', 'ac_ir']:  
                
                # 1. Get commands for this device name
                my_commands = cmd_data.get(name)
                if not my_commands:
                    logger.warning(f"No commands found in commands.yaml for '{name}'")
                    continue
                
                # 2. Find the linked IR Blaster in the 'all' registry
                blaster_name = my_commands.get('IR_device')
                blaster_obj = devices['all'].get(blaster_name)
                
                if not blaster_obj:
                    logger.error(f"Blaster '{blaster_name}' not found for {name}")
                    continue
                
                # 3. Clean commands (remove 'IR_device' key)
                clean_cmds = {k:v for k,v in my_commands.items() if k != 'IR_device'}

                new_virtual = None
                category = 'other'

                # 4. Create the Object
                if dev_type == 'television':
                    new_virtual = Television(name, blaster_obj, clean_cmds)
                    category = 'tvs'
                    
                elif dev_type == 'ac_ir':
                    new_virtual = AirConditioner(name, blaster_obj, command_dict=clean_cmds)
                    category = 'acs'
                
                if new_virtual:
                    devices[category][name] = new_virtual
                    devices['all'][name] = new_virtual
                    
        # ---------------------------------------------------------
        # 3. FETCH INITIAL STATES (PARALLEL)
        # ---------------------------------------------------------
        logger.info(f"Initializing state for {len(devices['all'])} devices (Threading)...")
        
        def _fetch_state(device):
            try:
                return device.get_state()
            except Exception as e:
                logger.error(f"Error fetching state for {device.name}: {e}")
                return None

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(_fetch_state, devices['all'].values())

        logger.info("All devices initialized.")
        
        # Return only the requested categories
        return {
            'switches': devices['switches'],
            'tvs': devices['tvs'],
            'acs': devices['acs'],
            'other': devices['other']
        }

    except FileNotFoundError as e:
        logger.error(f"Config file not found: {e}")
        return {'switches': {}, 'tvs': {}, 'acs': {}, 'other': {}}
    except yaml.YAMLError as exc:
        logger.error(f"Error parsing YAML file: {exc}")
        return {'switches': {}, 'tvs': {}, 'acs': {}, 'other': {}}
# utils/loader.py
import csv
import os

# CHANGE: Update imports to new locations
from devices.sonoff import SonoffSwitch
from cloud.sonoff_client import SonoffCloudClient

def load_switches():
    # CHANGE: Fix path logic to find config/switches.csv
    # This file is in /utils, so we go up one level (..) then into /config
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)
    csv_file = os.path.join(project_root, 'config', 'switches.csv')
    
    SWITCH_DICT = {}
    cloud = SonoffCloudClient()
    print(f"Loading switches from {csv_file}...")
    
    try:
        with open(csv_file, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                name = row['name']
                ip = row['ip']
                
                if not ip:
                    continue

                dev_type = row.get('type', 'sonoff').lower()
                
                raw_channel = row.get('channel', '').strip()
                channel = int(raw_channel) if raw_channel.isdigit() else None

                dev_id = row['device_id']
                dev_key = row['device_key']
                mac = row['mac']
                
                new_switch = None

                if dev_type == 'sonoff':
                    new_switch = SonoffSwitch(
                        name=name, 
                        ip=ip, 
                        device_id=dev_id, 
                        device_key=dev_key, 
                        mac=mac, 
                        channel=channel, 
                        cloud_client=cloud
                    )
                
                if new_switch:
                    SWITCH_DICT[name] = new_switch
                    chan_str = f" [Channel {channel}]" if channel is not None else ""
                    print(f" -> Loaded: {name} ({ip}){chan_str}")
        return SWITCH_DICT

    except FileNotFoundError:
        print(f"Error: Config file not found at {csv_file}")
        return None
    except KeyError as e:
        print(f"Error: Your CSV is missing a column: {e}")
        return None
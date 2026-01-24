import csv
import os
from SonoffSwitch import SonoffSwitch  # Updated class
from smart_cloud import SonoffCloudClient

def load_switches():
    # 1. Define the file path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(current_dir, 'switches.csv')
    
    # 2. Create the dictionary
    SWITCH_DICT = {}
    cloud = SonoffCloudClient()
    print(f"Loading switches from {csv_file}...")
    
    try:
        with open(csv_file, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # --- Extract Basic Data ---
                name = row['name']
                ip = row['ip']
                
                if not ip:
                    continue
    
                # --- Extract New Columns (Type & Channel) ---
                # 1. Device Type (Default to 'sonoff' for backward compatibility)
                dev_type = row.get('type', 'sonoff').lower()
    
                # 2. Channel (Handle empty strings safely)
                raw_channel = row.get('channel', '').strip()
                if raw_channel.isdigit():
                    channel = int(raw_channel) # Convert '0' -> 0
                else:
                    channel = None # Single device
    
                # --- Extract Sonoff Specifics ---
                dev_id = row['device_id']
                dev_key = row['device_key']
                mac = row['mac']
                
                # --- Factory Logic ---
                new_switch = None
    
                if dev_type == 'sonoff':
                    new_switch = SonoffSwitch(
                        name=name, 
                        ip=ip, 
                        device_id=dev_id, 
                        device_key=dev_key, 
                        mac=mac, 
                        channel=channel,  # <--- PASSING THE CHANNEL HERE
                        cloud_client=cloud
                    )
                
                # Future: elif dev_type == 'shelly': ...
    
                # --- Store Object ---
                if new_switch:
                    SWITCH_DICT[name] = new_switch
                    # Print status showing channel if it exists
                    chan_str = f" [Channel {channel}]" if channel is not None else ""
                    print(f" -> Loaded: {name} ({ip}){chan_str}")
        return SWITCH_DICT

    except FileNotFoundError:
        print("Error: switches.csv not found!")
        return None
    except KeyError as e:
        print(f"Error: Your CSV is missing a column: {e}")
        return None

# 3. Usage Example
if __name__ == "__main__":
    SWITCH_DICT = load_switches()
    # Test with the new split names
    if "Living room right" in SWITCH_DICT:
        print("\nTesting Multi-Channel Switch (Left)...")
        SWITCH_DICT["Living room right"].on() # Should only turn off channel 0
        
    if "Living room left" in SWITCH_DICT:
        print("\nTesting Multi-Channel Switch (Right)...")
        SWITCH_DICT["Living room left"].on() # Should only turn on channel 1
# convert_csv_yaml.py
import csv
import yaml
import os

def convert():
    # Define paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    csv_file = os.path.join(current_dir, 'config', 'switches.csv')
    yaml_file = os.path.join(current_dir, 'config', 'switches.yaml')

    print(f"Reading from: {csv_file}")
    
    devices = []
    
    try:
        with open(csv_file, mode='r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                # Clean up data
                name = row.get('name', '').strip()
                ip = row.get('ip', '').strip()
                
                # Skip empty lines
                if not name or not ip:
                    continue

                # Handle Integers (Channel)
                raw_channel = row.get('channel', '').strip()
                channel = int(raw_channel) if raw_channel.isdigit() else None

                # This ensures "True"/"true" becomes Python True, everything else False
                raw_stateless = row.get('stateless', '').strip().lower()
                is_stateless = (raw_stateless == 'true')

                # Build the dictionary object
                device_data = {
                    'name': name,
                    'ip': ip,
                    'type': row.get('type', 'sonoff').lower(),
                    'device_id': row.get('device_id', '').strip(),
                    'device_key': row.get('device_key', '').strip(),
                    'mac': row.get('mac', '').strip(),
                    'stateless': is_stateless  # <--- Add this field
                }
                
                # Only add channel if it exists (keeps YAML clean)
                if channel is not None:
                    device_data['channel'] = channel
                    
                devices.append(device_data)

        # Write to YAML
        with open(yaml_file, 'w') as yf:
            # We save it under a root key 'devices' for better organization
            yaml.dump({'devices': devices}, yf, sort_keys=False, default_flow_style=False)
            
        print(f"Success! Created {yaml_file} with {len(devices)} devices.")
        print("You can now delete switches.csv if you wish.")

    except FileNotFoundError:
        print(f"Error: Could not find {csv_file}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    convert()
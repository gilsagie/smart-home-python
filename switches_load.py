import csv
import os
from SonoffSwitch import SonoffSwitch  # Import your class
from smart_cloud import SonoffCloudClient
# 1. Define the file path (assumes same directory)
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
            # Extract data from the row
            name = row['name']
            ip = row['ip']
            if not ip:
                continue
            dev_id = row['device_id']
            dev_key = row['device_key']
            mac = row['mac']
            
            # Create the Object
            new_switch = SonoffSwitch(name=name, 
                                      ip=ip, 
                                      device_id=dev_id, 
                                      device_key=dev_key, 
                                      mac=mac, 
                                      cloud_client=cloud)
            
            # Store it in the dict using the 'name' as the key
            SWITCH_DICT[name] = new_switch
            print(f" -> Loaded: {name} ({ip})")

except FileNotFoundError:
    print("Error: switches.csv not found!")
except KeyError as e:
    print(f"Error: Your CSV is missing a column: {e}")

# 3. Usage Example
if __name__ == "__main__":
    # Now you can access switches by name!
    if "entrance light" in SWITCH_DICT:
        print("\nTurning on Living Room...")
        SWITCH_DICT["entrance light"].off()
        
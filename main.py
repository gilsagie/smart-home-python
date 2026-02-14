from utils.loader import load_devices
import logging
from devices.room import Room

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    
# 1. Load all devices from YAML
devices_map = load_devices()
all_devices_list = list(devices_map['all'].values()) # Assuming you expose 'all' or gather them

# 2. Filter specific devices for the Bedroom (Logic depends on your naming convention or config)
# For this example, let's manually pick some we know exist
bedroom_list = ['Bed room switch', 'Bed room TV', 'Bed room AC', 'Lamp']
bedroom_devices = [devices_map['all'][dev] for dev in bedroom_list]


# 3. Initialize the Room
bedroom = Room("Bedroom", device_list=[d for d in bedroom_devices if d])
dev = devices_map['all']['Bed room TV']
# 4. Control
bedroom.all.on()       # Turns ON TV, AC, Lights, Switches
bedroom.all.off()      # Turns OFF everything
bedroom.lights.off()   # Turns OFF only lights
bedroom.tv.off()        # Controls just the TV
bedroom.ac.set_temperature(24) # Controls just the AC
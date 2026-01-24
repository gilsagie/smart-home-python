import concurrent.futures

class DeviceGroup:
    """
    Manages a collection of SmartDevices using a Dictionary for fast lookup.
    """
    def __init__(self, name, devices=None):
        self.name = name
        # Storage is now a Dict: {'Device Name': DeviceObject}
        self.devices = {} 
        
        if devices:
            for dev in devices:
                self.add_device(dev)

    # --- Management Functions ---
    def add_device(self, device):
        """Adds a SmartDevice object to the group using its name as the key."""
        if device.name not in self.devices:
            self.devices[device.name] = device
            print(f"[{self.name}] Added device: {device.name}")
        else:
            print(f"[{self.name}] Device '{device.name}' already exists in group.")

    def remove_device(self, device_name):
        """Removes a device from the group by name."""
        if device_name in self.devices:
            del self.devices[device_name]
            print(f"[{self.name}] Removed device: {device_name}")

    def get_device(self, device_name):
        """Retrieve a specific device from the group by name."""
        return self.devices.get(device_name)

    def get_devices(self):
        """Returns the dictionary of devices."""
        return self.devices

    # --- Control Functions ---
    def set_state(self, state):
        """
        Turns all devices in the group to the specific state in parallel.
        """
        print(f"[{self.name}] Setting group to '{state}'...")
        
        results = {}
        
        def _switch_device(device):
            success = device.set_state(state)
            return device.name, success

        # Iterate over .values() since self.devices is now a dict
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_device = {
                executor.submit(_switch_device, dev): dev 
                for dev in self.devices.values()
            }
            
            for future in concurrent.futures.as_completed(future_to_device):
                dev_name, success = future.result()
                results[dev_name] = success
                
        return results

    def on(self):
        return self.set_state('on')

    def off(self):
        return self.set_state('off')
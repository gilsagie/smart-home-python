# devices/DeviceGroup.py
import concurrent.futures
import logging # <--- NEW IMPORT

logger = logging.getLogger("DeviceGroup") # <--- NEW LOGGER

class DeviceGroup:
    def __init__(self, name, devices=None):
        self.name = name
        self.devices = {} 
        
        if devices:
            for dev in devices:
                self.add_device(dev)

    def add_device(self, device):
        if device.name not in self.devices:
            self.devices[device.name] = device
            logger.info(f"[{self.name}] Added device: {device.name}") # <--- CHANGED
        else:
            logger.warning(f"[{self.name}] Device '{device.name}' already exists in group.") # <--- CHANGED

    def remove_device(self, device_name):
        if device_name in self.devices:
            del self.devices[device_name]
            logger.info(f"[{self.name}] Removed device: {device_name}") # <--- CHANGED

    def get_device(self, device_name):
        return self.devices.get(device_name)

    def get_devices(self):
        return self.devices

    def set_state(self, state):
        logger.info(f"[{self.name}] Setting group to '{state}'...") # <--- CHANGED
        
        results = {}
        
        def _switch_device(device):
            success = device.set_state(state)
            return device.name, success

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
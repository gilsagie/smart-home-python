# devices/appliances/other.py
import logging
from ..base import SmartDevice

logger = logging.getLogger("OtherAppliance")

class Other(SmartDevice):
    """
    A Universal Wrapper for uncategorized devices.
    """
    def __init__(self, name, device_obj):
        ip = getattr(device_obj, 'ip', '0.0.0.0')
        dev_id = getattr(device_obj, 'device_id', 'N/A')
        stateless = getattr(device_obj, 'stateless', False)
        
        super().__init__(name, ip=ip, device_id=dev_id, stateless=stateless)
        self.device = device_obj

    def set_state_lan(self, state):
        return self.device.set_state(state)

    def get_state_lan(self):
        return self.device.get_state()
    
    def on(self): return self.set_state('on')
    def off(self): return self.set_state('off')
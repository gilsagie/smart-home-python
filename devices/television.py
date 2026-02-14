# devices/television.py
from .base import SmartDevice
import logging

logger = logging.getLogger("Television")

class Television(SmartDevice):
    def __init__(self, name, blaster, command_dict):
        # We use the blaster's IP for reference, but we are virtual
        super().__init__(name, ip=blaster.ip, device_id="N/A", stateless=True)
        self.blaster = blaster
        self.commands = command_dict

    def send(self, command_name):
        hex_code = self.commands.get(command_name)
        if not hex_code:
            logger.error(f"[{self.name}] Command '{command_name}' not found.")
            return False
            
        logger.info(f"[{self.name}] Sending '{command_name}' via {self.blaster.name}...")
        return self.blaster.send_hex(hex_code, repeat=1)

    def on(self):
        return self.send('power')

    def off(self):
        return self.send('power')

    # Required Abstract Methods
    def set_state_lan(self, state):
        return self.send(state) # Allows calling .set_state('on')

    def get_state_lan(self):
        return "N/A"
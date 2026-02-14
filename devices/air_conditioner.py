# devices/air_conditioner.py
import logging
from .base import SmartDevice

logger = logging.getLogger("UniversalAC")

class AirConditioner(SmartDevice):
    """
    A Universal Wrapper for AC units.
    - If the backing device is 'Smart' (Sensibo), it proxies commands to it.
    - If the backing device is 'Dumb' (IR Blaster), it constructs Hex commands.
    """
    def __init__(self, name, device_obj, command_dict=None):
        # Initialize as a stateless device (since IR devices can't report state)
        # We borrow the IP from the backing device if possible
        ip = getattr(device_obj, 'ip', '0.0.0.0')
        super().__init__(name, ip=ip, device_id="N/A", stateless=True)
        
        self.device = device_obj
        self.commands = command_dict or {}
        
        # Local state tracking (for IR devices that can't "read" the AC)
        self._temp = 24
        self._mode = "cool"
        self._is_on = False

    def on(self):
        """
        Turns the AC ON.
        - Sensibo: Calls .on()
        - IR: Sends 'on' hex OR re-sends the current mode/temp settings.
        """
        self._is_on = True
        logger.info(f"[{self.name}] Turning ON...")

        # 1. SMART: Sensibo has native .on()
        # We check if the device implies it is 'smart' by having set_temperature
        if hasattr(self.device, 'set_temperature'):
            return self.device.on()

        # 2. IR: Try to find an explicit 'on' or 'power' command
        if self._send_ir_command("on"): return True
        if self._send_ir_command("power"): return True

        # 3. IR Fallback: Most ACs turn on when you send the settings
        # e.g., Send "cool_24"
        return self._apply_ir_settings()

    def off(self):
        """
        Turns the AC OFF.
        """
        self._is_on = False
        logger.info(f"[{self.name}] Turning OFF...")

        # 1. SMART
        if hasattr(self.device, 'set_temperature'):
            return self.device.off()

        # 2. IR
        if self._send_ir_command("off"): return True
        if self._send_ir_command("power"): return True
        
        logger.warning(f"[{self.name}] No 'off' or 'power' command found in YAML.")
        return False

    def set_temperature(self, degrees):
        """
        Sets the target temperature.
        Example: ac.set_temperature(25)
        """
        self._temp = int(degrees)
        logger.info(f"[{self.name}] Setting temperature to {self._temp}°C")

        # 1. SMART
        if hasattr(self.device, 'set_temperature'):
            return self.device.set_temperature(self._temp)

        # 2. IR (Only send if we think the AC is on, or if we want to turn it on)
        self._is_on = True 
        return self._apply_ir_settings()

    def set_mode(self, mode):
        """
        Sets the operation mode.
        Options: 'cool', 'heat', 'fan', 'dry', 'auto'
        """
        self._mode = mode.lower()
        logger.info(f"[{self.name}] Setting mode to {self._mode}")

        # 1. SMART
        if hasattr(self.device, 'set_mode'):
            return self.device.set_mode(self._mode)

        # 2. IR
        self._is_on = True
        return self._apply_ir_settings()

    # --- Helper Methods for IR Logic ---

    def _apply_ir_settings(self):
        """
        Constructs the key (e.g., 'cool_24') and sends it.
        """
        # Construct key: e.g. "cool_24"
        cmd_key = f"{self._mode}_{self._temp}"
        return self._send_ir_command(cmd_key)

    def _send_ir_command(self, cmd_key):
        """
        Looks up the key in commands.yaml and sends via the blaster.
        """
        hex_code = self.commands.get(cmd_key)
        
        if not hex_code:
            # Silent fail for 'on'/'off' lookups (so we can fallback)
            # But specific fail for mode/temp
            if cmd_key not in ['on', 'power', 'off']:
                logger.warning(f"[{self.name}] Command '{cmd_key}' not found in configuration.")
            return False

        logger.info(f"[{self.name}] Sending IR command: '{cmd_key}' via {self.device.name}")
        
        # Determine how to send based on the backing device type
        if hasattr(self.device, 'send_hex'):
            return self.device.send_hex(hex_code)
        elif hasattr(self.device, 'send'):
            return self.device.send(hex_code)
        
        logger.error(f"[{self.name}] Backing device {self.device.name} has no send method.")
        return False

    # --- Required Abstract Methods from Base ---
    def set_state_lan(self, state):
        if state == 'on': return self.on()
        if state == 'off': return self.off()
        return False

    def get_state_lan(self):
        # If smart, proxy the state
        if hasattr(self.device, 'get_state'):
            return self.device.get_state()
        # If IR, return our optimistic guess
        return 'on' if self._is_on else 'off'
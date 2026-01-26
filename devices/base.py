# devices/base.py
import logging # <--- NEW IMPORT

# Create logger
logger = logging.getLogger("DeviceBase") # <--- NEW LOGGER

class SmartDevice:
    """
    Base class for all Smart Home devices (Sonoff, Shelly, Tuya, etc.).
    """
    def __init__(self, name, ip, device_id, channel=None, cloud_client=None):
        self.name = name
        self.ip = ip
        self.device_id = device_id
        self.channel = channel
        self.cloud_client = cloud_client
        self._state = None
    
    @property
    def state(self):
        if self._state != 'on' and self._state != 'off':
             logger.info(f"[{self.name}] State unknown. Fetching...") # <--- CHANGED
             self.get_state()
        return self._state

    def set_state_lan(self, state):
        raise NotImplementedError("Subclasses must implement set_state_lan()")

    def set_state(self, state):
        # 1. Try LAN
        try:
            if self.set_state_lan(state):
                self._state = state
                return True
        except Exception as e:
            logger.warning(f"[{self.name}] LAN Exception: {e}") # <--- CHANGED (Warning, because we have backup)

        # 2. Fallback to Cloud
        if self.cloud_client:
            logger.info(f"[{self.name}] LAN failed/unreachable. Switching to Cloud...") # <--- CHANGED
            self._state = state
            return self.cloud_client.set_state(self.device_id, state, self.channel)
        
        logger.error(f"[{self.name}] Failed: LAN unreachable and no Cloud client connected.") # <--- CHANGED
        return False

    def on(self):
        return self.set_state('on')

    def off(self):
        return self.set_state('off')
    
    def get_state(self):
        # 1. Try LAN
        try:
            state = self.get_state_lan()
            if state is not None:
                self._state = state
                logger.info(f"[{self.name}] State (LAN): {state}") # <--- CHANGED
                return state
        except Exception as e:
            logger.debug(f"[{self.name}] LAN Get-State Error: {e}") # <--- CHANGED (Debug to reduce noise)

        # 2. Fallback to Cloud
        if self.cloud_client:
            logger.info(f"[{self.name}] LAN unreachable. Fetching state from Cloud...") # <--- CHANGED
            state = self.cloud_client.get_state(self.device_id, self.channel)
            if state is not None:
                self._state = state
            return state
        
        logger.error(f"[{self.name}] Error: Could not retrieve state (Device Offline).") # <--- CHANGED
        return None

    def get_state_lan(self):
        raise NotImplementedError("Subclasses must implement get_state_lan()")
# devices/base.py
import logging

logger = logging.getLogger("DeviceBase")

class SmartDevice:
    def __init__(self, name, ip, device_id, channel=None, cloud_client=None, stateless=False):
        self.name = name
        self.ip = ip
        self.device_id = device_id
        self.channel = channel
        self.cloud_client = cloud_client
        self.stateless = stateless
        self._state = None
    
    @property
    def state(self):
        if self.stateless:
            return "N/A"
        # Only fetch if we really don't know (None). 
        # If it is 'OFFLINE' or 'ERROR', we might want to respect that until forced refresh.
        if self._state is None:
             logger.info(f"[{self.name}] State unknown. Fetching...")
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
            logger.warning(f"[{self.name}] LAN Exception: {e}")

        # 2. Fallback to Cloud
        if self.cloud_client:
            logger.info(f"[{self.name}] LAN failed/unreachable. Switching to Cloud...")
            if self.cloud_client.set_state(self.device_id, state, self.channel):
                self._state = state
                return True
            else:
                return False
        
        logger.error(f"[{self.name}] Failed: LAN unreachable and no Cloud client connected.")
        return False

    def on(self):
        return self.set_state('on')

    def off(self):
        return self.set_state('off')
    
    def get_state(self):
        if self.stateless:
            return "N/A"
        
        # 1. Try LAN
        try:
            state = self.get_state_lan()
            if state is not None:
                self._state = state
                logger.info(f"[{self.name}] State (LAN): {state}")
                return state
        except Exception as e:
            logger.debug(f"[{self.name}] LAN Get-State Error: {e}")

        # 2. Fallback to Cloud
        if self.cloud_client:
            logger.info(f"[{self.name}] LAN unreachable. Fetching state from Cloud...")
            state = self.cloud_client.get_state(self.device_id, self.channel)
            if state is not None:
                self._state = state
                return state
        
        logger.error(f"[{self.name}] Error: Could not retrieve state (Device Offline).")
        # CHANGED: Mark as offline to prevent infinite fetch loops in the .state property
        self._state = "OFFLINE"
        return "OFFLINE"

    def get_state_lan(self):
        raise NotImplementedError("Subclasses must implement get_state_lan()")
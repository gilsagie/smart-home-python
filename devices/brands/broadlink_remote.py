# devices/brands/broadlink_remote.py
import broadlink
import logging
from ..base import SmartDevice

logger = logging.getLogger("Broadlink")

class BroadlinkRemote(SmartDevice):
    def __init__(self, name, ip, device_id, mac, cloud_client=None, stateless=True):
        super().__init__(name, ip, device_id, stateless=stateless)
        self.mac = mac
        self.device = None
        
        # Try to connect immediately, but don't crash if it fails
        self._connect()

    def _connect(self):
        try:
            self.device = broadlink.hello(self.ip)
            self.device.auth()
            logger.info(f"[{self.name}] Connected to Broadlink device.")
            return True
        except Exception as e:
            logger.warning(f"[{self.name}] Connection failed during init: {e}")
            self.device = None
            return False

    def send_hex(self, hex_data, repeat=1):
        # 1. Ensure we have a device object
        if not self.device:
            logger.info(f"[{self.name}] Device not connected. Retrying...")
            if not self._connect():
                return False

        # 2. Send Data
        try:
            packet = bytes.fromhex(hex_data)
            for _ in range(repeat):
                self.device.send_data(packet)
            return True
        except Exception as e:
            logger.warning(f"[{self.name}] Send failed: {e}. Retrying auth...")
            # Try re-auth once
            try:
                self.device.auth()
                self.device.send_data(packet)
                return True
            except Exception as e2:
                logger.error(f"[{self.name}] Retry failed: {e2}")
                return False

    def set_state_lan(self, state): return True
    def get_state_lan(self): return "N/A"
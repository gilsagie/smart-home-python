# devices/broadlink_remote.py
import broadlink
from ..base import SmartDevice

class BroadlinkRemote(SmartDevice):
    def __init__(self, name, ip, device_id, mac, cloud_client=None, stateless=True):
        super().__init__(name, ip, device_id, stateless=stateless)
        # Handle MAC formatting if needed (remove colons)
        self.device = broadlink.hello(ip)
        self.device.auth()

    def send_hex(self, hex_data, repeat=1):
        try:
            packet = bytes.fromhex(hex_data)
            # Send the packet multiple times
            for _ in range(repeat):
                self.device.send_data(packet)
            return True
        except Exception as e:
            # Try re-auth if it fails
            try:
                self.device.auth()
                self.device.send_data(packet)
                return True
            except:
                return False

    def set_state_lan(self, state): return True
    def get_state_lan(self): return "N/A"
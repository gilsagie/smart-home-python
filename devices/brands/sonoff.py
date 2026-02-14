# devices/sonoff.py
import requests
import json
import time
import base64
import hashlib
import logging # <--- NEW IMPORT
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

from ..base import SmartDevice

logger = logging.getLogger("SonoffLAN") # <--- NEW LOGGER

class SonoffSwitch(SmartDevice):
    def __init__(self, name, ip, device_id, device_key, mac=None, channel=None, cloud_client=None, stateless=False):
        super().__init__(name, ip, device_id, channel, cloud_client, stateless=stateless)
        self.device_key = device_key
        self.mac = mac
        self.port = 8081

    def _encrypt_payload(self, data_dict):
        # ... (Same encryption logic as before) ...
        data_str = json.dumps(data_dict, separators=(',', ':'))
        key_bytes = hashlib.md5(self.device_key.encode('utf-8')).digest()
        iv = get_random_bytes(16)
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
        ct_bytes = cipher.encrypt(pad(data_str.encode('utf-8'), AES.block_size))
        encoded_data = base64.b64encode(ct_bytes).decode('utf-8')
        encoded_iv = base64.b64encode(iv).decode('utf-8')
        return encoded_data, encoded_iv

    def _send_lan_request(self, endpoint, data_body):
        url = f"http://{self.ip}:{self.port}/zeroconf/{endpoint}"
        
        payload = {
            "sequence": str(int(time.time() * 1000)),
            "deviceid": self.device_id,
            "selfApikey": "123", 
        }

        if self.device_key:
            enc_data, iv = self._encrypt_payload(data_body)
            payload["encrypt"] = True
            payload["iv"] = iv
            payload["data"] = enc_data
        else:
            payload["data"] = data_body

        r = requests.post(url, json=payload, timeout=2) 
        return r.json()

    def set_state_lan(self, state):
        try:
            # logger.debug is useful here to avoid cluttering logs unless debugging
            logger.debug(f"[{self.name}] Trying LAN control (Sonoff)...") # <--- CHANGED
            
            if self.channel is not None:
                endpoint = "switches"
                payload = {
                    "switches": [
                        {"outlet": int(self.channel), "switch": state}
                    ]
                }
            else:
                endpoint = "switch"
                payload = {"switch": state}

            resp = self._send_lan_request(endpoint, payload)
            
            if resp.get('error') == 0:
                logger.info(f"[{self.name}] LAN Success.") # <--- CHANGED
                return True
            else:
                logger.error(f"[{self.name}] LAN Error: {resp}") # <--- CHANGED
                return False
                
        except Exception as e:
            logger.warning(f"[{self.name}] LAN Unreachable ({e})") # <--- CHANGED
            return False
        
    def get_state_lan(self):
        resp = self._send_lan_request('info', {})
        
        if not resp or resp.get('error') != 0:
            return None

        data = resp.get('data', {})

        if self.channel is not None:
            switches = data.get('switches', [])
            for sw in switches:
                if sw.get('outlet') == self.channel:
                    return sw.get('switch')
        else:
            return data.get('switch')
            
        return None
import requests
import json
import time
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

class SonoffSwitch:
    # 1. Add cloud_client as an optional argument
    def __init__(self, name, ip, device_id, device_key, mac=None, cloud_client=None):
        self.name = name
        self.ip = ip
        self.device_id = device_id
        self.device_key = device_key
        self.mac = mac
        self.cloud_client = cloud_client  # Store the shared cloud connection
        self.port = 8081

    def _encrypt_payload(self, data_dict):
        # ... (Same encryption code as before) ...
        data_str = json.dumps(data_dict, separators=(',', ':'))
        key_bytes = hashlib.md5(self.device_key.encode('utf-8')).digest()
        iv = get_random_bytes(16)
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
        ct_bytes = cipher.encrypt(pad(data_str.encode('utf-8'), AES.block_size))
        encoded_data = base64.b64encode(ct_bytes).decode('utf-8')
        encoded_iv = base64.b64encode(iv).decode('utf-8')
        return encoded_data, encoded_iv

    def _send_lan_request(self, endpoint, data_body):
        """Helper to send the actual POST request via LAN"""
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

        # Short timeout for LAN (so we switch to cloud quickly if it fails)
        r = requests.post(url, json=payload, timeout=2) 
        return r.json()

    def _set_state_lan(self, state):
        """Internal function to try LAN control"""
        try:
            print(f"[{self.name}] Trying LAN control...")
            resp = self._send_lan_request("switch", {"switch": state})
            
            if resp.get('error') == 0:
                print(f"[{self.name}] LAN Success.")
                return True
            else:
                print(f"[{self.name}] LAN Error: {resp}")
                return False
        except Exception as e:
            print(f"[{self.name}] LAN Unreachable ({e})")
            return False

    # --- MAIN CONTROL FUNCTION ---
    def set_state(self, state):
        """
        The Smart Hybrid Logic:
        1. Try LAN (Fastest).
        2. If LAN fails, use the shared Cloud Client (Reliable).
        """
        
        # 1. Try LAN
        if self._set_state_lan(state):
            return True

        # 2. Fallback to Cloud
        if self.cloud_client:
            print(f"[{self.name}] Switching to Cloud...")
            return self.cloud_client.set_state(self.device_id, state)
        
        print(f"[{self.name}] Failed: LAN unreachable and no Cloud client connected.")
        return False

    # --- User Friendly Functions ---
    def on(self):
        return self.set_state('on')

    def off(self):
        return self.set_state('off')
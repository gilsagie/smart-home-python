# devices/sonoff.py
import requests
import json
import time
import base64
import hashlib
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

# CHANGE: Relative import from the same package
from .base import SmartDevice

class SonoffSwitch(SmartDevice):
    def __init__(self, name, ip, device_id, device_key, mac=None, channel=None, cloud_client=None):
        # 2. Initialize the Parent
        # We pass the new 'channel' argument up to SmartDevice
        super().__init__(name, ip, device_id, channel, cloud_client)
        
        self.device_key = device_key
        self.mac = mac
        self.port = 8081

    def _encrypt_payload(self, data_dict):
        """Helper: Encrypts data for Sonoff DIY mode"""
        data_str = json.dumps(data_dict, separators=(',', ':'))
        key_bytes = hashlib.md5(self.device_key.encode('utf-8')).digest()
        iv = get_random_bytes(16)
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
        ct_bytes = cipher.encrypt(pad(data_str.encode('utf-8'), AES.block_size))
        encoded_data = base64.b64encode(ct_bytes).decode('utf-8')
        encoded_iv = base64.b64encode(iv).decode('utf-8')
        return encoded_data, encoded_iv

    def _send_lan_request(self, endpoint, data_body):
        """Helper: Sends the HTTP POST to the device"""
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

        # Short timeout so we fail fast and try Cloud if needed
        r = requests.post(url, json=payload, timeout=2) 
        return r.json()

    def set_state_lan(self, state):
        """
        The specific LAN protocol for Sonoff.
        Handles both Single-channel and Multi-channel devices.
        """
        try:
            print(f"[{self.name}] Trying LAN control (Sonoff)...")
            
            # --- LOGIC SPLIT FOR 2-WAY SWITCHES ---
            if self.channel is not None:
                # It's a multi-channel device (e.g., Dual R3)
                # Endpoint is 'switches', payload needs 'outlet' index
                endpoint = "switches"
                payload = {
                    "switches": [
                        {"outlet": int(self.channel), "switch": state}
                    ]
                }
            else:
                # It's a standard single relay (e.g., Basic / Mini)
                endpoint = "switch"
                payload = {"switch": state}
            # --------------------------------------

            resp = self._send_lan_request(endpoint, payload)
            
            if resp.get('error') == 0:
                print(f"[{self.name}] LAN Success.")
                return True
            else:
                print(f"[{self.name}] LAN Error: {resp}")
                return False
                
        except Exception as e:
            # We raise the error or return False so the Parent class knows to try Cloud
            print(f"[{self.name}] LAN Unreachable ({e})")
            return False
        
    def get_state_lan(self):
        """
        Queries the device directly via HTTP for its status.
        Target: /zeroconf/info
        """
        # Send an empty data body to the 'info' endpoint
        resp = self._send_lan_request('info', {})
        
        # Check if we got a valid response
        if not resp or resp.get('error') != 0:
            return None

        # Extract the 'data' block
        data = resp.get('data', {})

        # --- LOGIC SPLIT: Multi-Channel vs Single ---
        if self.channel is not None:
            # Multi-Channel (e.g., switches=[{outlet:0, switch:'on'}, ...])
            switches = data.get('switches', [])
            for sw in switches:
                if sw.get('outlet') == self.channel:
                    return sw.get('switch') # Returns 'on' or 'off'
        else:
            # Single Channel (e.g., switch='on')
            return data.get('switch')
            
        return None
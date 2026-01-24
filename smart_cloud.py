import requests
import json
import hmac
import hashlib
import base64
import random
import string
import urllib3
import os

# Disable SSL Warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class SonoffCloudClient:
    def __init__(self, app_id=None, app_secret=None, access_token=None, region='as'):
        self.app_id = app_id
        self.app_secret = app_secret
        self.access_token = access_token
        self.api_url = f'https://{region}-apia.coolkit.cc/v2'
        self._get_id_data()
        
    def _get_id_data(self):
        if self.app_id:
            return
        credentials = {}
        cred_file = os.path.join(os.path.dirname(__file__), 'credentials.txt')
        
        try:
            with open(cred_file, 'r') as f:
                for line in f:
                    # Skip empty lines or comments
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        credentials[key.strip()] = value.strip()
        
        except FileNotFoundError:
            print("Error: credentials.txt file not found!")
            exit()
        
        # 2. Extract variables
        self.app_id = credentials.get('APP_ID')
        self.app_secret = credentials.get('APP_SECRET')
        self.access_token = credentials.get('ACCESS_TOKEN')
        return

    def _get_signature(self, data_str):
        """Calculates the digital signature required by eWeLink"""
        digest = hmac.new(
            self.app_secret.encode('utf-8'), 
            data_str.encode('utf-8'), 
            hashlib.sha256
        ).digest()
        return base64.b64encode(digest).decode('utf-8')

    def _make_request(self, method, endpoint, payload=None):
        url = f"{self.api_url}{endpoint}"
        data_str = json.dumps(payload, separators=(',', ':')) if payload else ''
        sign = self._get_signature(data_str)
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',  # Use Token Directly
            'Content-Type': 'application/json',
            'X-CK-Appid': self.app_id,
            'X-CK-Nonce': ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        }

        # V2 API requires the signature in a special header 'Sign'
        headers['Authorization'] = f'Sign {sign}'
        # But wait! For authenticated requests, the Authorization header is usually 'Bearer <token>'
        # AND the signature goes into 'X-CK-Signature' or similar, OR we stack them.
        
        # CORRECTION For V2 API with Personal ID:
        # 1. Authorization: Bearer <token>
        # 2. X-CK-Appid: <appid>
        # 3. Signature is often NOT required for simple control if Bearer is present, 
        #    BUT if it is, it might be separate. 
        # Let's try the standard V2 Headers for control:
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-CK-Appid': self.app_id,
            'X-CK-Nonce': ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        }
        
        # Some endpoints require re-signing the payload even with Bearer. 
        # We will add it as a custom header just in case.
        headers['Sign'] = sign 

        try:
            if method == 'POST':
                r = requests.post(url, data=data_str, headers=headers, verify=False)
            else:
                r = requests.get(url, headers=headers, verify=False)
            return r.json()
        except Exception as e:
            print(f"Cloud Connection Error: {e}")
            return {'error': -1}
    
    def set_state(self, device_id, state, channel=None):
        """
        device_id: The ID from your CSV
        state: 'on' or 'off'
        channel: The specific channel (0, 1, etc.) for multi-switches. None for single.
        """
        print(f"[Cloud] Sending {state} to {device_id} (Channel: {channel})...")
        
        # --- LOGIC SPLIT ---
        if channel is not None:
            # Multi-Channel Payload (for 2-way switches)
            # The API expects a list of switches to update
            params = {
                "switches": [
                    {"outlet": int(channel), "switch": state}
                ]
            }
        else:
            # Single-Channel Payload (Standard)
            params = {
                "switch": state
            }
        # -------------------
        
        payload = {
            'type': 1, # 1 = Device
            'id': device_id,
            'params': params
        }
        
        resp = self._make_request('POST', '/device/thing/status', payload)
        
        # Check for success (error: 0)
        if resp.get('error') == 0:
            print("SUCCESS: Command delivered.")
            return True
        else:
            print(f"Cloud Error: {resp}")
            return False
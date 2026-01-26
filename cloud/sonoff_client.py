# cloud/sonoff_client.py
import requests
import json
import hmac
import hashlib
import base64
import random
import string
import urllib3
import os
import sys  # <--- ADD THIS IMPORT

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
        # Path fix to find config/credentials.txt
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        cred_file = os.path.join(project_root, 'config', 'credentials.txt')
        
        try:
            with open(cred_file, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        credentials[key.strip()] = value.strip()
        
        except FileNotFoundError:
            print(f"Error: credentials.txt not found at {cred_file}")
            sys.exit()  # <--- CHANGED from exit() to sys.exit()
            
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
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
            'X-CK-Appid': self.app_id,
            'X-CK-Nonce': ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        }
        
        headers['Sign'] = sign 

        try:
            if method == 'POST':
                r = requests.post(url, data=data_str, headers=headers)#, verify=False)
            else:
                r = requests.get(url, headers=headers)#, verify=False)
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
        
        if channel is not None:
            params = {
                "switches": [
                    {"outlet": int(channel), "switch": state}
                ]
            }
        else:
            params = {
                "switch": state
            }
        
        payload = {
            'type': 1, 
            'id': device_id,
            'params': params
        }
        
        resp = self._make_request('POST', '/device/thing/status', payload)
        
        if resp.get('error') == 0:
            print("SUCCESS: Command delivered.")
            return True
        else:
            print(f"Cloud Error: {resp}")
            return False
        
    def get_state(self, device_id, channel=None):
        """
        Fetches state handling 'thingList' and Multi-Gang (2-channel) devices.
        """
        endpoint = f'/device/thing?id={device_id}'
        print(f"[Cloud] Fetching status for {device_id}...")
        
        resp = self._make_request('GET', endpoint)
        
        if resp.get('error') != 0:
            print(f"[Cloud] API Error {resp.get('error')}: {resp.get('msg')}")
            return None

        params = None
        data = resp.get("data", {})

        if "thingList" in data:
            for thing in data["thingList"]:
                item_data = thing.get("itemData", {})
                if item_data.get("deviceid") == device_id:
                    params = item_data.get("params", {})
                    break
        elif "itemData" in data:
            params = data["itemData"].get("params", {})
        elif "params" in data:
            params = data.get("params", {})

        if not params:
            print(f"[Cloud] Error: Could not find params for {device_id}")
            return None

        if channel is not None:
            switches = params.get("switches", [])
            for sw in switches:
                if sw.get("outlet") == channel:
                    return sw.get("switch")
            
            if f"switch_{channel}" in params:
                 return params[f"switch_{channel}"]

            print(f"[Cloud] Warning: Channel {channel} requested but not found in params.")

        if "switch" in params:
            return params["switch"]
            
        return None
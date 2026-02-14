# cloud/sonoff_client.py
import requests
import json
import hmac
import hashlib
import base64
import random
import string
import urllib3
import logging
from utils.config import get_sonoff_creds  # <--- NEW IMPORT

# Disable SSL Warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = logging.getLogger("SonoffCloud")

class SonoffCloudClient:
    def __init__(self, app_id=None, app_secret=None, access_token=None, region='as'):
        # Allow overrides, otherwise load from .env
        creds = get_sonoff_creds()
        
        self.app_id = app_id or creds['app_id']
        self.app_secret = app_secret or creds['app_secret']
        self.access_token = access_token or creds['access_token']
        # If the user passed a region, use it, otherwise use config
        self.region = region if region != 'as' else creds['region']
        
        if not self.app_id or not self.access_token:
            logger.warning("Sonoff credentials missing or incomplete.")
            
        self.api_url = f'https://{self.region}-apia.coolkit.cc/v2'

    # ... (Rest of the class methods: _get_signature, _make_request, set_state, get_state remain EXACTLY the same) ...
    def _get_signature(self, data_str):
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
                r = requests.post(url, data=data_str, headers=headers)
            else:
                r = requests.get(url, headers=headers)
            return r.json()
        except Exception as e:
            logger.error(f"Cloud Connection Error: {e}")
            return {'error': -1}
    
    def set_state(self, device_id, state, channel=None):
        logger.info(f"Sending {state} to {device_id} (Channel: {channel})...")
        
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
            logger.info("Command delivered successfully.")
            return True
        else:
            logger.error(f"Cloud API Error: {resp}")
            return False
        
    def get_state(self, device_id, channel=None):
        endpoint = f'/device/thing?id={device_id}'
        logger.info(f"Fetching status for {device_id}...")
        
        resp = self._make_request('GET', endpoint)
        
        if resp.get('error') != 0:
            logger.error(f"API Error {resp.get('error')}: {resp.get('msg')}")
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
            logger.error(f"Could not find params for {device_id}")
            return None

        if channel is not None:
            switches = params.get("switches", [])
            for sw in switches:
                if sw.get("outlet") == channel:
                    return sw.get("switch")
            
            if f"switch_{channel}" in params:
                 return params[f"switch_{channel}"]

            logger.warning(f"Channel {channel} requested but not found in params.")

        if "switch" in params:
            return params["switch"]
            
        return None
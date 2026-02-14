# cloud/sensibo_client.py
import requests
import logging
from utils.config import get_sensibo_creds  # <--- NEW IMPORT

logger = logging.getLogger("SensiboCloud")

class SensiboCloudClient:
    def __init__(self):
        self.base_url = "https://home.sensibo.com/api/v2"
        
        creds = get_sensibo_creds()
        self.api_key = creds['api_key']
        
        if not self.api_key:
            logger.warning("SENSIBO_API_KEY missing in .env")

    # ... (Rest of the class methods: set_state, send_ac_state, get_state, get_measurements remain EXACTLY the same) ...
    def set_state(self, device_id, state, channel=None):
        return self.send_ac_state(device_id, {'on': (state == 'on')})

    def send_ac_state(self, device_id, state_dict):
        if not self.api_key:
            return False

        url = f"{self.base_url}/pods/{device_id}/acStates"
        params = {'apiKey': self.api_key}
        payload = {"acState": state_dict}
        
        logger.info(f"Sensibo [{device_id}] Setting: {state_dict}...")
        
        try:
            resp = requests.post(url, params=params, json=payload, timeout=5)
            data = resp.json()
            
            if resp.status_code == 200 and data.get('status') == 'success':
                logger.info(" -> Success.")
                return True
            else:
                logger.error(f" -> Sensibo API Error: {data}")
                return False
        except Exception as e:
            logger.error(f" -> Connection Failed: {e}")
            return False

    def get_state(self, device_id, channel=None):
        if not self.api_key: return None
        
        url = f"{self.base_url}/pods/{device_id}"
        params = {'apiKey': self.api_key, 'fields': 'acState'}
        
        try:
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            
            if resp.status_code == 200 and data.get('status') == 'success':
                pod = data.get('result', {})
                ac_state = pod.get('acState', {})
                is_on = ac_state.get('on', False)
                return 'on' if is_on else 'off'
            else:
                logger.error(f"Sensibo API Error: {data}")

        except Exception as e:
            logger.error(f"Sensibo Connection Failed: {e}")
            
        return None
    
    def get_measurements(self, device_id):
        if not self.api_key:
            return None

        url = f"{self.base_url}/pods/{device_id}"
        params = {
            'apiKey': self.api_key, 
            'fields': 'measurements'
        }
        
        try:
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            
            if resp.status_code == 200 and data.get('status') == 'success':
                return data.get('result', {}).get('measurements', {})
            
            logger.error(f"Sensibo API Error (Measurements): {data}")
            return None
            
        except Exception as e:
            logger.error(f"Sensibo Connection Failed: {e}")
            return None
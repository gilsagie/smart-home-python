# -*- coding: utf-8 -*-
"""
Created on Thu Jan 29 19:18:53 2026

@author: User
"""

# cloud/sensibo_client.py
import requests
import json
import logging
import os

logger = logging.getLogger("SensiboCloud")

class SensiboCloudClient:
    def __init__(self):
        self.api_key = None
        self._get_credentials()
        self.base_url = "https://home.sensibo.com/api/v2"

    def _get_credentials(self):
        credentials = {}
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(current_dir)
        cred_file = os.path.join(project_root, 'config', 'credentials.txt')
        
        try:
            with open(cred_file, 'r') as f:
                for line in f:
                    if '=' in line:
                        key, value = line.strip().split('=', 1)
                        credentials[key.strip()] = value.strip()
            
            self.api_key = credentials.get('SENSIBO_API_KEY')
            if not self.api_key:
                logger.warning("SENSIBO_API_KEY missing in credentials.txt")
                
        except FileNotFoundError:
            logger.error(f"credentials.txt not found at {cred_file}")

    def set_state(self, device_id, state, channel=None):
        # Maps standard "on/off" to Sensibo format
        return self.send_ac_state(device_id, {'on': (state == 'on')})

    def send_ac_state(self, device_id, state_dict):
        """
        Sends a specific dictionary of AC settings.
        Example state_dict: {'targetTemperature': 24, 'mode': 'cool'}
        """
        if not self.api_key:
            return False

        url = f"{self.base_url}/pods/{device_id}/acStates"
        params = {'apiKey': self.api_key}
        
        # Sensibo API requires data nested in "acState"
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
        
        # CHANGED: Query the Pod directly for current status, not history
        url = f"{self.base_url}/pods/{device_id}"
        
        # We only ask for the 'acState' field to keep it fast
        params = {'apiKey': self.api_key, 'fields': 'acState'}
        
        try:
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            
            if resp.status_code == 200 and data.get('status') == 'success':
                # The 'result' here is the Pod object itself
                pod = data.get('result', {})
                ac_state = pod.get('acState', {})
                
                # Debugging: Uncomment if you still have issues
                # logger.info(f"Sensibo Raw State: {ac_state}")

                is_on = ac_state.get('on', False)
                return 'on' if is_on else 'off'
            else:
                logger.error(f"Sensibo API Error: {data}")

        except Exception as e:
            logger.error(f"Sensibo Connection Failed: {e}")
            
        return None
    
    def get_measurements(self, device_id):
        """
        Fetches current room temperature, humidity, and battery voltage.
        """
        if not self.api_key:
            return None

        # We query the specific pod for its 'measurements' field
        url = f"{self.base_url}/pods/{device_id}"
        params = {
            'apiKey': self.api_key, 
            'fields': 'measurements'
        }
        
        try:
            resp = requests.get(url, params=params, timeout=5)
            data = resp.json()
            
            if resp.status_code == 200 and data.get('status') == 'success':
                # Result is a dictionary containing the 'measurements' object
                return data.get('result', {}).get('measurements', {})
            
            logger.error(f"Sensibo API Error (Measurements): {data}")
            return None
            
        except Exception as e:
            logger.error(f"Sensibo Connection Failed: {e}")
            return None
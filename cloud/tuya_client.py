# cloud/tuya_client.py
import tinytuya
import os
import sys
import logging

# Create logger for this module (Same style as Sonoff)
logger = logging.getLogger("TuyaCloud")

class TuyaCloudClient:
    def __init__(self, api_region="eu"):
        self.api_key = None
        self.api_secret = None
        self.api_device_id = None
        self.region = api_region
        self.cloud = None

        # 1. Load credentials from file (Like Sonoff)
        self._get_credentials()

        # 2. Connect to Tuya Cloud
        if self.api_key and self.api_secret:
            try:
                logger.info(f"Connecting to Tuya Cloud (Region: {self.region})...")
                self.cloud = tinytuya.Cloud(
                    apiRegion=self.region, 
                    apiKey=self.api_key, 
                    apiSecret=self.api_secret, 
                    apiDeviceID=self.api_device_id
                )
                logger.info("Tuya Cloud connected.")
            except Exception as e:
                logger.error(f"Tuya Cloud Connection Failed: {e}")
        else:
            logger.warning("Tuya Cloud credentials missing in credentials.txt")

    def _get_credentials(self):
        """
        Parses credentials.txt to find TUYA_API_KEY, TUYA_API_SECRET, etc.
        Mirrors the logic in SonoffCloudClient.
        """
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
        
        except FileNotFoundError:
            logger.error(f"credentials.txt not found at {cred_file}")
            return

        # Map the keys from the file to our variables
        self.api_key = credentials.get('TUYA_API_KEY')
        self.api_secret = credentials.get('TUYA_API_SECRET')
        self.api_device_id = credentials.get('TUYA_DEVICE_ID') # Needs ANY valid ID to start session
        self.region = credentials.get('TUYA_REGION', self.region)

    def set_state(self, device_id, state, channel=None):
        if not self.cloud:
            logger.error("Cloud not initialized.")
            return False
            
        # LOGIC CHANGE: Determine the correct code
        if channel:
            # If a channel is explicitly set (e.g., channel 2), use 'switch_2'
            cmd_code = f"switch_{channel}"
        else:
            # For standard single plugs/switches, the code is just 'switch'
            cmd_code = "switch"
            
        logger.info(f"Sending {state} to {device_id} (Code: {cmd_code})...")
        
        commands = {
            "commands": [
                {"code": cmd_code, "value": (state == 'on')}
            ]
        }
        
        try:
            result = self.cloud.sendcommand(device_id, commands)
            if result and result.get('success'):
                logger.info("Command delivered successfully.")
                return True
            else:
                logger.error(f"Cloud API Error: {result}")
                return False
        except Exception as e:
            logger.error(f"Exception sending command: {e}")
            return False

    def get_state(self, device_id, channel=None):
        if not self.cloud:
            return None
        
        logger.info(f"Fetching status for {device_id}...")
        try:
            result = self.cloud.getstatus(device_id)
            
            if result and result.get('success'):
                status_list = result.get('result', [])
                
                # LOGIC CHANGE: Match the code we expect
                target_code = f"switch_{channel}" if channel else "switch"
                
                for item in status_list:
                    if item.get('code') == target_code:
                        return 'on' if item.get('value') else 'off'
                
                # Debugging: Show available codes if we missed
                available_codes = [x.get('code') for x in status_list]
                logger.warning(f"Code '{target_code}' not found. Available: {available_codes}")
            else:
                logger.error(f"Cloud Get Status Failed: {result}")
                
        except Exception as e:
            logger.error(f"Exception fetching status: {e}")
            
        return None

    def get_state(self, device_id, channel=None):
        if not self.cloud:
            return None
        
        logger.info(f"Fetching status for {device_id}...")
        try:
            result = self.cloud.getstatus(device_id)
            # Result format example: {'success': True, 'result': [{'code': 'switch_1', 'value': True}, ...]}
            
            if result and result.get('success'):
                status_list = result.get('result', [])
                target_code = f"switch_{channel if channel else '1'}"
                
                for item in status_list:
                    if item.get('code') == target_code:
                        return 'on' if item.get('value') else 'off'
                
                logger.warning(f"Code {target_code} not found in cloud response.")
            else:
                logger.error(f"Cloud Get Status Failed: {result}")
                
        except Exception as e:
            logger.error(f"Exception fetching status: {e}")
            
        return None
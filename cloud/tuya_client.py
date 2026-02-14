# cloud/tuya_client.py
import tinytuya
import logging
from utils.config import get_tuya_creds  # <--- NEW IMPORT

logger = logging.getLogger("TuyaCloud")

class TuyaCloudClient:
    def __init__(self, api_region="eu"):
        self.cloud = None

        # Load credentials
        creds = get_tuya_creds()
        self.api_key = creds['api_key']
        self.api_secret = creds['api_secret']
        self.api_device_id = creds['device_id']
        # Prefer .env region, fallback to arg
        self.region = creds['region'] if creds['region'] else api_region

        # Connect to Tuya Cloud
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
            logger.warning("Tuya credentials missing in .env")

    # ... (Rest of the class methods: set_state, get_state remain EXACTLY the same) ...
    def set_state(self, device_id, state, channel=None):
        if not self.cloud:
            logger.error("Cloud not initialized.")
            return False
            
        if channel:
            cmd_code = f"switch_{channel}"
        else:
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
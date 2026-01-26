# -*- coding: utf-8 -*-
# cloud/tuya_client.py
import tinytuya
import os

class TuyaCloudClient:
    def __init__(self, api_region="eu"):
        # We assume credentials might be in environment variables or hardcoded for now
        # Ideally, add TUYA_API_KEY, TUYA_API_SECRET to your credentials.txt loader
        self.api_key = os.getenv("TUYA_API_KEY", "") 
        self.api_secret = os.getenv("TUYA_API_SECRET", "")
        self.api_device_id = os.getenv("TUYA_ANY_DEVICE_ID", "") # Needed for initial connection
        self.region = api_region
        self.cloud = None

        if self.api_key and self.api_secret:
            print("[TuyaCloud] Connecting to Cloud...")
            self.cloud = tinytuya.Cloud(
                apiRegion=self.region, 
                apiKey=self.api_key, 
                apiSecret=self.api_secret, 
                apiDeviceID=self.api_device_id
            )

    def set_state(self, device_id, state, channel=None):
        if not self.cloud:
            print("[TuyaCloud] Not configured (Missing Keys).")
            return False
            
        print(f"[TuyaCloud] Sending {state} to {device_id}...")
        
        # Logic to convert channel to DPS index
        dps_index = str(channel) if channel else '1'
        
        # Use Tuya's official command format
        commands = {
            "commands": [
                {"code": f"switch_{dps_index}", "value": (state == 'on')}
            ]
        }
        
        # Send Command
        result = self.cloud.sendcommand(device_id, commands)
        
        if result and result.get('success'):
            return True
        else:
            print(f"[TuyaCloud] Error: {result}")
            return False

    def get_state(self, device_id, channel=None):
        if not self.cloud:
            return None
            
        result = self.cloud.getstatus(device_id)
        
        # Parse result... (This implementation depends on exact API response)
        # For now, we return None to force LAN priority or implementation later
        return None

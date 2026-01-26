# -*- coding: utf-8 -*-
"""
Created on Mon Jan 26 18:58:58 2026

@author: User
"""

# devices/tuya.py
import tinytuya
import time
from .base import SmartDevice

class TuyaSwitch(SmartDevice):
    def __init__(self, name, ip, device_id, local_key, version=3.3, channel=None, cloud_client=None):
        super().__init__(name, ip, device_id, channel, cloud_client)
        
        self.local_key = local_key
        self.version = version
        
        # Initialize TinyTuya Device
        # We use OutletDevice as a generic handler for switches/plugs
        self.device = tinytuya.OutletDevice(
            dev_id=self.device_id,
            address=self.ip,
            local_key=self.local_key, 
            version=self.version
        )
        
        # Optimization: Persist connection if possible, but handle disconnects gracefully
        self.device.set_socketPersistent(False) 

    def _get_dps_index(self):
        """
        Maps the channel (int) to Tuya's DPS index (str).
        Default is '1' for single switches.
        """
        return str(self.channel) if self.channel else '1'

    def set_state_lan(self, state):
        """
        Implementation of Abstract Method.
        Uses TinyTuya to send command locally.
        """
        print(f"[{self.name}] Trying LAN control (Tuya)...")
        
        try:
            target_bool = (state == 'on')
            dps_index = self._get_dps_index()
            
            # Send payload: {'1': True} or {'2': False}
            payload = self.device.generate_payload(
                tinytuya.CONTROL, 
                {dps_index: target_bool}
            )
            
            # Send request
            data = self.device._send_receive(payload)
            
            # TinyTuya returns None on failure or a dict on success
            if data and 'Error' not in data:
                print(f"[{self.name}] LAN Success.")
                return True
            else:
                print(f"[{self.name}] LAN Error: {data}")
                return False
                
        except Exception as e:
            print(f"[{self.name}] LAN Unreachable ({e})")
            return False

    def get_state_lan(self):
        """
        Queries status via LAN.
        Parses Tuya's 'dps' dictionary (e.g. {'1': True, '2': False}).
        """
        try:
            data = self.device.status()
            
            if not data or 'dps' not in data:
                return None
            
            dps = data['dps']
            dps_index = self._get_dps_index()
            
            if dps_index in dps:
                is_on = dps[dps_index]
                return 'on' if is_on else 'off'
            
            return None
            
        except Exception as e:
            print(f"[{self.name}] LAN Get-State Error: {e}")
            return None
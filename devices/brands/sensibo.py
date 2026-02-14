# -*- coding: utf-8 -*-
"""
Created on Thu Jan 29 19:19:13 2026

@author: User
"""

# devices/sensibo.py
from ..base import SmartDevice
import logging

logger = logging.getLogger("SensiboDevice")

class SensiboAC(SmartDevice):
    def __init__(self, name, device_id, cloud_client=None, stateless=False):
        super().__init__(name, ip=None, device_id=device_id, channel=None, cloud_client=cloud_client, stateless=stateless)

    def set_state_lan(self, state):
        return False # Always force cloud

    def get_state_lan(self):
        return None # Always force cloud

    # --- NEW AC CAPABILITIES ---

    def set_temperature(self, degrees):
        """ Sets target temperature (Integer) """
        if self.cloud_client:
            return self.cloud_client.send_ac_state(self.device_id, {'targetTemperature': int(degrees)})
        return False

    def set_mode(self, mode):
        """ Options: 'cool', 'heat', 'fan', 'dry', 'auto' """
        if self.cloud_client:
            # Also ensure device is ON when setting mode
            return self.cloud_client.send_ac_state(self.device_id, {'on': True, 'mode': mode})
        return False

    def set_fan(self, level):
        """ Options: 'quiet', 'low', 'medium', 'medium_high', 'high', 'auto' """
        if self.cloud_client:
            return self.cloud_client.send_ac_state(self.device_id, {'fanLevel': level})
        return False
    
    def get_room_temperature(self):
        """ Returns the actual room temperature in Celsius. """
        if self.cloud_client:
            data = self.cloud_client.get_measurements(self.device_id)
            if data:
                return data.get('temperature')
        return None

    def get_humidity(self):
        """ Returns the relative humidity %. """
        if self.cloud_client:
            data = self.cloud_client.get_measurements(self.device_id)
            if data:
                return data.get('humidity')
        return None

    # --- SWING CONTROL ---
    def set_swing(self, mode):
        """
        Common modes: 'stopped', 'rangeFull', 'fixedTop', 'fixedMiddle', 'fixedBottom'
        """
        if self.cloud_client:
            return self.cloud_client.send_ac_state(self.device_id, {'swing': mode})
        return False
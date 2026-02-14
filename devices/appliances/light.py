# -*- coding: utf-8 -*-
"""
Created on Sat Feb 14 15:58:58 2026

@author: User
"""

# devices/appliances/light.py
import logging
from ..base import SmartDevice

logger = logging.getLogger("Light")

class Light(SmartDevice):
    """
    A Universal Wrapper for Lights.
    It wraps a physical device (Sonoff, Tuya, etc.) and proxies commands to it.
    
    Since the physical device already handles LAN -> Cloud fallback, 
    this wrapper simply calls the physical device's methods.
    """
    def __init__(self, name, device_obj):
        # Initialize Base with properties from the backing device
        # We use getattr to be safe, but these should exist on all SmartDevices
        super().__init__(
            name, 
            ip=getattr(device_obj, 'ip', None), 
            device_id=getattr(device_obj, 'device_id', None), 
            stateless=getattr(device_obj, 'stateless', False)
        )
        self.device = device_obj

    def set_state_lan(self, state):
        """
        Implementation of Abstract Method.
        We proxy the request to the backing device. 
        
        The backing device's .set_state() method already contains the 
        logic to try LAN first, and fall back to Cloud if LAN fails.
        """
        return self.device.set_state(state)

    def get_state_lan(self):
        """
        Implementation of Abstract Method.
        We proxy the status check to the backing device.
        """
        return self.device.get_state()

    # Explicit on/off methods for convenience
    def on(self):
        return self.set_state('on')

    def off(self):
        return self.set_state('off')
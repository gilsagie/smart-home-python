# -*- coding: utf-8 -*-
"""
Created on Sat Feb 14 16:01:06 2026

@author: User
"""

# devices/appliances/switch.py
import logging
from ..base import SmartDevice

logger = logging.getLogger("SwitchAppliance")

class Switch(SmartDevice):
    """
    A Universal Wrapper for Switches.
    """
    def __init__(self, name, device_obj):
        # Inherit properties
        ip = getattr(device_obj, 'ip', '0.0.0.0')
        dev_id = getattr(device_obj, 'device_id', 'N/A')
        stateless = getattr(device_obj, 'stateless', False)
        
        super().__init__(name, ip=ip, device_id=dev_id, stateless=stateless)
        self.device = device_obj

    def set_state_lan(self, state):
        return self.device.set_state(state)

    def get_state_lan(self):
        return self.device.get_state()

    def on(self):
        return self.set_state('on')

    def off(self):
        return self.set_state('off')
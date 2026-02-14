# -*- coding: utf-8 -*-
"""
Created on Sat Feb 14 16:22:04 2026

@author: User
"""

# devices/room.py
import logging
from .device_group import DeviceGroup
from .appliances.television import Television
from .appliances.air_conditioner import AirConditioner
from .appliances.light import Light
from .appliances.switch import Switch
from .appliances.other import Other

logger = logging.getLogger("Room")

class Room:
    def __init__(self, name, device_list=None):
        self.name = name
        
        # 1. Individual Device Slots (Singletons)
        self.tv = None
        self.ac = None
        
        # 2. Functional Device Groups
        self.lights = DeviceGroup(f"{name}_Lights")
        self.switches = DeviceGroup(f"{name}_Switches")
        self.others = DeviceGroup(f"{name}_Others")
        
        # 3. Master Group (Controls everything)
        self.all = DeviceGroup(f"{name}_All")

        # 4. Auto-Sort Devices on Init
        if device_list:
            for device in device_list:
                self.add_device(device)

    def add_device(self, device):
        """
        Sorts a device into the correct category and adds it to the 'all' group.
        """
        # Always add to the Master 'all' group
        self.all.add_device(device)
        
        # Sort based on Class Type
        if isinstance(device, Light):
            self.lights.add_device(device)
            
        elif isinstance(device, Switch):
            self.switches.add_device(device)
            
        elif isinstance(device, Television):
            if self.tv:
                logger.warning(f"[{self.name}] Overwriting existing TV '{self.tv.name}' with '{device.name}'")
            self.tv = device
            
        elif isinstance(device, AirConditioner):
            if self.ac:
                logger.warning(f"[{self.name}] Overwriting existing AC '{self.ac.name}' with '{device.name}'")
            self.ac = device
            
        else:
            # Fallback for 'Other' or unknown types
            self.others.add_device(device)

    def remove_device(self, device_or_name):
        """
        Removes a device from all internal groups and slots.
        Accepts either a Device object or a name string.
        """
        # Resolve Name
        name = device_or_name
        if hasattr(device_or_name, 'name'):
            name = device_or_name.name
            
        logger.info(f"[{self.name}] Removing device '{name}' from room.")

        # Remove from Groups
        self.all.remove_device(name)
        self.lights.remove_device(name)
        self.switches.remove_device(name)
        self.others.remove_device(name)
        
        # Clear Slots if matching
        if self.tv and self.tv.name == name:
            self.tv = None
        if self.ac and self.ac.name == name:
            self.ac = None

    def __repr__(self):
        return (f"<Room '{self.name}': "
                f"TV={self.tv is not None}, "
                f"AC={self.ac is not None}, "
                f"Lights={len(self.lights.devices)}, "
                f"Switches={len(self.switches.devices)}, "
                f"All={len(self.all.devices)}>")
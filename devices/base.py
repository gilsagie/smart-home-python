# -*- coding: utf-8 -*-
"""
Created on Sat Jan 24 14:27:10 2026

@author: User
"""
class SmartDevice:
    """
    Base class for all Smart Home devices (Sonoff, Shelly, Tuya, etc.).
    Implements the Hybrid Logic: Try LAN first -> Fallback to Cloud.
    """
    def __init__(self, name, ip, device_id, channel=None, cloud_client=None):
        self.name = name
        self.ip = ip
        self.device_id = device_id
        self.channel = channel  # New: Stores 0 or 1 for multi-switch devices
        self.cloud_client = cloud_client
        self._state = None
    
    @property
    def state(self):
        if self._state != 'on' and self._state != 'off':
             print(f"[{self.name}] State unknown. Fetching...")
             self.get_state() # This updates self._state internally
        
        return self._state

    def set_state_lan(self, state):
        """
        ABSTRACT METHOD: Child classes (like SonoffSwitch) must implement 
        their specific LAN protocol here.
        """
        raise NotImplementedError("Subclasses must implement set_state_lan()")

    def set_state(self, state):
        """
        The Universal Hybrid Logic:
        1. Try LAN (Fastest).
        2. If LAN fails, use the shared Cloud Client (Reliable).
        """
        # 1. Try LAN
        try:
            # We trust the child class to handle the specific LAN logic
            if self.set_state_lan(state):
                self._state = state
                return True
        except Exception as e:
            # If LAN crashes (e.g. connection timeout), we just log it and move to Cloud
            print(f"[{self.name}] LAN Exception: {e}")

        # 2. Fallback to Cloud
        if self.cloud_client:
            print(f"[{self.name}] LAN failed/unreachable. Switching to Cloud...")
            # We now pass 'channel' to the cloud!
            self._state = state
            return self.cloud_client.set_state(self.device_id, state, self.channel)
        
        print(f"[{self.name}] Failed: LAN unreachable and no Cloud client connected.")
        return False

    # --- User Friendly Shortcuts ---
    def on(self):
        return self.set_state('on')

    def off(self):
        return self.set_state('off')
    
    def get_state(self):
        """
        Returns 'on', 'off', or None (if unreachable).
        Hybrid Logic: Try LAN first -> Fallback to Cloud.
        """
        # 1. Try LAN
        try:
            state = self.get_state_lan()
            if state is not None:
                self._state = state
                print(f"[{self.name}] State (LAN): {state}")
                return state
        except Exception as e:
            print(f"[{self.name}] LAN Get-State Error: {e}")

        # 2. Fallback to Cloud
        if self.cloud_client:
            print(f"[{self.name}] LAN unreachable. Fetching state from Cloud...")
            state = self.cloud_client.get_state(self.device_id, self.channel)
            if state is not None:
                self._state = state # <--- Update Cache
            return state
        
        print(f"[{self.name}] Error: Could not retrieve state (Device Offline).")
        return None

    def get_state_lan(self):
        """
        ABSTRACT METHOD: Child classes must implement this.
        Should return 'on', 'off', or None.
        """
        raise NotImplementedError("Subclasses must implement get_state_lan()")
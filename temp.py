# -*- coding: utf-8 -*-
"""
Created on Sat Feb 14 17:44:10 2026

@author: User
"""

import logging
from utils.loader import load_devices
from devices.brands.sonoff import SonoffSwitch
from devices.brands.tuya import TuyaSwitch
from devices.brands.sensibo import SensiboAC

# Configure logging to show us what's happening
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("TestMigration")

def test_cloud_connections():
    print("\n" + "="*50)
    print("STARTING CLOUD CREDENTIALS TEST")
    print("="*50 + "\n")

    # 1. Load Devices (This triggers the new CloudClient __init__ logic)
    print(">>> Loading devices from configuration...")
    try:
        devices_map = load_devices()
        all_devices = devices_map.get('all', {})
        print(f">>> Found {len(all_devices)} total devices.\n")
    except Exception as e:
        print(f"!!! CRITICAL FAIL: Could not load devices. {e}")
        return

    # 2. Track which brands we have tested
    tested_brands = {
        'Sonoff': False,
        'Tuya': False,
        'Sensibo': False
    }

    # 3. Iterate through devices and test one of each type
    for name, device in all_devices.items():
        
        # --- TEST SONOFF ---
        if isinstance(device, SonoffSwitch) and not tested_brands['Sonoff']:
            print(f"--- Testing SONOFF (via {name}) ---")
            client = device.cloud_client
            
            # Check if Client loaded creds
            if not client.app_id or not client.access_token:
                print(f"❌ FAIL: Sonoff credentials missing in client (Check .env)")
            else:
                # Force a cloud fetch
                state = client.get_state(device.device_id, device.channel)
                if state is not None:
                    print(f"✅ PASS: Fetched state '{state}' from Sonoff Cloud.")
                else:
                    print(f"⚠️ FAIL: Credentials loaded, but could not fetch state. (Check Device ID/Permissions)")
            tested_brands['Sonoff'] = True
            print("")

        # --- TEST TUYA ---
        elif isinstance(device, TuyaSwitch) and not tested_brands['Tuya']:
            print(f"--- Testing TUYA (via {name}) ---")
            client = device.cloud_client
            
            # Check if Client connected
            if client.cloud is None:
                print(f"❌ FAIL: Tuya Cloud not connected (Check .env keys)")
            else:
                # Force a cloud fetch
                state = client.get_state(device.device_id, device.channel)
                if state is not None:
                    print(f"✅ PASS: Fetched state '{state}' from Tuya Cloud.")
                else:
                    print(f"⚠️ FAIL: Cloud connected, but request failed. (Check Device ID)")
            tested_brands['Tuya'] = True
            print("")

        # --- TEST SENSIBO ---
        elif isinstance(device, SensiboAC) and not tested_brands['Sensibo']:
            print(f"--- Testing SENSIBO (via {name}) ---")
            client = device.cloud_client
            
            if not client.api_key:
                print(f"❌ FAIL: Sensibo API Key missing (Check .env)")
            else:
                state = client.get_state(device.device_id)
                if state is not None:
                    print(f"✅ PASS: Fetched state '{state}' from Sensibo Cloud.")
                else:
                    print(f"⚠️ FAIL: Credentials loaded, but request failed. (Check Device ID)")
            tested_brands['Sensibo'] = True
            print("")

    # 4. Summary
    print("="*50)
    print("TEST SUMMARY")
    for brand, tested in tested_brands.items():
        if tested:
            print(f"{brand}: Tested")
        else:
            print(f"{brand}: No devices found in config to test.")
    print("="*50)

if __name__ == "__main__":
    test_cloud_connections()
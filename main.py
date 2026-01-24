from switches_load import load_switches


# 3. Usage
if __name__ == "__main__":
    SWITCH_DICT = load_switches()
    # This will try LAN first. 
    # If your laptop is on a different WiFi than the light, it will auto-switch to Cloud!
    if "Entrance light" in SWITCH_DICT:
        SWITCH_DICT["Entrance light"].off()
        
    if "Living room right" in SWITCH_DICT:
        print("\nTesting Multi-Channel Switch (Left)...")
        SWITCH_DICT["Stove light"].off() # Should only turn off channel 0
        
    if "Living room left" in SWITCH_DICT:
        print("\nTesting Multi-Channel Switch (Right)...")
        SWITCH_DICT["Kitchen light"].on() # Should only turn on channel 1

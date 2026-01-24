from switches_load import SWITCH_DICT


# 3. Usage
if __name__ == "__main__":
    
    # This will try LAN first. 
    # If your laptop is on a different WiFi than the light, it will auto-switch to Cloud!
    if "Entrance light" in SWITCH_DICT:
        SWITCH_DICT["Entrance light"].off()
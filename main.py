from switches_load import load_switches

# 3. Usage
if __name__ == "__main__":
    SWITCH_DICT = load_switches()
    
    
    device = SWITCH_DICT["Kitchen light"]
    
    current_status = device.get_state() # Checks LAN -> Then Cloud
    
    if current_status == 'off':
        print("The kitchen light is off, turning it on...")
        device.on()
    elif current_status == 'on':
        print("The kitchen light is already ON.")
    else:
        print("Error")

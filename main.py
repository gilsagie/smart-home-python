from utils.loader import load_switches

# 3. Usage
if __name__ == "__main__":
    SWITCH_DICT = load_switches()
    
    
    device = SWITCH_DICT["Entrance light"]
    
    current_status = device.get_state() # Checks LAN -> Then Cloud
    print(current_status)
    device.off()
    
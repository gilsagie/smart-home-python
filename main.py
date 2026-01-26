from utils.loader import load_switches

if __name__ == "__main__":
    # This loads devices AND fetches their initial states
    SWITCH_DICT = load_switches()
    
    if "Lamp" in SWITCH_DICT:
        device = SWITCH_DICT["Lamp"]
        
        # 1. Check the Cached State (Instant)
        print(f"Initial Cached State: {device.state}")
        
        # 2. Toggle based on cache
        device.on()
        if device.state == 'on':
            print("Light is ON. Turning OFF...")
            #device.off()
        elif device.state == 'off':
            print("Light is OFF. Turning ON...")
            #device.on()
        else:
            print("ERROR")
            
        # 3. Check Cache again (Updated automatically by .on()/.off())
        print(f"New Cached State: {device.state}")
        
    else:
        print("Device 'Entrance light' not found.")
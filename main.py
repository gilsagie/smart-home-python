from utils.loader import load_switches
import logging

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    # This loads devices AND fetches their initial states
    SWITCH_DICT = load_switches()
    
    if "AC" in SWITCH_DICT:
        ac = SWITCH_DICT["AC"]
        current_temp = ac.get_room_temperature()
        humidity = ac.get_humidity()
        
        print(f"Current Room Status: {current_temp}°C | {humidity}% Humidity")
        # 1. Basic On/Off
        ac.off()
        
        # 2. Specific AC Commands
        # Note: These methods only exist on the SensiboAC object
        if hasattr(ac, 'set_temperature'):
            print("Setting AC to 23°C Heat...")
            ac.set_mode('heat')
            ac.set_temperature(23)
            ac.set_fan('high')

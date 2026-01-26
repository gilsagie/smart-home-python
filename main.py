import logging
import time
from utils.loader import load_switches

# 1. CONFIGURE LOGGING (Do this once, at the very top)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)

# 2. Create a logger for this file
logger = logging.getLogger("Main")

if __name__ == "__main__":
    logger.info("System starting up...")
    
    # This loads devices AND fetches their initial states
    SWITCH_DICT = load_switches()
    
    if "Entrance light" in SWITCH_DICT:
        device = SWITCH_DICT["Entrance light"]
        
        # 1. Check the Cached State
        logger.info(f"Initial Cached State: {device.state}")
        
        # 2. Toggle based on cache
        if device.state == 'on':
            logger.info("Light is ON. Sending OFF command...")
            #device.off()
        else:
            logger.info("Light is OFF. Sending ON command...")
            #device.on()
            
        # 3. Check Cache again
        logger.info(f"New Cached State: {device.state}")
        
    else:
        logger.error("Device 'Entrance light' not found in configuration.")
        
    logger.info("Script finished.")
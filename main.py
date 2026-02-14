from utils.loader import load_devices
import logging

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    
    # main.py

    devices = load_devices()
    
    # These calls work automatically, routing to different IR blasters
    # based on the definitions in commands.yaml
    devices["Bed room AC"].on()
    devices["Bed room AC"].on() 

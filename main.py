from utils.loader import load_switches
import logging

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    
    # main.py

    switches = load_switches()
    
    # These calls work automatically, routing to different IR blasters
    # based on the definitions in commands.yaml
    switches["Bed room AC"].on()
    switches["Bed room AC"].on() 

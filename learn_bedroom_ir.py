import broadlink
import time

# --- CONFIGURATION ---
IP = "192.168.1.48" # Your Broadlink IP
# ---------------------

def learn_ir():
    print(f"Connecting to {IP}...")
    try:
        device = broadlink.hello(IP)
        device.auth()
        print(f"Connected to {device.type}!")
    except Exception as e:
        print(f"Connection failed: {e}")
        return

    while True:
        cmd_name = input("\nType the command name (e.g., 'tv_vol_up') or 'q' to quit: ")
        if cmd_name.lower() == 'q': break

        print(f"1. Point your remote at the Broadlink device.")
        print(f"2. Get ready to press '{cmd_name}'.")
        input("3. Press Enter on your keyboard to START LISTENING...")
        
        try:
            device.enter_learning()
            print(">>> ORANGE LED SHOULD BE ON. PRESS BUTTON NOW! <<<")
            
            # Listen for data for 10 seconds
            start_time = time.time()
            packet = None
            
            while time.time() - start_time < 10:
                time.sleep(0.5)
                try:
                    packet = device.check_data()
                    if packet: break
                except:
                    pass
            
            if packet:
                hex_code = packet.hex()
                # VALIDATION: Check if code is suspiciously short
                if len(hex_code) < 100:
                    print(f"❌ Captured code is too short ({len(hex_code)} chars). Likely noise.")
                    print(f"   Code: {hex_code}")
                    print("   Try holding the button slightly longer.")
                else:
                    print(f"✅ SUCCESS! Valid code captured ({len(hex_code)} chars).")
                    print("-" * 20)
                    print(f"{cmd_name}: \"{hex_code}\"")
                    print("-" * 20)
                    print("Copy the line above into your commands.yaml")
            else:
                print("❌ Timeout. No data received.")

        except Exception as e:
            print(f"Error during learning: {e}")

if __name__ == "__main__":
    learn_ir()
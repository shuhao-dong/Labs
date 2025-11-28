import asyncio
import time
import struct
import requests  # <--- NEW: For HTTP requests
from bleak import BleakScanner

# --- CONFIGURATION ---
TARGET_NAME = "Lab4-Adv"
COMPANY_ID = 0x0059 

# ThingsBoard Config
TB_URL = "https://demo.thingsboard.io/api/v1"
TB_ACCESS_TOKEN = "yyg96elwr9hjg19hfgot"  # <--- PASTE TOKEN HERE

# State variables for throttling
last_sent_time = 0
UPLOAD_INTERVAL = 1.0 # Send to cloud every 1 second (even if BLE is faster)

def push_to_cloud(temperature):
    """Sends JSON data to ThingsBoard via HTTP"""
    url = f"{TB_URL}/{TB_ACCESS_TOKEN}/telemetry"
    payload = {"temperature": temperature}
    
    try:
        response = requests.post(url, json=payload, timeout=2)
        if response.status_code == 200:
            print(f" -> Cloud Upload Success: {temperature}")
        else:
            print(f" -> Cloud Error: {response.status_code}")
    except Exception as e:
        print(f" -> Cloud Connection Failed: {e}")

def detection_callback(device, advertisement_data):
    global last_sent_time
    
    if device.name and device.name == TARGET_NAME:
        if COMPANY_ID in advertisement_data.manufacturer_data:
            raw_bytes = advertisement_data.manufacturer_data[COMPANY_ID]
            
            try:
                # 1. Decode BLE
                temp_int = struct.unpack_from("<h", raw_bytes, 0)[0]
                temperature_c = temp_int / 100.0
                
                # Print real-time to console (Fast)
                print(f"[{device.address}] BLE Rx: {temperature_c:.2f} °C")
                
                # 2. Upload to Cloud (Throttled)
                current_time = time.time()
                if (current_time - last_sent_time) >= UPLOAD_INTERVAL:
                    push_to_cloud(temperature_c)
                    last_sent_time = current_time
                    
            except Exception as e:
                print(f"Error: {e}")

async def main():
    print(f"Starting Gateway for {TARGET_NAME}...")
    scanner = BleakScanner(detection_callback=detection_callback, scanning_mode='active')
    await scanner.start()
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopping Gateway...")
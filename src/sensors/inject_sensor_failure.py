'''
Sensor Module Failure Injector
Works with main_integrated.py
Run: python inject_sensor_failure.py (from sensors folder)
'''

import json
import time
import os
import sys
from datetime import datetime

# Configuration - signal file in parent directory (src/)
SIGNAL_FILE = "failure_signal.json"

# Available failure types
FAILURE_TYPES = {
    "1": "PROGRAM_CRASH",
    "2": "IK_FAILURE", 
    "3": "ROBOT_STUCK",
    "4": "COLLISION"
}

# Available subfailures per type
SUBFAILURES = {
    "PROGRAM_CRASH": {
        "1": "RuntimeError",
        "2": "MemoryError", 
        "3": "Corrupt Checkpoint",
        "4": "Hang (Watchdog)"
    },
    "IK_FAILURE": {
        "1": "Non-critical skip",
        "2": "Critical retreat"
    },
    "ROBOT_STUCK": {
        "1": "Movement timeout"
    },
    "COLLISION": {
        "1": "Perturbation recovery"
    }
}

def inject_failure(failure_type, subfailure=1):
    """Inject a failure signal for main_integrated.py"""
    signal_data = {
        "type": failure_type,
        "subfailure": subfailure,
        "timestamp": datetime.now().isoformat(),
        "injected_by": "sensor_injector"
    }
    
    # Write signal file to parent directory (src/)
    with open(SIGNAL_FILE, "w") as f:
        json.dump(signal_data, f, indent=2)
    
    print(f"[INJECTED] {failure_type} (subfailure {subfailure})")
    print(f"[FILE] {SIGNAL_FILE} created")
    return signal_data

def clear_signal():
    """Clear the signal file"""
    if os.path.exists(SIGNAL_FILE):
        os.remove(SIGNAL_FILE)
        print("[CLEARED] Signal file removed")

def wait_for_inspection():
    """Wait for inspection to start - look for checkpoint in parent directory"""
    print("\n[WAITING] Looking for main_integrated.py...")
    print("[TIP] Make sure Terminal 1 is running: python sensors/main_integrated.py")
    
    # Check for checkpoint file in parent directory (src/)
    checkpoint_file = "checkpoint.json"
    while not os.path.exists(checkpoint_file):
        time.sleep(0.5)
    
    print("[DETECTED] Inspection is running!")
    print("[READY] Ready to inject")

def main():
    print("="*60)
    print("  SENSOR MODULE FAILURE INJECTOR")
    print("  (Works with sensors/main_integrated.py)")
    print("="*60)
    print("\nMake sure Terminal 1 is running: python sensors/main_integrated.py")
    print(f"Signal file will be created at: {SIGNAL_FILE}\n")
    
    # Wait for inspection
    wait_for_inspection()
    
    # Show options
    print("\n" + "-"*40)
    print("FAILURE TYPES:")
    for key, value in FAILURE_TYPES.items():
        print(f"  {key}. {value}")
    
    choice = input("\nSelect failure type (1-4): ").strip()
    
    if choice not in FAILURE_TYPES:
        print("[ERROR] Invalid choice")
        return
    
    failure_type = FAILURE_TYPES[choice]
    
    # Show subfailures
    print(f"\nSubfailures for {failure_type}:")
    for key, value in SUBFAILURES.get(failure_type, {"1": "Default"}).items():
        print(f"  {key}. {value}")
    
    sub_choice = input("\nSelect subfailure (default 1): ").strip() or "1"
    subfailure = int(sub_choice) if sub_choice.isdigit() else 1
    
    # Confirm
    print(f"\n[CONFIRM] Injecting {failure_type} (subfailure {subfailure})")
    confirm = input("Proceed? (y/n): ").strip().lower()
    
    if confirm != "y":
        print("[CANCELLED]")
        return
    
    # Inject
    inject_failure(failure_type, subfailure)
    
    print("\n[SUCCESS] Failure injected!")
    print("[MONITOR] Watch Terminal 1 for recovery behavior")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[ABORTED] User cancelled")
        clear_signal()
    except Exception as e:
        print(f"[ERROR] {e}")
        clear_signal()
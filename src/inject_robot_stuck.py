# inject_robot_stuck.py
# Failure Case 3: Robot Stuck
# Run in Terminal 2 while main.py runs in Terminal 1.
#
# What it does:
#   - Injects ROBOT_STUCK signal at selected pose(s)
#   - Main.py detects and classifies as ROBOT_STUCK
#   - Recovery: Local offset → Retreat → Resume
#
# Poses (different from previous failure types):
#   - Target 2 (index 1) - entry pose
#   - Target 7 (index 7) - mid-inspection
#   - Target 15 (index 19) - exit zone
#   - Target 18 (index 22) - near wrist flip

import time
import json
import os
from .inject_base import (
    print_header, pick_subfailure, pick_pose,
    write_signal, wait_for_pose, SIGNAL_FILE
)

# Single failure type - no subfailures
SUBFAILURES = {
    "1": "Robot Stuck at selected pose",
}

# ── NEW POSES FOR ROBOT STUCK ──
INJECT_POSES = [
    (1,  "Target 2",  "entry pose"),
    (7,  "Target 7",  "mid-inspection"),
    (19, "Target 15", "exit zone"),
    (22, "Target 18", "near wrist flip"),
]

def main():
    print("\n" + "="*52)
    print("  BIW Failure Injection — Robot Stuck")
    print("="*52)
    
    print("\nTarget poses:")
    print("  [01] Target 2   ← entry pose")
    print("  [07] Target 7   ← mid-inspection")
    print("  [19] Target 15  ← exit zone")
    print("  [22] Target 18  ← near wrist flip")
    
    print("\nSubfailures:")
    print("  1. Robot Stuck at selected pose")

    ans = input("\nRun injection? (y/n): ").strip().lower()
    if ans != "y":
        print("Aborted.")
        return

    print("\nInject at which pose?")
    print("  1. [01] Target 2   — entry pose")
    print("  2. [07] Target 7   — mid-inspection")
    print("  3. [19] Target 15  — exit zone")
    print("  4. [22] Target 18  — near wrist flip")
    print("  5. All poses in sequence")
    
    while True:
        choice = input("Choice: ").strip()
        if choice == "1":
            poses = [(1, "Target 2", "entry pose")]
            break
        elif choice == "2":
            poses = [(7, "Target 7", "mid-inspection")]
            break
        elif choice == "3":
            poses = [(19, "Target 15", "exit zone")]
            break
        elif choice == "4":
            poses = [(22, "Target 18", "near wrist flip")]
            break
        elif choice == "5":
            poses = [
                (1, "Target 2", "entry pose"),
                (7, "Target 7", "mid-inspection"),
                (19, "Target 15", "exit zone"),
                (22, "Target 18", "near wrist flip"),
            ]
            break
        print("  Invalid choice.")

    for idx, name, note in poses:
        # Wait until we're at the pose BEFORE target (idx-1)
        print(f"\n  Waiting to inject at {name} (index {idx}) - {note}")
        while True:
            time.sleep(0.3)
            if not os.path.exists(os.path.join("..", os.path.join("..", "checkpoint.json"))):
                continue
            try:
                with open(os.path.join("..", os.path.join("..", "checkpoint.json"))) as f:
                    ckpt = json.load(f)
                if ckpt.get("pose_index") == idx - 1:
                    print(f"  [INJECT] At pose {idx-1} - writing ROBOT_STUCK signal for {name}")
                    break
            except Exception:
                continue

        # Write the ROBOT_STUCK signal
        print(f"  [{idx:02d}] Injecting ROBOT_STUCK at {name}")
        write_signal("ROBOT_STUCK", subfailure=1)

        # Wait for recovery to complete with timeout
        print(f"  Waiting for recovery to complete...")
        timeout = 25  # 25 seconds max
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(0.5)
            if not os.path.exists(os.path.join("..", os.path.join("..", "checkpoint.json"))):
                break
            try:
                with open(os.path.join("..", os.path.join("..", "checkpoint.json"))) as f:
                    ckpt = json.load(f)
                if ckpt.get("state") == "COMPLETE":
                    break
                if ckpt.get("state") == "ABORTED":
                    print(f"  [WARN] main.py aborted. Exiting...")
                    break
            except Exception:
                continue
        else:
            print(f"  [WARN] Timeout waiting for recovery. Exiting...")

        if poses.index((idx, name, note)) < len(poses) - 1:
            print(f"  Recovery confirmed. Moving to next pose...\n")
            time.sleep(1.5)

    print("\n[DONE] All ROBOT_STUCK injections complete. Check Terminal 1 for recovery log.")

if __name__ == "__main__":
    main()
# inject_ik_failure.py
# Failure Case 2: IK Failure
# Run in Terminal 2 while main.py runs in Terminal 1.
#
# What it does:
#   - Injects IK_FAILURE signal at selected pose(s)
#   - Main.py detects and classifies as IK_FAILURE
#   - Recovery: Skip non-critical poses, Retreat for critical poses
#
# Non-critical poses (skip and continue):
#   - Target 8a (index 9)
#   - Target 13 (index 16)
#
# Critical poses (retreat to home and stop):
#   - Target 11 (index 14)
#   - Target 11a (index 23)

import time
import json
import os
from inject_base import (
    print_header, pick_subfailure, pick_pose,
    write_signal, wait_for_pose, SIGNAL_FILE
)

# Single failure type - no subfailures
SUBFAILURES = {
    "1": "IK Failure at selected pose",
}

# IK Failure poses (same as base)
# But we'll use the same pose picker
# Non-critical: 8a (9), 13 (16)
# Critical: 11 (14), 11a (23)

def main():
    print("\n" + "="*52)
    print("  BIW Failure Injection — IK Failure")
    print("="*52)
    
    print("\nTarget poses:")
    print("  [09] Target 8a  ← NON-CRITICAL (skip and continue)")
    print("  [14] Target 11  ← CRITICAL (retreat to home)")
    print("  [16] Target 13  ← NON-CRITICAL (skip and continue)")
    print("  [23] Target 11a ← CRITICAL (retreat to home)")
    
    print("\nSubfailures:")
    print("  1. IK Failure at selected pose")

    ans = input("\nRun injection? (y/n): ").strip().lower()
    if ans != "y":
        print("Aborted.")
        return

    print("\nInject at which pose?")
    print("  1. [09] Target 8a  — NON-CRITICAL (skip and continue)")
    print("  2. [14] Target 11  — CRITICAL (retreat to home)")
    print("  3. [16] Target 13  — NON-CRITICAL (skip and continue)")
    print("  4. [23] Target 11a — CRITICAL (retreat to home)")
    print("  5. All poses in sequence")
    
    while True:
        choice = input("Choice: ").strip()
        if choice == "1":
            poses = [(9, "Target 8a", "NON-CRITICAL (skip)")]
            break
        elif choice == "2":
            poses = [(14, "Target 11", "CRITICAL (retreat)")]
            break
        elif choice == "3":
            poses = [(16, "Target 13", "NON-CRITICAL (skip)")]
            break
        elif choice == "4":
            poses = [(23, "Target 11a", "CRITICAL (retreat)")]
            break
        elif choice == "5":
            poses = [
                (9, "Target 8a", "NON-CRITICAL (skip)"),
                (14, "Target 11", "CRITICAL (retreat)"),
                (16, "Target 13", "NON-CRITICAL (skip)"),
                (23, "Target 11a", "CRITICAL (retreat)"),
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
                    print(f"  [INJECT] At pose {idx-1} - writing IK_FAILURE signal for {name}")
                    break
            except Exception:
                continue

        # Write the IK_FAILURE signal
        print(f"  [{idx:02d}] Injecting IK_FAILURE at {name}")
        write_signal("IK_FAILURE", subfailure=1)

        # Wait for recovery to complete with timeout
        print(f"  Waiting for recovery to complete...")
        timeout = 15  # 15 seconds max
        start_time = time.time()
        while time.time() - start_time < timeout:
            time.sleep(0.5)
            if not os.path.exists(os.path.join("..", os.path.join("..", "checkpoint.json"))):
                # Main.py cleared checkpoint - likely done
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

if __name__ == "__main__":
    main()
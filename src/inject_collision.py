# inject_collision.py
# Failure Case 4: Collision
# Run in Terminal 2 while main.py runs in Terminal 1.
#
# What it does:
#   - Injects COLLISION signal at selected pose(s)
#   - Main.py detects and classifies as COLLISION
#   - Recovery: Local Z offset → Retreat → Resume
#
# Poses (different from previous failure types):
#   - Target 4 (index 2) - entry zone
#   - Target 9 (index 12) - mid-inspection
#   - Target 12 (index 15) - deep zone
#   - Target 16 (index 20) - exit zone

import time
import json
import os
from .inject_base import (
    print_header, pick_subfailure, pick_pose,
    write_signal, wait_for_pose, SIGNAL_FILE
)

# Single failure type - no subfailures
SUBFAILURES = {
    "1": "Collision at selected pose",
}

# ── NEW POSES FOR COLLISION ──
INJECT_POSES = [
    (2,  "Target 4",  "entry zone"),
    (12, "Target 9",  "mid-inspection"),
    (15, "Target 12", "deep zone"),
    (20, "Target 16", "exit zone"),
]

def main():
    print("\n" + "="*52)
    print("  BIW Failure Injection — Collision")
    print("="*52)
    
    print("\nTarget poses:")
    print("  [02] Target 4   ← entry zone")
    print("  [12] Target 9   ← mid-inspection")
    print("  [15] Target 12  ← deep zone")
    print("  [20] Target 16  ← exit zone")
    
    print("\nSubfailures:")
    print("  1. Collision at selected pose")

    ans = input("\nRun injection? (y/n): ").strip().lower()
    if ans != "y":
        print("Aborted.")
        return

    print("\nInject at which pose?")
    print("  1. [02] Target 4   — entry zone")
    print("  2. [12] Target 9   — mid-inspection")
    print("  3. [15] Target 12  — deep zone")
    print("  4. [20] Target 16  — exit zone")
    print("  5. All poses in sequence")
    
    while True:
        choice = input("Choice: ").strip()
        if choice == "1":
            poses = [(2, "Target 4", "entry zone")]
            break
        elif choice == "2":
            poses = [(12, "Target 9", "mid-inspection")]
            break
        elif choice == "3":
            poses = [(15, "Target 12", "deep zone")]
            break
        elif choice == "4":
            poses = [(20, "Target 16", "exit zone")]
            break
        elif choice == "5":
            poses = [
                (2, "Target 4", "entry zone"),
                (12, "Target 9", "mid-inspection"),
                (15, "Target 12", "deep zone"),
                (20, "Target 16", "exit zone"),
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
                    print(f"  [INJECT] At pose {idx-1} - writing COLLISION signal for {name}")
                    break
            except Exception:
                continue

        # Write the COLLISION signal
        print(f"  [{idx:02d}] Injecting COLLISION at {name}")
        write_signal("COLLISION", subfailure=1)

        # Wait for recovery to complete with timeout
        print(f"  Waiting for recovery to complete...")
        timeout = 120  # 2 minutes max
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

    print("\n[DONE] All COLLISION injections complete. Check Terminal 1 for recovery log.")

if __name__ == "__main__":
    main()
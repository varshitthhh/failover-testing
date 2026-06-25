# inject_memory_error.py
# Case 1.2: MemoryError mid-inspection
# Run in Terminal 2 while main.py runs in Terminal 1.
#
# Subfailure: MemoryError at selected pose

import time
import json
import os
from inject_base import (
    print_header, pick_subfailure, pick_pose,
    write_signal, wait_for_pose, SIGNAL_FILE
)

SUBFAILURES = {
    "1": "MemoryError at selected pose",
}

def main():
    print("\n" + "="*52)
    print("  BIW Failure Injection — MemoryError")
    print("="*52)
    
    print("\nTarget poses:")
    for idx, name, note in [
        (9, "Target 8a", "post-wrist reconfig, before T8a→T9 jump"),
        (14, "Target 11", "deepest inspection anchor, long retreat"),
        (16, "Target 13", "wrist config change, before T13→T15 jump"),
        (23, "Target 11a", "last complex pose, J6=179.99, wrist flip zone"),
    ]:
        print(f"  [{idx:02d}] {name}  ← {note}")

    ans = input("\nRun injection? (y/n): ").strip().lower()
    if ans != "y":
        print("Aborted.")
        return

    print("\nInject at which pose?")
    print("  1. [09] Target 8a")
    print("  2. [14] Target 11")
    print("  3. [16] Target 13")
    print("  4. [23] Target 11a")
    print("  5. All poses in sequence")
    
    while True:
        choice = input("Choice: ").strip()
        if choice == "1":
            poses = [(9, "Target 8a", "")]
            break
        elif choice == "2":
            poses = [(14, "Target 11", "")]
            break
        elif choice == "3":
            poses = [(16, "Target 13", "")]
            break
        elif choice == "4":
            poses = [(23, "Target 11a", "")]
            break
        elif choice == "5":
            poses = [
                (9, "Target 8a", ""),
                (14, "Target 11", ""),
                (16, "Target 13", ""),
                (23, "Target 11a", ""),
            ]
            break
        print("  Invalid choice.")

    for idx, name, note in poses:
        # Wait until we're at the pose BEFORE target (idx-1)
        print(f"\n  Waiting to inject at {name} (index {idx})...")
        while True:
            time.sleep(0.3)
            if not os.path.exists("checkpoint.json"):
                continue
            try:
                with open("checkpoint.json") as f:
                    ckpt = json.load(f)
                # Write signal when we're at the pose BEFORE target
                if ckpt.get("pose_index") == idx - 1:
                    print(f"  [INJECT] At pose {idx-1} - writing signal for {name}")
                    break
            except Exception:
                continue

        # Write the signal (MemoryError)
        print(f"  [{idx:02d}] Injecting MemoryError at {name}")
        write_signal("PROGRAM_CRASH", subfailure=2)  # subfailure=2 for MemoryError

        # Wait for recovery to complete (main.py retreats to home and exits)
        print(f"  Waiting for recovery to complete...")
        while True:
            time.sleep(0.5)
            if not os.path.exists("checkpoint.json"):
                break
            try:
                with open("checkpoint.json") as f:
                    ckpt = json.load(f)
                if ckpt.get("state") == "COMPLETE":
                    break
            except Exception:
                continue

        if poses.index((idx, name, note)) < len(poses) - 1:
            print(f"  Recovery confirmed. Moving to next pose...\n")
            time.sleep(1.5)

    print("\n[DONE] All MemoryError injections complete. Check Terminal 1 for recovery log.")

if __name__ == "__main__":
    main()
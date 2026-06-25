# inject_program_crash.py
# Case 1: Program crash subfailures
# Run in Terminal 2 while main.py runs in Terminal 1.
#
# Subfailures:
#   1. RuntimeError mid-inspection
#   2. MemoryError mid-inspection
#   3. Corrupt checkpoint (cold restart test)
#   4. Hang — watchdog fires

import time
import json
import os
from .inject_base import (
    print_header, pick_subfailure, pick_pose,
    write_signal, wait_for_pose, SIGNAL_FILE
)

SUBFAILURES = {
    "1": "RuntimeError mid-inspection",
    "2": "MemoryError mid-inspection",
    "3": "Corrupt checkpoint — kill main.py now, then restart it",
    "4": "Hang — watchdog timeout (ROBOT_STUCK fires after 8s)",
}

def corrupt_checkpoint():
    """Overwrite checkpoint.json with garbage JSON."""
    checkpoint_path = os.path.join("..", "checkpoint.json")
    with open(checkpoint_path, "w") as f:
        f.write('{"pose_index": 14, "pose_name": "Target 11", "joints_deg": [CORRUPTED')
    print("  [CHECKPOINT CORRUPTED] — now kill main.py (Ctrl+C in Terminal 1)")
    print("  Then restart main.py — it should detect corrupt checkpoint and handle it.")

def main():
    print_header("Program Crash", SUBFAILURES)

    ans = input("\nRun injection? (y/n): ").strip().lower()
    if ans != "y":
        print("Aborted.")
        return

    sub = pick_subfailure(SUBFAILURES)
    poses = pick_pose()

    if sub == 3:
        idx, name, note = poses[0]
        
        print("\n  Waiting for checkpoint.json to exist (main.py must be running)...")
        checkpoint_path = os.path.join("..", "checkpoint.json")
        while not os.path.exists(checkpoint_path):
            time.sleep(0.4)
        
        print(f"\n  Waiting to corrupt checkpoint at {name} (index {idx})...")
        while True:
            time.sleep(0.3)
            if not os.path.exists(checkpoint_path):
                continue
            try:
                with open(checkpoint_path) as f:
                    ckpt = json.load(f)
                if ckpt.get("pose_index") == idx - 1:
                    print(f"  [INJECT] At pose {idx-1} - corrupting checkpoint for {name}")
                    break
            except Exception:
                continue
        
        time.sleep(0.5)
        corrupt_checkpoint()
        
        # ── AUTOMATICALLY KILL MAIN.PY ──
        print("\n  [AUTO] Killing main.py process...")
        try:
            os.system("taskkill /F /IM python.exe /FI \"WINDOWTITLE eq *main.py*\" 2>nul")
            os.system('for /f "tokens=2" %i in (\'tasklist /FI "IMAGENAME eq python.exe" /FO TABLE ^| find "main.py"\') do taskkill /F /PID %i 2>nul')
            print("  [AUTO] main.py killed. Restart it now.")
        except Exception as e:
            print(f"  [WARN] Could not auto-kill: {e}")
            print("  [MANUAL] Press Ctrl+C in Terminal 1")
        
        print("\n  Now restart main.py:")
        print("  python main.py")
        print("  It should detect corrupt checkpoint and handle it.")
        return

    # Subfailures 1, 2, 4 — signal file method
    failure_type = {
        1: "PROGRAM_CRASH",
        2: "PROGRAM_CRASH",
        4: "ROBOT_STUCK",
    }[sub]

    for idx, name, note in poses:
        print(f"\n  Waiting to inject at {name} (index {idx})...")
        checkpoint_path = os.path.join("..", "checkpoint.json")
        while True:
            time.sleep(0.3)
            if not os.path.exists(checkpoint_path):
                continue
            try:
                with open(checkpoint_path) as f:
                    ckpt = json.load(f)
                if ckpt.get("pose_index") == idx - 1:
                    print(f"  [INJECT] At pose {idx-1} - writing signal for {name}")
                    break
            except Exception:
                continue

        if sub == 4:
            print(f"  [{idx:02d}] Injecting hang at {name} (ROBOT_STUCK)")
            write_signal("ROBOT_STUCK", subfailure=4)
        else:
            label = "RuntimeError" if sub == 1 else "MemoryError"
            print(f"  [{idx:02d}] Injecting {label} at {name}")
            write_signal("PROGRAM_CRASH", subfailure=sub)

        print(f"  Waiting for recovery to complete...")
        while True:
            time.sleep(0.5)
            if not os.path.exists(checkpoint_path):
                break
            try:
                with open(checkpoint_path) as f:
                    ckpt = json.load(f)
                if ckpt.get("state") == "COMPLETE":
                    break
            except Exception:
                continue

        if poses.index((idx, name, note)) < len(poses) - 1:
            print(f"  Recovery confirmed. Moving to next pose...\n")
            time.sleep(1.5)

    print("\n[DONE] All injections complete. Check Terminal 1 for recovery log.")

if __name__ == "__main__":
    main()
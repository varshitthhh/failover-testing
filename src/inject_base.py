# inject_base.py
# Shared helper for all inject_*.py scripts.
# Never run directly.

import json
import os
import time

SIGNAL_FILE = "failure_signal.json"

# ── Fix: checkpoint.json is in parent directory ──
def get_checkpoint_path():
    """Return path to checkpoint.json (in parent directory)"""
    return "checkpoint.json"

# ── Fix: Also ensure failure_signal.json is in root ──
# SIGNAL_FILE stays as "failure_signal.json" (in root, since scripts run from src/)

# Difficult poses — used by all inject scripts
INJECT_INDICES = [
    (9,  "Target 8a",  "post-wrist reconfig, before T8a→T9 jump"),
    (14, "Target 11",  "deepest inspection anchor, long retreat"),
    (16, "Target 13",  "wrist config change, before T13→T15 jump"),
    (23, "Target 11a", "last complex pose, J6=179.99, wrist flip zone"),
]

def print_header(case_name, subfailures: dict):
    print("\n" + "="*52)
    print(f"  BIW Failure Injection — {case_name}")
    print("="*52)
    print("\nTarget poses:")
    for idx, name, note in INJECT_INDICES:
        print(f"  [{idx:02d}] {name}  ← {note}")
    print("\nSubfailures:")
    for k, v in subfailures.items():
        print(f"  {k}. {v}")

def pick_subfailure(subfailures: dict) -> int:
    while True:
        ans = input("\nSubfailure number: ").strip()
        if ans in subfailures:
            return int(ans)
        print(f"  Enter one of: {list(subfailures.keys())}")

def pick_pose() -> tuple:
    print("\nInject at which pose?")
    for i, (idx, name, note) in enumerate(INJECT_INDICES, 1):
        print(f"  {i}. [{idx:02d}] {name}  — {note}")
    print(f"  {len(INJECT_INDICES)+1}. All poses in sequence")
    while True:
        ans = input("Choice: ").strip()
        if ans.isdigit():
            n = int(ans)
            if 1 <= n <= len(INJECT_INDICES):
                return [INJECT_INDICES[n-1]]
            if n == len(INJECT_INDICES) + 1:
                return INJECT_INDICES
        print("  Invalid choice.")

def write_signal(failure_type: str, subfailure: int, extra: dict = None):
    payload = {"type": failure_type, "subfailure": subfailure}
    if extra:
        payload.update(extra)
    with open(SIGNAL_FILE, "w") as f:
        json.dump(payload, f)
    print(f"  [SIGNAL WRITTEN] type={failure_type} subfailure={subfailure}")

def wait_for_pose(target_index: int, target_name: str, poll_interval=0.3):
    """Watch checkpoint.json — fire signal when robot is ABOUT to reach target_index."""
    print(f"\n  Waiting for pose [{target_index:02d}] {target_name} ...")
    last_index = -1
    
    # ── FIX: checkpoint.json is in parent directory ──
    checkpoint_path = "checkpoint.json"
    
    while True:
        time.sleep(poll_interval)
        if not os.path.exists(checkpoint_path):
            continue
        try:
            with open(checkpoint_path) as f:
                ckpt = json.load(f)
            current_index = ckpt.get("pose_index", -1)
            
            # If we see the pose BEFORE it's reached (current < target)
            # and the previous checkpoint was target-1, write signal NOW
            if current_index == target_index - 1 and last_index != current_index:
                # We're at the pose BEFORE target - write signal NOW
                print(f"\n  [INJECT] Writing signal at pose {target_index-1} (before {target_name})")
                return
                
            last_index = current_index
        except Exception:
            continue
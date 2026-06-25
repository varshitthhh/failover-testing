# ============================================================
# build_execution_path.py
# Builds two files:
#   path_original.json    — clean sequence, named targets only
#   path_execution.json   — full sequence with IW_ points inserted
#
# main.py reads path_execution.json at runtime.
# All IW_ joint values taken from confirmed motion validation log.
#
# Run: python build_execution_path.py
# (RoboDK does NOT need to be open — pure JSON generation)
# ============================================================

import json
from datetime import datetime

# ── Original named sequence (indices match INSPECTION_SEQUENCE in main.py) ───

ORIGINAL_SEQUENCE = [
    {"name": "Target 1",   "joints": [0.0,    0.0,   90.0,    0.0,    0.0,    0.0]},
    {"name": "Target 2",   "joints": [-84.1,  -1.24,  85.62,  -5.39, -74.98,   0.0]},
    {"name": "Target 4",   "joints": [-69.98, 31.07,  64.63,-116.44, -33.36,   0.0]},  # NOTE: corrected from log
    {"name": "Target 5",   "joints": [114.53,-91.95,  64.63,  12.34, -76.81,  60.61]},
    {"name": "Target 6",   "joints": [114.52,-89.16,  61.63,  -3.59, -65.82,  65.29]},
    {"name": "Target 7",   "joints": [-69.98,  29.07,  41.63,-101.44, -11.36,   0.0]},
    {"name": "Target 8",   "joints": [-69.98,  29.07,  41.63,-101.44,  12.64,   0.0]},
    {"name": "Target 8a",  "joints": [-69.97,  33.06,  45.85, -44.33, -69.18,   0.0]},
    {"name": "Target 9",   "joints": [-79.97,  39.07,  31.63,  72.41, -49.3,    0.0]},
    {"name": "Target 10",  "joints": [-79.96,  39.06,  31.63,  72.41, -77.29,   0.0]},
    {"name": "Target 11",  "joints": [-79.95,  39.06,  31.62,  60.41, -91.58,   0.0]},
    {"name": "Target 12",  "joints": [-69.98,  29.07,  45.11,-108.12,-107.3,    0.0]},
    {"name": "Target 13",  "joints": [114.73, -71.71,  45.1,   61.81,-114.19,  43.27]},
    {"name": "Target 15",  "joints": [-69.97,  29.05,  67.2,  -66.2,   52.6,   0.0]},
    {"name": "Target 16",  "joints": [-69.98,  29.06,  67.2,  -73.21,  64.61,  0.0]},
    {"name": "Target 17",  "joints": [-69.97,  29.05,  67.2,  -73.21,  91.61,  0.0]},
    {"name": "Target 18",  "joints": [-78.97,  31.05,  57.2,  -64.21, 115.61,  0.0]},
    {"name": "Target 11a", "joints": [-79.94,  39.05,  31.62,-135.47,  90.72, 179.99]},
    {"name": "Target 2",   "joints": [-84.1,   -1.24,  85.62,  -5.39, -74.98,  0.0]},
    {"name": "Target 1",   "joints": [0.0,     0.0,   90.0,    0.0,    0.0,   0.0]},
]

# ── IW_ waypoints — joints from ACTUAL motion validation log ─────────────────
# All entries: {"name": str, "joints": [...], "type": "iw", "note": str}

# T6 → T7  (2 IW points, J5 near-singular at IW1 — flagged, kept)
IW_T6_T7 = [
    {"name": "IW_T6_T7_1", "joints": [-69.98, 30.4,  54.96,-111.44,  -4.69, 0.0],
     "note": "J5=-4.69 near singular — flagged"},
    {"name": "IW_T6_T7_2", "joints": [-69.98, 29.74, 48.3, -106.44,  -8.03, 0.0],
     "note": "clean"},
]

# T8a → T9  (2 IW points)
IW_T8A_T9 = [
    {"name": "IW_T8a_T9_1", "joints": [-73.3,  35.06, 41.11,  -5.42, -62.55, 0.0],
     "note": "clean"},
    {"name": "IW_T8a_T9_2", "joints": [-76.64, 37.07, 36.37,  33.5,  -55.93, 0.0],
     "note": "clean"},
]

# T11a → T11  wrist flip fix (1 IW point — J6 cleared only)
IW_T11A_T11 = [
    {"name": "IW_T11a_T11_fix_1",
     "joints": [-79.94, 39.05, 31.62, -135.47, 90.72, 0.0],
     "note": "J6 cleared to 0 while J1-J5 frozen at T11a. Pure wrist rotation."},
]

# T13 → T15  (2 IW points, IW2 J5 near-singular — flagged, kept)
IW_T13_T15 = [
    {"name": "IW_T13_T15_1", "joints": [-69.98, 29.06, 52.47,-105.47, -43.33, 0.0],
     "note": "clean"},
    {"name": "IW_T13_T15_2", "joints": [-69.97, 29.06, 59.83, -85.84,   4.63, 0.0],
     "note": "J5=4.63 near singular — flagged"},
]

# T18 → T2  (3 IW points — exit corridor approach)
IW_T18_T2 = [
    {"name": "IW_T18_T2_1", "joints": [-80.25, 22.98, 64.31, -49.5,   67.96, 0.0],
     "note": "clean"},
    {"name": "IW_T18_T2_2", "joints": [-81.54, 14.9,  71.41, -34.8,   20.31, 0.0],
     "note": "clean"},
    {"name": "IW_T18_T2_3", "joints": [-82.82,  6.83, 78.52, -20.1,  -27.33, 0.0],
     "note": "clean"},
]

# ── Retreat IW_ points (anchor-to-anchor) ────────────────────────────────────

# T11 → T7  (retreat)
IW_RET_T11_T7 = [
    {"name": "IW_RET_T11_T7_1", "joints": [-76.63, 35.73, 34.96,   6.46, -64.84, 0.0],
     "note": "clean"},
    {"name": "IW_RET_T11_T7_2", "joints": [-73.3,  32.4,  38.29, -47.49, -38.1,  0.0],
     "note": "clean"},
]

# T7 → T4  (retreat)
IW_RET_T7_T4 = [
    {"name": "IW_RET_T7_T4_1", "joints": [-69.98, 29.74, 49.3, -106.44, -18.69, 0.0],
     "note": "clean"},
    {"name": "IW_RET_T7_T4_2", "joints": [-69.98, 30.4,  56.96,-111.44, -26.03, 0.0],
     "note": "clean"},
]

# T4 → T2  (retreat — visually confirmed no intermediates needed)
IW_RET_T4_T2 = []

# T2 → T1  (exit corridor — confirmed clean, no intermediates needed)
IW_RET_T2_T1 = []

# ── Build execution path ──────────────────────────────────────────────────────

def make_step(name, joints, step_type="target", note=""):
    return {
        "name":  name,
        "joints": joints,
        "type":  step_type,   # "target" or "iw"
        "note":  note,
    }

def build_execution_path():
    """
    Insert IW_ points between named targets at the correct positions.
    Returns list of step dicts in execution order.
    """
    path = []

    def add_target(idx):
        s = ORIGINAL_SEQUENCE[idx]
        path.append(make_step(s["name"], s["joints"], "target"))

    def add_iw_list(iw_list):
        for iw in iw_list:
            path.append(make_step(iw["name"], iw["joints"], "iw", iw.get("note","")))

    # Index reference (matches ORIGINAL_SEQUENCE above):
    # 0=T1, 1=T2, 2=T4, 3=T5, 4=T6, 5=T7, 6=T8, 7=T8a,
    # 8=T9, 9=T10, 10=T11, 11=T12, 12=T13, 13=T15, 14=T16,
    # 15=T17, 16=T18, 17=T11a, 18=T2(return), 19=T1(home)

    add_target(0)   # T1 home
    add_target(1)   # T2 entry  (T1→T2 confirmed clean)
    add_target(2)   # T4        (T2→T4: 393mm — NOTE below)
    add_target(3)   # T5
    add_target(4)   # T6
    add_iw_list(IW_T6_T7)
    add_target(5)   # T7
    add_target(6)   # T8
    add_target(7)   # T8a
    add_iw_list(IW_T8A_T9)
    add_target(8)   # T9
    add_target(9)   # T10
    add_target(10)  # T11
    add_target(11)  # T12
    add_target(12)  # T13
    add_iw_list(IW_T13_T15)
    add_target(13)  # T15
    add_target(14)  # T16
    add_target(15)  # T17
    add_target(16)  # T18
    add_iw_list(IW_T18_T2)
    add_target(17)  # T11a
    add_iw_list(IW_T11A_T11)
    add_target(10)  # T11  ← note: reusing index 10 (T11 second visit)
    add_iw_list(IW_T18_T2[::-1])  # T18→T2 intermediates reversed for return
    add_target(18)  # T2 return
    add_target(19)  # T1 home

    return path

# ── Wait — T18→T11a ordering needs checking ──────────────────────────────────
# Looking at original sequence: ...T18 → T11a → T2 → T1
# So the path after T18 is:  T18 → [IW_T18_T2] → T11a → [IW_T11a_T11] → T11 → ... T2 → T1?
# NO. The original sequence is T18 → T11a → T2 → T1.
# T18→T2 intermediates were for the T18→T2 jump in the ORIGINAL program (without T11a).
# With T11a in the path: T18 → T11a (direct) → T11 (via fix IW) → then what?
# T11 is already visited at index 10. After T11a, it's → T2 → T1.
# So: T11a → [IW_fix] → T11 → ??? → T2 → T1
# The original sequence ends: T11a → T2 → T1. T11 is NOT revisited after T11a.
# The fix IW gets us from T11a to T11 (wrist reorientation) but T11 is NOT
# in the sequence after T11a in Prog1. T11a IS the last inspection pose.
# Then it goes T11a → T2 (return) → T1.
# So IW_T11a_T11 is WRONG PLACEMENT. The fix should be:
#   T18 → T11a → [IW: J6 clear] → T2 → T1
# The J6 clear IW gets J6 from 179.99 to 0 before moving to T2.

# ── CORRECTED understanding ───────────────────────────────────────────────────
# T11a joints: [-79.94, 39.05, 31.62, -135.47, 90.72, 179.99]
# T2 joints:   [-84.1, -1.24, 85.62, -5.39, -74.98, 0.0]
# The J6=179.99 at T11a needs to be cleared BEFORE moving to T2.
# The IW_T18_T2 intermediates were for T18→T2 DIRECT (without T11a in between).
# With T11a: T18→T11a is a direct move. T11a→T2 is the problem move (J6 flip + long jump).
# The fix: clear J6 at T11a first (IW_fix), THEN move T2 via existing T18→T2 IW points.
# But T18→T2 IW points start from T18 arm position, not T11a arm position.
# T11a and T18 have different J1-J3, so IW_T18_T2 points are NOT usable for T11a→T2.
# 
# ACTUAL correct path:
#   T11a → IW_fix (J6→0, arm frozen) → T2 (direct, arm + wrist move together)
# T11a→T2 distance (arm): large jump — need to check if direct is OK.
# T11a TCP: (105.6, -883.2, 899.9). T2 TCP: (103.1, -555.1, 946.0). 
# Distance: sqrt((2.5)^2 + (328.1)^2 + (46.1)^2) ≈ 331mm. Large but manageable.
# With J6 cleared first, the arm move T11a→T2 only changes J4/J5 (J1-J3 near-identical).
# This is the same region as T9/T10/T11 moves — should be clean.

def build_execution_path_corrected():
    """
    Corrected execution path based on re-analysis of T11a→T2 transition.
    T18→T2 IW points are NOT used (T11a is between them).
    Instead: T11a → IW_fix(J6 clear) → T2 direct.
    """
    path = []

    def add(name, joints, step_type="target", note=""):
        path.append(make_step(name, joints, step_type, note))

    # T1 → T2 (clean)
    add("Target 1",  ORIGINAL_SEQUENCE[0]["joints"],  "target")
    add("Target 2",  ORIGINAL_SEQUENCE[1]["joints"],  "target")

    # T2 → T4 (393mm) — T3 invalid, no IW added from old script
    # From log: T3 intermediates were generated but T3 itself is invalid/unused.
    # The T2→T4 direct move in Prog1 was validated in earlier phases (19/19 poses OK).
    # Keep direct unless you observed a collision here specifically.
    add("Target 4",  ORIGINAL_SEQUENCE[2]["joints"],  "target",
        note="T2→T4 393mm direct — validated in Phase 5")

    add("Target 5",  ORIGINAL_SEQUENCE[3]["joints"],  "target")
    add("Target 6",  ORIGINAL_SEQUENCE[4]["joints"],  "target")

    # T6 → T7 (270mm)
    for iw in IW_T6_T7:
        add(iw["name"], iw["joints"], "iw", iw["note"])
    add("Target 7",  ORIGINAL_SEQUENCE[5]["joints"],  "target")

    add("Target 8",  ORIGINAL_SEQUENCE[6]["joints"],  "target")
    add("Target 8a", ORIGINAL_SEQUENCE[7]["joints"],  "target")

    # T8a → T9 (340mm)
    for iw in IW_T8A_T9:
        add(iw["name"], iw["joints"], "iw", iw["note"])
    add("Target 9",  ORIGINAL_SEQUENCE[8]["joints"],  "target")

    add("Target 10", ORIGINAL_SEQUENCE[9]["joints"],  "target")
    add("Target 11", ORIGINAL_SEQUENCE[10]["joints"], "target")
    add("Target 12", ORIGINAL_SEQUENCE[11]["joints"], "target")
    add("Target 13", ORIGINAL_SEQUENCE[12]["joints"], "target")

    # T13 → T15 (277mm)
    for iw in IW_T13_T15:
        add(iw["name"], iw["joints"], "iw", iw["note"])
    add("Target 15", ORIGINAL_SEQUENCE[13]["joints"], "target")

    add("Target 16", ORIGINAL_SEQUENCE[14]["joints"], "target")
    add("Target 17", ORIGINAL_SEQUENCE[15]["joints"], "target")
    add("Target 18", ORIGINAL_SEQUENCE[16]["joints"], "target")

    # T18 → T11a (direct — short enough, no IW needed)
    add("Target 11a", ORIGINAL_SEQUENCE[17]["joints"], "target")

    # T11a → T2: clear J6 first (wrist flip fix), then direct to T2
    add("IW_T11a_J6clear",
        [-79.94, 39.05, 31.62, -135.47, 90.72, 0.0],
        "iw",
        "J6 cleared at T11a pose. Pure wrist rotation, zero TCP displacement.")

    # T2 return
    add("Target 2",  ORIGINAL_SEQUENCE[18]["joints"], "target",
        note="return via exit corridor")
    add("Target 1",  ORIGINAL_SEQUENCE[19]["joints"], "target",
        note="home")

    return path


def main():
    # Build original (named targets only)
    original = [
        {"name": s["name"], "joints": s["joints"]}
        for s in ORIGINAL_SEQUENCE
    ]

    # Build execution path (with IW_ points)
    execution = build_execution_path_corrected()

    # Save path_original.json
    original_out = {
        "generated": datetime.now().isoformat(),
        "description": "Named targets only — no intermediates",
        "count": len(original),
        "path": original,
    }
    with open("path_original.json", "w") as f:
        json.dump(original_out, f, indent=2)
    print(f"[SAVED] path_original.json ({len(original)} steps)")

    # Save path_execution.json
    execution_out = {
        "generated": datetime.now().isoformat(),
        "description": "Full execution path with IW_ intermediates inserted",
        "count": len(execution),
        "target_count": sum(1 for s in execution if s["type"] == "target"),
        "iw_count":     sum(1 for s in execution if s["type"] == "iw"),
        "path": execution,
    }
    with open("path_execution.json", "w") as f:
        json.dump(execution_out, f, indent=2)
    print(f"[SAVED] path_execution.json ({len(execution)} steps: "
          f"{execution_out['target_count']} targets + {execution_out['iw_count']} IW points)")

    # Print summary
    print()
    print("Execution path summary:")
    for i, step in enumerate(execution):
        marker = "    " if step["type"] == "target" else " IW "
        note = f"  ← {step['note']}" if step.get("note") else ""
        print(f"  [{i:02d}] {marker} {step['name']}{note}")

if __name__ == "__main__":
    main()
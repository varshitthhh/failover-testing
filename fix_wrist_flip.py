# ============================================================
# fix_wrist_flip.py
# Adds the corrected single-intermediate for T11a → T11 wrist flip.
# Run this AFTER undo_intermediates.py (station must be clean).
#
# The fix: clear J6 to 0 while J1-J5 frozen at T11a values.
# J6 rotation = pure tool spin, zero TCP displacement.
# No vehicle collision possible.
#
# Run: python fix_wrist_flip.py
# ============================================================

import json
import time
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TARGET, ITEM_TYPE_FRAME
from robodk.robomath import pose_2_xyzrpw

# T11a joints (from station_analysis.json — verified)
T11A_JOINTS = [-79.94, 39.05, 31.62, -135.47, 90.72, 179.99]
T11_JOINTS  = [-79.95, 39.06, 31.62,   60.41, -91.58,   0.0]

# The fix intermediate: J6 cleared, everything else frozen at T11a
FIX_JOINTS = [-79.94, 39.05, 31.62, -135.47, 90.72, 0.0]
FIX_NAME   = "IW_T11a_T11_fix_1"

SPEED = 30.0  # mm/s

def main():
    RDK = Robolink()
    if not RDK.Connect():
        print("[ERROR] Cannot connect to RoboDK.")
        return

    robots = RDK.ItemList(ITEM_TYPE_ROBOT)
    if not robots:
        print("[ERROR] No robot found.")
        return
    robot = robots[0]
    robot.setSpeed(SPEED)

    frames = RDK.ItemList(ITEM_TYPE_FRAME)
    frame  = frames[0] if frames else RDK.ActiveStation()

    print(f"Robot : {robot.Name()}")
    print(f"Frame : {frame.Name()}")
    print()

    # ── Step 1: Add IW target to station ─────────────────────────────────────
    existing = RDK.Item(FIX_NAME, ITEM_TYPE_TARGET)
    if existing.Valid():
        print(f"[INFO] {FIX_NAME} already exists in station. Deleting and recreating.")
        existing.Delete()

    pose = robot.SolveFK(FIX_JOINTS)
    target = RDK.AddTarget(FIX_NAME, frame, robot)
    target.setAsJointTarget()
    target.setJoints(FIX_JOINTS)
    target.setPose(pose)

    xyzrpw = pose_2_xyzrpw(pose)
    print(f"[TARGET ADDED] {FIX_NAME}")
    print(f"  Joints : {FIX_JOINTS}")
    print(f"  TCP XYZ: ({xyzrpw[0]:.1f}, {xyzrpw[1]:.1f}, {xyzrpw[2]:.1f}) mm")
    print()

    # ── Step 2: Motion validation ─────────────────────────────────────────────
    print("Visually inspect the target in RoboDK now.")
    print("It should overlap with T11a TCP position (J6 only changed).")
    ans = input("\nRun motion test T11a → IW_fix → T11? (y/n): ").strip().lower()
    if ans != "y":
        print("[SKIPPED] Motion test skipped.")
        return

    # Move to T11a
    t11a = RDK.Item("Target 11a", ITEM_TYPE_TARGET)
    if not t11a.Valid():
        print("[ERROR] Target 11a not found in station.")
        return
    print("[MOVING] → Target 11a")
    robot.MoveJ(t11a)
    time.sleep(0.5)

    j_actual = robot.Joints().list()
    p_actual = pose_2_xyzrpw(robot.Pose())
    print(f"  At T11a — joints: {[round(j,2) for j in j_actual]}")
    print(f"  TCP: ({p_actual[0]:.1f}, {p_actual[1]:.1f}, {p_actual[2]:.1f}) mm")

    # Move to fix intermediate
    print(f"\n[MOVING] → {FIX_NAME}")
    robot.MoveJ(FIX_JOINTS)
    time.sleep(0.5)

    j_actual = robot.Joints().list()
    p_actual = pose_2_xyzrpw(robot.Pose())
    print(f"  At IW_fix — joints: {[round(j,2) for j in j_actual]}")
    print(f"  TCP: ({p_actual[0]:.1f}, {p_actual[1]:.1f}, {p_actual[2]:.1f}) mm")

    # Check TCP displacement from T11a (should be ~0)
    t11a_pose = pose_2_xyzrpw(t11a.Pose())
    dx = abs(p_actual[0] - t11a_pose[0])
    dy = abs(p_actual[1] - t11a_pose[1])
    dz = abs(p_actual[2] - t11a_pose[2])
    disp = (dx**2 + dy**2 + dz**2) ** 0.5
    print(f"\n  TCP displacement from T11a: {disp:.2f} mm  (expect < 5 mm)")
    if disp > 10.0:
        print("  [WARNING] Displacement unexpectedly large — check FK.")
    else:
        print("  [OK] TCP barely moved — wrist flip is clean.")

    # Move to T11
    t11 = RDK.Item("Target 11", ITEM_TYPE_TARGET)
    if not t11.Valid():
        print("[ERROR] Target 11 not found.")
        return
    print(f"\n[MOVING] → Target 11")
    robot.MoveJ(t11)
    time.sleep(0.5)

    j_actual = robot.Joints().list()
    p_actual = pose_2_xyzrpw(robot.Pose())
    print(f"  At T11 — joints: {[round(j,2) for j in j_actual]}")
    print(f"  TCP: ({p_actual[0]:.1f}, {p_actual[1]:.1f}, {p_actual[2]:.1f}) mm")

    print()
    print("="*50)
    print("Motion test complete.")
    print("Check RoboDK — was there any collision during T11a → IW_fix?")
    print("(T11a → IW_fix should show tool rotation only, no arm movement)")
    print("(IW_fix → T11 is the normal arm + wrist motion)")

if __name__ == "__main__":
    main()
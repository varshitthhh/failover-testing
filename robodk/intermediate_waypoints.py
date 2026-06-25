# ============================================================
# intermediate_waypoints.py
# Extracts interpolated intermediate waypoints between large-jump
# anchor pairs in the retreat path.
# 
# HOW TO RUN:
#   Terminal 1: RoboDK open with SingleRobot.rdk
#   Terminal 2: python intermediate_waypoints.py
#
# OUTPUT:
#   - intermediate_waypoints.json  (coordinates + joints)
#   - intermediate_waypoints.log   (health log, limits check)
#   - Adds targets to RoboDK station visually for inspection
#
# VALIDATE: visually check added targets in RoboDK for collisions
# ============================================================

import json
import time
import math
import logging
from datetime import datetime
from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TARGET, ITEM_TYPE_FRAME
from robodk.robomath import pose_2_xyzrpw, xyzrpw_2_pose, Mat

# ── Config ────────────────────────────────────────────────────────────────────

# Joint limits for Doosan M1013 (from analysis)
JOINT_LIMITS = {
    "lower": [-360, -360, -160, -360, -360, -360],
    "upper": [ 360,  360,  160,  360,  360,  360],
}

# Large-jump pairs needing intermediates (from geometry analysis)
# Format: (from_target, to_target, num_intermediates)
LARGE_JUMP_PAIRS = [
    ("Target 11a", "Target 11",  2),   # 364mm
    ("Target 13",  "Target 15",  2),   # 277mm
    ("Target 18",  "Target 2",   3),   # 399mm
    ("Target 3",   "Target 4",   3),   # 393mm
    ("Target 8a",  "Target 9",   2),   # 340mm
    ("Target 6",   "Target 7",   2),   # 270mm
]

# Retreat-specific large jumps (anchor-to-anchor)
RETREAT_JUMP_PAIRS = [
    ("Target 11",  "Target 7",   2),   # 277mm retreat
    ("Target 7",   "Target 4",   2),   # 270mm retreat
    ("Target 4",   "Target 1",   2),   # long retreat to home
]

OUTPUT_JSON = "intermediate_waypoints.json"
OUTPUT_LOG  = "intermediate_waypoints.log"
ROBOT_SPEED = 30.0  # mm/s — slow for validation

# ── Logger ────────────────────────────────────────────────────────────────────

logging.basicConfig(
    filename=OUTPUT_LOG,
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    datefmt="%H:%M:%S"
)
console = logging.getLogger("IW")
console.addHandler(logging.StreamHandler())


def log(msg, level="INFO"):
    if level == "ERROR":
        console.error(msg)
    elif level == "WARN":
        console.warning(msg)
    else:
        console.info(msg)


# ── Joint health check ────────────────────────────────────────────────────────

def check_joint_limits(joints, label=""):
    issues = []
    for i, j in enumerate(joints):
        lo = JOINT_LIMITS["lower"][i]
        hi = JOINT_LIMITS["upper"][i]
        if not (lo <= j <= hi):
            issues.append(f"J{i+1}={j:.2f} out of [{lo}, {hi}]")
        margin = min(abs(j - lo), abs(j - hi))
        if margin < 10.0:
            issues.append(f"J{i+1}={j:.2f} near limit (margin={margin:.1f} deg)")
    if issues:
        log(f"[LIMIT WARNING] {label}: {issues}", "WARN")
        return False
    log(f"[LIMIT OK] {label}: joints within safe range")
    return True


def check_singularity(joints, label=""):
    j5 = joints[4] if len(joints) > 4 else None
    if j5 is not None and abs(j5) < 5.0:
        log(f"[SINGULARITY RISK] {label}: J5={j5:.2f} deg (near 0)", "WARN")
        return True
    return False


def check_xyz_in_workspace(xyzrpw, label=""):
    x, y, z = xyzrpw[0], xyzrpw[1], xyzrpw[2]
    # Doosan M1013 reach ~1300mm, base at (401, 1165, 0)
    # Inspection zone from analysis: X[85,680], Y[-977,34], Z[587,946]
    WORKSPACE = {
        "x": (-200.0, 800.0),
        "y": (-1200.0, 100.0),
        "z": (400.0, 1100.0),
    }
    issues = []
    for ax, val in [("x", x), ("y", y), ("z", z)]:
        lo, hi = WORKSPACE[ax]
        if not (lo <= val <= hi):
            issues.append(f"{ax.upper()}={val:.1f} out of [{lo},{hi}]")
    if issues:
        log(f"[WORKSPACE VIOLATION] {label}: {issues}", "ERROR")
        return False
    log(f"[WORKSPACE OK] {label}: XYZ=({x:.1f},{y:.1f},{z:.1f})")
    return True


# ── Interpolation ─────────────────────────────────────────────────────────────

def interpolate_joints(j_start, j_end, n_steps):
    """
    Linear interpolation in joint space.
    Returns list of n_steps intermediate joint configs (excludes endpoints).
    """
    intermediates = []
    for step in range(1, n_steps + 1):
        t = step / (n_steps + 1)
        interp = [j_start[i] + t * (j_end[i] - j_start[i])
                  for i in range(len(j_start))]
        intermediates.append([round(v, 4) for v in interp])
    return intermediates


def interpolate_xyz(xyz_start, xyz_end, n_steps):
    """Cartesian linear interpolation for reference."""
    intermediates = []
    for step in range(1, n_steps + 1):
        t = step / (n_steps + 1)
        interp = [xyz_start[i] + t * (xyz_end[i] - xyz_start[i])
                  for i in range(3)]
        intermediates.append([round(v, 4) for v in interp])
    return intermediates


# ── FK via RoboDK ─────────────────────────────────────────────────────────────

def get_fk_pose(robot, joints):
    """Forward kinematics: joints → TCP pose xyzrpw."""
    try:
        from robodk.robomath import Mat
        j_mat = Mat([joints])
        # RoboDK SolveFK expects a joint vector
        pose = robot.SolveFK(joints)
        xyzrpw = pose_2_xyzrpw(pose)
        return [round(v, 4) for v in xyzrpw]
    except Exception as e:
        log(f"FK failed: {e}", "ERROR")
        return None


# ── Add target to RoboDK station ─────────────────────────────────────────────

def add_target_to_station(RDK, robot, name, joints, frame):
    """
    Creates a new RoboDK target from joint config.
    Visible in station tree for visual collision inspection.
    """
    try:
        # Get pose from FK
        pose = robot.SolveFK(joints)
        target = RDK.AddTarget(name, frame, robot)
        target.setAsJointTarget()
        from robodk.robomath import Mat
        import numpy as np
        j_mat = Mat([[j] for j in joints])
        target.setJoints(joints)
        target.setPose(pose)
        log(f"[TARGET ADDED] {name} added to RoboDK station")
        return target
    except Exception as e:
        log(f"[TARGET ADD FAILED] {name}: {e}", "ERROR")
        return None


# ── Move and log robot health ─────────────────────────────────────────────────

def move_and_log(robot, RDK, joints, label):
    """
    Move robot to joint config and log full health metrics.
    """
    try:
        robot.MoveJ(joints)
        time.sleep(0.4)  # settle

        actual_joints = robot.Joints().list()
        actual_pose   = robot.Pose()
        xyzrpw        = pose_2_xyzrpw(actual_pose)

        log(f"[MOVE OK] {label}")
        log(f"  Commanded joints : {[round(j,2) for j in joints]}")
        log(f"  Actual joints    : {[round(j,2) for j in actual_joints]}")
        log(f"  TCP XYZ          : ({xyzrpw[0]:.1f}, {xyzrpw[1]:.1f}, {xyzrpw[2]:.1f}) mm")
        log(f"  TCP RPW          : ({xyzrpw[3]:.2f}, {xyzrpw[4]:.2f}, {xyzrpw[5]:.2f}) deg")

        joint_ok   = check_joint_limits(actual_joints, label)
        sing_risk  = check_singularity(actual_joints, label)
        ws_ok      = check_xyz_in_workspace(xyzrpw, label)

        # Joint tracking error
        errors = [abs(actual_joints[i] - joints[i]) for i in range(len(joints))]
        max_err = max(errors)
        if max_err > 1.0:
            log(f"  [TRACKING ERROR] Max joint error: {max_err:.2f} deg", "WARN")

        return {
            "label":          label,
            "commanded_joints": [round(j, 4) for j in joints],
            "actual_joints":  [round(j, 4) for j in actual_joints],
            "tcp_xyzrpw":     [round(v, 4) for v in xyzrpw],
            "joint_ok":       joint_ok,
            "singularity":    sing_risk,
            "workspace_ok":   ws_ok,
            "max_tracking_error_deg": round(max_err, 4),
        }

    except Exception as e:
        log(f"[MOVE FAILED] {label}: {e}", "ERROR")
        return {"label": label, "error": str(e)}


# ── Main extraction logic ─────────────────────────────────────────────────────

def extract_intermediates(RDK, robot, frame, jump_pairs, tag=""):
    """
    For each large-jump pair:
    1. Get start/end joint configs from existing targets
    2. Interpolate n intermediate configs
    3. Run FK → get XYZ
    4. Validate limits, workspace, singularity
    5. Add to RoboDK station
    6. Optionally move robot through them (validation motion)
    """
    results = {}

    for (from_name, to_name, n_steps) in jump_pairs:
        pair_key = f"{tag}{from_name}→{to_name}"
        log(f"\n{'='*55}")
        log(f"Processing: {pair_key} ({n_steps} intermediates)")

        try:
            t_from = RDK.Item(from_name, ITEM_TYPE_TARGET)
            t_to   = RDK.Item(to_name,   ITEM_TYPE_TARGET)

            if not t_from.Valid() or not t_to.Valid():
                log(f"[SKIP] Target not found: {from_name} or {to_name}", "WARN")
                continue

            j_from = t_from.Joints().list()
            j_to   = t_to.Joints().list()
            xyz_from = pose_2_xyzrpw(t_from.Pose())[:3]
            xyz_to   = pose_2_xyzrpw(t_to.Pose())[:3]

            dist = math.sqrt(sum((xyz_to[i]-xyz_from[i])**2 for i in range(3)))
            log(f"  Cartesian distance: {dist:.1f} mm")
            log(f"  From joints: {[round(j,2) for j in j_from]}")
            log(f"  To   joints: {[round(j,2) for j in j_to]}")

            interp_joints = interpolate_joints(j_from, j_to, n_steps)
            interp_xyz    = interpolate_xyz(list(xyz_from), list(xyz_to), n_steps)

            pair_results = []
            for i, (joints, xyz_ref) in enumerate(zip(interp_joints, interp_xyz)):
                iname  = f"IW_{from_name.replace(' ','')}_{to_name.replace(' ','')}_{i+1}"
                label  = f"{pair_key} step {i+1}/{n_steps}"

                log(f"\n  -- Intermediate {i+1}: {iname}")
                log(f"     Joint config : {joints}")
                log(f"     XYZ ref (lin): {[round(v,1) for v in xyz_ref]}")

                # FK validation
                fk_xyzrpw = get_fk_pose(robot, joints)
                if fk_xyzrpw:
                    log(f"     FK TCP XYZ   : ({fk_xyzrpw[0]:.1f}, "
                        f"{fk_xyzrpw[1]:.1f}, {fk_xyzrpw[2]:.1f})")
                    check_joint_limits(joints, iname)
                    check_singularity(joints, iname)
                    check_xyz_in_workspace(fk_xyzrpw, iname)

                # Add to RoboDK for visual inspection
                add_target_to_station(RDK, robot, iname, joints, frame)

                pair_results.append({
                    "name":       iname,
                    "joints_deg": joints,
                    "fk_xyzrpw":  fk_xyzrpw,
                    "xyz_linear_ref": [round(v,4) for v in xyz_ref],
                })

            results[pair_key] = {
                "from":          from_name,
                "to":            to_name,
                "distance_mm":   round(dist, 2),
                "n_intermediates": n_steps,
                "waypoints":     pair_results,
            }

        except Exception as e:
            log(f"[ERROR] {pair_key}: {e}", "ERROR")
            results[pair_key] = {"error": str(e)}

    return results


def validate_motion_through_intermediates(robot, RDK, results):
    """
    Move robot through each interpolated waypoint sequence slowly.
    Logs actual joints + TCP at each step.
    Press ENTER to proceed to next pair.
    """
    log("\n" + "="*55)
    log("MOTION VALIDATION — moving through intermediates")
    log("Watch RoboDK for collisions. Press ENTER for each pair.")

    motion_log = {}

    for pair_key, data in results.items():
        if "error" in data:
            continue

        print(f"\n[VALIDATE] {pair_key} ({data['n_intermediates']} steps)")
        print(f"  Distance: {data['distance_mm']} mm")
        ans = input("  Move through this pair? (y/n): ").strip().lower()
        if ans != "y":
            log(f"[SKIPPED] {pair_key}")
            continue

        # Move to start target first
        try:
            t_from = RDK.Item(data["from"], ITEM_TYPE_TARGET)
            robot.MoveJ(t_from)
            log(f"[AT START] {data['from']}")
            time.sleep(0.5)
        except Exception as e:
            log(f"[FAILED TO REACH START] {data['from']}: {e}", "ERROR")
            continue

        step_logs = []
        for wp in data["waypoints"]:
            result = move_and_log(robot, RDK, wp["joints_deg"], wp["name"])
            step_logs.append(result)
            time.sleep(0.3)

        # Move to end target
        try:
            t_to = RDK.Item(data["to"], ITEM_TYPE_TARGET)
            robot.MoveJ(t_to)
            log(f"[AT END] {data['to']}")
        except Exception as e:
            log(f"[FAILED TO REACH END] {data['to']}: {e}", "ERROR")

        motion_log[pair_key] = step_logs
        print(f"  [DONE] Check RoboDK — any collisions visible? Note them.")

    return motion_log


def main():
    log("="*55)
    log("Intermediate Waypoint Extractor — BIW Recovery Framework")
    log(f"Started: {datetime.now().isoformat()}")

    # Connect
    RDK = Robolink()
    if not RDK.Connect():
        log("Cannot connect to RoboDK", "ERROR")
        return

    robots = RDK.ItemList(ITEM_TYPE_ROBOT)
    if not robots:
        log("No robot found", "ERROR")
        return
    robot = robots[0]
    robot.setSpeed(ROBOT_SPEED)

    # Get base frame
    frames = RDK.ItemList(ITEM_TYPE_FRAME)
    frame  = frames[0] if frames else RDK.ActiveStation()

    log(f"Robot : {robot.Name()}")
    log(f"Frame : {frame.Name()}")
    log(f"Speed : {ROBOT_SPEED} mm/s")

    all_results = {}

    # Phase 1: Inspection path large jumps
    log("\n[PHASE 1] Inspection path intermediates")
    insp_results = extract_intermediates(
        RDK, robot, frame, LARGE_JUMP_PAIRS, tag="INSP_"
    )
    all_results["inspection"] = insp_results

    # Phase 2: Retreat path large jumps
    log("\n[PHASE 2] Retreat path intermediates")
    ret_results = extract_intermediates(
        RDK, robot, frame, RETREAT_JUMP_PAIRS, tag="RET_"
    )
    all_results["retreat"] = ret_results

    # Save JSON
    with open(OUTPUT_JSON, "w") as f:
        json.dump(all_results, f, indent=2)
    log(f"\n[SAVED] {OUTPUT_JSON}")

    # Phase 3: Optional motion validation
    print("\n" + "="*55)
    print("Intermediate waypoints added to RoboDK station.")
    print("Visually inspect for collisions before motion test.")
    ans = input("\nProceed to motion validation? (y/n): ").strip().lower()
    if ans == "y":
        all_motion = {}
        print("\n-- Inspection path pairs --")
        all_motion["inspection"] = validate_motion_through_intermediates(
            robot, RDK, insp_results
        )
        print("\n-- Retreat path pairs --")
        all_motion["retreat"] = validate_motion_through_intermediates(
            robot, RDK, ret_results
        )
        all_results["motion_validation"] = all_motion
        with open(OUTPUT_JSON, "w") as f:
            json.dump(all_results, f, indent=2)
        log(f"[SAVED] Motion validation results appended to {OUTPUT_JSON}")

    log("\n[DONE] Review intermediate_waypoints.log for full health report.")
    print(f"\n[DONE] Check RoboDK station — IW_ targets added for visual review.")
    print(f"       Full log: {OUTPUT_LOG}")
    print(f"       JSON:     {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
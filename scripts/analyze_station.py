"""
BIW Recovery Framework — Station Analyzer
Run from VS Code with: python analyze_station.py
Requires RoboDK running with SingleRobot.rdk open.
"""

import sys
import json
import numpy as np
import os

try:
    from robodk.robolink import Robolink, ITEM_TYPE_ROBOT, ITEM_TYPE_TARGET, \
        ITEM_TYPE_PROGRAM, ITEM_TYPE_FRAME, ITEM_TYPE_TOOL, ITEM_TYPE_OBJECT
    from robodk.robomath import Mat, transl, roty, rotx, rotz, pose_2_xyzrpw
except ImportError:
    print("[ERROR] robodk not found. Activate your venv: biwrecovery_env")
    sys.exit(1)

OUTPUT_FILE = os.path.join("..", "robodk", os.path.join("..", "robodk", "station_analysis.json"))

rdk_file = os.path.join("..", "robodk", "SingleRobot.rdk")


def connect():
    RDK = Robolink()
    if not RDK.Connect():
        print("[ERROR] Cannot connect to RoboDK. Is it running with the .rdk open?")
        sys.exit(1)
    print("[OK] Connected to RoboDK")
    return RDK

def get_robot_info(RDK):
    robots = RDK.ItemList(ITEM_TYPE_ROBOT)
    if not robots:
        print("[WARN] No robot found")
        return {}, None
    robot = robots[0]
    joints = robot.Joints().list()
    joint_limits = robot.JointLimits()
    lower = [round(x, 3) for x in joint_limits[0].list()]
    upper = [round(x, 3) for x in joint_limits[1].list()]
    pose = robot.Pose()
    xyzrpw = pose_2_xyzrpw(pose)
    info = {
        "name": robot.Name(),
        "joints_current_deg": [round(j, 4) for j in joints],
        "joint_lower_limits_deg": lower,
        "joint_upper_limits_deg": upper,
        "tcp_pose_xyzrpw": [round(v, 4) for v in xyzrpw],
        "dof": len(joints),
    }
    print(f"\n[ROBOT] {info['name']}")
    print(f"  DOF: {info['dof']}")
    print(f"  Current Joints (deg): {info['joints_current_deg']}")
    print(f"  TCP (X,Y,Z,R,P,W mm/deg): {info['tcp_pose_xyzrpw']}")
    return info, robot

def get_targets(RDK, robot):
    targets = RDK.ItemList(ITEM_TYPE_TARGET)
    target_data = {}
    print(f"\n[TARGETS] Found {len(targets)} targets")
    for t in targets:
        name = t.Name()
        try:
            pose = t.Pose()
            xyzrpw = pose_2_xyzrpw(pose)
            joints_sol = robot.SolveIK(pose)
            joints_list = joints_sol.list() if joints_sol is not None else []
            reachable = len(joints_list) > 0 and not all(j == 0 for j in joints_list)
            target_data[name] = {
                "pose_xyzrpw": [round(v, 4) for v in xyzrpw],
                "joints_deg": [round(j, 4) for j in joints_list] if reachable else [],
                "reachable": reachable,
            }
            status = "OK" if reachable else "IK FAIL"
            print(f"  {name}: XYZ=({xyzrpw[0]:.1f}, {xyzrpw[1]:.1f}, {xyzrpw[2]:.1f}) mm  [{status}]")
        except Exception as e:
            target_data[name] = {"error": str(e)}
            print(f"  {name}: ERROR — {e}")
    return target_data

def get_frames(RDK):
    frames = RDK.ItemList(ITEM_TYPE_FRAME)
    frame_data = {}
    print(f"\n[FRAMES] Found {len(frames)} reference frames")
    for f in frames:
        name = f.Name()
        try:
            pose = f.Pose()
            xyzrpw = pose_2_xyzrpw(pose)
            frame_data[name] = {"pose_xyzrpw": [round(v, 4) for v in xyzrpw]}
            print(f"  {name}: XYZ=({xyzrpw[0]:.1f}, {xyzrpw[1]:.1f}, {xyzrpw[2]:.1f})")
        except Exception as e:
            frame_data[name] = {"error": str(e)}
    return frame_data

def get_tools(RDK):
    tools = RDK.ItemList(ITEM_TYPE_TOOL)
    tool_data = {}
    print(f"\n[TOOLS] Found {len(tools)} tools")
    for t in tools:
        name = t.Name()
        try:
            pose = t.Pose()
            xyzrpw = pose_2_xyzrpw(pose)
            tool_data[name] = {"pose_xyzrpw": [round(v, 4) for v in xyzrpw]}
            print(f"  {name}: XYZ=({xyzrpw[0]:.1f}, {xyzrpw[1]:.1f}, {xyzrpw[2]:.1f})")
        except Exception as e:
            tool_data[name] = {"error": str(e)}
    return tool_data

def get_objects(RDK):
    objects = RDK.ItemList(ITEM_TYPE_OBJECT)
    obj_data = {}
    print(f"\n[OBJECTS] Found {len(objects)} objects")
    for o in objects:
        name = o.Name()
        try:
            pose = o.Pose()
            xyzrpw = pose_2_xyzrpw(pose)
            obj_data[name] = {"pose_xyzrpw": [round(v, 4) for v in xyzrpw]}
            print(f"  {name}: XYZ=({xyzrpw[0]:.1f}, {xyzrpw[1]:.1f}, {xyzrpw[2]:.1f})")
        except Exception as e:
            obj_data[name] = {"error": str(e)}
    return obj_data

def get_program_info(RDK):
    programs = RDK.ItemList(ITEM_TYPE_PROGRAM)
    prog_data = {}
    print(f"\n[PROGRAMS] Found {len(programs)} programs")
    for p in programs:
        name = p.Name()
        prog_data[name] = {"name": name}
        print(f"  Program: {name}")
    return prog_data

def analyze_trajectory_geometry(target_data):
    names = sorted(target_data.keys())
    poses, valid_names = [], []
    for n in names:
        d = target_data[n]
        if "pose_xyzrpw" in d and d.get("reachable", False):
            poses.append(d["pose_xyzrpw"][:3])
            valid_names.append(n)
    if len(poses) < 2:
        print("\n[GEOMETRY] Not enough reachable poses")
        return {}
    poses_np = np.array(poses)
    dists = [np.linalg.norm(poses_np[i+1] - poses_np[i]) for i in range(len(poses_np)-1)]
    bbox_min = poses_np.min(axis=0)
    bbox_max = poses_np.max(axis=0)
    bbox_size = bbox_max - bbox_min
    total_path_length = sum(dists)
    print(f"\n[GEOMETRY] Trajectory Analysis")
    print(f"  Valid reachable poses : {len(valid_names)}")
    print(f"  Total path length     : {total_path_length:.1f} mm")
    print(f"  BBox min XYZ          : {bbox_min.round(1).tolist()}")
    print(f"  BBox max XYZ          : {bbox_max.round(1).tolist()}")
    print(f"  BBox size (mm)        : {bbox_size.round(1).tolist()}")
    print(f"\n  Inter-pose distances (mm):")
    for i, d in enumerate(dists):
        flag = "  <-- LARGE JUMP" if d > 300 else ""
        print(f"    {valid_names[i]} -> {valid_names[i+1]}: {d:.1f} mm{flag}")
    sing_warnings = []
    for n in valid_names:
        j = target_data[n].get("joints_deg", [])
        if len(j) >= 5 and abs(j[4]) < 5.0:
            sing_warnings.append({"target": n, "J5_deg": j[4]})
            print(f"  [SINGULARITY RISK] {n}: J5={j[4]:.2f} deg (near 0)")
    return {
        "valid_poses": valid_names,
        "inter_pose_distances_mm": [round(d, 2) for d in dists],
        "total_path_length_mm": round(total_path_length, 2),
        "bbox_min_mm": bbox_min.round(2).tolist(),
        "bbox_max_mm": bbox_max.round(2).tolist(),
        "bbox_size_mm": bbox_size.round(2).tolist(),
        "singularity_warnings": sing_warnings,
    }

def suggest_recovery_waypoints(target_data, geometry):
    valid = geometry.get("valid_poses", [])
    step = max(1, len(valid) // 5)
    anchors = valid[::step]
    if valid and valid[-1] not in anchors:
        anchors.append(valid[-1])
    print(f"\n[RECOVERY] Suggested recovery waypoints:")
    for i, a in enumerate(anchors):
        print(f"  R{i} <- {a}")
    return {f"R{i}": a for i, a in enumerate(anchors)}

def main():
    RDK = connect()
    result = {}
    robot_info, robot = get_robot_info(RDK)
    result["robot"] = robot_info
    result["frames"] = get_frames(RDK)
    result["tools"] = get_tools(RDK)
    result["objects"] = get_objects(RDK)
    result["targets"] = get_targets(RDK, robot)
    result["programs"] = get_program_info(RDK)
    result["geometry"] = analyze_trajectory_geometry(result["targets"])
    result["recovery_waypoint_suggestions"] = suggest_recovery_waypoints(
        result["targets"], result["geometry"]
    )
    with open(OUTPUT_FILE, "w") as f:
        json.dump(result, f, indent=2)
    print(f"\n[DONE] Full analysis saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
# test_anchor_indices.py
# Reads path_execution.json, prints correct anchor indices for RECOVERY_WAYPOINTS
# Run: python test_anchor_indices.py

import json

ANCHOR_TARGETS = {"Target 1", "Target 4", "Target 7", "Target 11", "Target 15", "Target 11a"}

with open("path_execution.json") as f:
    path = json.load(f)["path"]

print("Anchor name → correct index in path_execution.json:\n")
for i, step in enumerate(path):
    if step["name"] in ANCHOR_TARGETS and step["type"] == "target":
        print(f"  {i:02d}  {step['name']}")

print("\nFull path for reference:")
for i, step in enumerate(path):
    tag = " ←ANCHOR" if step["name"] in ANCHOR_TARGETS and step["type"] == "target" else ""
    print(f"  [{i:02d}] {step['type']:6}  {step['name']}{tag}")
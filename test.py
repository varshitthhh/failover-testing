# test.py - Quick check all files load without errors
# Run: python test.py

import os
import sys
import importlib
import subprocess
from pathlib import Path

print("="*60)
print("  QUICK CHECK - ALL PYTHON FILES")
print("="*60)

# ── Files to check ──
files_to_check = [
    # src/ - Source files
    ("src/inject_base.py", "Import inject_base"),
    ("src/inject_program_crash.py", "Import inject_program_crash"),
    ("src/inject_ik_failure.py", "Import inject_ik_failure"),
    ("src/inject_robot_stuck.py", "Import inject_robot_stuck"),
    ("src/inject_collision.py", "Import inject_collision"),
    ("src/main.py", "Import main"),
    
    # scripts/ - Utility scripts
    ("scripts/analyze_station.py", "Import analyze_station"),
    ("scripts/build_execution_path.py", "Import build_execution_path"),
    ("scripts/fix_wrist_flip.py", "Import fix_wrist_flip"),
    ("scripts/test_indices.py", "Import test_indices"),
    ("scripts/undo_intermediates.py", "Import undo_intermediates"),
]

# ── Check each file ──
passed = 0
failed = 0
failed_files = []

print("\nChecking files...\n")

for file_path, desc in files_to_check:
    # Convert path to module name
    module_path = file_path.replace("/", ".").replace("\\", ".").replace(".py", "")
    
    try:
        # Try importing the module
        importlib.import_module(module_path)
        print(f"  ✅ {desc}: OK")
        passed += 1
    except Exception as e:
        print(f"  ❌ {desc}: FAILED - {e}")
        failed += 1
        failed_files.append((file_path, str(e)))

print("\n" + "="*60)
print(f"  RESULTS: {passed} passed, {failed} failed")
print("="*60)

# ── Show failed files ──
if failed_files:
    print("\n❌ FAILED FILES:")
    for file_path, error in failed_files:
        print(f"  - {file_path}: {error}")

# ── Check critical file paths ──
print("\n" + "="*60)
print("  CRITICAL FILE CHECKS")
print("="*60)

# Check checkpoint.json existence
if os.path.exists("checkpoint.json"):
    print("  ✅ checkpoint.json exists")
else:
    print("  ⚠️ checkpoint.json not found (normal - will be created at runtime)")

# Check path_execution.json in robodk
if os.path.exists("robodk/path_execution.json"):
    print("  ✅ robodk/path_execution.json exists")
else:
    print("  ❌ robodk/path_execution.json MISSING")

# Check SingleRobot.rdk in robodk
if os.path.exists("robodk/SingleRobot.rdk"):
    print("  ✅ robodk/SingleRobot.rdk exists")
else:
    print("  ❌ robodk/SingleRobot.rdk MISSING")

# Check README.md
if os.path.exists("README.md"):
    print("  ✅ README.md exists")
else:
    print("  ❌ README.md MISSING")

# Check .gitignore
if os.path.exists(".gitignore"):
    print("  ✅ .gitignore exists")
else:
    print("  ❌ .gitignore MISSING")

print("\n" + "="*60)
print("  CHECK COMPLETE")
print("="*60)

if failed == 0:
    print("\n✅ ALL FILES PASSED!")
else:
    print(f"\n⚠️ {failed} FILE(S) FAILED. Check errors above.")
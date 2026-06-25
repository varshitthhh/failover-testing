# ============================================================
# undo_intermediates.py
# Removes all IW_ targets from RoboDK station
# Run: python undo_intermediates.py
# RoboDK must be open with SingleRobot.rdk
# ============================================================

from robodk.robolink import Robolink, ITEM_TYPE_TARGET

def main():
    RDK = Robolink()
    if not RDK.Connect():
        print("[ERROR] Cannot connect to RoboDK")
        return

    targets = RDK.ItemList(ITEM_TYPE_TARGET)
    removed = []
    skipped = []

    for t in targets:
        name = t.Name()
        if name.startswith("IW_"):
            try:
                t.Delete()
                removed.append(name)
                print(f"[REMOVED] {name}")
            except Exception as e:
                skipped.append(name)
                print(f"[FAILED]  {name} — {e}")

    print(f"\n[DONE] Removed {len(removed)}, Failed {len(skipped)}")
    if skipped:
        print(f"  Failed: {skipped}")

if __name__ == "__main__":
    main()
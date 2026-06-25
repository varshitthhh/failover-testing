\# Program Crash - Failure Recovery Tests



\## Overview

This folder contains the \*\*Program Crash\*\* failure recovery tests for the BIW inspection system.



| Subfailure | Description | Status |

|------------|-------------|--------|

| 1 | RuntimeError mid-inspection | ✅ PASSED |

| 2 | MemoryError mid-inspection | ✅ PASSED |

| 3 | Corrupt checkpoint (cold restart) | ✅ PASSED |

| 4 | Hang - Watchdog timeout | ✅ PASSED |



\---



\## Files in This Folder



| File | Purpose |

|------|---------|

| `main.py` | Main inspection + recovery framework |

| `inject\_program\_crash.py` | Combined injector for ALL 4 subfailures |

| `inject\_base.py` | Shared helper functions |

| `inject\_memory\_crash.py` | Standalone MemoryError injector (optional) |



\---



\## How to Run



\### Terminal 1 (Main Inspection):

```powershell

python main.py

Wait until you see \[STATE] INSPECTING and robot starts moving.



Terminal 2 (Inject Failure):

powershell

python inject\_program\_crash.py

Menu Selection:

text

Run injection? (y/n): y



Subfailure number:

&#x20; 1. RuntimeError

&#x20; 2. MemoryError

&#x20; 3. Corrupt checkpoint

&#x20; 4. Hang - Watchdog



Inject at which pose?

&#x20; 1. \[09] Target 8a

&#x20; 2. \[14] Target 11

&#x20; 3. \[16] Target 13

&#x20; 4. \[23] Target 11a

&#x20; 5. All poses in sequence

Expected Behavior for Each Subfailure

Subfailure 1 - RuntimeError

Inject.py writes signal at target pose



Main.py detects PROGRAM\_CRASH with subfailure=1



Incremental retreat from failure pose to home



Stops at home and exits (RECOVERY\_COMPLETE\_STOPPED\_AT\_HOME)



Subfailure 2 - MemoryError

Inject.py writes signal at target pose



Main.py detects PROGRAM\_CRASH with subfailure=2



Incremental retreat from failure pose to home



Stops at home and exits (RECOVERY\_COMPLETE\_STOPPED\_AT\_HOME)



Subfailure 3 - Corrupt Checkpoint

Inject.py waits at pose BEFORE target



Corrupts checkpoint.json with garbage data



Auto-kills main.py (no Ctrl+C needed!)



Rerun python main.py



Main.py detects corrupt checkpoint



Prompts: Resume from checkpoint? (y/n):



Type y → resumes from failure pose → completes inspection



Type n → clears checkpoint → starts fresh



Subfailure 4 - Hang / Watchdog

Inject.py writes ROBOT\_STUCK signal at target pose



Main.py detects signal at next pose



Local offset applied (Z+50mm)



Incremental retreat from failure pose to home



Stops at home and exits (RECOVERY\_COMPLETE\_STOPPED\_AT\_HOME)



Key Features in main.py

python

\# 1. CHECKPOINT MANAGER - Saves state after each pose

class CheckpointManager:

&#x20;   def save(self, pose\_index, pose\_name, joints):

&#x20;       # Saves checkpoint.json after every successful move



\# 2. HEALTH MONITOR - Watchdog thread

class HealthMonitor:

&#x20;   def \_run(self):

&#x20;       # Detects stuck robot after 8 seconds

&#x20;       if elapsed > WATCHDOG\_TIMEOUT:

&#x20;           self.failure\_type = FailureType.ROBOT\_STUCK

&#x20;           self.failure\_event.set()



\# 3. RECOVERY PATH MANAGER - Incremental retreat

class RecoveryPathManager:

&#x20;   def retreat(self, from\_pose\_index):

&#x20;       # Steps back through execution\_path one pose at a time

&#x20;       for idx in range(from\_pose\_index - 1, -1, -1):

&#x20;           # Moves to each pose in reverse order

&#x20;           # Stops at Target 1 (home)



\# 4. RECOVERY MANAGER - Policy per failure

class RecoveryManager:

&#x20;   def \_recover\_power\_loss(self, pose\_index):

&#x20;       # Returns 'restart' for PROGRAM\_CRASH

&#x20;       retreat\_ok = self.rpm.retreat(pose\_index)

&#x20;       return "restart"



\# 5. INSPECTION EXECUTOR - Main loop

class InspectionExecutor:

&#x20;   def run(self):

&#x20;       while idx < len(execution\_path):

&#x20;           # 1. Check signal file BEFORE moving

&#x20;           sig\_type, sig\_sub = self.\_check\_signal\_file()

&#x20;           if sig\_type:

&#x20;               self.failure\_index = idx

&#x20;               self.hm.signal\_failure(sig\_type)

&#x20;           

&#x20;           # 2. Handle failure

&#x20;           if self.hm.failure\_event.is\_set():

&#x20;               action = self.\_handle\_failure(ftype, failure\_idx)

&#x20;               if action == "restart":

&#x20;                   # OPTION A: Stop at home, no re-inspection

&#x20;                   self.logger.info("RECOVERY\_COMPLETE\_STOPPED\_AT\_HOME")

&#x20;                   self.\_set\_state(State.COMPLETE)

&#x20;                   return

&#x20;           

&#x20;           # 3. Move to pose

&#x20;           self.\_move\_step(step)

Key Variables:

python

failure\_index = -1    # Stores where failure was detected

start\_index = 0       # Where to start inspection from

Errors We Faced \& Solutions

Error 1: Signal Detected at Wrong Index

Problem: Signal written at Target 8a but detected at Target 11

Cause: Signal file checked AFTER moving to next pose

Fix: Store failure\_index = idx when signal detected, use it for retreat



Error 2: Infinite Loop After Retreat

Problem: main.py kept looping between failure and home

Cause: failure\_index not cleared after restart

Fix: Set failure\_index = -1 after handling failure



Error 3: No Incremental Recovery

Problem: Robot jumped directly to home instead of stepping back

Cause: Retreat started from wrong index (0 instead of failure pose)

Fix: Use stored failure\_index for retreat start



Error 4: Corrupt Checkpoint - Ctrl+C Not Working

Problem: Ctrl+C wouldn't kill main.py

Cause: RoboDK blocking keyboard interrupts

Fix: Auto-kill main.py from inject script using taskkill



Error 5: Inject Script Running After main.py Finished

Problem: Inject.py corrupted checkpoint after inspection completed

Cause: User ran inject.py too late

Fix: Run inject.py WHILE main.py is running



Error 6: Signal Check Timing

Problem: Signal written at Target 11 but detected at Target 13

Cause: Inject.py wrote signal AFTER pose completed

Fix: Inject.py waits for pose\_index == idx-1 (pose BEFORE target)



Test Matrix

Subfailure	Pose 1 (8a)	Pose 2 (11)	Pose 3 (13)	Pose 4 (11a)	All Poses

1\. RuntimeError	✅	✅	✅	✅	✅

2\. MemoryError	✅	✅	✅	✅	✅

3\. Corrupt Checkpoint	✅	✅	✅	✅	⏳

4\. Hang/Watchdog	✅	✅	✅	✅	⏳

Next Steps

After Program Crash is fully tested:



IK Failure → inject\_ik\_failure.py



Robot Stuck → inject\_robot\_stuck.py



E-Stop → inject\_estop.py



Collision → inject\_collision.py



Network Down → inject\_network.py



Vehicle Shifted → inject\_vehicle\_shifted.py



Variant Changed → inject\_variant\_changed.py



Power Loss → inject\_power\_loss.py



Cascading → inject\_cascading.py



Version Info

Version	Date	Changes

v1.0	2026-06-25	Initial Program Crash tests complete

All 4 subfailures working

Auto-kill for corrupt checkpoint

Incremental retreat working

Stop at home, no re-inspection

Summary

✅ Program Crash - ALL 4 SUBFAILURES WORKING



RuntimeError ✅



MemoryError ✅



Corrupt Checkpoint ✅



Hang/Watchdog ✅


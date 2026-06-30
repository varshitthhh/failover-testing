# watchdog.py
# Production supervisor for main.py.
# Run THIS instead of running main.py directly.
#
# What it does:
#   - Launches main.py as a child process
#   - If main.py exits with a non-zero code (crash, killed, OOM-killed) -> restarts it
#   - If main.py exits with code 0 (clean COMPLETE or deliberate quit) -> stops
#   - Logs every restart with timestamp + exit code to watchdog_log.json
#   - Caps restart attempts to avoid infinite crash-loop (max 5 restarts in 10 min window)
#
# main.py's existing checkpoint.json / checkpoint.json.bak system handles
# WHERE to resume from. This script only handles WHETHER to restart at all.

import subprocess
import sys
import time
import json
from datetime import datetime

MAX_RESTARTS = 5
RESTART_WINDOW_SEC = 600  # 10 minutes
RESTART_DELAY_SEC = 3
LOG_FILE = "watchdog_log.json"


def log_event(event, **kwargs):
    entry = {"ts": datetime.now().isoformat(), "event": event, **kwargs}
    print(f"[WATCHDOG] {event} | {kwargs}")
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")


def main():
    restart_times = []

    log_event("WATCHDOG_STARTED")

    while True:
        log_event("LAUNCHING_MAIN")
        start_time = time.time()

        proc = subprocess.Popen([sys.executable, "main.py"])
        proc.wait()
        exit_code = proc.returncode

        if exit_code == 0:
            log_event("MAIN_EXITED_CLEAN", exit_code=exit_code)
            break

        log_event("MAIN_CRASHED", exit_code=exit_code)

        # Restart-rate limiting: drop restarts older than the window
        now = time.time()
        restart_times = [t for t in restart_times if now - t < RESTART_WINDOW_SEC]
        restart_times.append(now)

        if len(restart_times) > MAX_RESTARTS:
            log_event("RESTART_LIMIT_EXCEEDED",
                      restarts=len(restart_times), window_sec=RESTART_WINDOW_SEC)
            print(f"[WATCHDOG] Too many crashes ({len(restart_times)}) in "
                  f"{RESTART_WINDOW_SEC}s. Stopping. Manual intervention required.")
            break

        log_event("RESTARTING", delay_sec=RESTART_DELAY_SEC,
                  restart_count=len(restart_times))
        time.sleep(RESTART_DELAY_SEC)

    log_event("WATCHDOG_STOPPED")


if __name__ == "__main__":
    main()
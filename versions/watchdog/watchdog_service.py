# watchdog_service.py
# Windows Service wrapper around the existing watchdog.py restart-loop logic.
#
# Install:   python watchdog_service.py install
# Start:     python watchdog_service.py start   (or: net start BIWWatchdog)
# Stop:      python watchdog_service.py stop    (or: net stop BIWWatchdog)
# Remove:    python watchdog_service.py remove
# Debug run (no install, runs in console): python watchdog_service.py debug
#
# Behavior: identical restart/rate-limit logic to watchdog.py. On Windows
# service stop, the running main.py child is killed immediately (proc.kill()),
# matching real E-stop / power-loss semantics — main.py's own checkpoint.json
# system is responsible for safe resume, not this script.

import sys
import os
import time
import json
import subprocess
import servicemanager
import win32event
import win32service
import win32serviceutil
from datetime import datetime

MAX_RESTARTS = 5
RESTART_WINDOW_SEC = 600  # 10 minutes
RESTART_DELAY_SEC = 3
LOG_FILE = "watchdog_log.json"

# IMPORTANT: set this to the absolute path of the memory_monitor (or whichever
# versions/ folder) directory containing main.py, since a Windows Service does
# not inherit your terminal's current working directory.
WORKDIR = r"C:\Users\sriva\Downloads\failover-testing\versions\memory_monitor"

# IMPORTANT: sys.executable resolves to pythonservice.exe (the service host),
# not the real python.exe, when running inside a Windows Service. Must point
# directly at the conda env's python.exe.
PYTHON_EXE = r"C:\Users\sriva\anaconda3\envs\biwrecovery_py311\python.exe"


def log_event(event, **kwargs):
    entry = {"ts": datetime.now().isoformat(), "event": event, **kwargs}
    path = os.path.join(WORKDIR, LOG_FILE)
    with open(path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    try:
        servicemanager.LogInfoMsg(f"[WATCHDOG] {event} | {kwargs}")
    except Exception:
        pass


class BIWWatchdogService(win32serviceutil.ServiceFramework):
    _svc_name_ = "BIWWatchdog"
    _svc_display_name_ = "BIW Inspection Watchdog"
    _svc_description_ = "Supervises main.py for the BIW failure-recovery framework, auto-restarting on crash."

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.running = True
        self.current_proc = None

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        self.running = False
        # Immediate kill, per design decision — no graceful wait.
        if self.current_proc and self.current_proc.poll() is None:
            log_event("SERVICE_STOP_KILLING_CHILD", pid=self.current_proc.pid)
            self.current_proc.kill()
        win32event.SetEvent(self.stop_event)

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, "")
        )
        self.main_loop()

    def main_loop(self):
        restart_times = []
        os.chdir(WORKDIR)
        log_event("WATCHDOG_STARTED")

        while self.running:
            log_event("LAUNCHING_MAIN")

            self.current_proc = subprocess.Popen([PYTHON_EXE, "main.py"], cwd=WORKDIR)

            # Poll instead of blocking wait() so SvcStop can interrupt promptly.
            while self.current_proc.poll() is None and self.running:
                # Wait up to 1s for either stop signal or natural process exit.
                rc = win32event.WaitForSingleObject(self.stop_event, 1000)
                if rc == win32event.WAIT_OBJECT_0:
                    break  # stop requested

            if not self.running:
                break

            exit_code = self.current_proc.returncode
            if exit_code is None:
                # We were killed via SvcStop while still running.
                break

            if exit_code == 0:
                log_event("MAIN_EXITED_CLEAN", exit_code=exit_code)
                break

            log_event("MAIN_CRASHED", exit_code=exit_code)

            now = time.time()
            restart_times = [t for t in restart_times if now - t < RESTART_WINDOW_SEC]
            restart_times.append(now)

            if len(restart_times) > MAX_RESTARTS:
                log_event("RESTART_LIMIT_EXCEEDED",
                          restarts=len(restart_times), window_sec=RESTART_WINDOW_SEC)
                break

            log_event("RESTARTING", delay_sec=RESTART_DELAY_SEC,
                      restart_count=len(restart_times))
            time.sleep(RESTART_DELAY_SEC)

        log_event("WATCHDOG_STOPPED")


if __name__ == "__main__":
    win32serviceutil.HandleCommandLine(BIWWatchdogService)
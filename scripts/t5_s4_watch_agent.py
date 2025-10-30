# scripts/t5_s4_watch_agent.py
import os, sys, time, subprocess
from pathlib import Path

EVENTS_PATH = Path("data/runtime/insight_events.jsonl")
TPL_PATH    = Path("data/nudges/nudge_templates.json")
LOG_PATH = Path("data/logs/clarity_gain_samples.jsonl")

POLL_SEC = 1.0
DEBOUNCE_SEC = 0.75

def sig(path: Path):
    if not path.exists():
        return (False, 0, 0.0)
    st = path.stat()
    return (True, st.st_size, st.st_mtime)

def run_agent():
    print("[watch] change detected → running agent…")
    try:
        subprocess.check_call([sys.executable, "-u", "-m", "src.agent.t5_s4_agent_loop"])
        print("[watch] agent run complete.\n")
    except subprocess.CalledProcessError as e:
        print(f"[watch] agent run failed (exit {e.returncode}).")

def main():
    print("[watch] T5-S4 watch mode: monitoring events and templates (Ctrl+C to stop)")
    last_evt = sig(EVENTS_PATH)
    last_tpl = sig(TPL_PATH)
    last_log = sig(LOG_PATH)

    # Initial run (only if events exist)
    if last_evt[0] and last_evt[1] > 0:
        run_agent()
    else:
        print("[watch] waiting for events file to appear/populate…")

    last_trigger = 0.0
    while True:
        time.sleep(POLL_SEC)
        cur_evt = sig(EVENTS_PATH)
        cur_tpl = sig(TPL_PATH)
        cur_log = sig(LOG_PATH)

        changed = (cur_evt != last_evt) or (cur_tpl != last_tpl) or (cur_log != last_log)
        now = time.time()  # ← make sure this line is here!
        
        if changed and (now - last_trigger) >= DEBOUNCE_SEC:
            last_evt, last_tpl = cur_evt, cur_tpl, cur_log
            last_trigger = now
            run_agent()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[watch] stopped.")

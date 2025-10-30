import subprocess, sys, os, glob

def run(cmd):
    print(">>", " ".join(cmd)); subprocess.check_call(cmd)

if __name__ == "__main__":
    # 1) Ensure aggregates exist (assumes Stage 4 pipeline already ran)
    # 2) Emit insight events (reuses your existing hook)
    if not glob.glob("data/metrics/aggregates_*.json"):
        print("[warn] no aggregates found. Run your Stage 4 aggregator first.")
    run([sys.executable, "-u", "scripts/insight_engine_hook.py",
         "--in_json", "data/metrics/clarity_gain_dashboard.json",
         "--aggregates_glob", "data/metrics/aggregates_*.json",
         "--out_jsonl", "data/runtime/insight_events.jsonl"])
    # 3) Agent loop (single pass) → render cards + log actions
    run([sys.executable, "-u", "-m", "src.agent.t5_s4_agent_loop"])

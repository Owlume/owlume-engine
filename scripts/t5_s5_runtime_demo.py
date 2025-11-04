# scripts/t5_s5_runtime_demo.py
import argparse, importlib, os, sys, subprocess

def main():
    p = argparse.ArgumentParser(description="T5-S5 Runtime Demo (emit -> process -> open)")
    src = p.add_mutually_exclusive_group(required=True)
    src.add_argument("--text", type=str)
    src.add_argument("--file", type=str)
    p.add_argument("--auto-open", action="store_true")
    p.add_argument("--user", type=str, default=None)
    p.add_argument("--cg-pre", type=float, default=None)
    args = p.parse_args()

    # Ensure repo root is importable
    sys.path.insert(0, os.getcwd())

    # 1) Emit
    try:
        emitter = importlib.import_module("src.agent.event_emitter")
        if args.file:
            # Let the emitter CLI read the file path properly
            subprocess.check_call([sys.executable, "-u", "-m", "src.agent.event_emitter", "--file", args.file] + (
                ["--user", args.user] if args.user else []
            ) + (
                ["--cg-pre", str(args.cg_pre)] if args.cg_pre is not None else []
            ))
        else:
            emitter.emit_reflection(text=args.text, user=args.user, cg_pre=args.cg_pre)
    except ModuleNotFoundError:
        # Fallback: run as a module (works even without __init__.py, as long as src is on sys.path)
        cmd = [sys.executable, "-u", "-m", "src.agent.event_emitter"]
        if args.file:
            cmd += ["--file", args.file]
        else:
            cmd += ["--text", args.text]
        if args.user:
            cmd += ["--user", args.user]
        if args.cg_pre is not None:
            cmd += ["--cg-pre", str(args.cg_pre)]
        subprocess.check_call(cmd)

    # 2) Process once in runtime mode using the SIM loop
    agent = importlib.import_module("scripts.t5_s4_agent_loop_sim")
    if not hasattr(agent, "run_runtime_once"):
        print("[runtime_demo] Update scripts/t5_s4_agent_loop_sim.py with run_runtime_once().", file=sys.stderr)
        sys.exit(2)

    out = agent.run_runtime_once(auto_open=args.auto_open)
    if out and "did" in out:
        print(f"[runtime_demo] Processed NEW_REFLECTION did={out['did']} → nudge generated.")
    else:
        print("[runtime_demo] No output or nothing processed.")

if __name__ == "__main__":
    main()

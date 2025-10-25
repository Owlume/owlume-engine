# scripts/dashboard_watch.py
# Polls /data/metrics for new/changed aggregates_*.json and re-runs:
#   augment → mini_dashboard → chart_pack → (T4-S4) light HTML report
#   + (T5-S3) emit a nudge via generate_nudge.py

import os, time, glob, subprocess as s, hashlib, sys, json
from pathlib import Path
import importlib.util

# ─── Nudge Integration Settings ──────────────────────────────
ENABLE_NUDGES = True
NUDGE_CMD = [
    sys.executable, "-u", "scripts/generate_nudge.py",
    "--templates", "data/nudge_templates.json",
    "--history", "data/runtime/nudge_history.json",
    "--context", "data/runtime/nudge_context.json"
]
NUDGE_LOG = "data/runtime/nudges_emitted.jsonl"  # append-only log

# DEV ONLY: always fire a nudge & force daytime & print candidates
NUDGE_EXTRA = ["--ignore_cooldown", "--debug", "--now", "2025-10-21T13:40:00+11:00"]
# For production, switch to:  NUDGE_EXTRA = []

# Ensure UTF-8 console on Windows if possible
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
ROOT = SCRIPT_DIR.parent
METRICS_DIR = ROOT / "data" / "metrics"

# --- Robust local import of render_report.main ---
def _import_render_light_report():
    try:
        if str(SCRIPT_DIR) not in sys.path:
            sys.path.insert(0, str(SCRIPT_DIR))
        from render_report import main as render_light_report  # type: ignore
        return render_light_report
    except Exception:
        rr_path = SCRIPT_DIR / "render_report.py"
        spec = importlib.util.spec_from_file_location("render_report", rr_path)
        if spec and spec.loader:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)  # type: ignore[attr-defined]
            return getattr(mod, "main")
        raise ImportError("Could not import render_report.main")

render_light_report = _import_render_light_report()


def fingerprint(paths):
    """Create a stable hash over file paths + mtime + size."""
    h = hashlib.sha256()
    for p in sorted(paths):
        try:
            st = os.stat(p)
            h.update(p.encode("utf-8"))
            h.update(str(int(st.st_mtime)).encode("utf-8"))
            h.update(str(st.st_size).encode("utf-8"))
        except FileNotFoundError:
            continue
    return h.hexdigest()


def run(cmd):
    """Run a subprocess in the repo root with nice logging."""
    print("›", " ".join(cmd))
    s.check_call(cmd, cwd=str(ROOT))


# ─── T5-S3: Nudge emission helper ────────────────────────────
def emit_nudge():
    """Run the nudge generator after each new aggregate."""
    if not ENABLE_NUDGES:
        return None
    try:
        out = s.check_output(NUDGE_CMD + NUDGE_EXTRA, text=True, cwd=str(ROOT))
        data = json.loads(out)

        # Append to a running log
        os.makedirs(os.path.dirname(NUDGE_LOG), exist_ok=True)
        with open(ROOT / NUDGE_LOG, "a", encoding="utf-8") as f:
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

        # Compact console line
        sel = data.get("selected")
        if sel:
            print(f"[NUDGE] {sel['id']} • {sel['tone']} • reason={data.get('reason','')}")
        else:
            print(f"[NUDGE] (none) reason={data.get('reason','')}")
        return data
    except s.CalledProcessError as e:
        print("[NUDGE] generator failed:", e)
    except Exception as e:
        print("[NUDGE] unexpected error:", e)
    return None


def autorender_report():
    """Render the T4-S4 Light HTML report; never crash the watcher."""
    try:
        print("[T4-S4] Auto-rendering Light HTML Report…")
        render_light_report()  # generates reports/owlume_light_report_*.html
        print("[T4-S4] Report rendered.")
    except Exception as e:
        print(f"[T4-S4] Report render failed: {e}")


def main():
    pattern = str(METRICS_DIR / "aggregates_*.json")
    print("[watch] Monitoring:", os.path.abspath(pattern))
    last_fp = None

    while True:
        # ignore any *_aug.json
        paths = [p for p in glob.glob(pattern) if not p.endswith("_aug.json")]
        cur_fp = fingerprint(paths)

        if cur_fp != last_fp:
            print("\n== change detected ==")
            try:
                # 1) augment (produces *_aug.json or enriches aggregates)
                run([sys.executable, "-u", "scripts/augment_aggregates.py"])
                # 2) mini dashboard refresh (text/console snapshot)
                run([sys.executable, "-u", "scripts/mini_dashboard.py"])
                # 3) chart pack (PNG/SVG charts)
                run([sys.executable, "-u", "scripts/chart_pack.py"])
                print("✓ refreshed dashboard & charts")

                # 4) T4-S4: render light HTML
                autorender_report()

                # 5) T5-S3: emit a nudge
                emit_nudge()

                last_fp = cur_fp
            except s.CalledProcessError as e:
                print("! pipeline failed:", e)

        time.sleep(2.0)  # poll interval


if __name__ == "__main__":
    main()






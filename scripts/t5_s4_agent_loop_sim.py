import subprocess, sys, os, glob, json, webbrowser, hashlib
from datetime import datetime, timezone

RUNTIME_DIR = "data/runtime"
EVENTS_PATH = os.path.join(RUNTIME_DIR, "insight_events.jsonl")
NUDGES_PATH = os.path.join(RUNTIME_DIR, "nudges.jsonl")
USER_RESPONSES_PATH = os.path.join(RUNTIME_DIR, "user_responses.jsonl")
NUDGE_HTML = "reports/nudge_cards_demo.html"

def _now_iso():
    return datetime.now(timezone.utc).isoformat()

def _ensure_runtime_dirs():
    os.makedirs(RUNTIME_DIR, exist_ok=True)
    os.makedirs("reports", exist_ok=True)

def _tail_last_new_reflection():
    if not os.path.exists(EVENTS_PATH):
        return None
    last = None
    with open(EVENTS_PATH, "r", encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
                if rec.get("type") == "NEW_REFLECTION":
                    last = rec
            except Exception:
                continue
    return last

def _hash_text(s: str) -> str:
    return hashlib.sha256((s or "").encode("utf-8")).hexdigest()[:12]

def _append_jsonl(path, obj):
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")

def _append_min_card_html(card):
    _ensure_runtime_dirs()
    if not os.path.exists(NUDGE_HTML):
        with open(NUDGE_HTML, "w", encoding="utf-8") as f:
            f.write("<!doctype html><meta charset='utf-8'><title>Owlume Nudge Cards</title><body style='font-family:system-ui;margin:24px'>\n")
    html = f"""
<div style="border:1px solid #ddd;border-radius:12px;padding:16px;margin:12px 0;box-shadow:0 2px 8px rgba(0,0,0,.05)">
  <div style="font-size:12px;color:#666">{card['timestamp']}</div>
  <h3 style="margin:6px 0 10px">Clarity Card — {card['mode']} × {card['principle']}</h3>
  <p style="margin:6px 0 6px"><b>DID:</b> {card['did']} &nbsp; <b>Conf:</b> {card['conf']:.2f}</p>
  <p style="margin:6px 0 6px"><b>Prompt:</b> {card['nudge']}</p>
</div>
"""
    with open(NUDGE_HTML, "a", encoding="utf-8") as f:
        f.write(html)

def _detect_best(text: str):
    # Try real engine if available; otherwise simulate a reasonable pick.
    try:
        from src.elenx_engine import detect
        out = detect(text)
        mode = out.get("mode") or out.get("mode_detected") or "Analytical"
        principle = out.get("principle") or out.get("principle_detected") or "Clarity"
        conf = float(out.get("conf", 0.6))
        empathy_state = out.get("empathy_state", {"active": True})
        return {"mode": mode, "principle": principle, "conf": conf, "empathy_state": empathy_state}
    except Exception:
        return {"mode": "Analytical", "principle": "Assumption", "conf": 0.55, "empathy_state": {"active": True}}

def _make_nudge_text(mode: str, principle: str, text_hash: str):
    return f"What assumption might be distorting your {mode.lower()} reasoning here? (ref {text_hash})"

def run_runtime_once(auto_open: bool = False):
    """
    Processes the latest NEW_REFLECTION event once, generates a nudge card,
    appends logs, and optionally opens the HTML preview. Returns the card dict.
    """
    _ensure_runtime_dirs()
    ev = _tail_last_new_reflection()
    if not ev:
        return None

    text = ev.get("text", "")
    did = ev.get("did", "DID-unknown")
    user = ev.get("user", "local")
    text_hash = _hash_text(text)

    pick = _detect_best(text)
    nudge = _make_nudge_text(pick["mode"], pick["principle"], text_hash)

    card = {
        "type": "NUDGE_CARD",
        "timestamp": _now_iso(),
        "did": did,
        "user": user,
        "mode": pick["mode"],
        "principle": pick["principle"],
        "conf": float(pick["conf"]),
        "empathy_state": pick.get("empathy_state", {}),
        "nudge": nudge,
        "text_hash": text_hash,
    }

    # 1) write nudge, 2) append minimal HTML
    _append_jsonl(NUDGES_PATH, card)
    _append_min_card_html(card)

    # 3) append live response log (demo cg bump if cg_pre provided)
    cg_pre = ev.get("cg_pre", None)
    cg_post = None
    cg_delta = None
    if isinstance(cg_pre, (float, int)):
        cg_post = min(1.0, float(cg_pre) + 0.1)
        cg_delta = float(cg_post - cg_pre)

    _append_jsonl(USER_RESPONSES_PATH, {
        "timestamp": _now_iso(),
        "did": did,
        "user": user,
        "mode": pick["mode"],
        "principle": pick["principle"],
        "conf": float(pick["conf"]),
        "cg_pre": cg_pre,
        "cg_post": cg_post,
        "cg_delta": cg_delta,
    })

    if auto_open:
        try:
            webbrowser.open(os.path.abspath(NUDGE_HTML))
        except Exception:
            pass

    # Optional: simulate a SHARE hook when env var set
    if os.getenv("OWLUME_SIMULATE_SHARE", "0") == "1":
        path = "data/logs/dilemmanet_actions.jsonl"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        _append_jsonl(path, {
            "timestamp": _now_iso(),
            "action": "SHARE_CARD",
            "did": did,
            "card_id": text_hash,
            "source": "runtime_demo"
        })

    return card

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

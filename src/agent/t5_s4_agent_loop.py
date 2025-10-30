import json, time, re, os
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime, timezone
from jinja2 import Template  # available in ChatGPT env; if not, swap to simple replace
from src.render_card import write_clarity_card_md

TEMPLATES_PATH = Path("data/nudges/nudge_templates.json")
EVENTS_PATH    = Path("data/runtime/insight_events.jsonl")
OUT_CARDS_HTML = Path("reports/nudge_cards_demo.html")
USER_RESP_LOG  = Path("data/runtime/user_responses.jsonl")
LOG_JSONL = Path("data/logs/clarity_gain_samples.jsonl")

def load_record_by_did(did: str):
    if not LOG_JSONL.exists():
        return None
    with LOG_JSONL.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line=line.strip()
            if not line: 
                continue
            try:
                os.startfile(str(path))
                rec=json.loads(line)
                if str(rec.get("did") or rec.get("id")) == did:
                    return rec
            except Exception:
                pass
    return None


# --- tiny expression evaluator for "when" ---
def match_when(expr: str, event: Dict[str, Any]) -> bool:
    # only support "event.type == '...'"
    m = re.fullmatch(r"event\.type\s*==\s*'([^']+)'", expr.strip())
    return bool(m and event.get("type") == m.group(1))

def load_templates() -> List[Dict[str, Any]]:
    data = json.loads(TEMPLATES_PATH.read_text(encoding="utf-8"))
    return data.get("templates", [])

def iter_events():
    # NOTE: utf-8-sig eats a BOM if present (Windows-safe)
    with EVENTS_PATH.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def render_template_str(s: str, ctx: Dict[str, Any]) -> str:
    return Template(s).render(**ctx)

def build_card(evt: Dict[str, Any], tpl: Dict[str, Any]) -> Dict[str, Any]:
    ctx = dict(evt)
    return {
        "did": evt.get("did",""),
        "mode": evt.get("mode",""),
        "principle": evt.get("principle",""),
        "cg_delta": evt.get("cg_delta"),          # ← add this line
        "title": render_template_str(tpl["title"], ctx),
        "subtitle": render_template_str(tpl["subtitle"], ctx),
        "actions": tpl.get("actions",[])
    }

def pick_templates_for(evt: Dict[str, Any], templates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    hits=[]
    for t in templates:
        if match_when(t.get("when",""), evt):
            hits.append(t)
    return hits

def simulate_user_response(card: Dict[str, Any]) -> Dict[str, Any]:
    from datetime import datetime, timezone
    actions = card.get("actions", [])
    choice = None

    # Prefer SHARE_CARD for the demo so a Clarity Card always generates
    for a in actions:
        if a.get("type") == "SHARE_CARD":
            choice = a
            break

    # If no SHARE_CARD, fall back to REPLAY
    if choice is None:
        for a in actions:
            if a.get("type") == "REPLAY":
                choice = a
                break

    # If still nothing, just pick the first action
    if choice is None and actions:
        choice = actions[0]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "did": card.get("did", ""),
        "action_id": choice.get("id") if choice else None,
        "action_type": choice.get("type") if choice else None,
        "mode": card.get("mode", ""),
        "principle": card.get("principle", "")
    }

def append_user_response(resp: Dict[str, Any]):
    USER_RESP_LOG.parent.mkdir(parents=True, exist_ok=True)
    with USER_RESP_LOG.open("a", encoding="utf-8") as f:
        f.write(json.dumps(resp, ensure_ascii=False)+"\n")

def run_once() -> List[Dict[str, Any]]:
    templates = load_templates()
    cards=[]
    for evt in iter_events():
        for t in pick_templates_for(evt, templates):
            cards.append(build_card(evt, t))
    return cards

if __name__ == "__main__":
    from src.ui_utils_nudge import render_nudge_cards
    cards = run_once()
    if not cards:
        print("[T5-S4] no cards to render (no matching events)"); exit(0)
    path = render_nudge_cards(cards, OUT_CARDS_HTML)
    print(f"[T5-S4] rendered {len(cards)} card(s) → {path}")
    
    # simulate one click per card
for c in cards:
    resp = simulate_user_response(c)
    append_user_response(resp)

    # If the simulated action is SHARE_CARD → generate Markdown Clarity Card
    if resp.get("action_type") == "SHARE_CARD":
        did = resp.get("did") or "unknown"

        # ✅ Try to load the full record by DID; fall back to minimal stub if missing
        rec = load_record_by_did(did)
        record = rec if rec else {
            "mode_detected": c.get("mode"),
            "principle_detected": c.get("principle"),
            "cg_delta": c.get("cg_delta"),
            "did": did,
            "timestamp": resp.get("timestamp"),
            "empathy_state": None
        }

        out_md = Path("reports/clarity_cards") / f"clarity_card_{did}.md"
        write_clarity_card_md(record, out_md)

        # add artifact path to response for traceability
        resp["artifact"] = str(out_md)
        append_user_response(resp)
        print(f"[T5-S4] SHARE_CARD → wrote {out_md}")


    print(f"[T5-S4] logged {len(cards)} user action(s) → {USER_RESP_LOG}")

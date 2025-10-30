from pathlib import Path
import json, html

HTML_FRAME = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>{title}</title>
<style>
  body{{font-family:ui-sans-serif,system-ui;margin:24px}}
  .card{{border:1px solid #ddd;border-radius:16px;padding:16px;margin:12px 0;box-shadow:0 2px 6px rgba(0,0,0,.06)}}
  .title{{font-weight:700;font-size:18px;margin-bottom:6px}}
  .subtitle{{color:#555;margin-bottom:12px}}
  .actions a{{display:inline-block;padding:8px 12px;border-radius:12px;border:1px solid #ccc;margin-right:8px;text-decoration:none}}
  .meta{{font-size:12px;color:#777;margin-top:8px}}
</style></head><body>
<h1>{h1}</h1>
{cards}
</body></html>"""


def render_nudge_cards(cards, out_html: Path):
    blocks=[]
    for c in cards:
        actions_html = "".join([f"<a href='#{html.escape(a.get('id',''))}'>{html.escape(a.get('label',''))}</a>" for a in c.get("actions",[])])
        blocks.append(
            f"<div class='card'>"
            f"<div class='title'>{html.escape(c.get('title',''))}</div>"
            f"<div class='subtitle'>{html.escape(c.get('subtitle',''))}</div>"
            f"<div class='actions'>{actions_html}</div>"
            f"<div class='meta'>did={html.escape(c.get('did',''))} · mode={html.escape(c.get('mode',''))} · principle={html.escape(c.get('principle',''))}</div>"
            f"</div>"
        )
    out_html.parent.mkdir(parents=True, exist_ok=True)
    out_html.write_text(HTML_FRAME.format(title="Nudge Cards", h1="Nudge Cards", cards="".join(blocks)), encoding="utf-8")
    return str(out_html)

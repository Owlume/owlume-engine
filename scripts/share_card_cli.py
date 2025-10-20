import json, sys, datetime, argparse, re

def iso_now():
    return datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00","Z")

def main():
    ap = argparse.ArgumentParser(description="Mark a record as shared (opt-in) in a JSONL file")
    ap.add_argument("jsonl", help="path to JSONL (e.g., data/logs/clarity_gain_samples_full.jsonl)")
    ap.add_argument("--session_id", help="exact session_id to update (e.g., SES-DID-2025-0014)")
    ap.add_argument("--did", help="DID to match either obj['did'] or the suffix of session_id (e.g., DID-2025-0014)")
    ap.add_argument("--index", type=int, help="1-based line index to update (fallback)")
    ap.add_argument("--channel", choices=["markdown","image"], default="markdown")
    ap.add_argument("--dry", action="store_true", help="print result to stdout without writing file")
    args = ap.parse_args()

    if not (args.session_id or args.did or args.index):
        print("[ERR] Provide one of --session_id, --did, or --index")
        sys.exit(1)

    updated_lines = []
    found = False

    with open(args.jsonl, "r", encoding="utf-8") as f:
        for n, line in enumerate(f, 1):
            s = line.strip()
            if not s:
                continue
            obj = json.loads(s)

            match = False
            # 1) Exact session_id
            if args.session_id and obj.get("session_id") == args.session_id:
                match = True
            # 2) DID: match top-level 'did' if present OR session_id suffix
            elif args.did:
                if obj.get("did") == args.did:
                    match = True
                else:
                    sid = obj.get("session_id","")
                    if sid.endswith(args.did):
                        match = True
            # 3) Index fallback (1-based)
            elif args.index and args.index == n:
                match = True

            if match:
                obj.setdefault("share", {})
                obj["share"] = {
                    "status": "opt_in",
                    "channel": args.channel,
                    "consent": True,
                    "timestamp": iso_now()
                }
                found = True

            updated_lines.append(json.dumps(obj, ensure_ascii=False))

    if not found:
        print("[WARN] No record matched your selector "
              f"({'--session_id ' + args.session_id if args.session_id else ''}"
              f"{' --did ' + args.did if args.did else ''}"
              f"{' --index ' + str(args.index) if args.index else ''}).")

    if args.dry:
        print("\n".join(updated_lines))
    else:
        with open(args.jsonl, "w", encoding="utf-8") as w:
            w.write("\n".join(updated_lines) + "\n")
        target = args.session_id or args.did or f"index={args.index}"
        print(f"[OK] updated {args.jsonl} (target={target}, channel={args.channel})")

if __name__ == "__main__":
    main()


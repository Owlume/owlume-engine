# L1 — Auto-Learning Loop

This loop periodically:
1) Aggregates metrics from `data/logs/*.jsonl` into `data/metrics/aggregates_*.json`.
2) Updates adaptive weights in `data/metrics/learned_weights.json` using EWMA + tempered softmax.
3) Commits changes if the update crosses a minimum-change threshold.

## Signals used
- `avg_delta` (Clarity Gain)
- `empathy_activation_rate`
- `n_records`
- `top_mode_principle_counts` (sparse counts for both Mode and Principle)

## Guardrails
- **Clamp**: weights ∈ [0.6, 1.6]
- **Softmax (T=0.25)**: normalizes relative shape while keeping mean ≈ 1.0
- **Min-change**: no commit when max change < 0.01
- **Empathy band**: keeps activation in ~15–35% unless data push otherwise

## Manual run
- VS Code: “L1 — Update weights now”
- GitHub Actions: **Actions → L1 — Auto-Learning Loop → Run workflow**

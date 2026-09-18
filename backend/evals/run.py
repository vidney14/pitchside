"""Run the agent against every labelled scenario and score it.

Usage:
    python -m evals.run
    python -m evals.run --provider gemini
    python -m evals.run --scenarios 1,4,13
"""
import argparse
import json
import time
from datetime import datetime
from pathlib import Path

from agent.cases import capture_failure
from agent.heal import heal
from pipeline.poison import SCENARIOS

RESULTS_DIR = Path(__file__).parent / "results"


def run_one(sid: int, provider: str) -> dict:
    expected = SCENARIOS[sid]["expected_action"]
    start = time.time()
    try:
        case = capture_failure(sid)
        result = heal(case, provider=provider)
        p = result["proposal"]
        actual = p.action if result["healed"] else "escalate"
        error = None
    except Exception as exc:
        error = str(exc)[:150]
        actual = "rate_limited" if "429" in error else "crash"
        p = None

    return {
        "scenario": sid,
        "name": SCENARIOS[sid]["name"],
        "expected": expected,
        "actual": actual,
        "correct": actual == expected,
        "confidence": round(p.confidence, 2) if p else None,
        "seconds": round(time.time() - start, 1),
        "error": error,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--provider", default="groq")
    ap.add_argument("--scenarios", default="")
    ap.add_argument("--pause", type=float, default=8.0, help="seconds between scenarios (rate limits)")
    args = ap.parse_args()

    ids = [int(s) for s in args.scenarios.split(",") if s.strip()] or sorted(SCENARIOS)
    rows = []
    for sid in ids:
        row = run_one(sid, args.provider)
        rows.append(row)
        mark = "OK  " if row["correct"] else "WRONG"
        print(f"{mark} {sid:>2} | exp {row['expected']:<18} got {row['actual']:<18} {row['seconds']}s")
        time.sleep(args.pause)

    scored = [r for r in rows if r["actual"] not in ("rate_limited", "crash")]
    skipped = len(rows) - len(scored)
    total = len(scored)
    correct = sum(r["correct"] for r in scored)
    should_esc = [r for r in scored if r["expected"] == "escalate"]
    esc_caught = sum(r["actual"] == "escalate" for r in should_esc)
    unsafe = [r for r in scored if r["expected"] == "escalate" and r["actual"] != "escalate"]

    print("\n" + "=" * 60)
    print(f"provider:            {args.provider}")
    if total == 0:
        print("no scored results (everything was rate-limited or crashed)")
    else:
        print(f"fix accuracy:        {correct}/{total} = {correct/total:.0%}")
        print(f"escalation recall:   {esc_caught}/{len(should_esc)} = {esc_caught/len(should_esc):.0%}" if should_esc else "escalation recall:   n/a (no escalate cases scored)")
        print(f"unsafe actions:      {len(unsafe)}  {[r['scenario'] for r in unsafe]}")
        print(f"mean latency:        {sum(r['seconds'] for r in scored)/total:.1f}s")
    print(f"skipped (rate limit/crash): {skipped}")

    RESULTS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    out = RESULTS_DIR / f"{args.provider}-{stamp}.json"
    out.write_text(json.dumps({"provider": args.provider, "rows": rows}, indent=2))
    print(f"saved: {out}")


if __name__ == "__main__":
    main() 
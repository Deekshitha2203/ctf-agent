import json, argparse, math, csv
from collections import defaultdict

def load(results_path):
    rows = []
    with open(results_path) as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows

def sample_sd(outcomes):
    n = len(outcomes)
    if n < 2:
        return None
    p = sum(outcomes) / n
    var = sum((x - p) ** 2 for x in outcomes) / (n - 1)
    return 100 * math.sqrt(var)

def summarize(rows, config_id="agent"):
    rows = [r for r in rows if r.get("config_id") == config_id]
    by_chal = defaultdict(list)
    for r in rows:
        by_chal[r["challenge_id"]].append(r)

    per_challenge = []
    total_success, total_attempts = 0, 0
    for cid, attempts in sorted(by_chal.items()):
        outcomes = [1 if a.get("verified") else 0 for a in attempts]
        n = len(outcomes)
        succ = sum(outcomes)
        rate = 100 * succ / n if n else None
        toks = [a.get("total_tokens") or 0 for a in attempts]
        secs = [a.get("elapsed_s") or 0 for a in attempts]
        per_challenge.append({
            "challenge_id": cid,
            "attempts": n,
            "successes": succ,
            "success_rate_pct": round(rate, 1) if rate is not None else None,
            "sample_sd_pp": round(sample_sd(outcomes), 1) if sample_sd(outcomes) is not None else None,
            "mean_total_tokens": round(sum(toks) / n, 1) if n else None,
            "mean_wall_s": round(sum(secs) / n, 1) if n else None,
        })
        total_success += succ
        total_attempts += n

    overall = round(100 * total_success / total_attempts, 1) if total_attempts else None

    # pass@k: fraction of challenges solved at least once within first k trials
    passk = {}
    for k in (1, 2, 3):
        solved = 0
        for cid, attempts in by_chal.items():
            first_k = sorted(attempts, key=lambda a: a.get("trial", 0))[:k]
            if any(a.get("verified") for a in first_k):
                solved += 1
        passk[f"pass@{k}"] = round(100 * solved / len(by_chal), 1) if by_chal else None

    return {
        "config_id": config_id,
        "n_challenges": len(by_chal),
        "total_attempts": total_attempts,
        "overall_success_rate_pct": overall,
        "pass_at_k": passk,
        "per_challenge": per_challenge,
    }

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="results/results.jsonl")
    ap.add_argument("--config", default="agent")
    ap.add_argument("--out", default="results/summary.json")
    ap.add_argument("--csv", default="results/per_challenge.csv")
    args = ap.parse_args()

    rows = load(args.results)
    s = summarize(rows, args.config)
    with open(args.out, "w") as f:
        json.dump(s, f, indent=2)

    cols = ["challenge_id", "attempts", "successes", "success_rate_pct",
            "sample_sd_pp", "mean_total_tokens", "mean_wall_s"]
    with open(args.csv, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        for pc in s["per_challenge"]:
            w.writerow(pc)

    print(json.dumps(s, indent=2))
    print(f"\nWrote {args.out} and {args.csv}")

if __name__ == "__main__":
    main()

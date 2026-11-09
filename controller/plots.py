import json, argparse
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", default="results/summary.json")
    ap.add_argument("--outdir", default="results")
    args = ap.parse_args()

    s = json.load(open(args.summary))
    pc = s["per_challenge"]
    if not pc:
        print("no data"); return
    ids = [p["challenge_id"] for p in pc]

    # 1. success rate + SD per challenge
    rates = [p["success_rate_pct"] or 0 for p in pc]
    sds = [p["sample_sd_pp"] or 0 for p in pc]
    fig, ax = plt.subplots(figsize=(max(6, len(ids)*0.7), 4))
    ax.bar(ids, rates, yerr=sds, capsize=4, color="#4C72B0")
    ax.set_ylabel("Success rate (%)"); ax.set_ylim(0, 105)
    ax.set_title("Success rate by challenge (error bars = sample SD, pp)")
    plt.xticks(rotation=45, ha="right"); plt.tight_layout()
    plt.savefig(f"{args.outdir}/success_rate.png", dpi=120); plt.close()

    # 2. mean tokens per challenge
    toks = [p["mean_total_tokens"] or 0 for p in pc]
    fig, ax = plt.subplots(figsize=(max(6, len(ids)*0.7), 4))
    ax.bar(ids, toks, color="#55A868")
    ax.set_ylabel("Mean total tokens"); ax.set_title("Mean token usage by challenge")
    plt.xticks(rotation=45, ha="right"); plt.tight_layout()
    plt.savefig(f"{args.outdir}/tokens.png", dpi=120); plt.close()

    # 3. mean wall-clock per challenge
    secs = [p["mean_wall_s"] or 0 for p in pc]
    fig, ax = plt.subplots(figsize=(max(6, len(ids)*0.7), 4))
    ax.bar(ids, secs, color="#C44E52")
    ax.set_ylabel("Mean wall-clock (s)"); ax.set_title("Mean solve time by challenge")
    plt.xticks(rotation=45, ha="right"); plt.tight_layout()
    plt.savefig(f"{args.outdir}/wall_time.png", dpi=120); plt.close()

    # 4. pass@k
    pk = s["pass_at_k"]
    ks = list(pk.keys()); vs = [pk[k] or 0 for k in ks]
    fig, ax = plt.subplots(figsize=(4, 4))
    ax.plot(ks, vs, marker="o", color="#8172B3")
    ax.set_ylabel("Challenges solved (%)"); ax.set_ylim(0, 105)
    ax.set_title("Pass@k")
    plt.tight_layout(); plt.savefig(f"{args.outdir}/pass_at_k.png", dpi=120); plt.close()

    print("Wrote success_rate.png, tokens.png, wall_time.png, pass_at_k.png to", args.outdir)

if __name__ == "__main__":
    main()

import os, json, time, shutil, argparse, datetime
from pathlib import Path
from controller import config
from controller.challenge import Challenge
from controller.evaluator import Evaluator
from controller.trace import Trace
from agent.sandbox import LocalSandbox
from agent.tools import ToolDispatcher, TOOL_SCHEMAS
from agent.agent_loop import Agent

DATASET = "external/CTFTiny/ctftiny.json"

def run_attempt(challenge_id, trial, model, results_path):
    run_id = f"{challenge_id}-t{trial}-{int(time.time())}"
    ws = f"workspaces/{run_id}"
    shutil.rmtree(ws, ignore_errors=True)            # fresh workspace
    trace_path = f"traces/{run_id}.jsonl"

    c = Challenge(DATASET, challenge_id)
    inv = c.stage_files(ws)
    t = Trace(trace_path, run_id)
    t.log("attempt_begin", challenge_id=challenge_id, trial=trial,
          category=c.category, model=model, file_inventory=inv,
          config=config.snapshot())

    sb = LocalSandbox(ws, timeout=config.TOOL_TIMEOUT_SECONDS,
                      max_output=config.MAX_TOOL_OUTPUT_CHARS)
    ev = Evaluator(c.expected_flag(), trace=t)
    disp = ToolDispatcher(sb, ev, t)
    ag = Agent(os.environ["LITELLM_TOKEN"], config.BASE_URL, model, disp, t, config)

    res = ag.run(c.solver_context(), TOOL_SCHEMAS)
    t.close()

    row = {
        "run_id": run_id, "config_id": config.CONFIG_ID,
        "challenge_id": challenge_id, "trial": trial,
        "status": res["status"], "verified": res["status"] == "solved",
        "elapsed_s": res["elapsed_s"],
        "total_tokens": res["total_tokens"],
        "input_tokens": res.get("input_tokens"),
        "output_tokens": res.get("output_tokens"),
        "cost_usd": round((res.get("input_tokens",0)/1e6)*config.PRICE_IN_PER_MTOK + (res.get("output_tokens",0)/1e6)*config.PRICE_OUT_PER_MTOK, 6),
        "steps": res["steps"],
        "model": model,
        "trace_file": trace_path,
        "sample_type": "live",
        "ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    with open(results_path, "a") as f:
        f.write(json.dumps(row) + "\n")
    return row

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--challenges", nargs="+", required=True)
    ap.add_argument("--trials", type=int, default=3)
    ap.add_argument("--model", default=config.MODEL)
    ap.add_argument("--results", default="results/results.jsonl")
    ap.add_argument("--sleep", type=float, default=5.0,
                    help="seconds between attempts to avoid rate limits")
    args = ap.parse_args()

    Path("results").mkdir(exist_ok=True)
    print(f"Running {len(args.challenges)} challenge(s) x {args.trials} trials on {args.model}")
    for cid in args.challenges:
        for trial in range(1, args.trials + 1):
            print(f"  {cid} trial {trial} ...", end=" ", flush=True)
            try:
                row = run_attempt(cid, trial, args.model, args.results)
                print(f"{row['status']}  ({row['elapsed_s']}s, {row['total_tokens']} tok)")
            except Exception as e:
                print(f"FAILED: {e}")
            time.sleep(args.sleep)
    print(f"\nDone. Results -> {args.results}")

if __name__ == "__main__":
    main()

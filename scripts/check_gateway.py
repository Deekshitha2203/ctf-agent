import os, sys, json, requests

TOKEN = os.environ.get("LITELLM_TOKEN")
BASE = os.environ.get("LITELLM_BASE_URL", "").rstrip("/")
if not TOKEN or not BASE:
    sys.exit("Set LITELLM_TOKEN and LITELLM_BASE_URL (run: source .env)")
H = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
API = BASE if BASE.endswith("/v1") else BASE + "/v1"

r = requests.get(f"{API}/models", headers=H, timeout=30)
print("models status:", r.status_code)
if r.status_code != 200:
    sys.exit(r.text[:500])
ids = [m["id"] for m in r.json().get("data", [])]
print("available models:"); [print("  ", i) for i in ids]

model = sys.argv[1] if len(sys.argv) > 1 else None
if not model:
    sys.exit("\nRe-run with a model id to test tool calling:  python scripts/check_gateway.py <model-id>")

tools = [{"type": "function", "function": {
    "name": "run_command",
    "description": "Run a shell command and return its output.",
    "parameters": {"type": "object",
                   "properties": {"cmd": {"type": "string"}},
                   "required": ["cmd"]}}}]
body = {"model": model, "max_tokens": 200, "tools": tools,
        "messages": [{"role": "user", "content": "List the files in the current directory using the tool."}]}
r = requests.post(f"{API}/chat/completions", headers=H, json=body, timeout=60)
print("\nchat status:", r.status_code)
data = r.json()
msg = data.get("choices", [{}])[0].get("message", {})
print("tool_calls:", json.dumps(msg.get("tool_calls"), indent=2))
print("usage:", data.get("usage"))
print("\nTOOL CALLING WORKS" if msg.get("tool_calls") else "\nNO TOOL CALL - try another model")

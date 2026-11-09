import os

CONFIG_ID = "agent"
MODEL = os.environ.get("CTF_MODEL", "claude-sonnet-5-5")
BASE_URL = os.environ.get("LITELLM_BASE_URL", "https://litellm.oit.duke.edu/v1").rstrip("/")

# Hard limits enforced in code (assignment requirement)
MAX_STEPS = 40                # model calls per attempt
MAX_WALL_SECONDS = 20 * 60    # 20 min per attempt
MAX_TOTAL_TOKENS = 600_000    # input + output per attempt
MAX_OUTPUT_TOKENS = 4096      # per model response

# Tool limits
TOOL_TIMEOUT_SECONDS = 60
MAX_TOOL_OUTPUT_CHARS = 8000  # truncate long outputs, log the truncation

# Solver sandbox
SOLVER_IMAGE = "ctf-solver:latest"
SOLVER_PLATFORM = "linux/amd64"

def snapshot():
    """Everything that defines this configuration, saved with every run."""
    return {k: v for k, v in globals().items()
            if k.isupper() and "TOKEN" not in k.replace("TOKENS", "")}

# Haiku 5.5 pricing (<=100k prompt tier), USD per 1M tokens. Update if gateway differs.
PRICE_IN_PER_MTOK = 0.10
PRICE_OUT_PER_MTOK = 0.50

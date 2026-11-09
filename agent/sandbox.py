import subprocess, shlex, os
from pathlib import Path

class LocalSandbox:
    """DEV ONLY. Runs commands in a subprocess scoped to the workspace dir.
    Does NOT provide network isolation. Replace with DockerSandbox for scored runs."""
    isolated = False

    def __init__(self, workspace_dir, timeout=60, max_output=8000):
        self.workspace = Path(workspace_dir).resolve()
        self.workspace.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout
        self.max_output = max_output

    def exec(self, command):
        """Returns dict: stdout, stderr, exit_code, timed_out, truncated."""
        try:
            p = subprocess.run(
                ["bash", "-lc", command],
                cwd=str(self.workspace),
                capture_output=True, text=True,
                timeout=self.timeout,
                env={"PATH": os.environ.get("PATH", ""), "HOME": str(self.workspace)},
            )
            out, err, code, to = p.stdout, p.stderr, p.returncode, False
        except subprocess.TimeoutExpired as e:
            out = e.stdout or ""
            err = (e.stderr or "") + f"\n[TIMEOUT after {self.timeout}s]"
            code, to = 124, True
        if isinstance(out, bytes): out = out.decode("utf-8", "replace")
        if isinstance(err, bytes): err = err.decode("utf-8", "replace")
        combined = out + (("\n[stderr]\n" + err) if err.strip() else "")
        truncated = len(combined) > self.max_output
        if truncated:
            h = self.max_output // 2
            combined = combined[:h] + f"\n...[TRUNCATED {len(combined)-self.max_output} chars]...\n" + combined[-h:]
        return {"output": combined, "exit_code": code,
                "timed_out": to, "truncated": truncated}

    def read_file(self, filename):
        p = (self.workspace / filename).resolve()
        if not str(p).startswith(str(self.workspace)):
            return {"error": "path escapes workspace"}
        if not p.exists():
            return {"error": f"no such file: {filename}"}
        data = p.read_bytes()[: self.max_output]
        try:
            return {"content": data.decode("utf-8")}
        except UnicodeDecodeError:
            return {"content": data.hex(), "encoding": "hex"}

    def reset(self):
        pass  # workspace is recreated fresh per attempt by the controller

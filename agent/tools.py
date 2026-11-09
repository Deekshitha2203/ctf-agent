# Tool schemas sent to the model (OpenAI/Anthropic tool-calling format)
TOOL_SCHEMAS = [
    {"type": "function", "function": {
        "name": "run_command",
        "description": "Run a bash command inside the isolated solver workspace. "
                       "Use for analyzing files, running scripts, decoding, etc. "
                       "No internet access. Returns combined stdout/stderr and exit code.",
        "parameters": {"type": "object", "properties": {
            "command": {"type": "string", "description": "The bash command to run."}
        }, "required": ["command"]}}},
    {"type": "function", "function": {
        "name": "read_file",
        "description": "Read a file from the solver workspace by name. "
                       "Returns UTF-8 text, or hex if the file is binary.",
        "parameters": {"type": "object", "properties": {
            "filename": {"type": "string", "description": "File name relative to the workspace."}
        }, "required": ["filename"]}}},
    {"type": "function", "function": {
        "name": "submit_flag",
        "description": "Submit a candidate flag for verification. Call this ONLY when you "
                       "believe you have found the flag. The result tells you if it was correct.",
        "parameters": {"type": "object", "properties": {
            "flag": {"type": "string", "description": "The candidate flag, e.g. flag{...}"}
        }, "required": ["flag"]}}},
]

class ToolDispatcher:
    """Validates tool calls and routes them. submit_flag goes to the controller's
    evaluator; everything else goes to the solver sandbox."""
    def __init__(self, sandbox, evaluator, trace):
        self.sandbox = sandbox
        self.evaluator = evaluator
        self.trace = trace

    def dispatch(self, name, args):
        if name == "run_command":
            cmd = args.get("command")
            if not isinstance(cmd, str) or not cmd.strip():
                return {"error": "command must be a non-empty string"}
            self.trace.log("tool_call", tool=name, command=cmd)
            r = self.sandbox.exec(cmd)
            self.trace.log("tool_result", tool=name, exit_code=r["exit_code"],
                           timed_out=r["timed_out"], truncated=r["truncated"],
                           output=r["output"])
            return r

        if name == "read_file":
            fn = args.get("filename")
            if not isinstance(fn, str) or not fn.strip():
                return {"error": "filename must be a non-empty string"}
            self.trace.log("tool_call", tool=name, filename=fn)
            r = self.sandbox.read_file(fn)
            self.trace.log("tool_result", tool=name, result_keys=list(r.keys()),
                           output=r.get("content", r.get("error", "")))
            return r

        if name == "submit_flag":
            flag = args.get("flag")
            if not isinstance(flag, str) or not flag.strip():
                return {"error": "flag must be a non-empty string"}
            self.trace.log("tool_call", tool=name)   # do not log raw flag
            verified = self.evaluator.verify(flag)
            return {"verified": verified,
                    "message": "Correct flag, challenge solved." if verified
                               else "Incorrect flag."}

        return {"error": f"unknown tool: {name}"}

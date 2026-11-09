import hashlib

class Evaluator:
    """Trusted flag verifier. Lives controller-side only.
    The solver calls submit_flag(); it never sees the expected value."""
    def __init__(self, expected_flag, trace=None):
        self._expected = (expected_flag or "").strip()
        self._exp_hash = hashlib.sha256(self._expected.encode()).hexdigest()
        self.trace = trace
        self.submissions = []

    def _normalize(self, flag):
        f = (flag or "").strip()
        # accept either "flag{...}" or bare "..." to be lenient on wrapping
        return f

    def verify(self, candidate):
        cand = self._normalize(candidate)
        verified = (cand == self._expected)
        # fallback: match if the inner content is identical ignoring flag{ } wrapper
        if not verified and self._expected:
            def inner(s):
                s = s.strip()
                if s.lower().startswith("flag{") and s.endswith("}"):
                    return s[5:-1]
                return s
            verified = inner(cand) == inner(self._expected) and inner(cand) != ""
        record = {
            "candidate_sha256": hashlib.sha256(cand.encode()).hexdigest(),
            "candidate_len": len(cand),
            "verified": verified,
        }
        self.submissions.append(record)
        if self.trace:
            # log WITHOUT the expected flag or the raw candidate
            self.trace.log("flag_submission", **record)
        return verified

import hashlib, json, shutil
from pathlib import Path
from nyuctf.dataset import CTFDataset
from nyuctf.challenge import CTFChallenge

# Files/dirs that must NEVER reach the solver (hold answers or server internals)
FORBIDDEN = {"challenge.json", "test_solver", "docker-compose.yml",
             "Dockerfile", ".git", "flag", "flag.txt"}

class Challenge:
    """Controller-side wrapper. Holds the flag; exposes a sanitized solver view."""
    def __init__(self, dataset_json, challenge_id):
        self.id = challenge_id
        self.ds = CTFDataset(dataset_json=dataset_json)
        self._c = CTFChallenge(self.ds.get(challenge_id), self.ds.basedir)
        self.name = self._c.name
        self.category = self._c.category
        self.description = self._c.description or ""
        self.listed_files = list(self._c.files or [])
        self._flag = self._c.flag                 # SECRET
        self.src_dir = Path(self._c.challenge_dir)

    def expected_flag(self):
        """Controller-only. Never call this from solver/agent code."""
        return self._flag

    def solver_context(self):
        """Exactly what the solver is allowed to see."""
        return {
            "challenge_id": self.id,
            "category": self.category,
            "description": self.description,
            "files": self.listed_files,
        }

    def stage_files(self, workspace_dir):
        """Copy ONLY the listed contestant files into a fresh workspace.
        Returns a hash inventory for the trace."""
        ws = Path(workspace_dir)
        ws.mkdir(parents=True, exist_ok=True)
        inventory = {}
        for fname in self.listed_files:
            if fname in FORBIDDEN:
                continue
            src = self.src_dir / fname
            if not src.exists() or not src.is_file():
                inventory[fname] = {"status": "missing_in_source"}
                continue
            dst = ws / fname
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            inventory[fname] = {
                "status": "staged",
                "sha256": hashlib.sha256(src.read_bytes()).hexdigest(),
                "bytes": src.stat().st_size,
            }
        return inventory

import json
import os
import subprocess
import sys
import unittest

from fakes import ROOT, memlib

sys.path.insert(0, os.path.join(ROOT, "hooks"))
import heavy_job_guard as hook  # noqa: E402

HOOK = os.path.join(ROOT, "hooks", "heavy_job_guard.py")
CFG = memlib.load_config("/nonexistent/memguard.json")

DENY = [
    "cd ~/proj && .venv/bin/python scripts/infer_batch.py > log 2>&1",
    "for s in a b; do python3 run_infer.py --in in/$s --device mps 2>&1 | tail -2; done",
    ".venv/bin/python predict.py --list work/part_01 --out x.csv --device mps --resume",
    "python3 - <<'EOF'\nimport torch\nprint(torch.ones(3))\nEOF",
    "python3 -c \"import torch; print(1)\"",
    "bash -c 'cd x; python infer.py --input a'",
    "/Applications/Blender.app/Contents/MacOS/Blender -b scene.blend -P render.py",
    "nohup python3 embed_corpus.py --all &",
    "caffeinate -i python3 scripts/train_small.py",
    "echo start >> run.log; .venv/bin/python scripts/finetune.py --device cuda",
    "heavy --name a -- python3 x.py && python3 infer.py --device mps",
    "python3 -c 'from transformers import AutoModel'",
    "uv run python train_lora.py --epochs 1",
    "time -p python3 infer.py --device mps",
    "(python3 infer.py --device mps)",
    "nice -n 10 python3 train.py",
    "HEAVY_ACTIVE=1 python3 infer.py --device mps",
    "/usr/bin/lockf /tmp/any.lock python3 infer.py --device mps",  # no lock-file exemption
]

ALLOW = [
    "pgrep -fl 'infer.py|train.py'",
    "grep -n 'import torch' notes.md",
    "python3 notes.py --summary 'infer.py ran on mps' --title 'x'",
    "heavy --name job --need 20 -- bash run_batch.sh in out mps",
    "cd ~/x && heavy --name t -- python infer.py --device mps",
    "MEMGUARD_LIGHT=1 python3 infer.py --help",
    "cat > scripts/infer_helper.py <<'EOF'\nimport torch\nEOF",
    "ls .venv/bin",
    "python3 -m py_compile hooks/heavy_job_guard.py",
    "echo 'python infer.py --device mps'",
    "sed -n 1,40p scripts/train.py; tail -3 batch.log",
    "git commit -m 'add infer.py --device mps'",
    "cd /p; until grep -q 'files,' batch.log; do sleep 5; done; cat batch.log",
    "python3 - <<'EOF'\nimport json\nprint(json.load(open('a.json')))\nEOF",
    "python3 - <<'EOF'\ns = \"don't break on a lone quote\"\nEOF",
    "~/.local/bin/heavy --name x -- python3 train.py",
    "time -p heavy --name a -- python3 infer.py --device mps",
    "( heavy --name a -- python3 infer.py --device mps )",
    "(heavy --name a -- python3 infer.py --device mps)",
    "nice -n 10 heavy --name a -- python3 train.py",
    "env FOO=1 heavy --name a -- python3 train.py",
]

# Documented gaps: the hook gets these wrong today. Kept as tests so a fix shows up.
KNOWN_FALSE_DENY = [
    "x=$(heavy --name a -- python3 infer.py --device mps)",
]
KNOWN_FALSE_ALLOW = [
    "./run_everything.sh",           # the heavy work hides inside a script
]


def run_cli(cmd, tool="Bash", raw=None):
    env = dict(os.environ, MEMGUARD_NO_STATUS="1", MEMGUARD_CONFIG="/nonexistent/memguard.json")
    inp = raw if raw is not None else json.dumps({"tool_name": tool, "tool_input": {"command": cmd}})
    p = subprocess.run([sys.executable, HOOK], input=inp, capture_output=True, text=True, timeout=30, env=env)
    if p.returncode != 0:
        return "error rc=%d %s" % (p.returncode, p.stderr[-300:])
    if not p.stdout.strip():
        return "allow"
    return json.loads(p.stdout)["hookSpecificOutput"]["permissionDecision"]


def decide(cmd):
    os.environ["MEMGUARD_NO_STATUS"] = "1"
    return "deny" if hook.decide({"tool_name": "Bash", "tool_input": {"command": cmd}}, CFG) else "allow"


class HookDecisionTest(unittest.TestCase):
    def test_deny(self):
        for c in DENY:
            with self.subTest(cmd=c):
                self.assertEqual(decide(c), "deny")

    def test_allow(self):
        for c in ALLOW:
            with self.subTest(cmd=c):
                self.assertEqual(decide(c), "allow")

    def test_known_gaps_still_behave_as_documented(self):
        for c in KNOWN_FALSE_DENY:
            with self.subTest(cmd=c):
                self.assertEqual(decide(c), "deny")
        for c in KNOWN_FALSE_ALLOW:
            with self.subTest(cmd=c):
                self.assertEqual(decide(c), "allow")

    def test_deny_message_points_at_the_queue(self):
        os.environ["MEMGUARD_NO_STATUS"] = "1"
        reason = hook.decide({"tool_name": "Bash", "tool_input": {"command": "python3 train.py"}}, CFG)
        self.assertIn("heavy --name", reason)
        self.assertIn("MEMGUARD_LIGHT=1", reason)


class HookCliTest(unittest.TestCase):
    def test_cli_deny_and_allow(self):
        self.assertEqual(run_cli("python3 infer.py --device mps"), "deny")
        self.assertEqual(run_cli("heavy --name a -- python3 infer.py --device mps"), "allow")

    def test_non_bash_tool_passes(self):
        self.assertEqual(run_cli("python infer.py --device mps", tool="Read"), "allow")

    def test_bad_input_passes(self):
        self.assertEqual(run_cli(None, raw="not json"), "allow")
        self.assertEqual(run_cli(None, raw="[1, 2]"), "allow")


if __name__ == "__main__":
    unittest.main()

"""Synthetic conversion worker. Never imports Hancom or opens real documents."""

import json
import os
from pathlib import Path
import subprocess
import sys
import time


input_path, output_path = map(Path, sys.argv[1:3])
spec = json.loads(input_path.read_text(encoding="utf-8"))
trace_path = output_path.parent.parent.parent / "events.jsonl"


def record(event: str, **values) -> None:
    with trace_path.open("a", encoding="utf-8") as trace:
        trace.write(json.dumps({"event": event, "job": output_path.parent.name, **values}) + "\n")


record("start", pid=os.getpid())
if spec.get("child"):
    options = {"stdout": sys.stdout, "stderr": sys.stderr} if spec.get("inherit_pipes", True) else {
        "stdout": subprocess.DEVNULL, "stderr": subprocess.DEVNULL,
    }
    child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"], **options)
    record("child", pid=child.pid)
if spec.get("partial"):
    output_path.write_bytes(b"synthetic-partial-output")
if spec.get("exit_parent"):
    record("parent_exit")
    sys.exit(7)
if spec.get("noisy"):
    # More than one pipe buffer: both pipes must be drained while the worker runs.
    sys.stdout.write("x" * 200_000)
    sys.stderr.write("y" * 200_000)
    sys.stdout.flush()
    sys.stderr.flush()
time.sleep(spec.get("delay", 0))
if spec.get("fail"):
    print("Synthetic conversion failure", file=sys.stderr)
    sys.exit(7)
if not spec.get("missing"):
    output_path.write_bytes(b"synthetic-pdf:" + spec.get("payload", "default").encode("utf-8"))
record("end")
if spec.get("cleanup_uncertain"):
    sys.exit(2)

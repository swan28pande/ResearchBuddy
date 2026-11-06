"""Runs short Python snippets the planner writes (for calculations and checks).

The snippet runs in a separate process: isolated mode (-I), an empty temp
directory, a stripped environment (no API keys), a wall-clock timeout, and CPU
and file-size limits on POSIX. This limits damage from buggy code but is NOT a
security sandbox (the process can still use the network and read files). Run the
backend in a container, or set CODE_EXECUTION_ENABLED=0 to turn the tool off.
"""

import os
import subprocess
import sys
import tempfile
from typing import List

from .base import CODE_EXECUTION, Source, Tool, ToolError, truncate


def _limit_resources(cpu_seconds: int):
    def apply():
        try:
            import resource
            resource.setrlimit(resource.RLIMIT_CPU, (cpu_seconds, cpu_seconds))
            resource.setrlimit(resource.RLIMIT_FSIZE, (1_000_000, 1_000_000))
        except (ImportError, ValueError, OSError):
            pass
    return apply


class PythonExecutor(Tool):
    name = "python_exec"
    category = CODE_EXECUTION
    description = "Runs a Python snippet in a subprocess and returns its stdout"
    priority = 10

    def __init__(self, exec_timeout: int = 10):
        self.exec_timeout = exec_timeout
        self.timeout = exec_timeout + 5  # router timeout must outlast the subprocess timeout

    def available(self) -> bool:
        return os.getenv("CODE_EXECUTION_ENABLED", "1") != "0"

    def _run(self, code: str) -> List[Source]:
        with tempfile.TemporaryDirectory() as tmp:
            try:
                proc = subprocess.run(
                    [sys.executable, "-I", "-c", code],
                    capture_output=True, text=True, timeout=self.exec_timeout, cwd=tmp,
                    env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
                    preexec_fn=_limit_resources(self.exec_timeout) if os.name == "posix" else None,
                )
            except subprocess.TimeoutExpired:
                # Same code will time out again, so don't retry.
                raise ToolError(f"code ran longer than {self.exec_timeout}s", retryable=False)
        if proc.returncode != 0:
            raise ToolError(f"exit {proc.returncode}: {truncate(proc.stderr, 400)}", retryable=False)
        return [Source(
            title="Python execution result",
            snippet=truncate(proc.stdout, 2000) or "(no output)",
            metadata={"code": code},
        )]

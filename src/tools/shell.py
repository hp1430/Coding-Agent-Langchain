import os
import re
from shlex import shlex
import subprocess
import sys
import time
from tracemalloc import start
from turtle import stamp

from configs.config import get_work_dir
from tools.jobs import BackgroundJob, now_iso, read_log_tail, register, stop_pid


MAX_OUTPUT_CHARS = 8000 
DEFAULT_TIMEOUT = 30

BLOCKED_COMMAND_PATTERNS = (
    r"\bsudo\b",
    r"\brm\s+-[a-zA-Z]*r[a-zA-Z]*f\b",
    r"\bmkfs\b",
    r"\bshutdown\b",
    r"\breboot\b",
    r":\(\)\s*\{",
    r"\bdd\s+if=",
    r"curl\s+[^|]*\|\s*(ba)?sh",
    r"wget\s+[^|]*\|\s*(ba)?sh",
    r"\bchmod\s+777\b",
)

SERVER_PATTERNS = (
    r"\bflask(\s+--app)?\s+run\b",
    r"\buvicorn\b",
    r"\bgunicorn\b",
    r"\bhypercorn\b",
    r"\bpython[0-9.]*\s+\S*app\.py\b",
    r"\bnpm\s+start\b",
    r"\bnpx\s+(serve|next|vite|nuxt)\b",
    r"\bstreamlit\s+run\b",
)

## Python specific handling patterns:

_PIP_PREFIX = re.compile(
    r"^(?:pip[0-9.]*|python[0-9.]*\s+-m\s+pip)\b",
    re.IGNORECASE,
)
_PYTHON_PREFIX = re.compile(r"^python[0-9.]*\b", re.IGNORECASE)
_FLASK_PREFIX = re.compile(r"^flask\b", re.IGNORECASE)

def deny_command(command: str) -> str | None:
    stripped = command.strip()
    if not stripped:
        return "Blocked by middleware: command is empty"

    for pattern in BLOCKED_COMMAND_PATTERNS:
        if re.search(pattern, command, flags=re.IGNORECASE):
            return f"Blocked by middleware: command matched a dangerous pattern {pattern}"

    return None

def looks_like_server(command: str) -> bool:
    return any(re.search(pattern, command, flags=re.IGNORECASE) for pattern in SERVER_PATTERNS)

def rewrite_command(command: str) -> str:
    exe = shlex.quote(sys.executable)

    stripped = command.strip()

    if _PIP_PREFIX.match(stripped):
        return _PIP_PREFIX.sub(f"{exe} -m pip", stripped, count=1)

    if _PYTHON_PREFIX.match(stripped):
        return _PYTHON_PREFIX.sub(exe, stripped, count=1)

    if _FLASK_PREFIX.match(stripped):
        return _FLASK_PREFIX.sub(f"{exe} -m flask", stripped, count=1)

    return command

def _clip(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text

    return text[:MAX_OUTPUT_CHARS] + "\n... (truncated)"

def _run_foreground(command: str, timeout: int) -> str:
    cwd = get_work_dir()
    cwd.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")

    try:
        completed = subprocess.run(
            ["/bin/bash", "-lc", command],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as e:
        stdout = (e.stdout or "") + (e.stderr or "")
        return (
            f"Timed out after {timeout}s (process killed),"
            "If this is a server, re-run with background-true."
            f"{_clip(str(sys.stdout))}"
        )

    # command completed successfully
    chunks = []
    if completed.stdout:
        chunks.append(completed.stdout.rstrip())
    if completed.stderr:
        chunks.append(completed.stderr.rstrip())

    body = "\n".join(chunks) if chunks else "No output."
    return f"exit_code={completed.returncode}\ncwd={cwd}\n_{_clip(body)}"

def run_background(command: str) -> str:
    cwd = get_work_dir()
    cwd.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.setdefault("PYTHONUNBUFFERED", "1")
    log_dir = cwd / ".agent_jobs"
    log_dir.mkdir(parents=True, exist_ok=True)

    stamp = now_iso().replace(":", "").replace("+", "")
    tmp_log = log_dir / f"pending-{stamp}.log"
    log_file = tmp_log.open("w", encoding="utf-8")

    try:
        proc = subprocess.Popen(
            ["/bin/bash", "-lc", command],
            cwd=cwd,
            env=env,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    finally:
        log_file.close()

    log_path = log_dir / f"{proc.pid}.log"
    tmp_log.rename(log_path)

    register(
        BackgroundJob(
            pid=proc.pid,
            command=command,
            log_path=log_path,
            started_at=now_iso(),
            proc=proc,
        )
    )

    time.sleep(1)
    tail = read_log_tail(log_path)
    if proc.poll() is not None:
        stop_pid(proc.pid)
        return (
            f"Background command exitted immediately (pid={proc.pid})."
            f"exit_code={proc.returncode}.\n{_clip(tail)}"
        )

    # if the process is still running
    urls = re.findall(r"https?://[^\s]+", tail)
    url_line = f"Open in the browser: {urls[0]}\n" if urls else (
        "No url in the log yet - try http://127.0.0.1:3000"
        "and check list_jobs if it is blank.\n"
    )

    return (
        f"{url_line}\n"
        f"Started background job (pid={proc.pid}).\n"
        f"Log: {log_path}\n"
        f"cwd={cwd}\n"
        f"Use list jobs/stop_job to manage it.\n"
        f"------ output so far ------\n {_clip(tail) or 'No output yet.'}"
    )
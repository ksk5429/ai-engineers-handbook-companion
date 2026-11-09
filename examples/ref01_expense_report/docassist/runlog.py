"""Run records: an append-only event log written by the runner, plus measurements.

The event log is the authoritative history of a run. It is written by this code as
each step happens (one JSON object per line, flushed immediately), so it survives a
crash. A narrative written afterwards by a model or a person is not a substitute.

Limits of this evidence: the log shows what this process recorded. It does not
prove the host clock was right, that the files were not edited afterwards (hashes
detect edits only if the hash itself is kept elsewhere), or that a remote service
did what its response says.
"""

from __future__ import annotations

import ctypes
import hashlib
import json
import platform
import sys
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sha256_tree(paths: list[Path]) -> str:
    """One hash over several files (name + content), order-independent."""
    digest = hashlib.sha256()
    for path in sorted(paths, key=lambda p: p.as_posix()):
        digest.update(path.name.encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def peak_rss_bytes() -> int | None:
    """Peak resident memory of this process, or None where it cannot be read."""
    if sys.platform == "win32":
        class Counters(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_ulong), ("PageFaultCount", ctypes.c_ulong),
                        ("PeakWorkingSetSize", ctypes.c_size_t),
                        ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t),
                        ("PeakPagefileUsage", ctypes.c_size_t)]
        counters = Counters()
        counters.cb = ctypes.sizeof(Counters)
        kernel32, psapi = ctypes.WinDLL("kernel32"), ctypes.WinDLL("psapi")
        kernel32.GetCurrentProcess.restype = ctypes.c_void_p      # a HANDLE is pointer-sized
        psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p, ctypes.POINTER(Counters),
                                               ctypes.c_ulong]
        handle = kernel32.GetCurrentProcess()
        if psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), counters.cb):
            return int(counters.PeakWorkingSetSize)
        return None
    try:
        import resource  # Unix only
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return int(peak if sys.platform == "darwin" else peak * 1024)  # macOS bytes, Linux KiB
    except (ImportError, OSError):
        return None


def environment() -> dict[str, Any]:
    return {"python": platform.python_version(), "implementation": platform.python_implementation(),
            "os": platform.platform(), "machine": platform.machine()}


# --8<-- [start:recorder]
class RunRecorder:
    """Appends events to <run_dir>/events.jsonl and flushes each one to disk."""

    def __init__(self, run_dir: Path) -> None:
        self.run_dir = run_dir
        run_dir.mkdir(parents=True, exist_ok=True)
        self.path = run_dir / "events.jsonl"
        self.seq = len(load_events(run_dir))
        self._t0 = time.perf_counter()
        self._cpu0 = time.process_time()
        if not tracemalloc.is_tracing():
            tracemalloc.start()

    def emit(self, event_type: str, **data: Any) -> dict[str, Any]:
        self.seq += 1
        event = {"seq": self.seq, "type": event_type,
                 "utc": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                 "t_s": round(time.perf_counter() - self._t0, 6), **data}
        with self.path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event) + "\n")
            handle.flush()
        return event

    def resources(self) -> dict[str, Any]:
        _, traced_peak = tracemalloc.get_traced_memory()
        return {"wall_s": round(time.perf_counter() - self._t0, 4),
                "cpu_s": round(time.process_time() - self._cpu0, 4),
                "python_heap_peak_bytes": traced_peak,
                "process_peak_rss_bytes": peak_rss_bytes()}
# --8<-- [end:recorder]


def load_events(run_dir: Path) -> list[dict[str, Any]]:
    path = run_dir / "events.jsonl"
    if not path.exists():
        return []
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            events.append(json.loads(line))
    return events

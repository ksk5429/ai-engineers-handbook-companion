"""Shared test helpers. Tests never call Ollama or the network, and never draw the held-out
fixtures: where a held-out image file is needed, a blank placeholder PNG stands in for it."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from PIL import Image  # noqa: E402

R1_TRIALS = HERE.parent.parent / "reviews" / "evidence" / "mm01" / "TRIALS.json"


PS_HEADER = "NAME           ID              SIZE      PROCESSOR    CONTEXT    RUNNER      UNTIL"


class FakeMachine:
    """Stands in for `ollama ps`, `ollama --version` and `nvidia-smi` (no real command runs).
    The model counts as loaded once the first model call has been made."""

    def __init__(self, model_gpu: int = 1, processor: str = "100% GPU", preloaded: bool = False) -> None:
        self.loaded = preloaded
        self.model_gpu = model_gpu
        self.processor = processor

    def call_made(self) -> None:
        self.loaded = True

    def __call__(self, args: list[str]) -> str:
        if args[:2] == ["ollama", "ps"]:
            row = f"\nqwen3-vl:8b    901cae732162    6.1 GB    {self.processor}     8192       llamacpp    4 minutes"
            return PS_HEADER + (row if self.loaded else "") + "\n"
        if args[:2] == ["ollama", "--version"]:
            return "ollama version is fake\n"
        if args[0] == "nvidia-smi" and "--query-gpu=index,temperature.gpu" in args:
            return "0, 50\n1, 55\n"
        if args[0] == "nvidia-smi":
            used = {0: "300 MiB", 1: "300 MiB"}
            if self.loaded:
                used[self.model_gpu] = "6500 MiB"
            return ("index, name, memory.used [MiB], temperature.gpu\n"
                    f"0, NVIDIA GeForce RTX 2060, {used[0]}, 50\n1, NVIDIA GeForce RTX 4070, {used[1]}, 55\n")
        raise AssertionError(f"unexpected command {args}")


def placeholder_heldout(folder: Path) -> Path:
    """Blank 1280x800 stand-ins for ho_a/b/c.png and a matching cases_heldout.json, so the
    pre-flight logic can be tested before the real held-out images exist."""
    spec = json.loads((HERE / "heldout_spec_v2.json").read_text("utf-8"))
    folder.mkdir(parents=True, exist_ok=True)
    fixtures = []
    for i, fx in enumerate(spec["heldout"]["fixtures"]):
        path = folder / fx["file"]
        Image.new("RGB", (1280, 800), (i * 40, 0, 0)).save(path)
        fixtures.append({"image": fx["file"], "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                         "width": 1280, "height": 800})
    (folder / spec["heldout"]["cases_file"]).write_text(
        json.dumps({"placeholder": True, "fixtures": fixtures}), encoding="utf-8")
    return folder

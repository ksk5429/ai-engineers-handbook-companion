"""Run the MM01 trials through a vision model served by Ollama, with and without pre-flight.

  python run_trials.py --dry-run                     # v1 set: pre-flight and prompts, no model
  python run_trials.py --protocol v2 --dry-run       # all 25 v2 bundles, no model
  python run_trials.py --model qwen3-vl:8b --seeds 1 2 3                  # v1 protocol (live)
  python run_trials.py --protocol v2 --set heldout --out ../../reviews/evidence/mm01_v2  # Block H

Output goes to --out (default runs/, which git ignores), so a reader never overwrites the
book's evidence; the evidence folder is written only when it is named explicitly. A live run
appends each call to <name>.jsonl as soon as it completes (a crash loses nothing; --resume
skips the calls already there), then writes <name>.json and <name>.md. Every reply is stored
verbatim, with a hash of the code and protocol that produced it. The copies of the images
that the model saw are deleted at the end unless --keep-images is given.
Results describe one local model on a few constructed trials: an illustration, not a benchmark.
"""

from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from bundle import (agent_prompt, agent_prompt_v2, as_dict, b64, discard_agent_images,
                    image_for_agent, preflight)
from trials import (FIXTURES, SPEC_V2, Trial, evaluate, evaluate_v2, load, load_dev_v2,
                    load_spec_trials, pipeline_passed_v2, read_spec)

HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "runs"
DEFAULT_HOLD_FLAG = r"C:\ProgramData\paperkit-locks\bench_hold.flag"
HOST = "http://127.0.0.1:11434"
STOP_TEMP_C = 87
CODE_FILES = ("bundle.py", "trials.py", "make_fixtures.py", "run_trials.py", "rescore.py",
              "score_replies.py", "PROTOCOL_v2.md", "heldout_spec_v2.json")
V1_MISSING_RULE = "If the image is too old, from the wrong window, or missing"


def hold_flag() -> Path:
    return Path(os.environ.get("HANDBOOK_HOLD_FLAG", DEFAULT_HOLD_FLAG))


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def code_hashes() -> dict[str, str]:
    return {n: sha256_file(HERE / n) if (HERE / n).is_file() else "missing" for n in CODE_FILES}


def code_digest(hashes: dict[str, str]) -> str:
    return hashlib.sha256("".join(f"{k}:{v}\n" for k, v in sorted(hashes.items())).encode()
                          ).hexdigest()


# ------------------------------------------------------------------ model and machine calls
def main_gpu() -> int | None:
    value = os.environ.get("HANDBOOK_MAIN_GPU")
    return int(value) if value not in (None, "") else None


def ollama_options(seed: int) -> dict[str, Any]:
    gpu = main_gpu()
    return {"num_ctx": 8192, "temperature": 0.7, "seed": seed,
            **({"main_gpu": gpu} if gpu is not None else {})}


def call_ollama(model: str, prompt: str, image: Path | None, seed: int, think: bool) -> dict[str, Any]:
    message: dict[str, Any] = {"role": "user", "content": prompt}
    if image is not None:
        message["images"] = [b64(image)]
    body = {"model": model, "messages": [message], "stream": False, "format": "json", "think": think,
            "options": ollama_options(seed)}
    request = urllib.request.Request(f"{HOST}/api/chat", data=json.dumps(body).encode(),
                                     headers={"content-type": "application/json"}, method="POST")
    started = time.perf_counter()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # never via a proxy
    try:
        with opener.open(request, timeout=600) as response:
            data = json.loads(response.read())
    except (urllib.error.URLError, http.client.HTTPException, TimeoutError, OSError,
            json.JSONDecodeError) as exc:
        return {"error": f"{type(exc).__name__}: {exc}", "wall_s": round(time.perf_counter() - started, 2)}
    if not isinstance(data, dict):
        return {"error": f"unexpected response type {type(data).__name__}",
                "wall_s": round(time.perf_counter() - started, 2)}
    msg = data.get("message") or {}
    content = msg.get("content") or ""
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError:
        parsed = None
    thinking = msg.get("thinking") or ""
    return {"raw": content, "parsed": parsed if isinstance(parsed, dict) else None,
            "parsed_type": type(parsed).__name__, "thinking": thinking,
            "thinking_chars": len(thinking), "wall_s": round(time.perf_counter() - started, 2),
            "prompt_eval_count": data.get("prompt_eval_count"), "eval_count": data.get("eval_count"),
            "options_sent": body["options"]}


def call_with_retry(call: Callable[[], dict[str, Any]]) -> dict[str, Any]:
    """Retry once with the same seed; a second failure is status 'error' (never scored)."""
    first = call()
    if "error" not in first:
        return {**first, "status": "ok", "attempts": 1}
    second = call()
    if "error" not in second:
        return {**second, "status": "ok", "attempts": 2, "first_error": first["error"]}
    return {**second, "status": "error", "attempts": 2, "first_error": first["error"]}


def run_cmd(args: list[str]) -> str | None:
    """Output of a local command, or None if it is not installed or fails to start."""
    try:
        return subprocess.run(args, capture_output=True, text=True, timeout=60).stdout
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return None


def gpu_temperatures() -> dict[int, int] | None:
    out = run_cmd(["nvidia-smi", "--query-gpu=index,temperature.gpu",
                   "--format=csv,noheader,nounits"])
    if not out:
        return None
    temps = {}
    for line in out.strip().splitlines():
        try:
            index, temp = (int(v) for v in line.split(","))
        except ValueError:
            return None
        temps[index] = temp
    return temps


def stop_reason() -> str | None:
    """Board stop rules, checked before every call. Fails closed if the GPU cannot be read."""
    if hold_flag().exists():
        return f"bench hold flag present: {hold_flag()}"
    temps = gpu_temperatures()
    if temps is None:
        return "nvidia-smi unavailable: GPU temperature cannot be checked"
    for index in {0, main_gpu() if main_gpu() is not None else 0}:
        if temps.get(index, 0) >= STOP_TEMP_C:
            return f"GPU {index} at {temps[index]} C (stop at {STOP_TEMP_C} C)"
    return None


def loaded_models(ps: str | None) -> list[str] | None:
    """Model names listed by `ollama ps` (None if the command is unavailable)."""
    if ps is None:
        return None
    return [line.split()[0] for line in ps.strip().splitlines()[1:] if line.strip()]


def busiest_gpu(smi: str | None) -> int | None:
    """Index of the GPU with the most memory in use: a heuristic for where the model sits."""
    best = None
    for line in (smi or "").strip().splitlines()[1:]:
        parts = [p.strip() for p in line.split(",")]
        try:
            index, used = int(parts[0]), float(parts[2].split()[0])
        except (IndexError, ValueError):
            return None
        if best is None or used > best[1]:
            best = (index, used)
    return None if best is None else best[0]


def placement(model: str) -> dict[str, Any]:
    ps = run_cmd(["ollama", "ps"])
    smi = run_cmd(["nvidia-smi", "--query-gpu=index,name,memory.used,temperature.gpu", "--format=csv"])
    row = next((line for line in (ps or "").splitlines() if line.split()[:1] == [model]), "")
    return {"checked_utc": now(), "ollama_ps": ps, "nvidia_smi": smi, "requested_main_gpu": main_gpu(),
            "model_row": row, "model_fully_on_gpu": "100% GPU" in row,
            "busiest_gpu_index": busiest_gpu(smi)}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# ------------------------------------------------------------------ the call plan
@dataclass(frozen=True)
class Call:
    trial: Trial
    block: str            # "v1", "H" or "D"
    arm: str              # "v1" (protocol v1), "P2" (prompt v2) or "P1" (prompt v1 arm)
    seed: int

    @property
    def key(self) -> str:
        return f"{self.block}|{self.arm}|{self.trial.bundle.task_id}|{self.seed}"

    def prompt(self) -> str:
        return agent_prompt_v2(self.trial.bundle) if self.arm == "P2" else agent_prompt(self.trial.bundle)

    def score(self, parsed: dict[str, Any] | None) -> dict[str, Any]:
        if self.arm == "v1":
            return evaluate(parsed, self.trial.label)
        return evaluate_v2(parsed, self.trial.label)


def v1_trials() -> list[Trial]:
    bundles, labels = load()
    return [Trial(bundle=b, label=labels[b.task_id], image_dir=FIXTURES, set_name="dev",
                  preflight_expect="new_observation" if labels[b.task_id]["expect"] == "new_observation"
                  else "send_to_agent") for b in bundles]


def build_plan(protocol: str, which: str, seeds: list[int], spec: Path,
               heldout_dir: Path | None) -> list[Call]:
    """v1: trial-major, as the v1 run. v2: Block H then Block D, seed-major (Section 8)."""
    if protocol == "v1":
        return [Call(t, "v1", "v1", s) for t in v1_trials() for s in seeds]
    plan: list[Call] = []
    if which in ("heldout", "all"):
        held = load_spec_trials(spec, heldout_dir)
        for s in seeds:
            plan += [Call(t, "H", "P2", s) for t in held]
            plan += [Call(t, "H", "P1", s) for t in held if t.also_v1]
    if which in ("dev", "all"):
        dev = load_dev_v2()
        for s in seeds:
            plan += [Call(t, "D", "P2", s) for t in dev]
    return plan


def unique_bundles(plan: list[Call]) -> list[Call]:
    seen, out = set(), []
    for c in plan:
        k = (c.block, c.arm, c.trial.bundle.task_id)
        if k not in seen:
            seen.add(k)
            out.append(c)
    return out


def t6_ok(call: Call, prompt: str) -> bool | None:
    """Prompt v2 renders, and a text-only render has no instruction to request a screenshot."""
    if call.arm != "P2":
        return None
    if call.trial.bundle.screenshot is not None:
        return True
    return V1_MISSING_RULE not in prompt and "A screenshot is not required." in prompt


# ------------------------------------------------------------------ dry run and live run
def dry_rows(plan: list[Call], work: Path, made: list[Path]) -> list[dict[str, Any]]:
    rows = []
    for c in unique_bundles(plan):
        b = c.trial.bundle
        pre = preflight(b, c.trial.image_dir)
        image = image_for_agent(b, c.trial.image_dir, work)
        if image is not None:
            made.append(image)
        try:
            prompt, render_error = c.prompt(), None
        except (KeyError, IndexError, ValueError) as exc:
            prompt, render_error = "", f"{type(exc).__name__}: {exc}"
        rows.append({"set": c.trial.set_name, "block": c.block, "arm": c.arm,
                     "task_id": b.task_id, "mode": b.mode, "expect": c.trial.label["expect"],
                     "preflight": pre, "preflight_expect": c.trial.preflight_expect,
                     "preflight_decision_ok": pre["action"] == c.trial.preflight_expect,
                     "prompt": prompt, "render_error": render_error,
                     "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
                     "t6_ok": None if render_error else t6_ok(c, prompt),
                     "agent_image_sha256": sha256_file(image) if image else None})
    return rows


def read_jsonl(jsonl: Path) -> list[dict[str, Any]]:
    """Rows of a run file; blank lines are skipped and a truncated last line (a crash during
    the write) is dropped. A bad line elsewhere is an error."""
    lines = [x for x in jsonl.read_text("utf-8").splitlines() if x.strip()]
    rows = []
    for i, line in enumerate(lines):
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            if i != len(lines) - 1:
                raise
    return rows


def repair_tail(jsonl: Path) -> None:
    """Cut a partial last line (a crash during a write) so new rows start on a fresh line;
    the cut text is kept in a 'repair' row."""
    text = jsonl.read_text("utf-8")
    if not text or text.endswith("\n"):
        return
    cut = text.rfind("\n") + 1
    jsonl.write_text(text[:cut], encoding="utf-8")
    append(jsonl, {"kind": "repair", "utc": now(), "dropped_partial_line": text[cut:]})


def resume_conflicts(rows: list[dict[str, Any]], digest: str, model: str, think: bool) -> list[str]:
    """A resumed run must use the same code, protocol, model and think setting."""
    out = set()
    for r in rows:
        if r.get("kind") != "call":
            continue
        if r["code_sha256"] != digest:
            out.add(f"code_sha256 {r['code_sha256'][:12]} != current {digest[:12]}")
        if r["request"]["model"] != model or r["request"]["think"] != think:
            out.add(f"model/think {r['request']['model']}/{r['request']['think']} != {model}/{think}")
    return sorted(out)


def append(jsonl: Path, row: dict[str, Any]) -> None:
    with jsonl.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        fh.flush()
        os.fsync(fh.fileno())


def call_row(c: Call, args: argparse.Namespace, image: Path | None, digest: str) -> dict[str, Any]:
    b = c.trial.bundle
    pre = preflight(b, c.trial.image_dir)
    prompt = c.prompt()
    started = now()
    reply = call_with_retry(lambda: call_ollama(args.model, prompt, image, c.seed, args.think == "on"))
    score = c.score(reply.get("parsed")) if reply["status"] == "ok" else None
    if score is None:                    # an error is never graded (Section 6.1)
        pipe = None
    elif c.arm == "v1":
        pipe = (c.trial.label["expect"] == "new_observation") if not pre["proceed"] else score["passed"]
    else:
        pipe = pipeline_passed_v2(pre, score, c.trial.label)
    return {"kind": "call", "key": c.key, "set": c.trial.set_name, "block": c.block, "arm": c.arm,
            "prompt_version": "v2" if c.arm == "P2" else "v1", "task_id": b.task_id,
            "mode": b.mode, "seed": c.seed, "expect": c.trial.label["expect"],
            "hypotheses": list(c.trial.hypotheses), "preflight": pre,
            "preflight_expect": c.trial.preflight_expect,
            "preflight_decision_ok": pre["action"] == c.trial.preflight_expect,
            "request": {"model": args.model, "think": args.think == "on", "format": "json",
                        "options": ollama_options(c.seed), "image_attached": image is not None},
            "prompt_sha256": hashlib.sha256(prompt.encode()).hexdigest(),
            "agent_image_sha256": sha256_file(image) if image else None,
            "started_utc": started, "reply": reply, "status": reply["status"], "score": score,
            "pipeline_passed": pipe, "code_sha256": digest, "bundle": as_dict(b)}


def live(plan: list[Call], args: argparse.Namespace, out: Path, name: str, work: Path,
         made: list[Path], digest: str) -> int:
    jsonl = out / f"{name}.jsonl"
    if jsonl.exists() and not args.resume:
        print(f"{jsonl} exists: use --resume to continue it, or choose another --out",
              file=sys.stderr)
        return 2
    if jsonl.exists():
        repair_tail(jsonl)
    previous = read_jsonl(jsonl) if jsonl.exists() else []
    conflicts = resume_conflicts(previous, digest, args.model, args.think == "on")
    if conflicts:
        print(f"cannot resume {jsonl}: {conflicts}", file=sys.stderr)
        return 2
    done = {r["key"] for r in previous if r.get("kind") == "call"}
    models = loaded_models(run_cmd(["ollama", "ps"]))
    if models is None or models:
        print(f"`ollama ps` must run and show no loaded model before the window (Section 8 step 5); "
              f"got {models}. Run `ollama stop <model>` first.", file=sys.stderr)
        return 5
    checked = False
    for c in plan:
        if c.key in done:
            continue
        reason = stop_reason()
        if reason:
            print(f"stopping before {c.key}: {reason}", file=sys.stderr)
            append(jsonl, {"kind": "stop", "utc": now(), "before": c.key, "reason": reason})
            return 4
        image = image_for_agent(c.trial.bundle, c.trial.image_dir, work)
        if image is not None:
            made.append(image)
        row = call_row(c, args, image, digest)
        append(jsonl, row)
        score = row["score"] or {}
        print(f"{c.key:<44} expect={row['expect']:<15} got={score.get('decision')!s:<15} "
              f"passed={score.get('passed')}  status={row['status']}  preflight={row['preflight']['action']}")
        if not checked and row["status"] == "ok":
            checked = True
            place = placement(args.model)
            append(jsonl, {"kind": "placement", **place})
            want = main_gpu()
            if want is not None and place["busiest_gpu_index"] != want:
                append(jsonl, {"kind": "deviation", "utc": now(),
                               "text": f"model appears to be on GPU {place['busiest_gpu_index']} "
                                       f"(most memory in use), not GPU {want}; continue only while GPU 0 < "
                                       f"{STOP_TEMP_C} C; wall times not comparable"})
            if not place["model_fully_on_gpu"]:
                print(f"{args.model} not fully on GPU, stopping:\n{place['ollama_ps']}", file=sys.stderr)
                return 5
    return 0


def fixture_hashes(plan: list[Call]) -> dict[str, Any]:
    dirs = {str(c.trial.image_dir) for c in plan}
    out = {}
    for d in sorted(dirs):
        for cases in ("cases.json", "cases_heldout.json"):
            p = Path(d) / cases
            if p.is_file():
                out[str(p.relative_to(HERE)) if p.is_relative_to(HERE) else str(p)] = sha256_file(p)
    return out


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--protocol", choices=["v1", "v2"], default="v1",
                   help="v1 (default): the 12 v1 trials, prompt v1, labels v1. v2: PROTOCOL_v2.md")
    p.add_argument("--set", dest="which", choices=["heldout", "dev", "all"], default="all",
                   help="v2 only: heldout = Block H (spec trials, P2 then P1 arm), dev = Block D")
    p.add_argument("--spec", type=Path, default=SPEC_V2, help="v2 trial spec (default heldout_spec_v2.json)")
    p.add_argument("--heldout-dir", type=Path, default=None,
                   help="folder with the spec's images and cases file (default: the spec's output_dir)")
    p.add_argument("--model", default="qwen3-vl:8b")
    p.add_argument("--seeds", type=int, nargs="+", default=None,
                   help="default: [1] for v1, the spec's seeds [1, 2, 3] for v2")
    p.add_argument("--dry-run", action="store_true", help="pre-flight and prompts only; no model, no Ollama")
    p.add_argument("--think", choices=["on", "off"], default="on")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output folder (default runs/, git-ignored)")
    p.add_argument("--resume", action="store_true", help="continue an interrupted live run in --out")
    p.add_argument("--keep-images", action="store_true", help="keep the agent's image copies")
    args = p.parse_args(argv)
    if args.seeds is None:
        args.seeds = read_spec(args.spec)["model_settings"]["seeds"] if args.protocol == "v2" else [1]
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    work = out / "agent_images"
    name = ("PREFLIGHT" if args.dry_run else "TRIALS") + ("_v2" if args.protocol == "v2" else "")
    hashes = code_hashes()
    digest = code_digest(hashes)
    plan = build_plan(args.protocol, args.which, args.seeds, args.spec, args.heldout_dir)
    deviations: list[str] = []
    made: list[Path] = []
    status = 0
    try:
        if args.dry_run:
            rows = dry_rows(plan, work, made)
            status = 0 if all(r["preflight_decision_ok"] and r["t6_ok"] is not False for r in rows) else 1
        else:
            gate = dry_rows(plan, work, made)
            bad = [r["task_id"] for r in gate if not r["preflight_decision_ok"] or r["t6_ok"] is False]
            if bad:
                print(f"pre-flight gate failed (Section 8 step 4), no model called: {bad}", file=sys.stderr)
                return 3
            if args.protocol == "v2":
                want = read_spec(args.spec)["model_settings"]["options"]["main_gpu"]
                if main_gpu() is None:
                    print("set HANDBOOK_MAIN_GPU (protocol v2 requires main_gpu "
                          f"{want}) before a live run", file=sys.stderr)
                    return 2
                if main_gpu() != want:
                    deviations.append(f"main_gpu {main_gpu()} requested; protocol says {want}")
                if args.think != "on":
                    deviations.append("think off; protocol v2 Section 7 fixes think: true")
            status = live(plan, args, out, name, work, made, digest)
            if status == 2:                      # refused: an earlier run's files stay untouched
                return 2
            rows = read_jsonl(out / f"{name}.jsonl") if (out / f"{name}.jsonl").exists() else []
    finally:
        deleted = [] if args.keep_images else discard_agent_images(made, work)
    runtime = "not queried (dry run)" if args.dry_run else (
        (run_cmd(["ollama", "--version"]) or "ollama not installed").strip())
    calls = [r for r in rows if r.get("kind", "call") == "call"]
    record = {"generated_utc": now(), "generator": "examples/mm01_screen_grounding/run_trials.py",
              "protocol": args.protocol, "set": args.which if args.protocol == "v2" else "dev (v1)",
              "model": None if args.dry_run else args.model, "runtime": runtime, "seeds": args.seeds,
              "dry_run": args.dry_run, "think": args.think, "think_api_field": args.think == "on",
              "options": {k: v for k, v in ollama_options(0).items() if k != "seed"},
              "env_HANDBOOK_MAIN_GPU": os.environ.get("HANDBOOK_MAIN_GPU"),
              "hold_flag_path": str(hold_flag()),
              "ollama_ps_after_load": next((r["ollama_ps"] for r in rows if r.get("kind") == "placement"), None),
              "placement": next((r for r in rows if r.get("kind") == "placement"), None),
              "stops": [r for r in rows if r.get("kind") == "stop"],
              "errors": [r["key"] for r in calls if r.get("status") == "error"],
              "deviations": deviations + [r["text"] for r in rows if r.get("kind") == "deviation"],
              "exit_status": status,
              "code_sha256": digest, "code_files": hashes, "fixture_cases_sha256": fixture_hashes(plan),
              "agent_images": ("kept (--keep-images)" if args.keep_images else
                               f"{len(deleted)} work copies deleted at the end of the run (retention rule); "
                               "the fixture PNGs are test assets and are kept"),
              "environment": {"python": platform.python_version(), "os": platform.platform()},
              "note": "Constructed images and transcripts; one local model; illustration, not a benchmark.",
              "rows": calls}
    (out / f"{name}.json").write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    text = render(record) if args.protocol == "v1" else render_v2(record)
    (out / f"{name}.md").write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {out / name}.json and .md (exit {status})")
    return status


# ------------------------------------------------------------------ reports
def render(r: dict[str, Any]) -> str:
    out = [f"# MM01 {'pre-flight (dry run)' if r['dry_run'] else 'trials'} (generated)", "",
           f"Generated {r['generated_utc']} by `{r['generator']}`. {r['note']}", "",
           f"- Model: {r['model']}; runtime: {r['runtime']}; seeds: {r['seeds']}; think: {r['think']} (API-level); temperature 0.7",
           f"- Environment: Python {r['environment']['python']} on {r['environment']['os']}",
           f"- Code sha256 (bundle, trials, make_fixtures, run_trials, rescore, score_replies, protocol v2, spec v2): `{r['code_sha256']}`", ""]
    if r["dry_run"]:
        out += ["| Trial | Mode | Expected | Pre-flight action | Findings | Pre-flight correct |",
                "|---|---|---|---|---|---|"]
        for row in r["rows"]:
            out.append(f"| {row['task_id']} | {row['mode']} | {row['expect']} | "
                       f"{row['preflight']['action']} | {'; '.join(row['preflight']['findings']) or '-'} | "
                       f"{row['preflight_decision_ok']} |")
        ok = sum(row["preflight_decision_ok"] for row in r["rows"])
        return "\n".join(out + ["", f"Pre-flight correct: {ok}/{len(r['rows'])}"]) + "\n"
    out += ["| Trial | Mode | Seed | Expected | Model decision | Target | Concepts | Passed | Pre-flight | Wall s |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    for row in r["rows"]:
        parsed = row["reply"].get("parsed") or {}
        s = row["score"] or {}
        out.append(f"| {row['task_id']} | {row['mode']} | {row['seed']} | {row['expect']} | "
                   f"{parsed.get('decision', 'unparsed') if row['status'] == 'ok' else 'error'} | "
                   f"{s.get('target_ok')} | {s.get('concepts_ok')} | {s.get('passed')} | "
                   f"{row['preflight']['action']} | {row['reply'].get('wall_s')} |")
    by_trial: dict[str, list[bool]] = {}
    for row in r["rows"]:
        if row["status"] == "ok":
            by_trial.setdefault(row["task_id"], []).append(row["score"]["passed"])
    out += ["", "Passed / runs per trial: " + "; ".join(f"{k} {sum(v)}/{len(v)}" for k, v in by_trial.items()), ""]
    return "\n".join(out) + "\n"


def render_v2(r: dict[str, Any]) -> str:
    out = [f"# MM01 protocol v2 {'pre-flight (dry run)' if r['dry_run'] else 'trials'} (generated)", "",
           f"Generated {r['generated_utc']} by `{r['generator']}`. {r['note']}", "",
           f"- Set: {r['set']}; model: {r['model']}; runtime: {r['runtime']}; seeds: {r['seeds']}; "
           f"think: {r['think']} (API-level); options: {r['options']}",
           f"- Environment: Python {r['environment']['python']} on {r['environment']['os']}",
           f"- Code sha256: `{r['code_sha256']}`; agent images: {r['agent_images']}",
           f"- Errors: {r['errors'] or 'none'}; stops: {len(r['stops'])}; deviations: {r['deviations'] or 'none'}", ""]
    if r["dry_run"]:
        out += ["| Set | Block | Arm | Trial | Mode | Expected | Pre-flight | Expected pre-flight | Findings | Pre-flight ok | T6 |",
                "|---|---|---|---|---|---|---|---|---|---|---|"]
        for row in r["rows"]:
            out.append(f"| {row['set']} | {row['block']} | {row['arm']} | {row['task_id']} | {row['mode']} | "
                       f"{row['expect']} | {row['preflight']['action']} | {row['preflight_expect']} | "
                       f"{'; '.join(row['preflight']['findings']) or '-'} | {row['preflight_decision_ok']} | "
                       f"{row['t6_ok'] if row['t6_ok'] is not None else '-'} |")
        ok = sum(row["preflight_decision_ok"] for row in r["rows"])
        t6 = [row["t6_ok"] for row in r["rows"] if row["t6_ok"] is not None]
        return "\n".join(out + ["", f"Pre-flight as expected: {ok}/{len(r['rows'])}; "
                                    f"T6 renders ok: {sum(t6)}/{len(t6)}"]) + "\n"
    out += ["| Block | Arm | Trial | Seed | Expected | Decision | Target | Concepts | Must-not | Problem found | Passed | Pipeline | Wall s |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for row in r["rows"]:
        s = row["score"] or {}
        out.append(f"| {row['block']} | {row['arm']} | {row['task_id']} | {row['seed']} | {row['expect']} | "
                   f"{s.get('decision') if row['status'] == 'ok' else 'error'} | {s.get('target_ok')} | "
                   f"{s.get('concepts_ok')} | {s.get('must_not_ok')} | {s.get('problem_found_ok')} | "
                   f"{s.get('passed')} | {row['pipeline_passed']} | {row['reply'].get('wall_s')} |")
    counts: dict[str, list[bool]] = {}
    for row in r["rows"]:
        if row["status"] == "ok":
            counts.setdefault(f"{row['arm']} {row['task_id']}", []).append(row["score"]["passed"])
    out += ["", "Passed / runs (counts, not rates; errors excluded): "
            + "; ".join(f"{k} {sum(v)}/{len(v)}" for k, v in counts.items()), ""]
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    sys.exit(main())

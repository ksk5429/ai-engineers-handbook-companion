"""run_trials.py without Ollama: dry runs (review H2), the v2 plan order (Section 8), per-call
JSONL rows and resume (M2), image deletion (M5), code hash (M8), stop rules and the hold flag.
The model call and the machine probes are replaced by fakes; nothing reaches the network."""

from __future__ import annotations

import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import helpers
import run_trials as rt


class Base(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        self.out = self.dir / "out"
        self.held = helpers.placeholder_heldout(self.dir / "held")
        env = {"HANDBOOK_HOLD_FLAG": str(self.dir / "no_such.flag"), "HANDBOOK_MAIN_GPU": "1"}
        self.env = mock.patch.dict(os.environ, env)
        self.env.start()
        self.quiet = contextlib.redirect_stdout(io.StringIO())
        self.quiet.__enter__()

    def tearDown(self) -> None:
        self.quiet.__exit__(None, None, None)
        self.env.stop()
        self.tmp.cleanup()


class DryRun(Base):
    def test_v1_dry_run_needs_no_ollama(self) -> None:
        with mock.patch.object(rt, "run_cmd", side_effect=AssertionError("no command in a dry run")), \
             mock.patch.object(rt, "call_ollama", side_effect=AssertionError("no model in a dry run")):
            self.assertEqual(rt.main(["--dry-run", "--out", str(self.out)]), 0)
        rec = json.loads((self.out / "PREFLIGHT.json").read_text("utf-8"))
        self.assertEqual(len(rec["rows"]), 12)
        self.assertTrue(all(r["preflight_decision_ok"] for r in rec["rows"]))
        self.assertEqual(rec["code_sha256"], rt.code_digest(rt.code_hashes()))
        self.assertEqual(rec["runtime"], "not queried (dry run)")
        self.assertFalse((self.out / "agent_images").exists())          # copies deleted (M5)

    def test_v2_dry_run_all_25(self) -> None:
        code = rt.main(["--protocol", "v2", "--dry-run", "--out", str(self.out), "--heldout-dir", str(self.held)])
        self.assertEqual(code, 0)
        rec = json.loads((self.out / "PREFLIGHT_v2.json").read_text("utf-8"))
        self.assertEqual(len(rec["rows"]), 25)
        self.assertTrue(all(r["preflight_decision_ok"] for r in rec["rows"]))
        self.assertTrue(all(r["t6_ok"] for r in rec["rows"] if r["arm"] == "P2"))
        blocked = sorted(r["task_id"] for r in rec["rows"] if r["preflight"]["action"] == "new_observation")
        self.assertEqual(blocked, ["E1_stale", "E2_wrong_window", "HC3_term_stale", "HC4_term_wrong_window"])

    def test_keep_images(self) -> None:
        rt.main(["--dry-run", "--out", str(self.out), "--keep-images"])
        names = sorted(p.name for p in (self.out / "agent_images").iterdir())
        self.assertTrue(all(n.startswith("img_") for n in names))
        self.assertEqual(len(names), 7)      # 7 distinct (image, selection) pairs among 9 screenshot trials

    def test_default_out_is_gitignored_runs(self) -> None:
        self.assertEqual(rt.DEFAULT_OUT, helpers.HERE / "runs")
        gitignore = (helpers.HERE.parent.parent / ".gitignore").read_text("utf-8")
        self.assertIn("examples/*/runs/", gitignore)


class Plan(Base):
    def test_block_h_then_d_seed_major(self) -> None:
        plan = rt.build_plan("v2", "all", [1, 2, 3], rt.SPEC_V2, self.held)
        self.assertEqual(len(plan), 75)
        keys = [(c.block, c.arm, c.seed) for c in plan]
        self.assertEqual(keys[:13], [("H", "P2", 1)] * 10 + [("H", "P1", 1)] * 3)
        self.assertEqual(sum(1 for k in keys if k[0] == "H"), 39)
        self.assertEqual(keys[39:], [("D", "P2", s) for s in (1, 2, 3) for _ in range(12)])
        self.assertEqual([c.trial.bundle.task_id for c in plan[10:13]],
                         ["HA3_sheet_typed_only", "HC2_term_typed_only", "HC5_term_voice_only"])

    def test_set_selection(self) -> None:
        self.assertEqual(len(rt.build_plan("v2", "heldout", [1], rt.SPEC_V2, self.held)), 13)
        self.assertEqual(len(rt.build_plan("v2", "dev", [1], rt.SPEC_V2, self.held)), 12)
        self.assertEqual(len(rt.build_plan("v1", "all", [1, 2], rt.SPEC_V2, None)), 24)

    def test_p1_arm_uses_prompt_v1(self) -> None:
        plan = rt.build_plan("v2", "heldout", [1], rt.SPEC_V2, self.held)
        p1 = [c for c in plan if c.arm == "P1"][0]
        self.assertIn("or missing, ask for a new screenshot", p1.prompt())
        p2 = [c for c in plan if c.arm == "P2"][0]
        self.assertIn("A screenshot is not required.", p2.prompt())


def fake_reply(decision: str = "clarify") -> dict:
    return {"raw": json.dumps({"decision": decision}), "parsed": {"decision": decision},
            "thinking": "t", "thinking_chars": 1, "wall_s": 0.0, "prompt_eval_count": 1, "eval_count": 1}


class Live(Base):
    def run_live(self, extra: list[str], call=None, machine: helpers.FakeMachine | None = None) -> int:
        machine = machine or helpers.FakeMachine()
        model = call or (lambda *a: fake_reply())

        def calling(*a):
            machine.call_made()
            return model(*a)
        with mock.patch.object(rt, "run_cmd", side_effect=machine), \
             mock.patch.object(rt, "call_ollama", side_effect=calling):
            return rt.main(["--protocol", "v2", "--set", "heldout", "--seeds", "1", "--out", str(self.out),
                            "--heldout-dir", str(self.held)] + extra)

    def jsonl(self) -> list[dict]:
        return [json.loads(x) for x in (self.out / "TRIALS_v2.jsonl").read_text("utf-8").splitlines()]

    def test_rows_written_per_call_and_crash_loses_nothing(self) -> None:
        n = {"calls": 0}

        def crash_on_fourth(*_a):
            n["calls"] += 1
            if n["calls"] == 4:
                raise RuntimeError("simulated crash")
            return fake_reply()
        with self.assertRaises(RuntimeError):
            self.run_live([], crash_on_fourth)
        calls = [r for r in self.jsonl() if r["kind"] == "call"]
        self.assertEqual(len(calls), 3)
        self.assertFalse((self.out / "agent_images").exists())          # deleted even after a crash
        self.assertEqual(self.run_live([]), 2)                          # refuses without --resume
        self.assertEqual(self.run_live(["--resume", "--think", "off"]), 2)   # settings must match
        with (self.out / "TRIALS_v2.jsonl").open("a", encoding="utf-8") as fh:
            fh.write('{"kind": "call", "key": "trunc')                  # crash during a write
        self.assertEqual(self.run_live(["--resume"]), 0)
        rows = rt.read_jsonl(self.out / "TRIALS_v2.jsonl")              # every line parses again
        self.assertEqual([r["dropped_partial_line"] for r in rows if r["kind"] == "repair"],
                         ['{"kind": "call", "key": "trunc'])
        calls = [r for r in rows if r["kind"] == "call"]
        self.assertEqual(len(calls), 13)
        self.assertEqual(len({c["key"] for c in calls}), 13)
        row = calls[0]
        self.assertEqual(row["code_sha256"], rt.code_digest(rt.code_hashes()))
        self.assertTrue(row["request"]["think"])
        self.assertEqual(row["request"]["options"]["main_gpu"], 1)
        self.assertEqual(row["reply"]["thinking"], "t")
        rec = json.loads((self.out / "TRIALS_v2.json").read_text("utf-8"))
        self.assertEqual(len(rec["rows"]), 13)
        self.assertIn("100% GPU", rec["ollama_ps_after_load"])

    def test_error_retried_once_then_recorded(self) -> None:
        self.assertEqual(self.run_live([], lambda *a: {"error": "timeout", "wall_s": 1.0}), 0)
        calls = [r for r in self.jsonl() if r["kind"] == "call"]
        self.assertTrue(all(r["status"] == "error" and r["reply"]["attempts"] == 2 for r in calls))
        self.assertTrue(all(r["score"] is None and r["pipeline_passed"] is None for r in calls))

    def test_model_loaded_before_window_refuses(self) -> None:
        machine = helpers.FakeMachine(preloaded=True)
        self.assertEqual(self.run_live([], lambda *a: self.fail("model called"), machine), 5)

    def test_partial_gpu_stops(self) -> None:
        self.assertEqual(self.run_live([], None, helpers.FakeMachine(processor="45%/55% CPU/GPU")), 5)
        self.assertEqual(len([r for r in self.jsonl() if r["kind"] == "call"]), 1)

    def test_model_on_gpu0_is_a_deviation(self) -> None:
        self.assertEqual(self.run_live([], None, helpers.FakeMachine(model_gpu=0)), 0)
        rec = json.loads((self.out / "TRIALS_v2.json").read_text("utf-8"))
        self.assertEqual(rec["placement"]["busiest_gpu_index"], 0)
        self.assertTrue(any("GPU 0" in d for d in rec["deviations"]))

    def test_placement_on_gpu1_no_deviation(self) -> None:
        self.assertEqual(self.run_live([]), 0)
        rec = json.loads((self.out / "TRIALS_v2.json").read_text("utf-8"))
        self.assertEqual((rec["placement"]["busiest_gpu_index"], rec["deviations"]), (1, []))

    def test_think_off_is_a_deviation(self) -> None:
        self.assertEqual(self.run_live(["--think", "off"]), 0)
        rec = json.loads((self.out / "TRIALS_v2.json").read_text("utf-8"))
        self.assertTrue(any("think off" in d for d in rec["deviations"]))

    def test_ollama_reply_shapes(self) -> None:
        """call_ollama on odd server responses (the HTTP layer is faked, nothing is sent)."""
        class Resp(io.BytesIO):
            def __enter__(self):
                return self

            def __exit__(self, *a):
                return False
        cases = [(b'{"message": null}', None), (b'[1, 2]', "unexpected response type"),
                 (b'{"message": {"content": "[1]"}}', None)]
        for body, err in cases:
            opener = mock.Mock(open=mock.Mock(return_value=Resp(body)))
            with mock.patch.object(rt.urllib.request, "build_opener", return_value=opener):
                r = rt.call_ollama("m", "p", None, 1, True)
            if err:
                self.assertIn(err, r["error"])
            else:
                self.assertIsNone(r["parsed"])
        import http.client
        opener = mock.Mock(open=mock.Mock(side_effect=http.client.IncompleteRead(b"x")))
        with mock.patch.object(rt.urllib.request, "build_opener", return_value=opener):
            self.assertIn("IncompleteRead", rt.call_ollama("m", "p", None, 1, True)["error"])

    def test_non_dict_parsed_is_unparsed(self) -> None:
        def listy(*_a):
            return {**fake_reply(), "raw": "[1]", "parsed": None, "parsed_type": "list"}
        self.assertEqual(self.run_live([], listy), 0)
        calls = [r for r in self.jsonl() if r["kind"] == "call"]
        self.assertTrue(all(r["score"]["passed"] is False for r in calls))

    def test_hold_flag_stops_before_any_call(self) -> None:
        flag = self.dir / "bench_hold.flag"
        flag.write_text("hold")
        with mock.patch.dict(os.environ, {"HANDBOOK_HOLD_FLAG": str(flag)}):
            self.assertEqual(self.run_live([], lambda *a: self.fail("model called under a hold")), 4)
        self.assertEqual([r["kind"] for r in self.jsonl()], ["stop"])

    def test_default_hold_flag_path(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            self.assertEqual(rt.hold_flag(), Path(r"C:\ProgramData\paperkit-locks\bench_hold.flag"))

    def test_main_gpu_required_for_v2_live(self) -> None:
        with mock.patch.dict(os.environ, {"HANDBOOK_MAIN_GPU": ""}):
            self.assertEqual(self.run_live([], lambda *a: self.fail("model called")), 2)

    def test_hot_gpu_stops(self) -> None:
        with mock.patch.object(rt, "gpu_temperatures", return_value={0: 87, 1: 50}):
            self.assertIn("GPU 0", rt.stop_reason())
        with mock.patch.object(rt, "gpu_temperatures", return_value=None):
            self.assertIn("unavailable", rt.stop_reason())
        with mock.patch.object(rt, "gpu_temperatures", return_value={0: 60, 1: 86}):
            self.assertIsNone(rt.stop_reason())

    def test_gate_blocks_live_run_when_images_missing(self) -> None:
        self.held = self.dir / "empty"
        self.assertEqual(self.run_live([], lambda *a: self.fail("model called")), 3)


if __name__ == "__main__":
    unittest.main()

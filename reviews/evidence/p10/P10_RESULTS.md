# P10 results (generated)

Generated 2026-11-09T07:19:10+00:00 by `examples/ref01_expense_report/experiments/p10_trials.py` under P10_PREREGISTRATION.md v1.0.

**Decision: NOT PROMOTED** (null: mechanism confirmed, not promoted)

- R1 failed: P(v2.1) - P(v1) = 0 < 3
- Dev gate: {"v2": {"G1": true, "G2": false, "G3": true}, "v2.1": {"G1": true, "G2": true, "G3": true}}
- Rules: {"R1": false, "R2": true, "R3": true, "R4": true}; new failure categories: []
- P (held-out correct deliverables of 15): {"v1": 0, "v2.1": 0}; held-out runs with a C3 failure: {"v1": 9, "v2.1": 0}
- One-sided Fisher p (information only): 1.0000

| Held-out claim | v1 | v2.1 |
|---|---|---|
| claim_heldout_1.json | 0 | 0 |
| claim_heldout_2.json | 0 | 0 |
| claim_heldout_3.json | 0 | 0 |

Windows: 3, total 1525.271 s (dev 490.682 s completed; dev 217.267 s completed; heldout 817.322 s completed).

## dev (S10, development evidence)

| Metric | v1 | v2 | v2.1 |
|---|---|---|---|
| runs | `10` | `10` | `10` |
| P_correct_deliverables | `0` | `1` | `0` |
| S1_label_match | `0` | `1` | `0` |
| S2_passed | `0` | `1` | `2` |
| schema_valid | `8` | `6` | `10` |
| S3_c3 | `{"runs": 6, "items": 12, "subcategories": {"rule_as_line": 12}}` | `{"runs": 0, "items": 0, "subcategories": {}}` | `{"runs": 0, "items": 0, "subcategories": {}}` |
| S4_failed_checks | `{"C6_decision_consistent": 6, "C3_quotes_in_source": 6, "C5_total_is_sum": 2}` | `{"C4_not_above_claimed": 3, "C6_decision_consistent": 3, "C5_total_is_sum": 2}` | `{"C4_not_above_claimed": 3, "C5_total_is_sum": 4, "C6_decision_consistent": 6}` |
| categories | `{"no_answer": 2, "text_reply": 2, "C6_decision_consistent": 6, "C5_total_is_sum": 2, "C3_quotes_in_source": 6}` | `{"C4_not_above_claimed": 3, "C6_decision_consistent": 3, "C5_total_is_sum": 2, "schema_violation": 4}` | `{"C5_total_is_sum": 4, "C4_not_above_claimed": 3, "C6_decision_consistent": 6}` |
| S5_tokens | `{"prompt_eval_count": {"n": 10, "median": 4888.0, "total": 54375}, "eval_count": {"n": 10, "median": 522.0, "total": 6320}}` | `{"prompt_eval_count": {"n": 10, "median": 5728.0, "total": 57401}, "eval_count": {"n": 10, "median": 480.0, "total": 6081}}` | `{"prompt_eval_count": {"n": 10, "median": 5052.0, "total": 53382}, "eval_count": {"n": 10, "median": 487.0, "total": 5626}}` |
| S6_wall_s | `{"run": {"n": 10, "median": 14.1053, "total": 169.798}, "driver_process": {"n": 10, "median": 18.3935, "total": 216.228}}` | `{"run": {"n": 10, "median": 12.773399999999999, "total": 155.806}, "driver_process": {"n": 10, "median": 17.877, "total": 200.847}}` | `{"run": {"n": 10, "median": 12.671700000000001, "total": 149.083}, "driver_process": {"n": 10, "median": 16.8285, "total": 186.307}}` |
| S7_model_calls | `{"n": 10, "median": 4.5, "total": 49}` | `{"n": 10, "median": 5.0, "total": 50}` | `{"n": 10, "median": 4.5, "total": 47}` |
| S8_citation_accuracy | `[12, 24]` | `[20, 20]` | `[30, 30]` |
| S9_checker | `{"rejected": 10}` | `{"rejected": 10}` | `{"rejected": 10}` |
| blocked_after_retry | `0` | `0` | `0` |
| retries | `0` | `0` | `0` |
| options_assertion_failed | `0` | `0` | `0` |

## heldout

| Metric | v1 | v2.1 |
|---|---|---|
| runs | `15` | `15` |
| P_correct_deliverables | `0` | `0` |
| S1_label_match | `0` | `0` |
| S2_passed | `1` | `1` |
| schema_valid | `13` | `11` |
| S3_c3 | `{"runs": 9, "items": 24, "subcategories": {"rule_as_line": 24}}` | `{"runs": 0, "items": 0, "subcategories": {}}` |
| S4_failed_checks | `{"C3_quotes_in_source": 9, "C4_not_above_claimed": 10, "C5_total_is_sum": 7, "C6_decision_consistent": 8}` | `{"C4_not_above_claimed": 10, "C5_total_is_sum": 5, "C6_decision_consistent": 7}` |
| categories | `{"C3_quotes_in_source": 9, "C4_not_above_claimed": 10, "no_answer": 1, "text_reply": 1, "C5_total_is_sum": 7, "C6_decision_consistent": 8, "schema_violation": 1}` | `{"C5_total_is_sum": 5, "C4_not_above_claimed": 10, "C6_decision_consistent": 7, "schema_violation": 3, "no_answer": 1, "text_reply": 1}` |
| S5_tokens | `{"prompt_eval_count": {"n": 15, "median": 6245, "total": 91449}, "eval_count": {"n": 15, "median": 674, "total": 12326}}` | `{"prompt_eval_count": {"n": 15, "median": 6763, "total": 98759}, "eval_count": {"n": 15, "median": 658, "total": 12558}}` |
| S6_wall_s | `{"run": {"n": 15, "median": 15.3633, "total": 293.073}, "driver_process": {"n": 15, "median": 19.732, "total": 347.807}}` | `{"run": {"n": 15, "median": 16.7582, "total": 303.19}, "driver_process": {"n": 15, "median": 22.329, "total": 373.109}}` |
| S7_model_calls | `{"n": 15, "median": 5, "total": 74}` | `{"n": 15, "median": 5, "total": 77}` |
| S8_citation_accuracy | `[23, 60]` | `[34, 49]` |
| S9_checker | `{"rejected": 14, "accepted": 1}` | `{"rejected": 15}` |
| blocked_after_retry | `0` | `0` |
| retries | `0` | `0` |
| options_assertion_failed | `0` | `0` |

One model, synthetic claims, 15 held-out runs per arm; Fisher p and the per-claim table are information only, not significance claims. Checker results are descriptive.

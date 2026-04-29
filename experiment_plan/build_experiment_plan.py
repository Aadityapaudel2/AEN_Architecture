from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "experiment_plan"
DATA = OUT / "data"
VIS = OUT / "visualizations"
CODE = OUT / "code_proposals"
COLAB = Path(r"N:\Research\colab_outputs")
CB075 = Path(r"N:\Research\currentCBs\cb07_5.py")


ANALYSIS = {
    "aime2025_07": [
        "Permutation cycle types / order divides 6",
        "Complete consensus on a count with a missing conjugacy-class case.",
        "All roles counted permutations whose cycle lengths divide 6, but omitted one legal cycle type. The method was right; the partition checklist was incomplete.",
        "Cycle-type partition checklist; conjugacy class formula; mandatory exhaustive partition ledger before final summation.",
        "enumerative completeness guard",
        False,
    ],
    "aime2025_09": [
        "Conditional probability on die-face sticker survival",
        "Aria/Artemis disagreed, denominator logic was unstable, but Athena finalized anyway.",
        "Reports disagree about valid sequence counts and denominator construction. The math failure is conditioning under overwrites: visible stickers are survival events, not independent face choices.",
        "State-space conditioning for overwrite processes; survival/no-future-hit events; denominator reconstruction by explicit face-state DP.",
        "conditional probability state DP",
        True,
    ],
    "aime2025_10": [
        "Rotated triangle and nonconvex hexagon area",
        "Open geometric/arithmetic blocker became a confident final answer.",
        "Both peer reports explicitly reported unresolved shoelace/orientation disagreement. Athena finalized from a non-closed geometry route.",
        "Circumcenter rotation coordinates; oriented shoelace for named vertex order; validate sign and winding before nearest-integer closeout.",
        "oriented geometry finish check",
        True,
    ],
    "aime2025_11": [
        "Maximizing grid adjacent differences",
        "Peer disagreement between two degree-sorting totals; Athena selected one.",
        "The route recognized bipartite separation but mishandled degree distribution by partition/color and assignment weights. Later runs recovered this, so it is a recoverable audit-route failure.",
        "Checkerboard partitions on 8x8 grid; degree counts by color; rearrangement inequality with signed degree weights.",
        "weighted rearrangement audit",
        False,
    ],
    "aime2025_15": [
        "Partitioning a 10x10 grid into rectangular cell loops",
        "False uniqueness proof for nested squares.",
        "The roles assumed the concentric-square decomposition was unique and did not enumerate strip/frame alternatives.",
        "Transfer/backtracking enumeration of loop tilings; boundary-frame recursion; counterexample search before uniqueness claims.",
        "tiling enumeration instead of uniqueness assertion",
        True,
    ],
    "aime2025_17": [
        "Directed path count in a ladder/diagonal graph without edge reuse",
        "Repeated false closeouts across every recorded AIME-2026 attempt.",
        "The controller repeatedly accepted high-confidence wrong answers. The underlying math needs graph-state transfer because no-repeated-edge couples local choices across columns.",
        "Transfer matrix on frontier states; directed edge-use constraints; compute N by column DP and only then take square root.",
        "state transfer for graph walks",
        True,
    ],
    "aime2025_18": [
        "Nonconvex pentagon coordinates and modular area filter",
        "Near miss by off-by-two count.",
        "The route likely had the right coordinate family but leaked boundary cases through strict inequalities or area divisibility.",
        "Coordinate parametrization of nonconvex pentagons; strict inequalities; modular area divisibility and endpoint audits.",
        "endpoint and inequality audit",
        False,
    ],
    "aime2025_21": [
        "Circle tangent to parabola, sum of possible radii",
        "Recoverable algebraic route failure.",
        "The failed run did not consistently reduce tangency to normal-distance conditions and sum all real radii. A later selected run solved it.",
        "Parabola normal parametrization; distance-to-center radius equation; discriminant/root-sum finish.",
        "analytic tangency normal route",
        False,
    ],
    "aime2025_23": [
        "Isosceles triangle incenter and integer side constraints",
        "Open trig/number-theory blocker finalized as a candidate.",
        "Peer reports identified a bad half-angle/inradius formula and unresolved integer constraints. The final answer was emitted despite no closed Diophantine route.",
        "Incenter perimeter formulas; half-angle identities; integer side constraints; rationality checks before minimization.",
        "geometry-to-Diophantine audit",
        False,
    ],
    "aime2025_24": [
        "Infinite decimal/geometric series floor modulo 1000",
        "Consensus on coefficient extraction with floor/carry error.",
        "The model extracted late coefficients but mishandled the tail/floor carry. The tail must be bounded tightly enough to know the floor modulo 1000.",
        "Series coefficient extraction; tail bounds; floor carry audit under multiplication by 10^100.",
        "floor/tail carry discipline",
        False,
    ],
    "aime2025_28": [
        "Counting cousin sets for finite integer sets",
        "Capacity lower bound mistaken for exact-achievability proof.",
        "The route proved a lower bound and enough capacity, then invented an exact construction. Exact target count requires structural counting.",
        "Matching-count DP for neighbor choices; exact construction counts; never use capacity as existence without a constructive count.",
        "exact combinatorial construction audit",
        False,
    ],
    "aime2025_29": [
        "Left-associative custom operation over compositions of 12",
        "Stable undercount by invariant-only reasoning.",
        "Reports compressed the process into a subtraction-sum invariant and did not enumerate accumulator states over all compositions.",
        "Dynamic programming over partial sum, accumulator value, and parity; composition enumeration; verify invariants against DP.",
        "state DP for custom operations",
        True,
    ],
    "aime2025_30": [
        "Ordered 7-tuples modulo 3 with cyclic cubic sum",
        "Enumeration acknowledged incomplete, then Athena finalized.",
        "Both peers reported unresolved enumeration under the mod-3 sum constraint. Athena emitted a number anyway.",
        "Modulo-3 enumeration; condition on total sum; truth tables for cyclic cubic terms; exhaustive 3^7 or compressed DP.",
        "finite-field exhaustive enumeration",
        True,
    ],
}


def ensure_dirs() -> None:
    for path in [DATA, VIS, CODE]:
        path.mkdir(parents=True, exist_ok=True)


def collect_records() -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for folder in sorted(p for p in COLAB.iterdir() if p.is_dir() and p.name.startswith("AIME-2026_export")):
        private_files = sorted(folder.glob("*_PRIVATE_FULL.csv"))
        if not private_files:
            continue
        df = pd.read_csv(private_files[0], dtype=str).fillna("")
        for _, row in df.iterrows():
            qid = str(row.get("id") or row.get("question_id") or "").strip()
            if not qid:
                continue
            payload_path = folder / "result_payloads" / f"{qid}.json"
            payload = {}
            if payload_path.exists():
                try:
                    payload = json.loads(payload_path.read_text(encoding="utf-8"))
                except Exception:
                    payload = {}
            state = payload.get("controller_state") or {}
            peer = state.get("peer_report_meta") or {}
            timing = payload.get("timing_summary") or {}
            token_proof = payload.get("token_proof") or {}
            role_tokens = token_proof.get("roles") or {}
            qnum = int(re.search(r"(\d+)$", qid).group(1))
            submitted = str(row.get("model_answer_normalized") or row.get("model_answer_raw") or row.get("model_submitted_answer") or "").strip()
            expected = str(row.get("expected_answer_normalized") or row.get("expected_answer") or "").strip()
            rows.append(
                {
                    "run": folder.name,
                    "qid": qid,
                    "problem_number": qnum,
                    "submitted": submitted,
                    "expected": expected,
                    "correct": str(row.get("correct", "")).strip().lower() == "true",
                    "status": str(row.get("status", "") or payload.get("status", "")),
                    "verified": str(row.get("verified", "") or payload.get("verified", "")),
                    "loops": int(float(str(row.get("loops") or payload.get("loop_index") or 0) or 0)),
                    "turns": int(float(str(row.get("turns") or payload.get("turn_index") or 0) or 0)),
                    "time_taken_seconds": float(str(row.get("time_taken_seconds") or payload.get("elapsed_seconds") or 0) or 0),
                    "sum_turn_wall_seconds": float(str(row.get("sum_turn_wall_seconds") or timing.get("sum_turn_wall_seconds") or 0) or 0),
                    "total_tokens": int(float(str(row.get("total_tokens") or token_proof.get("total_tokens") or 0) or 0)),
                    "peer_validation_status": str(state.get("peer_validation_status", "")),
                    "open_objections": " | ".join(str(x) for x in (state.get("open_objections") or [])),
                    "athena_candidate": str(state.get("athena_exact_candidate_answer", "") or state.get("athena_candidate_answer", "")),
                    "athena_confidence": str(state.get("athena_confidence_pct", "")),
                    "aria_candidate": str((peer.get("Aria") or {}).get("candidate_exact_integer", "")),
                    "aria_confidence": str((peer.get("Aria") or {}).get("confidence_pct", "")),
                    "artemis_candidate": str((peer.get("Artemis") or {}).get("candidate_exact_integer", "")),
                    "artemis_confidence": str((peer.get("Artemis") or {}).get("confidence_pct", "")),
                    "athena_tokens": int((role_tokens.get("solver") or {}).get("total_tokens", 0) or 0),
                    "aria_tokens": int((role_tokens.get("agent") or {}).get("total_tokens", 0) or 0),
                    "artemis_tokens": int((role_tokens.get("clerk") or {}).get("total_tokens", 0) or 0),
                    "payload_path": str(payload_path) if payload_path.exists() else "",
                    "transcript_path": str(row.get("transcript_path", "")),
                }
            )
    return pd.DataFrame(rows).sort_values(["problem_number", "run"]).reset_index(drop=True)


def snippet(lines: list[str], start: int, end: int) -> str:
    return "\n".join(f"{i:5}: {lines[i-1]}" for i in range(start, end + 1))


def write_svg_bar(path: Path, title: str, labels: list[str], values: list[int], color: str) -> None:
    width, height = 920, 360
    left, right, top, bottom = 70, 24, 52, 64
    chart_w, chart_h = width - left - right, height - top - bottom
    maxv = max(values) if values else 1
    gap = 6
    bar_w = max(8, (chart_w - gap * (len(values) - 1)) / max(1, len(values)))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#fff"/>',
        f'<text x="{left}" y="30" font-family="Segoe UI, Arial" font-size="20" font-weight="700" fill="#111827">{html.escape(title)}</text>',
        f'<line x1="{left}" y1="{height-bottom}" x2="{width-right}" y2="{height-bottom}" stroke="#cbd5e1"/>',
    ]
    for i, (label, value) in enumerate(zip(labels, values)):
        h = 0 if maxv == 0 else value / maxv * chart_h
        x = left + i * (bar_w + gap)
        y = height - bottom - h
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_w:.1f}" height="{h:.1f}" rx="3" fill="{color}"/>')
        parts.append(f'<text x="{x+bar_w/2:.1f}" y="{y-6:.1f}" text-anchor="middle" font-family="Segoe UI, Arial" font-size="11" fill="#111827">{value}</text>')
        parts.append(f'<text x="{x+bar_w/2:.1f}" y="{height-bottom+18}" text-anchor="middle" font-family="Segoe UI, Arial" font-size="10" fill="#334155" transform="rotate(-45 {x+bar_w/2:.1f},{height-bottom+18})">{html.escape(label)}</text>')
    parts.append("</svg>")
    path.write_text("\n".join(parts), encoding="utf-8")


def markdown_table(df: pd.DataFrame) -> str:
    cols = [str(col) for col in df.columns]
    lines = [
        "| " + " | ".join(cols) + " |",
        "| " + " | ".join("---" for _ in cols) + " |",
    ]
    for _, row in df.iterrows():
        cells = []
        for col in cols:
            text = str(row[col]).replace("\n", " ").replace("|", "\\|")
            cells.append(text)
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> None:
    ensure_dirs()
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    runs = collect_records()
    runs.to_csv(DATA / "aime2026_all_recorded_attempts.csv", index=False)

    full_run = "AIME-2026_export_full_dataset_30q_20260428-022518"
    full = runs[runs["run"].eq(full_run)].copy()
    full_fail = full[~full["correct"]].copy()
    rows = []
    for _, full_row in full_fail.iterrows():
        qid = str(full_row["qid"])
        topic, mode, wrong, material, axis, stable = ANALYSIS[qid]
        attempts = runs[runs["qid"].eq(qid)].sort_values("run")
        rows.append(
            {
                "qid": qid,
                "problem_number": int(full_row["problem_number"]),
                "expected": full_row["expected"],
                "full_run_answer": full_row["submitted"],
                "attempts": int(len(attempts)),
                "correct_attempts": int(attempts["correct"].sum()),
                "all_recorded_answers": ", ".join(attempts["submitted"].astype(str).tolist()),
                "stable_miss": bool(stable),
                "peer_validation_full_run": str(full_row["peer_validation_status"]),
                "athena_full_run": f"{full_row['athena_candidate']}/{full_row['athena_confidence']}",
                "aria_full_run": f"{full_row['aria_candidate']}/{full_row['aria_confidence']}",
                "artemis_full_run": f"{full_row['artemis_candidate']}/{full_row['artemis_confidence']}",
                "topic": topic,
                "failure_mode": mode,
                "what_went_wrong": wrong,
                "study_material": material,
                "v34_axis": axis,
            }
        )
    failures = pd.DataFrame(rows).sort_values(["stable_miss", "problem_number"], ascending=[False, True])
    failures.to_csv(DATA / "failure_diagnosis.csv", index=False)

    run_summary = runs.groupby("run").agg(
        rows=("qid", "count"),
        correct=("correct", "sum"),
        mean_loops=("loops", "mean"),
        mean_seconds=("time_taken_seconds", "mean"),
        mean_tokens=("total_tokens", "mean"),
    ).reset_index()
    run_summary["accuracy_percent"] = (run_summary["correct"] / run_summary["rows"] * 100).round(2)
    run_summary.to_csv(DATA / "run_summary.csv", index=False)

    q_summary = runs.groupby("qid").agg(
        problem_number=("problem_number", "first"),
        attempts=("qid", "count"),
        correct_attempts=("correct", "sum"),
        expected=("expected", lambda x: next((str(v) for v in x if str(v).strip()), "")),
        answers=("submitted", lambda x: ", ".join(str(v) for v in x)),
        max_loops=("loops", "max"),
        mean_tokens=("total_tokens", "mean"),
    ).reset_index()
    q_summary["failures"] = q_summary["attempts"] - q_summary["correct_attempts"]
    q_summary.to_csv(DATA / "problem_attempt_summary.csv", index=False)

    summary = {
        "generated_at_utc": generated,
        "recorded_attempts": int(len(runs)),
        "recorded_runs": int(runs["run"].nunique()),
        "full_run": full_run,
        "full_run_accuracy": {
            "correct": int(full["correct"].sum()),
            "rows": int(len(full)),
            "percent": round(float(full["correct"].sum()) / len(full) * 100, 2),
        },
        "stable_misses": failures[failures["stable_miss"]]["qid"].tolist(),
        "full_run_misses": failures["qid"].tolist(),
        "failures": failures.to_dict(orient="records"),
        "runs": run_summary.to_dict(orient="records"),
    }
    (DATA / "experiment_plan_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    write_svg_bar(VIS / "recorded_attempts_by_problem.svg", "Recorded attempts per full-run miss", failures["problem_number"].astype(str).tolist(), failures["attempts"].astype(int).tolist(), "#2563eb")
    write_svg_bar(VIS / "correct_attempts_by_problem.svg", "Correct attempts per full-run miss", failures["problem_number"].astype(str).tolist(), failures["correct_attempts"].astype(int).tolist(), "#16a34a")
    write_svg_bar(VIS / "full_run_misses_by_problem.svg", "Full-run miss set", failures["problem_number"].astype(str).tolist(), [1] * len(failures), "#dc2626")

    lines = CB075.read_text(encoding="utf-8").splitlines()
    controller = f"""# Controller Loop Closeout Proposal

Generated: {generated}

## Finding

`GLOBAL_MAX_BIG_LOOPS = 3` is read, but it is only an upper bound. The current closeout gate allows loop 1 to terminate whenever `selected_candidate != "none"` and `loop_no >= MIN_BIG_LOOP_FOR_CLOSEOUT`. With `GLOBAL_MIN_BIG_LOOP_FOR_CLOSEOUT = 1`, a mandatory Athena finalization answer can close the run even when peer validation remains `disagreement_open`, reports are collapsed, peer confidence is zero, or explicit objections exist.

This is why the loop knob looks inaccurate: the max-loop cap is respected by the `for` range, but the permissive closeout break fires before loop 2 can begin.

## Exact Current Snippets

### Knobs Are Read

```python
{snippet(lines, 240, 257)}
```

### Run Emits Simple Arbitration Contract

```python
{snippet(lines, 2627, 2644)}
```

The emitted `closeout_requires_exact_integer_consensus: False` is important. It documents that strict consensus is not currently required.

### Athena Mandatory Finalization Can Create A Candidate After Disagreement

```python
{snippet(lines, 2933, 3005)}
```

The finalizer creates an `athena_mandatory_final_answer_turn` arbitration result for any non-`none` Athena final answer.

### Current Closeout Gate

```python
{snippet(lines, 3013, 3057)}
```

Line 3040 is the missing link: it ignores `closeout_objections`, `peer_validation_status`, `final_trio_exact_alignment`, `final_confident_enough`, and `peers_confident_enough`.

## Proposed Pseudocode Patch

```python
closeout_ready = (
    int(loop_no) >= int(MIN_BIG_LOOP_FOR_CLOSEOUT)
    and str(selected_candidate) != "none"
    and not closeout_objections
    and str(state.get("peer_validation_status")) == "confidence_aligned"
    and bool(final_trio_exact_alignment)
    and bool(final_confident_enough)
    and bool(peers_confident_enough)
)

if closeout_ready:
    status = "closed_out_strict_confidence_aligned"
    verified = True
    submission_answer_override = str(selected_candidate)
    ...
    break

state["recent_summary"] = list(state.get("recent_summary") or [])[-12:]
state["peer_reasoning_log"] = list(state.get("peer_reasoning_log") or [])[-18:]
continue
```

## Optional Explicit Knobs

```python
GLOBAL_REQUIRE_CONFIDENCE_ALIGNED_CLOSEOUT = True
GLOBAL_REQUIRE_TRIO_EXACT_CLOSEOUT = True
GLOBAL_REQUIRE_NO_OPEN_OBJECTIONS_CLOSEOUT = True
GLOBAL_ALLOW_MANDATORY_FINALIZATION_FALLBACK_ON_LAST_LOOP = True
```

If the run reaches `MAX_BIG_LOOPS` and still has disagreement, the final answer can be exported as `verified=False` or as a separate fallback, but it should not be marked verified by simple arbitration.
"""
    (CODE / "controller_loop_closeout_proposal.md").write_text(controller, encoding="utf-8")

    next_config = """# Next-run controller knobs proposed for the V31/V34 experiment.

GLOBAL_MAX_BIG_LOOPS = 3
GLOBAL_MIN_BIG_LOOP_FOR_CLOSEOUT = 1
GLOBAL_CLOSEOUT_CONFIDENCE_PCT = 85
GLOBAL_INNER_TOTAL_EXCHANGES = 3
GLOBAL_MAX_TURN_TOKENS = 0

ATHENA_MAX_TOKENS = 50000
ARIA_MAX_TOKENS = 50000
ARTEMIS_MAX_TOKENS = 50000

ATHENA_OPEN_MAX_TOKENS = 10000
ATHENA_SYNTHESIS_MAX_TOKENS = 10000
ATHENA_FINAL_MAX_TOKENS = 256

PEER_EXCHANGE_MAX_TOKENS = 10000
PEER_REPORT_MAX_TOKENS = 10000
ARIA_EXCHANGE_MAX_TOKENS = 10000
ARTEMIS_EXCHANGE_MAX_TOKENS = 10000
ARIA_REPORT_MAX_TOKENS = 10000
ARTEMIS_REPORT_MAX_TOKENS = 10000

GLOBAL_SHOW_STREAMING = False
GLOBAL_PRINT_PROGRESS_LINES = True
GLOBAL_ENABLE_TOKEN_STREAMING = True
GLOBAL_STREAM_PRINT_ROLE_PREFIX = True
GLOBAL_STREAM_TOKEN_MODE = "word"

# Proposed additional closeout-safety toggles for review before code change:
GLOBAL_REQUIRE_CONFIDENCE_ALIGNED_CLOSEOUT = True
GLOBAL_REQUIRE_TRIO_EXACT_CLOSEOUT = True
GLOBAL_REQUIRE_NO_OPEN_OBJECTIONS_CLOSEOUT = True
GLOBAL_ALLOW_MANDATORY_FINALIZATION_FALLBACK_ON_LAST_LOOP = True
"""
    (CODE / "next_run_config.py").write_text(next_config, encoding="utf-8")

    proposal_sections = []
    for _, row in failures.iterrows():
        proposal_sections.append(f"""### {row['qid']}: {row['topic']}

Failure diagnosis: {row['what_went_wrong']}

Material to study: {row['study_material']}

Proposed answer-blind V34 boot records:

**Athena line**
```text
BOOT_RECORD role=Athena axis={row['v34_axis']} source={row['qid']}
When a problem matches this axis, do not finalize from a plausible route alone. Build the canonical route ledger, identify the exact state/enumeration object, and close only after every case class or algebraic branch has an auditable finish. If peer reports expose disagreement or an open blocker, convert the blocker into the next-loop work item rather than emitting a verified final answer.
```

**Aria line**
```text
BOOT_RECORD role=Aria axis={row['v34_axis']} source={row['qid']}
Provide the constructive solution route without relying on the final integer. For this axis, make the state table, case partition, recurrence, or coordinate formula explicit enough that Athena can reproduce it. Flag any capacity argument, symmetry shortcut, or inferred uniqueness claim that has not been backed by an exact enumeration or construction.
```

**Artemis line**
```text
BOOT_RECORD role=Artemis axis={row['v34_axis']} source={row['qid']}
Audit for the specific historical failure: {row['failure_mode']} Require a missing-case checklist, endpoint/carry check, or blocker resolution before supporting closeout. If confidence is high but the route has not discharged this audit, report an open blocker and keep the candidate unverified.
```
""")
    dataset = f"""# V34 Additive Runtime-at-Boot Dataset Proposal

Generated: {generated}

This proposal is additive. It should not replace V31/V33. The goal is to add answer-blind study records that teach *how* to solve the recurring failure axes without injecting final answers.

## Design Rule

The boot record may mention a problem axis and a historical failure mode, but the boot record should not encode the target contest answer. The intended improvement is route discipline: enumerate, audit, and refuse premature closeout.

## Priority Order

1. Stable misses with zero correct recorded AIME-2026 attempts: Q09, Q10, Q15, Q17, Q29, Q30.
2. Recoverable misses that were solved in at least one run but failed in the full run: Q07, Q11, Q18, Q21, Q23, Q24, Q28.
3. Controller closeout fix before large-scale V34 scoring. The dataset can teach caution, but the controller must stop marking open-blocker finalizations as verified.

## Proposed Records

{''.join(proposal_sections)}
"""
    (OUT / "dataset_proposal_v34.md").write_text(dataset, encoding="utf-8")

    table = markdown_table(
        failures[
            [
                "qid",
                "expected",
                "full_run_answer",
                "attempts",
                "correct_attempts",
                "stable_miss",
                "peer_validation_full_run",
                "topic",
                "failure_mode",
            ]
        ]
    )
    readme = f"""# Experiment Plan: V31 Runtime-at-Boot to V34 Additive Repair

Generated: {generated}

This folder prepares the next big run. It is centered on performance-enhancing ideas, not a retroactive paper claim.

## Open The UI

Start with [`index.html`](index.html). It gives the compact dashboard, the failure table, and links to the code and dataset proposals.

## Main Verdict

- V31/V33 Runtime-at-Boot should be preserved as the canonical base.
- V34 should be additive: small answer-blind route-study records aimed at stable miss axes.
- The concrete controller issue is closeout, not boot-read failure. CB8 has certified that the roles read the boot data.
- `GLOBAL_MAX_BIG_LOOPS = 3` is only a cap. Current CB7.5 closes at loop 1 whenever Athena finalization produces a selected candidate and `MIN_BIG_LOOP_FOR_CLOSEOUT <= 1`.
- Before a giant V34 run, review [`code_proposals/controller_loop_closeout_proposal.md`](code_proposals/controller_loop_closeout_proposal.md).

## Recorded Full-Run Baseline

Full run: `{full_run}`

Accuracy: {summary['full_run_accuracy']['correct']}/{summary['full_run_accuracy']['rows']} = {summary['full_run_accuracy']['percent']}%

Full-run misses: {', '.join(failures['qid'].tolist())}

Stable misses with no correct recorded AIME-2026 attempt: {', '.join(failures[failures['stable_miss']]['qid'].tolist())}

## Failure Table

{table}

## Folder Map

- [`index.html`](index.html): visual planning UI.
- [`dataset_proposal_v34.md`](dataset_proposal_v34.md): answer-blind V34 additive boot-record proposal for Athena, Aria, and Artemis.
- [`code_proposals/controller_loop_closeout_proposal.md`](code_proposals/controller_loop_closeout_proposal.md): exact current CB7.5 line references and pseudocode patch.
- [`code_proposals/next_run_config.py`](code_proposals/next_run_config.py): next-run knob block plus proposed closeout-safety toggles.
- [`data/aime2026_all_recorded_attempts.csv`](data/aime2026_all_recorded_attempts.csv): all parsed AIME-2026 attempts found under `N:\\Research\\colab_outputs`.
- [`data/failure_diagnosis.csv`](data/failure_diagnosis.csv): concise diagnosis table.
- [`data/problem_attempt_summary.csv`](data/problem_attempt_summary.csv): per-problem attempt matrix.
- [`data/run_summary.csv`](data/run_summary.csv): per-run score/timing summary.
- [`data/experiment_plan_summary.json`](data/experiment_plan_summary.json): UI source summary.
- [`visualizations/`](visualizations/): SVG summary figures.
"""
    (OUT / "README.md").write_text(readme, encoding="utf-8")

    def td(x: object) -> str:
        return f"<td>{html.escape(str(x))}</td>"

    rows_html = "\n".join(
        "<tr>" + "".join(td(row[col]) for col in ["qid", "expected", "full_run_answer", "attempts", "correct_attempts", "stable_miss", "peer_validation_full_run", "v34_axis"]) + "</tr>"
        for _, row in failures.iterrows()
    )
    cards = "\n".join(
        f"""<article class="case-card {'stable' if row['stable_miss'] else 'recoverable'}">
<div class="case-kicker">{html.escape(row['qid'])} - expected {html.escape(str(row['expected']))} - full run {html.escape(str(row['full_run_answer']))}</div>
<h3>{html.escape(row['topic'])}</h3>
<p><strong>What went wrong:</strong> {html.escape(row['what_went_wrong'])}</p>
<p><strong>Study material:</strong> {html.escape(row['study_material'])}</p>
</article>"""
        for _, row in failures.iterrows()
    )
    index = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>AEN Experiment Plan · V34 Additive Repair</title>
<style>
:root{{--ink:#111827;--muted:#475569;--line:#d8dee9;--panel:#fff;--red:#b91c1c;--blue:#1d4ed8;--green:#15803d}}
*{{box-sizing:border-box}} body{{margin:0;font-family:Segoe UI,Arial,sans-serif;color:var(--ink);background:#eef2f7;line-height:1.45}}
header{{padding:34px 28px 22px;background:#0f172a;color:white}} header h1{{margin:0 0 8px;font-size:34px;letter-spacing:0}} header p{{margin:0;max-width:1050px;color:#cbd5e1}}
main{{max-width:1220px;margin:0 auto;padding:24px}} .grid{{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:14px}}
.metric,section{{background:var(--panel);border:1px solid var(--line);border-radius:8px}} .metric{{padding:16px}} .metric .label{{color:var(--muted);font-size:13px}} .metric .value{{font-size:28px;font-weight:800;margin-top:4px}}
section{{padding:20px;margin-top:18px}} h2{{margin:0 0 12px;font-size:22px}} a{{color:var(--blue)}} .callout{{border-left:5px solid var(--red);background:#fff7ed;padding:14px 16px;margin:14px 0}}
.table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:8px}} table{{border-collapse:collapse;width:100%;min-width:960px}} th,td{{border-bottom:1px solid var(--line);padding:10px 12px;text-align:left;vertical-align:top}} th{{background:#f1f5f9;font-size:13px}}
.case-grid{{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}} .case-card{{border:1px solid var(--line);border-radius:8px;padding:16px;background:#fff}} .case-card.stable{{border-left:5px solid var(--red)}} .case-card.recoverable{{border-left:5px solid var(--green)}} .case-kicker{{color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.04em}} .case-card h3{{margin:8px 0;font-size:18px}}
.figures,.code-links{{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px}} .figures img{{width:100%;border:1px solid var(--line);border-radius:8px;background:white}} .code-links a{{display:block;padding:14px;border:1px solid var(--line);border-radius:8px;background:#f8fafc;text-decoration:none;font-weight:700}}
@media(max-width:900px){{.grid,.figures,.case-grid,.code-links{{grid-template-columns:1fr}} header h1{{font-size:28px}}}}
</style></head><body>
<header><h1>AEN V34 Experiment Plan</h1><p>Preparing the next big run from certified Runtime-at-Boot V31/V33: preserve the canonical base, add answer-blind route-study records, and fix the controller closeout path that exits at loop 1 despite open blockers.</p></header>
<main>
<div class="grid"><div class="metric"><div class="label">Recorded AIME-2026 attempts</div><div class="value">{len(runs)}</div></div><div class="metric"><div class="label">Recorded run folders</div><div class="value">{runs['run'].nunique()}</div></div><div class="metric"><div class="label">Full-run accuracy</div><div class="value">{summary['full_run_accuracy']['correct']}/{summary['full_run_accuracy']['rows']}</div></div><div class="metric"><div class="label">Stable zero-correct misses</div><div class="value">{int(failures['stable_miss'].sum())}</div></div></div>
<section><h2>Decision Point</h2><div class="callout"><strong>The loop knob is not broken as a cap.</strong> It is bypassed by a permissive closeout condition: loop 1 closes whenever Athena finalization yields any selected candidate and <code>GLOBAL_MIN_BIG_LOOP_FOR_CLOSEOUT = 1</code>.</div><p>Review the exact line references and pseudocode in <a href="code_proposals/controller_loop_closeout_proposal.md">controller_loop_closeout_proposal.md</a>.</p></section>
<section><h2>Failure Matrix</h2><div class="table-wrap"><table><thead><tr><th>Problem</th><th>Expected</th><th>Full-run answer</th><th>Attempts</th><th>Correct attempts</th><th>Stable miss</th><th>Peer status</th><th>V34 axis</th></tr></thead><tbody>{rows_html}</tbody></table></div></section>
<section><h2>Figures</h2><div class="figures"><img src="visualizations/recorded_attempts_by_problem.svg" alt="Recorded attempts by problem"><img src="visualizations/correct_attempts_by_problem.svg" alt="Correct attempts by problem"><img src="visualizations/full_run_misses_by_problem.svg" alt="Full run misses by problem"></div></section>
<section><h2>Failure Diagnoses</h2><div class="case-grid">{cards}</div></section>
<section><h2>Plan Files</h2><div class="code-links"><a href="dataset_proposal_v34.md">V34 additive dataset proposal</a><a href="code_proposals/controller_loop_closeout_proposal.md">Controller closeout proposal</a><a href="code_proposals/next_run_config.py">Next-run knob block</a></div></section>
</main></body></html>
"""
    (OUT / "index.html").write_text(index, encoding="utf-8")

    nav = REPO / "NAVIGATION.md"
    nav_text = nav.read_text(encoding="utf-8") if nav.exists() else ""
    if "experiment_plan/README.md" not in nav_text:
        nav.write_text(nav_text.rstrip() + "\n- [Experiment Plan](experiment_plan/README.md) - April 29 V34 additive Runtime-at-Boot repair plan, failure diagnosis UI, and controller closeout proposal.\n", encoding="utf-8")

    readme_path = REPO / "README.md"
    root_readme = readme_path.read_text(encoding="utf-8") if readme_path.exists() else ""
    if "experiment_plan/" not in root_readme:
        readme_path.write_text(root_readme.rstrip() + "\n\n## Current Experiment Planning\n\nThe April 29 V34 planning package is in [`experiment_plan/`](experiment_plan/README.md). It analyzes recorded transcript failures, proposes answer-blind Runtime-at-Boot additions, and isolates the CB7.5 closeout condition that prevents `GLOBAL_MAX_BIG_LOOPS=3` from producing additional loops.\n", encoding="utf-8")

    docs_index = REPO / "docs" / "index.md"
    if docs_index.exists():
        docs_text = docs_index.read_text(encoding="utf-8")
        if "experiment_plan/" not in docs_text:
            docs_index.write_text(docs_text.rstrip() + "\n\n## Experiment Planning\n\nThe April 29 V34 planning package is available in [`experiment_plan`](../experiment_plan/README.md): it contains the failure diagnosis dashboard, proposed answer-blind boot additions, and a controller closeout patch proposal.\n", encoding="utf-8")

    print(json.dumps({"created": str(OUT), "records": len(runs), "failures": len(failures), "stable": int(failures["stable_miss"].sum())}, indent=2))


if __name__ == "__main__":
    main()

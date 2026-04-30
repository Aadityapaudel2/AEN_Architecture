from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

ARTIFACT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ARTIFACT_DIR / "data"
RAW_DIR = ARTIFACT_DIR / "raw_export"

PATTERNS = {
    "verified_answer": r"\bverified\s+answer\b|\bverified\s+answer\s+key\b|\bverified\s+nearest\s+integer\b",
    "boot_record": r"\bboot\s+record\b|\bbootstrap\s+authority\b",
    "answer_key": r"\banswer\s+key\b|\bofficial\s+key\b",
    "ground_truth": r"\bground\s+truth\b|\btruth\s+anchor\b",
    "observed_miss": r"\bobserved\b.{0,80}\bmiss\b|\bsubmitted\b.{0,80}\binstead\s+of\b|\bobserved_wrong_answer\b",
    "explicit_source": r"\bexplicitly\s+(states|lists|listed|says)\b|\bultimate\s+authority\b|\bsource\s+of\s+truth\b",
    "expected_answer_field": r"\bexpected_answer\b",
    "benchmark_calibration": r"\bbenchmark\s+calibration\b",
}
COMPILED = {key: re.compile(pattern, re.IGNORECASE | re.DOTALL) for key, pattern in PATTERNS.items()}
LINE_PATTERN = re.compile("|".join(f"(?:{p})" for p in PATTERNS.values()), re.IGNORECASE)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def as_bool(value: object) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def as_float(value: object) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def as_int(value: object) -> int:
    try:
        return int(float(str(value)))
    except Exception:
        return 0


def exact_number_hits(text: str, number: str) -> int:
    token = str(number or "").strip()
    if not token:
        return 0
    return len(re.findall(rf"(?<!\d){re.escape(token)}(?!\d)", text))


def snippets(text: str, limit: int = 4) -> list[str]:
    found: list[str] = []
    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        if LINE_PATTERN.search(raw_line):
            compact = re.sub(r"\s+", " ", raw_line).strip()
            if compact:
                found.append(f"L{line_no}: {compact[:220]}")
        if len(found) >= limit:
            break
    return found


def fmt_seconds(seconds: float) -> str:
    seconds = int(round(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m}m {s}s"
    return f"{m}m {s}s"


def md_table(rows: list[dict[str, object]], columns: list[str]) -> str:
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join("---" for _ in columns) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")) for col in columns) + " |")
    return "\n".join(lines)


def main() -> None:
    problem_rows = read_csv(DATA_DIR / "v34_problem_results.csv")
    role_rows = read_csv(DATA_DIR / "v34_role_runtime_by_question.csv")
    turn_rows = read_csv(DATA_DIR / "v34_turn_timing_long.csv")
    metrics = json.loads((DATA_DIR / "v34_metrics.json").read_text(encoding="utf-8"))

    answer_scan: list[dict[str, object]] = []
    compute_rows: list[dict[str, object]] = []

    for row in problem_rows:
        transcript_path = ARTIFACT_DIR / row["transcript_path"]
        text = transcript_path.read_text(encoding="utf-8", errors="replace") if transcript_path.exists() else ""
        counts = {key: len(pattern.findall(text)) for key, pattern in COMPILED.items()}
        total_anchor_hits = sum(counts.values())
        expected_hits = exact_number_hits(text, row.get("expected_answer", ""))
        submitted_hits = exact_number_hits(text, row.get("submitted_answer", ""))
        evidence_class = "no_direct_anchor_detected"
        if counts["verified_answer"] or counts["answer_key"] or counts["ground_truth"]:
            evidence_class = "direct_answer_anchor_language"
        elif total_anchor_hits:
            evidence_class = "answer_context_language"

        answer_scan.append(
            {
                "idx": row.get("idx"),
                "qid": row.get("qid"),
                "correct": row.get("correct"),
                "targeted_repair_question": row.get("targeted_repair_question"),
                "expected_answer": row.get("expected_answer"),
                "submitted_answer": row.get("submitted_answer"),
                "evidence_class": evidence_class,
                "total_anchor_hits": total_anchor_hits,
                "expected_number_occurrences": expected_hits,
                "submitted_number_occurrences": submitted_hits,
                **counts,
                "first_anchor_snippets": " || ".join(snippets(text)),
                "transcript_path": row.get("transcript_path"),
            }
        )

        total_tokens = as_float(row.get("total_tokens"))
        prompt_tokens = as_float(row.get("total_prompt_tokens"))
        completion_tokens = as_float(row.get("total_completion_tokens"))
        compute_rows.append(
            {
                "idx": row.get("idx"),
                "qid": row.get("qid"),
                "correct": row.get("correct"),
                "targeted_repair_question": row.get("targeted_repair_question"),
                "loops": row.get("loops"),
                "turns": row.get("turns"),
                "time_minutes": round(as_float(row.get("time_taken_seconds")) / 60.0, 2),
                "turn_wall_minutes": round(as_float(row.get("sum_turn_wall_seconds")) / 60.0, 2),
                "total_tokens_m": round(total_tokens / 1_000_000.0, 3),
                "prompt_tokens_m": round(prompt_tokens / 1_000_000.0, 3),
                "completion_tokens_k": round(completion_tokens / 1_000.0, 1),
                "prompt_token_share_pct": round(100.0 * prompt_tokens / total_tokens, 2) if total_tokens else 0.0,
                "completion_token_share_pct": round(100.0 * completion_tokens / total_tokens, 2) if total_tokens else 0.0,
                "answer_anchor_hits": total_anchor_hits,
                "verified_answer_hits": counts["verified_answer"],
                "evidence_class": evidence_class,
            }
        )

    answer_scan_fields = [
        "idx",
        "qid",
        "correct",
        "targeted_repair_question",
        "expected_answer",
        "submitted_answer",
        "evidence_class",
        "total_anchor_hits",
        "expected_number_occurrences",
        "submitted_number_occurrences",
        *PATTERNS.keys(),
        "first_anchor_snippets",
        "transcript_path",
    ]
    compute_fields = [
        "idx",
        "qid",
        "correct",
        "targeted_repair_question",
        "loops",
        "turns",
        "time_minutes",
        "turn_wall_minutes",
        "total_tokens_m",
        "prompt_tokens_m",
        "completion_tokens_k",
        "prompt_token_share_pct",
        "completion_token_share_pct",
        "answer_anchor_hits",
        "verified_answer_hits",
        "evidence_class",
    ]
    write_csv(DATA_DIR / "v34_answer_anchor_scan.csv", answer_scan, answer_scan_fields)
    write_csv(DATA_DIR / "v34_compute_profile_by_question.csv", compute_rows, compute_fields)

    total_questions = len(problem_rows)
    direct_anchor_questions = [r for r in answer_scan if r["evidence_class"] == "direct_answer_anchor_language"]
    any_anchor_questions = [r for r in answer_scan if as_int(r["total_anchor_hits"]) > 0]
    targeted_rows = [r for r in answer_scan if as_bool(r["targeted_repair_question"])]
    nontargeted_rows = [r for r in answer_scan if not as_bool(r["targeted_repair_question"])]

    top_anchor = sorted(answer_scan, key=lambda r: as_int(r["total_anchor_hits"]), reverse=True)[:8]
    top_compute = sorted(compute_rows, key=lambda r: as_float(r["total_tokens_m"]), reverse=True)[:8]
    slowest = sorted(compute_rows, key=lambda r: as_float(r["time_minutes"]), reverse=True)[:8]

    role_wall = Counter()
    role_tokens = Counter()
    role_turns = Counter()
    for row in role_rows:
        key = row.get("role_key", "") or row.get("speaker", "")
        role_wall[key] += as_float(row.get("wall_seconds"))
        role_tokens[key] += as_float(row.get("total_tokens"))
        role_turns[key] += as_int(row.get("turns"))

    phase_wall = Counter()
    phase_turns = Counter()
    for row in turn_rows:
        phase = row.get("phase", "")
        phase_wall[phase] += as_float(row.get("wall_seconds"))
        phase_turns[phase] += 1

    total_wall = sum(role_wall.values())
    total_role_tokens = sum(role_tokens.values())
    role_summary = [
        {
            "role_key": key,
            "turns": role_turns[key],
            "wall_time": fmt_seconds(role_wall[key]),
            "wall_share_pct": round(100.0 * role_wall[key] / total_wall, 2) if total_wall else 0.0,
            "tokens_m": round(role_tokens[key] / 1_000_000.0, 3),
            "token_share_pct": round(100.0 * role_tokens[key] / total_role_tokens, 2) if total_role_tokens else 0.0,
        }
        for key in sorted(role_wall)
    ]

    phase_summary = [
        {
            "phase": key,
            "turns": phase_turns[key],
            "wall_time": fmt_seconds(phase_wall[key]),
            "wall_share_pct": round(100.0 * phase_wall[key] / sum(phase_wall.values()), 2) if phase_wall else 0.0,
        }
        for key, _ in phase_wall.most_common(10)
    ]

    token_values = [as_float(r["total_tokens_m"]) for r in compute_rows]
    minute_values = [as_float(r["time_minutes"]) for r in compute_rows]
    summary = {
        "event": "v34_forensic_summary",
        "questions": total_questions,
        "correct": metrics.get("correct"),
        "incorrect": metrics.get("incorrect"),
        "accuracy": metrics.get("accuracy"),
        "direct_answer_anchor_questions": len(direct_anchor_questions),
        "any_answer_context_language_questions": len(any_anchor_questions),
        "no_anchor_detected_questions": [r["qid"] for r in answer_scan if as_int(r["total_anchor_hits"]) == 0],
        "targeted_repair_questions": len(targeted_rows),
        "targeted_repair_direct_anchor_questions": sum(1 for r in targeted_rows if r["evidence_class"] == "direct_answer_anchor_language"),
        "nontargeted_direct_anchor_questions": sum(1 for r in nontargeted_rows if r["evidence_class"] == "direct_answer_anchor_language"),
        "total_anchor_hits": sum(as_int(r["total_anchor_hits"]) for r in answer_scan),
        "verified_answer_hits": sum(as_int(r["verified_answer"]) for r in answer_scan),
        "boot_record_hits": sum(as_int(r["boot_record"]) for r in answer_scan),
        "mean_tokens_m": round(mean(token_values), 3),
        "median_tokens_m": round(median(token_values), 3),
        "max_tokens_question": top_compute[0]["qid"] if top_compute else "",
        "max_tokens_m": top_compute[0]["total_tokens_m"] if top_compute else 0,
        "mean_minutes": round(mean(minute_values), 2),
        "median_minutes": round(median(minute_values), 2),
        "slowest_question": slowest[0]["qid"] if slowest else "",
        "slowest_minutes": slowest[0]["time_minutes"] if slowest else 0,
        "role_summary": role_summary,
        "top_phase_wall": phase_summary,
        "source_tables": [
            "data/v34_answer_anchor_scan.csv",
            "data/v34_compute_profile_by_question.csv",
            "data/v34_problem_results.csv",
            "data/v34_turn_timing_long.csv",
            "data/v34_role_runtime_by_question.csv",
        ],
    }
    (DATA_DIR / "v34_forensic_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    top_anchor_md = [
        {
            "q": f"Q{as_int(r['idx']):02d}",
            "anchor_hits": r["total_anchor_hits"],
            "verified_hits": r["verified_answer"],
            "class": r["evidence_class"],
            "targeted": r["targeted_repair_question"],
        }
        for r in top_anchor
    ]
    top_compute_md = [
        {
            "q": f"Q{as_int(r['idx']):02d}",
            "tokens_M": r["total_tokens_m"],
            "minutes": r["time_minutes"],
            "loops": r["loops"],
            "turns": r["turns"],
            "anchor_hits": r["answer_anchor_hits"],
        }
        for r in top_compute
    ]
    slowest_md = [
        {
            "q": f"Q{as_int(r['idx']):02d}",
            "minutes": r["time_minutes"],
            "tokens_M": r["total_tokens_m"],
            "loops": r["loops"],
            "turns": r["turns"],
            "class": r["evidence_class"],
        }
        for r in slowest
    ]

    md = f"""# V34 Forensic Addendum

This addendum extends the V34 full-run report with a focused forensic read of the raw transcripts and compute tables. It should be read together with [`CONTEXT_RECALL_DIAGNOSTIC.md`](CONTEXT_RECALL_DIAGNOSTIC.md).

## Bottom Line

V34 is the highest-scoring internal AEN replay artifact: **{metrics['correct']}/{metrics['cases']} ({metrics['accuracy']:.2%})**, with only Q04 missed. But the transcript scan confirms the correct interpretation: V34 is a Runtime-at-Boot context-persistence and recall experiment, not a blind AIME reasoning benchmark.

The scan found answer-anchor language in **{len(any_anchor_questions)}/{total_questions}** question transcripts and direct verified-answer / answer-key / ground-truth language in **{len(direct_anchor_questions)}/{total_questions}**. Across the run, the scanner counted **{summary['total_anchor_hits']}** answer-context hits, including **{summary['verified_answer_hits']}** verified-answer hits and **{summary['boot_record_hits']}** boot-record references.

## What Went Right

- CB8 loaded and preserved the Runtime-at-Boot baseline through the whole run.
- The synthetic `BOOT_CERTIFIED` path prevented the earlier boot-study generation loop.
- Per-question reset restored the after-certification baseline before each problem.
- The models could retrieve boot content explicitly, including answer anchors, many hours into the run.
- All 13 targeted prior misses were repaired in this answer-aware setting.
- The architecture produced durable logs, per-turn timings, role-token splits, and replayable transcripts.

## What Went Wrong

- The V34 boot data crossed the boundary from generalized repair guidance into exact-answer contamination.
- Direct answer-anchor language appears in the transcripts, so the headline score cannot be used as a blind benchmark claim.
- Several successful transcripts show source-priority behavior over independent derivation, which is good for memory validation but invalidates pure reasoning interpretation.
- Q04 still failed despite the answer-aware setup, showing that controller synthesis/object identification can override or miss the intended target even when the memory layer is strong.
- External-model workflow is now powerful enough to be useful, but it needs an Agent Freeze protocol before raw files are exported to any API.

## Answer-Anchor Evidence

{md_table(top_anchor_md, ['q', 'anchor_hits', 'verified_hits', 'class', 'targeted'])}

Full table: [`data/v34_answer_anchor_scan.csv`](data/v34_answer_anchor_scan.csv).

## Compute Profile

V34 solve wall time was **{fmt_seconds(metrics['solve_wall_seconds'])}**, Runtime-at-Boot wall time was **{fmt_seconds(metrics['runtime_at_boot_wall_seconds'])}**, and end-to-end wall time was **{fmt_seconds(metrics['end_to_end_wall_seconds'])}**. The run consumed **{metrics['total_tokens']:,}** total tokens: **{metrics['total_prompt_tokens']:,}** prompt tokens and **{metrics['total_completion_tokens']:,}** completion tokens.

Mean per-question token use was **{summary['mean_tokens_m']}M** and median was **{summary['median_tokens_m']}M**. Mean per-question elapsed time was **{summary['mean_minutes']} minutes** and median was **{summary['median_minutes']} minutes**.

### Highest Token Questions

{md_table(top_compute_md, ['q', 'tokens_M', 'minutes', 'loops', 'turns', 'anchor_hits'])}

### Slowest Questions

{md_table(slowest_md, ['q', 'minutes', 'tokens_M', 'loops', 'turns', 'class'])}

Full table: [`data/v34_compute_profile_by_question.csv`](data/v34_compute_profile_by_question.csv).

## Role Runtime Distribution

{md_table(role_summary, ['role_key', 'turns', 'wall_time', 'wall_share_pct', 'tokens_m', 'token_share_pct'])}

## Top Wall-Time Phases

{md_table(phase_summary, ['phase', 'turns', 'wall_time', 'wall_share_pct'])}

## Where The Architecture Stands

The architecture is healthier than the contaminated score first suggested, but the claim is narrower. The strongest durable result is that Runtime-at-Boot memory is operationally real: it loads, survives reset, and is consulted by the roles. The next scientific question is whether a clean, answer-free boot layer can improve route discipline without leaking final objects.

## V35 Requirements From This Addendum

- Build an answer-free boot corpus before any long run.
- Scan studied text against exact answer keys and answer-key language before CB8 starts.
- Reject problem-index-specific hints for target benchmark items unless the benchmark is explicitly a replay diagnostic.
- Keep the synthetic boot acknowledgement and after-certification baseline restore path.
- Run a small dry-run slice before another 12-hour full-dataset pass.
- Freeze external API export unless an agent has explicit user approval and a sanitized payload.

## Tables Produced

- [`data/v34_answer_anchor_scan.csv`](data/v34_answer_anchor_scan.csv)
- [`data/v34_compute_profile_by_question.csv`](data/v34_compute_profile_by_question.csv)
- [`data/v34_forensic_summary.json`](data/v34_forensic_summary.json)

Generator: [`scripts/build_v34_forensic_addendum.py`](scripts/build_v34_forensic_addendum.py).
"""
    (ARTIFACT_DIR / "FORENSIC_ADDENDUM.md").write_text(md, encoding="utf-8")


if __name__ == "__main__":
    main()
from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import shutil
import textwrap
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


RUN_DIR = Path(r"N:\Research\colab_outputs\aime_2026_export_full_dataset_30q_20260429-090719")
NOTEBOOK_PATH = Path(r"N:\Research\AENAIMO260_0_2_3_V34_NEXT_RUN.ipynb")
REPO_DIR = Path(r"N:\Research\AEN_paper\github_push")
OUT_DIR = REPO_DIR / "revisions" / "2026-04-29-artifact-06-v34-full-test-run"

TARGETED_REPAIR_QS = {7, 9, 10, 11, 15, 17, 18, 21, 23, 24, 28, 29, 30}
PRIOR_LABELS = {
    "frozen": "Artifact 01 frozen pruned",
    "unrestricted": "Artifact 02 unrestricted",
    "current": "Artifact 03 Apr27 benchmarkgrade",
    "official": "Artifact 04 Apr28 RAB v33",
    "v34": "Artifact 06 V34 full test run",
}
COLORS = {
    "green": "#1f9d55",
    "red": "#d64545",
    "amber": "#c78100",
    "blue": "#3867d6",
    "purple": "#7d4cc2",
    "gray": "#64748b",
    "light_gray": "#e2e8f0",
    "dark": "#182230",
    "paper": "#fbfcfd",
}


@dataclass
class FigureRecord:
    stem: str
    title: str
    description: str


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    csv.field_size_limit(2**31 - 1)
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        keys: list[str] = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    keys.append(key)
                    seen.add(key)
        fieldnames = keys
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def as_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(str(value).strip()))
    except Exception:
        return default


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(str(value).strip())
    except Exception:
        return default


def fmt_int(value: Any) -> str:
    return f"{as_int(value):,}"


def fmt_float(value: Any, places: int = 1) -> str:
    return f"{as_float(value):,.{places}f}"


def fmt_pct(value: float) -> str:
    return f"{100.0 * float(value):.2f}%"


def fmt_duration(seconds: float) -> str:
    total = int(round(seconds))
    hours, rem = divmod(total, 3600)
    minutes, secs = divmod(rem, 60)
    if hours:
        return f"{hours}h {minutes:02d}m {secs:02d}s"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"


def safe_md(text: Any) -> str:
    return str(text or "").replace("|", "\\|").replace("\n", " ").strip()


def q_label(idx: int) -> str:
    return f"Q{idx:02d}"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_revision_var(path: Path, name: str) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    match = re.search(rf"{re.escape(name)}\s*=\s*[\"']([^\"']+)[\"']", text)
    return match.group(1) if match else ""


def copy_raw_export() -> list[dict[str, Any]]:
    raw_dir = OUT_DIR / "raw_export"
    manifest_rows: list[dict[str, Any]] = []
    for source in sorted(RUN_DIR.rglob("*")):
        if not source.is_file():
            continue
        rel = source.relative_to(RUN_DIR)
        dest = raw_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest)
        manifest_rows.append(
            {
                "relative_path": str(Path("raw_export") / rel).replace("\\", "/"),
                "source_path": str(source),
                "bytes": source.stat().st_size,
                "sha256": sha256_file(dest),
            }
        )
    return manifest_rows


def save_figure(fig: plt.Figure, stem: str, title: str, description: str, figures: list[FigureRecord]) -> None:
    vis_dir = OUT_DIR / "visualizations"
    vis_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(vis_dir / f"{stem}.svg", format="svg", bbox_inches="tight")
    fig.savefig(vis_dir / f"{stem}.png", dpi=180, bbox_inches="tight")
    plt.close(fig)
    figures.append(FigureRecord(stem=stem, title=title, description=description))


def add_watermark(ax: plt.Axes, text: str = "AEN V34 full test run") -> None:
    ax.text(
        0.995,
        0.01,
        text,
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=8,
        color="#94a3b8",
    )


def classify_diagnosis(row: dict[str, Any]) -> str:
    idx = as_int(row["idx"])
    if not as_bool(row["correct"]) and idx == 4:
        return (
            "Regression: the final consensus counted generating pairs/factorizations "
            "instead of distinct integer values; the collision/injectivity audit did not stop closeout."
        )
    if idx in TARGETED_REPAIR_QS and as_bool(row["correct"]):
        return "Targeted V34 Runtime-at-Boot repair succeeded on a prior miss."
    if as_bool(row["correct"]):
        return "Stable correct closeout."
    return "Incorrect closeout."


def build_prior_rows() -> tuple[list[dict[str, Any]], dict[tuple[str, int], dict[str, Any]]]:
    prior_path = REPO_DIR / "revisions" / "data" / "all_four_artifacts_q1_q30_long.csv"
    rows = read_csv(prior_path)
    normalized: list[dict[str, Any]] = []
    by_key: dict[tuple[str, int], dict[str, Any]] = {}
    for row in rows:
        idx = as_int(row.get("idx"))
        run_key = str(row.get("run_key") or "")
        item = {
            "run_key": run_key,
            "run_label": PRIOR_LABELS.get(run_key, str(row.get("run_label") or run_key)),
            "idx": idx,
            "id": row.get("id", ""),
            "answer": row.get("answer", ""),
            "expected_answer": row.get("expected_answer", ""),
            "correct": as_bool(row.get("correct")),
            "valid_answer": as_bool(row.get("valid_answer")),
            "status": row.get("status", ""),
            "total_tokens": as_int(row.get("total_tokens")),
            "time_taken_seconds": as_float(row.get("time_taken_seconds")),
            "turns": as_int(row.get("turns")),
            "loops": as_int(row.get("loops")),
            "total_prompt_tokens": as_int(row.get("total_prompt_tokens")),
            "total_completion_tokens": as_int(row.get("total_completion_tokens")),
        }
        normalized.append(item)
        by_key[(run_key, idx)] = item
    return normalized, by_key


def build_run_rows() -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[int, dict[str, Any]]]:
    full_rows = read_csv(RUN_DIR / "AIME-2026_dataset_PRIVATE_FULL.csv")
    payload_dir = RUN_DIR / "result_payloads"
    transcript_dir = RUN_DIR / "transcripts"
    problem_rows: list[dict[str, Any]] = []
    role_rows: list[dict[str, Any]] = []
    turn_rows: list[dict[str, Any]] = []
    payloads_by_idx: dict[int, dict[str, Any]] = {}

    for raw in full_rows:
        idx = as_int(raw.get("problem_idx"))
        qid = str(raw.get("id") or f"aime_2026_{idx:02d}")
        payload_path = payload_dir / f"{qid}.json"
        payload = read_json(payload_path) if payload_path.exists() else {}
        payloads_by_idx[idx] = payload
        transcript_path = transcript_dir / f"{qid}.txt"
        transcript_chars = transcript_path.stat().st_size if transcript_path.exists() else 0
        state = payload.get("controller_state") or {}
        timing = payload.get("timing_summary") or {}
        token_proof = payload.get("token_proof") or {}
        peer_meta = state.get("peer_report_meta") or {}

        role_wall = timing.get("speaker_wall_seconds") or {}
        role_tokens = token_proof.get("roles") or {}
        candidate_rows = {
            "athena_candidate": state.get("athena_candidate_answer", ""),
            "athena_confidence": as_int(state.get("athena_confidence_pct")),
            "aria_candidate": "",
            "aria_confidence": 0,
            "artemis_candidate": "",
            "artemis_confidence": 0,
        }
        for speaker, meta in peer_meta.items():
            low = str(speaker).strip().lower()
            if low == "aria":
                candidate_rows["aria_candidate"] = str(meta.get("answer_signal_integer") or meta.get("candidate_exact_integer") or "")
                candidate_rows["aria_confidence"] = as_int(meta.get("answer_signal_confidence_pct", meta.get("confidence_pct")))
            elif low == "artemis":
                candidate_rows["artemis_candidate"] = str(meta.get("answer_signal_integer") or meta.get("candidate_exact_integer") or "")
                candidate_rows["artemis_confidence"] = as_int(meta.get("answer_signal_confidence_pct", meta.get("confidence_pct")))

        row = {
            "idx": idx,
            "qid": qid,
            "expected_answer": str(raw.get("expected_answer_normalized") or raw.get("expected_answer") or ""),
            "submitted_answer": str(raw.get("model_answer_normalized") or raw.get("model_submitted_answer") or raw.get("final_answer") or ""),
            "correct": as_bool(raw.get("correct")),
            "valid_answer": as_bool(raw.get("valid_answer")),
            "status": str(raw.get("status") or payload.get("status") or ""),
            "verified": as_bool(raw.get("verified")),
            "loops": as_int(raw.get("loops") or payload.get("loop_index")),
            "turns": as_int(raw.get("turns") or payload.get("turn_index")),
            "time_taken_seconds": as_float(raw.get("time_taken_seconds") or payload.get("elapsed_seconds")),
            "sum_turn_wall_seconds": as_float(raw.get("sum_turn_wall_seconds") or timing.get("sum_turn_wall_seconds")),
            "total_prompt_tokens": as_int(raw.get("total_prompt_tokens") or token_proof.get("total_prompt_tokens")),
            "total_completion_tokens": as_int(raw.get("total_completion_tokens") or token_proof.get("total_completion_tokens")),
            "total_tokens": as_int(raw.get("total_tokens") or token_proof.get("total_tokens")),
            "question_run_id": str(raw.get("question_run_id") or payload.get("question_run_id") or ""),
            "submission_mode": str(payload.get("submission_mode") or ""),
            "peer_validation_ready": bool(payload.get("peer_validation_ready", False)),
            "transcript_chars": int(transcript_chars),
            "targeted_repair_question": idx in TARGETED_REPAIR_QS,
            "transcript_path": f"raw_export/transcripts/{qid}.txt",
            "result_payload_path": f"raw_export/result_payloads/{qid}.json",
            "problem": str(raw.get("question") or ""),
            **candidate_rows,
        }
        row["diagnosis"] = classify_diagnosis(row)
        problem_rows.append(row)

        for role_key, vals in role_tokens.items():
            speaker = str(vals.get("speaker") or {"solver": "Athena", "agent": "Aria", "clerk": "Artemis"}.get(role_key, role_key))
            role_rows.append(
                {
                    "idx": idx,
                    "qid": qid,
                    "role_key": role_key,
                    "speaker": speaker,
                    "turns": as_int(vals.get("turns")),
                    "prompt_tokens": as_int(vals.get("prompt_tokens")),
                    "completion_tokens": as_int(vals.get("completion_tokens")),
                    "total_tokens": as_int(vals.get("total_tokens")),
                    "wall_seconds": as_float(role_wall.get(speaker)),
                }
            )
        for turn in payload.get("turn_timing_log") or []:
            turn_rows.append(
                {
                    "idx": idx,
                    "qid": qid,
                    "turn": as_int(turn.get("turn")),
                    "speaker": turn.get("speaker", ""),
                    "runtime_label": turn.get("runtime_label", ""),
                    "phase": turn.get("phase", ""),
                    "ok": bool(turn.get("ok", False)),
                    "wall_seconds": as_float(turn.get("wall_seconds")),
                }
            )

    problem_rows.sort(key=lambda item: as_int(item["idx"]))
    role_rows.sort(key=lambda item: (as_int(item["idx"]), str(item["speaker"])))
    turn_rows.sort(key=lambda item: (as_int(item["idx"]), as_int(item["turn"])))
    return problem_rows, role_rows, turn_rows, payloads_by_idx


def build_slices(problem_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    slices: list[tuple[str, list[dict[str, Any]]]] = [("Q1-Q30", problem_rows)]
    for start in range(1, 31, 5):
        chunk = [row for row in problem_rows if start <= as_int(row["idx"]) <= start + 4]
        slices.append((f"Q{start}-Q{start + 4}", chunk))
    rows: list[dict[str, Any]] = []
    for name, chunk in slices:
        cases = len(chunk)
        correct = sum(1 for row in chunk if as_bool(row["correct"]))
        total_tokens = sum(as_int(row["total_tokens"]) for row in chunk)
        total_seconds = sum(as_float(row["time_taken_seconds"]) for row in chunk)
        rows.append(
            {
                "run_key": "v34",
                "run_label": PRIOR_LABELS["v34"],
                "slice": name,
                "cases": cases,
                "correct": correct,
                "losses": cases - correct,
                "accuracy": round(correct / cases, 6) if cases else 0.0,
                "mean_total_tokens": round(total_tokens / cases, 1) if cases else 0.0,
                "mean_seconds": round(total_seconds / cases, 3) if cases else 0.0,
                "tokens_per_correct": round(total_tokens / correct, 1) if correct else "",
                "mean_turns": round(sum(as_int(row["turns"]) for row in chunk) / cases, 3) if cases else 0.0,
                "mean_loops": round(sum(as_int(row["loops"]) for row in chunk) / cases, 3) if cases else 0.0,
            }
        )
    return rows


def build_comparison_rows(
    prior_rows: list[dict[str, Any]],
    prior_by_key: dict[tuple[str, int], dict[str, Any]],
    problem_rows: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    v34_long: list[dict[str, Any]] = []
    for row in problem_rows:
        v34_long.append(
            {
                "run_key": "v34",
                "run_label": PRIOR_LABELS["v34"],
                "idx": row["idx"],
                "id": row["qid"],
                "answer": row["submitted_answer"],
                "expected_answer": row["expected_answer"],
                "correct": row["correct"],
                "valid_answer": row["valid_answer"],
                "status": row["status"],
                "closeout_mode": "Max loop arbitration" if "max_loop" in str(row["status"]) else "Strict trio confidence",
                "total_tokens": row["total_tokens"],
                "time_taken_seconds": row["time_taken_seconds"],
                "turns": row["turns"],
                "loops": row["loops"],
                "total_prompt_tokens": row["total_prompt_tokens"],
                "total_completion_tokens": row["total_completion_tokens"],
                "peer_validation_ready": row["peer_validation_ready"],
                "peer_candidates": f"Aria={row.get('aria_candidate','')}; Artemis={row.get('artemis_candidate','')}",
                "athena_confidence_pct": row.get("athena_confidence", ""),
            }
        )
    all_long = list(prior_rows) + v34_long

    by_idx = {as_int(row["idx"]): row for row in problem_rows}
    comparison: list[dict[str, Any]] = []
    for idx in range(1, 31):
        v34 = by_idx[idx]
        out: dict[str, Any] = {
            "idx": idx,
            "expected_answer": v34["expected_answer"],
            "v34_answer": v34["submitted_answer"],
            "v34_correct": v34["correct"],
            "v34_status": v34["status"],
            "v34_tokens": v34["total_tokens"],
            "v34_seconds": round(as_float(v34["time_taken_seconds"]), 4),
            "v34_loops": v34["loops"],
            "v34_turns": v34["turns"],
            "targeted_repair_question": v34["targeted_repair_question"],
            "diagnosis": v34["diagnosis"],
        }
        for run_key in ["frozen", "unrestricted", "current", "official"]:
            prior = prior_by_key.get((run_key, idx), {})
            out[f"{run_key}_answer"] = prior.get("answer", "")
            out[f"{run_key}_correct"] = prior.get("correct", "")
            out[f"{run_key}_tokens"] = prior.get("total_tokens", "")
            prior_correct = as_bool(prior.get("correct"))
            v34_correct = as_bool(v34["correct"])
            if prior and prior_correct == v34_correct:
                delta = "same_correct" if v34_correct else "same_wrong"
            elif prior and v34_correct and not prior_correct:
                delta = "v34_fix"
            elif prior and prior_correct and not v34_correct:
                delta = "v34_regression"
            else:
                delta = "unknown"
            out[f"v34_vs_{run_key}"] = delta
        comparison.append(out)

    summary_rows: list[dict[str, Any]] = []
    for run_key in ["frozen", "unrestricted", "current", "official", "v34"]:
        rows = [row for row in all_long if row["run_key"] == run_key]
        correct = sum(1 for row in rows if as_bool(row["correct"]))
        total_tokens = sum(as_int(row.get("total_tokens")) for row in rows)
        total_seconds = sum(as_float(row.get("time_taken_seconds")) for row in rows)
        total_completion = sum(as_int(row.get("total_completion_tokens")) for row in rows)
        summary_rows.append(
            {
                "run_key": run_key,
                "run_label": PRIOR_LABELS.get(run_key, run_key),
                "cases": len(rows),
                "correct": correct,
                "incorrect": len(rows) - correct,
                "accuracy": round(correct / len(rows), 6) if rows else 0.0,
                "mean_total_tokens": round(total_tokens / len(rows), 1) if rows else 0.0,
                "total_tokens": total_tokens,
                "mean_seconds": round(total_seconds / len(rows), 3) if rows else 0.0,
                "total_seconds": round(total_seconds, 3),
                "mean_completion_tokens": round(total_completion / len(rows), 1) if rows else 0.0,
                "tokens_per_correct": round(total_tokens / correct, 1) if correct else "",
            }
        )
    return comparison, summary_rows


def boot_rows(boot_summary: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for role_key, report in (boot_summary.get("roles") or {}).items():
        memory = report.get("memory_study") or {}
        baseline = report.get("memory_baseline") or {}
        rows.append(
            {
                "runtime_label": role_key,
                "role_name": report.get("role_name", role_key),
                "status": report.get("status", ""),
                "passed": report.get("passed", False),
                "certification_line_count": report.get("line_count", 0),
                "certified_count": report.get("certified_count", 0),
                "probe_count": report.get("probe_count", 0),
                "memory_line_count": memory.get("memory_line_count", report.get("memory_line_count", 0)),
                "memory_chunk_count": memory.get("memory_chunk_count", report.get("memory_chunk_count", 0)),
                "study_passes": memory.get("study_passes", 0),
                "expected_study_turns": memory.get("expected_study_turns", 0),
                "ack_count": memory.get("ack_count", 0),
                "ack_success_count": memory.get("ack_success_count", 0),
                "study_ack_mode": memory.get("study_ack_mode", ""),
                "model_generation_used_for_study_ack": memory.get("model_generation_used_for_study_ack", ""),
                "baseline_stage": baseline.get("baseline_stage", ""),
                "baseline_dialogue_messages": baseline.get("dialogue_messages", 0),
                "baseline_committed_prompt_tokens": baseline.get("committed_prompt_tokens", 0),
                "elapsed_seconds": report.get("elapsed_seconds", 0),
            }
        )
    return rows


def make_figures(
    problem_rows: list[dict[str, Any]],
    role_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    boot_table: list[dict[str, Any]],
    figures: list[FigureRecord],
) -> None:
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "axes.edgecolor": "#cbd5e1",
            "axes.labelcolor": COLORS["dark"],
            "xtick.color": COLORS["dark"],
            "ytick.color": COLORS["dark"],
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
        }
    )
    idxs = [as_int(row["idx"]) for row in problem_rows]
    correct_flags = [as_bool(row["correct"]) for row in problem_rows]
    colors = [COLORS["green"] if ok else COLORS["red"] for ok in correct_flags]

    # 01 headline
    fig, ax = plt.subplots(figsize=(10.5, 4.8))
    correct = sum(correct_flags)
    incorrect = len(problem_rows) - correct
    ax.bar(["Correct", "Incorrect"], [correct, incorrect], color=[COLORS["green"], COLORS["red"]], width=0.55)
    ax.set_ylim(0, 30)
    ax.set_ylabel("Questions")
    ax.set_title("V34 Full Test Run: 29/30 on AIME-2026")
    for i, value in enumerate([correct, incorrect]):
        ax.text(i, value + 0.6, f"{value}", ha="center", va="bottom", fontsize=16, fontweight="bold")
    ax.text(
        0.98,
        0.70,
        "Accuracy: 96.67%\nOnly miss: Q04\nRuntime-at-Boot: passed\nController: strict trio confidence + max-loop fallback",
        transform=ax.transAxes,
        ha="right",
        va="center",
        fontsize=12,
        bbox={"boxstyle": "round,pad=0.45", "fc": "#f8fafc", "ec": "#cbd5e1"},
    )
    add_watermark(ax)
    save_figure(fig, "01_headline_scoreboard", "Headline Scoreboard", "Correct/incorrect headline for the V34 run.", figures)

    # 02 result grid
    fig, ax = plt.subplots(figsize=(15, 2.8))
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1)
    ax.axis("off")
    for i, row in enumerate(problem_rows):
        ok = as_bool(row["correct"])
        rect = Rectangle((i + 0.05, 0.15), 0.9, 0.7, facecolor=COLORS["green"] if ok else COLORS["red"], edgecolor="white", linewidth=1.5)
        ax.add_patch(rect)
        ax.text(i + 0.5, 0.61, q_label(as_int(row["idx"])), ha="center", va="center", color="white", fontsize=10, fontweight="bold")
        ax.text(i + 0.5, 0.38, str(row["submitted_answer"]), ha="center", va="center", color="white", fontsize=9)
    ax.text(0, 0.98, "Q1-Q30 outcome grid: green = correct, red = incorrect; text = submitted answer", ha="left", va="top", fontsize=12, color=COLORS["dark"])
    save_figure(fig, "02_q1_q30_result_grid", "Q1-Q30 Result Grid", "Per-question outcome grid with submitted answers.", figures)

    # 03 cumulative
    fig, ax = plt.subplots(figsize=(12, 5.2))
    cumulative = []
    running = 0
    for ok in correct_flags:
        running += int(ok)
        cumulative.append(running)
    ax.step(idxs, cumulative, where="post", color=COLORS["green"], linewidth=3, label="V34")
    # Prior cumulative lines from comparison rows.
    for run_key, color in [("frozen", "#94a3b8"), ("unrestricted", "#3867d6"), ("current", "#7d4cc2"), ("official", "#c78100")]:
        running = 0
        values = []
        for row in comparison_rows:
            running += int(as_bool(row.get(f"{run_key}_correct")))
            values.append(running)
        ax.step(idxs, values, where="post", linewidth=1.8, label=PRIOR_LABELS[run_key].replace("Artifact ", "A"), color=color, alpha=0.85)
    ax.set_xlabel("Question")
    ax.set_ylabel("Cumulative correct")
    ax.set_title("Cumulative Score Trajectory")
    ax.set_xticks(idxs)
    ax.set_ylim(0, 30)
    ax.grid(axis="y", color="#e2e8f0")
    ax.legend(loc="lower right", fontsize=8)
    add_watermark(ax)
    save_figure(fig, "03_cumulative_score_trajectory", "Cumulative Score Trajectory", "V34 cumulative score against prior artifact trajectories.", figures)

    # 04 wall time by question
    fig, ax = plt.subplots(figsize=(13, 5.2))
    wall = [as_float(row["time_taken_seconds"]) / 60.0 for row in problem_rows]
    ax.bar(idxs, wall, color=colors)
    ax.axhline(sum(wall) / len(wall), color=COLORS["dark"], linestyle="--", linewidth=1, label="mean")
    ax.set_xlabel("Question")
    ax.set_ylabel("Wall time (minutes)")
    ax.set_title("Per-Question Wall Time")
    ax.set_xticks(idxs)
    ax.grid(axis="y", color="#e2e8f0")
    ax.legend()
    add_watermark(ax)
    save_figure(fig, "04_wall_time_by_question", "Wall Time by Question", "Per-question solve wall time; miss shown in red.", figures)

    # 05 tokens by question
    fig, ax = plt.subplots(figsize=(13, 5.2))
    total_m = [as_int(row["total_tokens"]) / 1_000_000 for row in problem_rows]
    completion_k = [as_int(row["total_completion_tokens"]) / 1000 for row in problem_rows]
    ax.bar(idxs, total_m, color=colors, alpha=0.9, label="total tokens (M)")
    ax2 = ax.twinx()
    ax2.plot(idxs, completion_k, color=COLORS["blue"], marker="o", linewidth=1.8, label="completion tokens (K)")
    ax.set_xlabel("Question")
    ax.set_ylabel("Total tokens (millions)")
    ax2.set_ylabel("Completion tokens (thousands)")
    ax.set_title("Per-Question Token Load")
    ax.set_xticks(idxs)
    ax.grid(axis="y", color="#e2e8f0")
    ax.legend(loc="upper left")
    ax2.legend(loc="upper right")
    save_figure(fig, "05_tokens_by_question", "Token Load by Question", "Total and completion-token load per question.", figures)

    # 06 loops and turns
    fig, ax = plt.subplots(figsize=(13, 5.2))
    loops = [as_int(row["loops"]) for row in problem_rows]
    turns = [as_int(row["turns"]) for row in problem_rows]
    ax.bar(idxs, loops, color=COLORS["amber"], width=0.7, label="loops")
    ax2 = ax.twinx()
    ax2.plot(idxs, turns, color=COLORS["purple"], marker="s", linewidth=2, label="turns")
    ax.set_xlabel("Question")
    ax.set_ylabel("Loops")
    ax2.set_ylabel("Turns")
    ax.set_title("Controller Depth: Loops and Turns")
    ax.set_xticks(idxs)
    ax.set_ylim(0, 3.5)
    ax.grid(axis="y", color="#e2e8f0")
    ax.legend(loc="upper left")
    ax2.legend(loc="upper right")
    save_figure(fig, "06_loops_turns_by_question", "Loops and Turns", "Controller loop count and total turns per question.", figures)

    by_idx_role = defaultdict(dict)
    for row in role_rows:
        by_idx_role[as_int(row["idx"])][str(row["speaker"])] = row
    role_order = ["Athena", "Aria", "Artemis"]
    role_colors = {"Athena": "#3867d6", "Aria": "#7d4cc2", "Artemis": "#c78100"}

    # 07 role wall stack
    fig, ax = plt.subplots(figsize=(13, 5.2))
    bottom = [0.0 for _ in problem_rows]
    for role in role_order:
        vals = [as_float(by_idx_role[as_int(row["idx"])].get(role, {}).get("wall_seconds")) / 60.0 for row in problem_rows]
        ax.bar(idxs, vals, bottom=bottom, label=role, color=role_colors[role])
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_xlabel("Question")
    ax.set_ylabel("Role wall time (minutes)")
    ax.set_title("Role Wall-Time Stack")
    ax.set_xticks(idxs)
    ax.grid(axis="y", color="#e2e8f0")
    ax.legend(ncol=3)
    save_figure(fig, "07_role_wall_time_stacked", "Role Wall Time", "Stacked wall time by role for each question.", figures)

    # 08 role tokens stack
    fig, ax = plt.subplots(figsize=(13, 5.2))
    bottom = [0.0 for _ in problem_rows]
    for role in role_order:
        vals = [as_int(by_idx_role[as_int(row["idx"])].get(role, {}).get("total_tokens")) / 1_000_000 for row in problem_rows]
        ax.bar(idxs, vals, bottom=bottom, label=role, color=role_colors[role])
        bottom = [b + v for b, v in zip(bottom, vals)]
    ax.set_xlabel("Question")
    ax.set_ylabel("Role tokens (millions)")
    ax.set_title("Role Token Stack")
    ax.set_xticks(idxs)
    ax.grid(axis="y", color="#e2e8f0")
    ax.legend(ncol=3)
    save_figure(fig, "08_role_tokens_stacked", "Role Tokens", "Stacked total tokens by role for each question.", figures)

    # 09 five-artifact scoreboard
    fig, ax = plt.subplots(figsize=(11, 5.4))
    labels = [row["run_label"].replace("Artifact ", "A") for row in summary_rows]
    scores = [as_int(row["correct"]) for row in summary_rows]
    means = [as_float(row["mean_total_tokens"]) / 1_000_000 for row in summary_rows]
    bars = ax.bar(range(len(labels)), scores, color=["#94a3b8", "#3867d6", "#7d4cc2", "#c78100", COLORS["green"]])
    ax.set_ylim(0, 30)
    ax.set_ylabel("Correct / 30")
    ax.set_title("Five-Artifact Scoreboard")
    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=18, ha="right")
    for bar, score, mean in zip(bars, scores, means):
        ax.text(bar.get_x() + bar.get_width() / 2, score + 0.5, f"{score}/30\n{mean:.2f}M mean toks", ha="center", va="bottom", fontsize=9)
    ax.grid(axis="y", color="#e2e8f0")
    save_figure(fig, "09_five_artifact_scoreboard", "Five Artifact Scoreboard", "Score and mean-token comparison across the artifact ledger.", figures)

    # 10 delta grid
    fig, ax = plt.subplots(figsize=(15, 4.8))
    runs = ["frozen", "unrestricted", "current", "official", "v34"]
    ax.set_xlim(0, 30)
    ax.set_ylim(0, len(runs))
    ax.set_xticks([i + 0.5 for i in range(30)])
    ax.set_xticklabels([str(i) for i in range(1, 31)], fontsize=8)
    ax.set_yticks([i + 0.5 for i in range(len(runs))])
    ax.set_yticklabels([PRIOR_LABELS[r].replace("Artifact ", "A") for r in runs], fontsize=9)
    for y, run in enumerate(runs):
        for i, comp in enumerate(comparison_rows):
            if run == "v34":
                ok = as_bool(comp["v34_correct"])
            else:
                ok = as_bool(comp.get(f"{run}_correct"))
            ax.add_patch(Rectangle((i, len(runs) - y - 1), 1, 1, facecolor=COLORS["green"] if ok else COLORS["red"], edgecolor="white", linewidth=0.8))
    ax.invert_yaxis()
    ax.set_title("Outcome Grid Across Artifact Ledger")
    ax.set_xlabel("AIME-2026 question index")
    ax.tick_params(length=0)
    save_figure(fig, "10_artifact_delta_grid", "Artifact Outcome Grid", "Correct/incorrect grid for V34 against the prior four artifacts.", figures)

    # 11 Runtime-at-Boot
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8))
    roles = [str(row["role_name"]) for row in boot_table]
    axes[0].bar(roles, [as_int(row["memory_line_count"]) for row in boot_table], color=COLORS["blue"])
    axes[0].set_title("Memory lines")
    axes[0].set_ylim(0, max(120, max(as_int(row["memory_line_count"]) for row in boot_table) + 10))
    axes[1].bar(roles, [as_int(row["baseline_dialogue_messages"]) for row in boot_table], color=COLORS["purple"])
    axes[1].set_title("Baseline dialogue messages")
    axes[2].bar(roles, [as_int(row["baseline_committed_prompt_tokens"]) / 1000 for row in boot_table], color=COLORS["amber"])
    axes[2].set_title("Baseline committed prompt tokens (K)")
    for ax in axes:
        ax.grid(axis="y", color="#e2e8f0")
        ax.tick_params(axis="x", rotation=20)
    fig.suptitle("Runtime-at-Boot Certification Shape: synthetic study ack, MCQ certified, after-certification baseline")
    save_figure(fig, "11_runtime_at_boot_certification", "Runtime-at-Boot Certification", "Role-level Runtime-at-Boot memory, baseline, and prompt-token profile.", figures)

    # 12 Q04 failure
    q04 = next(row for row in problem_rows if as_int(row["idx"]) == 4)
    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.axis("off")
    ax.text(0.02, 0.92, "Q04 Failure Diagnostic", fontsize=18, fontweight="bold", color=COLORS["dark"])
    ax.text(0.02, 0.80, f"Expected answer: {q04['expected_answer']}   Submitted: {q04['submitted_answer']}", fontsize=14, color=COLORS["red"])
    ax.text(0.02, 0.68, f"Loops: {q04['loops']}   Turns: {q04['turns']}   Wall: {fmt_duration(as_float(q04['time_taken_seconds']))}   Tokens: {fmt_int(q04['total_tokens'])}", fontsize=12)
    wrapped = textwrap.fill(str(q04["diagnosis"]), width=105)
    ax.text(0.02, 0.52, wrapped, fontsize=12, va="top")
    ax.text(
        0.02,
        0.23,
        "Interpretive error: it validated the count of generating pairs/factorizations (137),\n"
        "but the problem asked for distinct integer values (70). This is exactly the kind\n"
        "of object-identification/collision check the next repair should target.",
        fontsize=12,
        bbox={"boxstyle": "round,pad=0.45", "fc": "#fff7ed", "ec": "#fed7aa"},
    )
    save_figure(fig, "12_q04_failure_diagnostic", "Q04 Failure Diagnostic", "The lone V34 miss and its failure mode.", figures)

    # 13 band accuracy
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    bands = []
    acc = []
    for start in range(1, 31, 5):
        chunk = [row for row in problem_rows if start <= as_int(row["idx"]) <= start + 4]
        bands.append(f"Q{start}-Q{start+4}")
        acc.append(sum(as_bool(row["correct"]) for row in chunk) / len(chunk))
    ax.bar(bands, [100 * x for x in acc], color=[COLORS["red"] if x < 1 else COLORS["green"] for x in acc])
    ax.set_ylim(0, 105)
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Accuracy by Five-Question Band")
    ax.grid(axis="y", color="#e2e8f0")
    for i, value in enumerate(acc):
        ax.text(i, 100 * value + 1, f"{int(value * 5)}/5", ha="center")
    save_figure(fig, "13_band_accuracy", "Band Accuracy", "Accuracy by five-question band.", figures)

    # 14 efficiency vs score
    fig, ax = plt.subplots(figsize=(9.5, 5.4))
    for row in summary_rows:
        ax.scatter(as_float(row["mean_total_tokens"]) / 1_000_000, as_int(row["correct"]), s=160, label=row["run_key"])
        ax.text(as_float(row["mean_total_tokens"]) / 1_000_000 + 0.03, as_int(row["correct"]), row["run_key"], va="center", fontsize=9)
    ax.set_xlabel("Mean total tokens / problem (millions)")
    ax.set_ylabel("Correct / 30")
    ax.set_title("Score vs Compute")
    ax.grid(color="#e2e8f0")
    save_figure(fig, "14_score_vs_compute", "Score vs Compute", "Accuracy and token cost across the artifact ledger.", figures)

    # 15 closeout status
    fig, ax = plt.subplots(figsize=(13, 4.8))
    status_colors = [COLORS["green"] if "strict" in str(row["status"]) else COLORS["amber"] for row in problem_rows]
    ax.bar(idxs, [1 for _ in problem_rows], color=status_colors)
    for row in problem_rows:
        ax.text(as_int(row["idx"]), 0.5, str(row["loops"]), ha="center", va="center", color="white", fontweight="bold")
    ax.set_yticks([])
    ax.set_xticks(idxs)
    ax.set_title("Closeout Mode by Question (number = loop index)")
    ax.set_xlabel("Question")
    ax.text(0.01, 0.9, "green=strict trio confidence; amber=max-loop best-confidence arbitration", transform=ax.transAxes, fontsize=10)
    save_figure(fig, "15_closeout_status_grid", "Closeout Status", "Strict versus max-loop closeout modes by question.", figures)

    # 16 transcript size
    fig, ax = plt.subplots(figsize=(13, 5.2))
    chars_k = [as_int(row["transcript_chars"]) / 1000 for row in problem_rows]
    ax.bar(idxs, chars_k, color=colors)
    ax.set_xlabel("Question")
    ax.set_ylabel("Transcript size (KB)")
    ax.set_title("Transcript Size by Question")
    ax.set_xticks(idxs)
    ax.grid(axis="y", color="#e2e8f0")
    save_figure(fig, "16_transcript_size_by_question", "Transcript Size", "Transcript file size by question.", figures)

    # Per-question profile figures.
    qvis_dir = OUT_DIR / "visualizations" / "questions"
    qvis_dir.mkdir(parents=True, exist_ok=True)
    for row in problem_rows:
        idx = as_int(row["idx"])
        qid = str(row["qid"])
        fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
        role_map = by_idx_role[idx]
        role_names = role_order
        axes[0].bar(role_names, [as_float(role_map.get(role, {}).get("wall_seconds")) / 60 for role in role_names], color=[role_colors[r] for r in role_names])
        axes[0].set_title("Role wall minutes")
        axes[0].grid(axis="y", color="#e2e8f0")
        axes[1].bar(role_names, [as_int(role_map.get(role, {}).get("total_tokens")) / 1_000_000 for role in role_names], color=[role_colors[r] for r in role_names])
        axes[1].set_title("Role tokens (M)")
        axes[1].grid(axis="y", color="#e2e8f0")
        fig.suptitle(
            f"{q_label(idx)} {qid}: {'correct' if as_bool(row['correct']) else 'incorrect'} | "
            f"submitted {row['submitted_answer']} / expected {row['expected_answer']} | loops {row['loops']}, turns {row['turns']}"
        )
        fig.tight_layout()
        fig.savefig(qvis_dir / f"q{idx:02d}_profile.svg", format="svg", bbox_inches="tight")
        fig.savefig(qvis_dir / f"q{idx:02d}_profile.png", dpi=180, bbox_inches="tight")
        plt.close(fig)


def markdown_table(rows: list[dict[str, Any]], fields: list[tuple[str, str]]) -> str:
    lines = []
    headers = [label for _, label in fields]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join("---" for _ in headers) + " |")
    for row in rows:
        lines.append("| " + " | ".join(safe_md(row.get(key, "")) for key, _ in fields) + " |")
    return "\n".join(lines)


def write_question_reports(
    problem_rows: list[dict[str, Any]],
    role_rows: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
) -> None:
    out_dir = OUT_DIR / "per_question_reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    role_by_idx: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in role_rows:
        role_by_idx[as_int(row["idx"])].append(row)
    comp_by_idx = {as_int(row["idx"]): row for row in comparison_rows}
    for row in problem_rows:
        idx = as_int(row["idx"])
        comp = comp_by_idx[idx]
        outcome = "correct" if as_bool(row["correct"]) else "incorrect"
        fields = [
            {"metric": "Submitted", "value": row["submitted_answer"]},
            {"metric": "Expected", "value": row["expected_answer"]},
            {"metric": "Outcome", "value": outcome},
            {"metric": "Status", "value": row["status"]},
            {"metric": "Loops", "value": row["loops"]},
            {"metric": "Turns", "value": row["turns"]},
            {"metric": "Wall time", "value": fmt_duration(as_float(row["time_taken_seconds"]))},
            {"metric": "Total tokens", "value": fmt_int(row["total_tokens"])},
            {"metric": "Completion tokens", "value": fmt_int(row["total_completion_tokens"])},
            {"metric": "Targeted V34 repair question", "value": str(bool(row["targeted_repair_question"]))},
        ]
        prior_rows = []
        for key in ["frozen", "unrestricted", "current", "official", "v34"]:
            prior_rows.append(
                {
                    "artifact": PRIOR_LABELS[key],
                    "answer": comp.get(f"{key}_answer", row["submitted_answer"] if key == "v34" else ""),
                    "correct": comp.get(f"{key}_correct", row["correct"] if key == "v34" else ""),
                    "tokens": fmt_int(comp.get(f"{key}_tokens", row["total_tokens"] if key == "v34" else 0)),
                }
            )
        candidate_rows = [
            {"role": "Athena", "candidate": row.get("athena_candidate", ""), "confidence": row.get("athena_confidence", "")},
            {"role": "Aria", "candidate": row.get("aria_candidate", ""), "confidence": row.get("aria_confidence", "")},
            {"role": "Artemis", "candidate": row.get("artemis_candidate", ""), "confidence": row.get("artemis_confidence", "")},
        ]
        lines = [
            f"# {q_label(idx)} {row['qid']} Report",
            "",
            f"Outcome: **{outcome}**. Submitted `{row['submitted_answer']}`; expected `{row['expected_answer']}`.",
            "",
            f"![Question profile](../visualizations/questions/q{idx:02d}_profile.svg)",
            "",
            "## Metrics",
            "",
            markdown_table(fields, [("metric", "metric"), ("value", "value")]),
            "",
            "## Role Runtime",
            "",
            markdown_table(
                role_by_idx[idx],
                [
                    ("speaker", "role"),
                    ("turns", "turns"),
                    ("wall_seconds", "wall_seconds"),
                    ("prompt_tokens", "prompt_tokens"),
                    ("completion_tokens", "completion_tokens"),
                    ("total_tokens", "total_tokens"),
                ],
            ),
            "",
            "## Final Candidate State",
            "",
            markdown_table(candidate_rows, [("role", "role"), ("candidate", "candidate"), ("confidence", "confidence")]),
            "",
            "## Artifact Comparison",
            "",
            markdown_table(prior_rows, [("artifact", "artifact"), ("answer", "answer"), ("correct", "correct"), ("tokens", "tokens")]),
            "",
            "## Diagnostic",
            "",
            str(row["diagnosis"]),
            "",
            "## Source",
            "",
            f"- Transcript: [`{row['transcript_path']}`](../{row['transcript_path']})",
            f"- Result payload: [`{row['result_payload_path']}`](../{row['result_payload_path']})",
        ]
        (out_dir / f"q{idx:02d}_{row['qid']}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_visual_index(figures: list[FigureRecord]) -> None:
    lines = [
        "# V34 Visual Index",
        "",
        "Every global figure is emitted as both SVG and PNG. Per-question profile figures are under `visualizations/questions/`.",
        "",
    ]
    for record in figures:
        lines.extend(
            [
                f"## {record.title}",
                "",
                record.description,
                "",
                f"- SVG: [`{record.stem}.svg`](visualizations/{record.stem}.svg)",
                f"- PNG: [`{record.stem}.png`](visualizations/{record.stem}.png)",
                "",
                f"![{record.title}](visualizations/{record.stem}.svg)",
                "",
            ]
        )
    lines.extend(
        [
            "## Per-Question Profiles",
            "",
            "| question | SVG | PNG |",
            "| --- | --- | --- |",
        ]
    )
    for idx in range(1, 31):
        lines.append(
            f"| Q{idx:02d} | [`q{idx:02d}_profile.svg`](visualizations/questions/q{idx:02d}_profile.svg) | "
            f"[`q{idx:02d}_profile.png`](visualizations/questions/q{idx:02d}_profile.png) |"
        )
    (OUT_DIR / "VISUAL_INDEX.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_main_report(
    problem_rows: list[dict[str, Any]],
    slices: list[dict[str, Any]],
    comparison_rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
    boot_table: list[dict[str, Any]],
    score_summary: dict[str, Any],
    attached_summary: dict[str, Any],
    boot_summary: dict[str, Any],
    source_manifest: list[dict[str, Any]],
) -> dict[str, Any]:
    correct = sum(as_bool(row["correct"]) for row in problem_rows)
    cases = len(problem_rows)
    incorrect_rows = [row for row in problem_rows if not as_bool(row["correct"])]
    total_solve_seconds = as_float(attached_summary.get("total_wall_seconds")) or sum(as_float(row["time_taken_seconds"]) for row in problem_rows)
    boot_seconds = as_float(boot_summary.get("elapsed_seconds"))
    end_to_end_seconds = total_solve_seconds + boot_seconds
    total_tokens = sum(as_int(row["total_tokens"]) for row in problem_rows)
    total_prompt = sum(as_int(row["total_prompt_tokens"]) for row in problem_rows)
    total_completion = sum(as_int(row["total_completion_tokens"]) for row in problem_rows)
    total_turns = sum(as_int(row["turns"]) for row in problem_rows)
    total_loops = sum(as_int(row["loops"]) for row in problem_rows)
    loop_counts = Counter(as_int(row["loops"]) for row in problem_rows)
    status_counts = Counter(str(row["status"]) for row in problem_rows)
    targeted = [row for row in problem_rows if bool(row["targeted_repair_question"])]
    targeted_correct = sum(as_bool(row["correct"]) for row in targeted)
    artifact04_fixed = [row for row in comparison_rows if str(row.get("v34_vs_official")) == "v34_fix"]
    artifact04_regressed = [row for row in comparison_rows if str(row.get("v34_vs_official")) == "v34_regression"]

    code_revisions = {
        "cb05_prompting": read_revision_var(REPO_DIR / "next_run_v34" / "codeblocks" / "cb05.py", "CB05_PROMPTING_REVISION"),
        "cb07_5_dynamic": read_revision_var(REPO_DIR / "next_run_v34" / "codeblocks" / "cb07_5.py", "CB07_5_DYNAMIC_REVISION"),
        "cb08_runtime": read_revision_var(REPO_DIR / "next_run_v34" / "codeblocks" / "cb08.py", "CB08_RUNTIME_REVISION"),
        "cb12_dataset": read_revision_var(REPO_DIR / "next_run_v34" / "codeblocks" / "cb12.py", "CB12_GENERIC_HF_REVISION"),
        "cb13_package": read_revision_var(REPO_DIR / "next_run_v34" / "codeblocks" / "cb13.py", "CB13_GENERIC_SCORE_REVISION"),
    }
    metrics = {
        "artifact": "06",
        "name": "V34 full test run",
        "source_export": str(RUN_DIR),
        "notebook": str(NOTEBOOK_PATH),
        "packaged_at_utc": score_summary.get("packaged_at_utc", ""),
        "cases": cases,
        "correct": correct,
        "incorrect": cases - correct,
        "accuracy": correct / cases if cases else 0.0,
        "misses": [row["qid"] for row in incorrect_rows],
        "runtime_at_boot_passed": bool(score_summary.get("runtime_at_boot_passed", False)),
        "solve_wall_seconds": total_solve_seconds,
        "runtime_at_boot_wall_seconds": boot_seconds,
        "end_to_end_wall_seconds": end_to_end_seconds,
        "total_tokens": total_tokens,
        "total_prompt_tokens": total_prompt,
        "total_completion_tokens": total_completion,
        "mean_total_tokens": total_tokens / cases if cases else 0.0,
        "mean_seconds": total_solve_seconds / cases if cases else 0.0,
        "total_turns": total_turns,
        "total_loops": total_loops,
        "loop_counts": dict(sorted(loop_counts.items())),
        "status_counts": dict(status_counts),
        "targeted_repair_questions": sorted(TARGETED_REPAIR_QS),
        "targeted_repair_correct": targeted_correct,
        "targeted_repair_total": len(targeted),
        "artifact04_fixed_indices": [row["idx"] for row in artifact04_fixed],
        "artifact04_regressed_indices": [row["idx"] for row in artifact04_regressed],
        "code_revisions": code_revisions,
        "source_file_count": len(source_manifest),
        "source_bytes": sum(as_int(row["bytes"]) for row in source_manifest),
    }
    write_json(OUT_DIR / "data" / "v34_metrics.json", metrics)

    headline_rows = [
        {"metric": "Score", "value": f"{correct}/{cases}"},
        {"metric": "Accuracy", "value": fmt_pct(metrics["accuracy"])},
        {"metric": "Miss", "value": ", ".join(metrics["misses"]) or "none"},
        {"metric": "Runtime-at-Boot", "value": "passed" if metrics["runtime_at_boot_passed"] else "failed"},
        {"metric": "Solve wall time", "value": fmt_duration(total_solve_seconds)},
        {"metric": "Runtime-at-Boot wall time", "value": fmt_duration(boot_seconds)},
        {"metric": "End-to-end wall time", "value": fmt_duration(end_to_end_seconds)},
        {"metric": "Total tokens", "value": fmt_int(total_tokens)},
        {"metric": "Mean tokens/question", "value": fmt_int(round(metrics["mean_total_tokens"]))},
        {"metric": "Total turns", "value": fmt_int(total_turns)},
        {"metric": "Loop distribution", "value": ", ".join(f"L{k}: {v}" for k, v in sorted(loop_counts.items()))},
    ]
    per_question_table = []
    for row in problem_rows:
        per_question_table.append(
            {
                "q": q_label(as_int(row["idx"])),
                "answer": row["submitted_answer"],
                "expected": row["expected_answer"],
                "ok": "yes" if as_bool(row["correct"]) else "NO",
                "loops": row["loops"],
                "turns": row["turns"],
                "minutes": round(as_float(row["time_taken_seconds"]) / 60.0, 2),
                "tokens_M": round(as_int(row["total_tokens"]) / 1_000_000, 3),
                "report": f"[link](per_question_reports/q{as_int(row['idx']):02d}_{row['qid']}.md)",
            }
        )
    summary_display = []
    for row in summary_rows:
        summary_display.append(
            {
                "artifact": row["run_label"],
                "score": f"{row['correct']}/{row['cases']}",
                "accuracy": fmt_pct(as_float(row["accuracy"])),
                "mean_tokens": fmt_int(round(as_float(row["mean_total_tokens"]))),
                "mean_seconds": fmt_duration(as_float(row["mean_seconds"])),
            }
        )

    lines = [
        "# V34 Full Test Run",
        "",
        "This artifact is the full post-run analysis package for the April 29, 2026 V34 AIME-2026 run.",
        "It is based on the Colab export at `N:\\Research\\colab_outputs\\aime_2026_export_full_dataset_30q_20260429-090719` and the notebook `N:\\Research\\AENAIMO260_0_2_3_V34_NEXT_RUN.ipynb`.",
        "",
        "## Headline",
        "",
        f"V34 scored **{correct}/{cases} ({fmt_pct(metrics['accuracy'])})**. Runtime-at-Boot passed. The only miss was **Q04**, where the system closed on `137` while the expected distinct-integer answer was `70`.",
        "",
        "![Headline scoreboard](visualizations/01_headline_scoreboard.svg)",
        "",
        markdown_table(headline_rows, [("metric", "metric"), ("value", "value")]),
        "",
        "## What Changed",
        "",
        "- Runtime-at-Boot moved from model-generated boot-study acknowledgements to synthetic exact acknowledgement commits. This removed the boot-time thinking/echo loop while still inserting the study prompts and `BOOT_CERTIFIED` assistant turns into the session transcript.",
        "- The V34 boot layer used the additive answer-aware repair dataset: 113 selected memory records per role, two study passes, 20 chunks per role, 40 synthetic study turns per role, then 30 MCQ certification probes per role.",
        "- The captured baseline is after certification: 140 dialogue messages per role, with about 223k-225k committed prompt tokens restored before each benchmark question.",
        "- The controller used strict trio-confidence closeout with exact integer agreement; max-loop best-confidence arbitration was only available after loop 3.",
        "- Main solving/report budgets were 10k tokens per turn, final answer budget was 256 tokens, and each role had a 1.01M-token runtime context envelope.",
        "",
        "## Expectation Versus Outcome",
        "",
        "Expectation was that V34 would repair the 13 known Runtime-at-Boot v33 failures without reintroducing the boot-study hang. That mostly happened: all 13 targeted prior misses were repaired. The tradeoff was a new Q04 regression caused by a semantic object error, not by boot failure.",
        "",
        f"- Targeted prior failures repaired: **{targeted_correct}/{len(targeted)}**.",
        f"- Net change versus Artifact 04: **+{len(artifact04_fixed) - len(artifact04_regressed)}** questions.",
        f"- Fixed versus Artifact 04: {', '.join(q_label(as_int(row['idx'])) for row in artifact04_fixed)}.",
        f"- Regressed versus Artifact 04: {', '.join(q_label(as_int(row['idx'])) for row in artifact04_regressed) or 'none'}.",
        "",
        "## Full Run Tables",
        "",
        "### Per-Question Summary",
        "",
        markdown_table(per_question_table, [("q", "q"), ("answer", "answer"), ("expected", "expected"), ("ok", "ok"), ("loops", "loops"), ("turns", "turns"), ("minutes", "minutes"), ("tokens_M", "tokens_M"), ("report", "report")]),
        "",
        "### Artifact Comparison",
        "",
        markdown_table(summary_display, [("artifact", "artifact"), ("score", "score"), ("accuracy", "accuracy"), ("mean_tokens", "mean_tokens"), ("mean_seconds", "mean_seconds")]),
        "",
        "## Runtime-at-Boot",
        "",
        "Runtime-at-Boot was structurally healthy in this run. The important architectural change is that the study acknowledgement was no longer generated by the model. It was committed synthetically into the session transcript, so boot memory was present without inviting a long thinking transcript during boot.",
        "",
        markdown_table(
            boot_table,
            [
                ("role_name", "role"),
                ("status", "status"),
                ("memory_line_count", "memory_lines"),
                ("memory_chunk_count", "chunks"),
                ("study_passes", "passes"),
                ("expected_study_turns", "study_turns"),
                ("ack_success_count", "ack_success"),
                ("study_ack_mode", "ack_mode"),
                ("baseline_dialogue_messages", "baseline_msgs"),
                ("baseline_committed_prompt_tokens", "baseline_prompt_tokens"),
            ],
        ),
        "",
        "![Runtime-at-Boot certification](visualizations/11_runtime_at_boot_certification.svg)",
        "",
        "## Controller And Compute",
        "",
        f"The solve phase took **{fmt_duration(total_solve_seconds)}**. Runtime-at-Boot took **{fmt_duration(boot_seconds)}** before the dataset run, for an approximate end-to-end runtime of **{fmt_duration(end_to_end_seconds)}**. Total token traffic was **{fmt_int(total_tokens)}** tokens, dominated by prompt tokens because each turn replayed the large post-certification memory baseline.",
        "",
        f"Closeout status counts: {', '.join(f'{k}: {v}' for k, v in status_counts.items())}. Loop counts: {', '.join(f'loop {k}: {v}' for k, v in sorted(loop_counts.items()))}.",
        "",
        "![Wall time](visualizations/04_wall_time_by_question.svg)",
        "",
        "![Token load](visualizations/05_tokens_by_question.svg)",
        "",
        "![Role wall time](visualizations/07_role_wall_time_stacked.svg)",
        "",
        "## What Went Right",
        "",
        "- The synthetic boot-study acknowledgement fixed the earlier boot failure mode: no generated thinking transcript was needed to study Runtime-at-Boot records.",
        "- Every targeted V34 repair question landed correct, including the late hard failures Q28, Q29, and Q30.",
        "- The stricter controller spent more work on difficult questions instead of prematurely closing on first-loop agreement. Q10, Q11, Q12, Q15, Q20, Q21, Q22, Q23, Q26, and Q29 all used extra loops or max-loop arbitration.",
        "- The full architecture stayed coherent under a very large restored memory baseline: per-problem resets restored boot memory and preserved the after-certification transcript.",
        "",
        "## What Went Wrong",
        "",
        "- Q04 is a clean semantic-object failure. The model counted valid generating pairs/factorizations (`137`) rather than distinct integer values (`70`). The peers aligned around the wrong object and the collision/injectivity audit did not block closeout.",
        "- Compute cost rose sharply. V34 is the highest-scoring run, but also far heavier than the earlier 21/30 efficiency artifact because the 223k-token boot baseline is replayed in every role session.",
        "- Two correct questions closed by max-loop best-confidence arbitration, not strict trio-confidence. That is acceptable under the configured policy, but it marks a residual confidence/coordination ceiling.",
        "",
        "![Q04 failure diagnostic](visualizations/12_q04_failure_diagnostic.svg)",
        "",
        "## Where We Stand",
        "",
        "Within this answer-aware repair-at-boot experiment, the observed ceiling moved to **29/30**. The remaining ceiling blocker is not general capacity; it is object identification under duplicate-generating maps. The next targeted repair should focus on distinct-value counting, collision checks, and explicit answer-object audits before confidence closeout.",
        "",
        "This should not be described as a blind public benchmark score. V34 contains additive answer-aware repairs for known AIME-2026 failures, so the durable claim is architectural: the runtime can ingest a large repair memory, certify it, replay it per problem, and convert a 17/30 Runtime-at-Boot failure into a 29/30 full-run repair while leaving an auditable miss.",
        "",
        "## Figures And Data",
        "",
        "- Full figure index: [`VISUAL_INDEX.md`](VISUAL_INDEX.md)",
        "- Per-question reports: [`per_question_reports/`](per_question_reports/)",
        "- Derived tables: [`data/`](data/)",
        "- Raw Colab export copy: [`raw_export/`](raw_export/)",
        "- Source manifest: [`SOURCE_MANIFEST.csv`](SOURCE_MANIFEST.csv)",
        "",
        "## Code Revisions",
        "",
        markdown_table([{"component": k, "revision": v} for k, v in code_revisions.items()], [("component", "component"), ("revision", "revision")]),
        "",
    ]
    (OUT_DIR / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return metrics


def write_repro_and_manifest(source_manifest: list[dict[str, Any]], metrics: dict[str, Any]) -> None:
    write_csv(OUT_DIR / "SOURCE_MANIFEST.csv", source_manifest)
    lines = [
        "# V34 Reproducibility Notes",
        "",
        f"- Local source export: `{RUN_DIR}`",
        f"- Notebook used by the run: `{NOTEBOOK_PATH}`",
        f"- Packaged at UTC: `{metrics.get('packaged_at_utc', '')}`",
        f"- Runtime-at-Boot passed: `{metrics.get('runtime_at_boot_passed')}`",
        f"- Score: `{metrics.get('correct')}/{metrics.get('cases')}`",
        f"- Solve wall time: `{fmt_duration(metrics.get('solve_wall_seconds', 0))}`",
        f"- Runtime-at-Boot wall time: `{fmt_duration(metrics.get('runtime_at_boot_wall_seconds', 0))}`",
        "",
        "This package copies the raw Colab export into `raw_export/` and then derives all tables and figures from those files.",
        "",
        "The V34 run is answer-aware because the Runtime-at-Boot v34 dataset includes repair rows for known AIME-2026 failures. Treat the artifact as an architecture/repair-memory experiment, not as a blind contest submission claim.",
        "",
    ]
    (OUT_DIR / "REPRODUCIBILITY.md").write_text("\n".join(lines), encoding="utf-8")

    manifest = [
        "# V34 Artifact Manifest",
        "",
        f"Generated artifact folder: `{OUT_DIR}`",
        "",
        "| path | purpose |",
        "| --- | --- |",
        "| `README.md` | Full analysis report |",
        "| `VISUAL_INDEX.md` | Global and per-question figure index |",
        "| `per_question_reports/` | One report for each AIME-2026 question |",
        "| `visualizations/` | SVG and PNG figures |",
        "| `data/` | Derived CSV/JSON analysis tables |",
        "| `raw_export/` | Copied Colab export used as source evidence |",
        "| `scripts/analyze_v34_full_run.py` | Generator used to rebuild this package |",
        "| `SOURCE_MANIFEST.csv` | Checksums and sizes for copied source files |",
        "",
        f"Copied source files: `{metrics.get('source_file_count')}`.",
        f"Copied source bytes: `{fmt_int(metrics.get('source_bytes'))}`.",
        "",
    ]
    (OUT_DIR / "MANIFEST.md").write_text("\n".join(manifest), encoding="utf-8")


def update_text_file_once(path: Path, marker: str, block: str, after_heading: str | None = None) -> None:
    text = path.read_text(encoding="utf-8", errors="replace")
    if marker in text:
        return
    if after_heading and after_heading in text:
        text = text.replace(after_heading, after_heading + "\n\n" + block.strip() + "\n", 1)
    else:
        text = text.rstrip() + "\n\n" + block.strip() + "\n"
    path.write_text(text, encoding="utf-8")


def update_repo_navigation(metrics: dict[str, Any]) -> None:
    rel = "revisions/2026-04-29-artifact-06-v34-full-test-run/"
    block = (
        "<!-- V34_FULL_TEST_RUN_START -->\n"
        "## Latest: V34 Full Test Run\n\n"
        f"The April 29 V34 answer-aware Runtime-at-Boot repair run reached **{metrics['correct']}/{metrics['cases']} "
        f"({fmt_pct(metrics['accuracy'])})** on the full AIME-2026 Q1-Q30 dataset. "
        "Runtime-at-Boot passed, all 13 targeted prior misses were repaired, and the only miss was Q04 "
        "(`137` submitted vs `70` expected) from a distinct-value/object-identification failure.\n\n"
        f"Read the full package: [`{rel}`]({rel}).\n"
        "<!-- V34_FULL_TEST_RUN_END -->"
    )
    update_text_file_once(REPO_DIR / "README.md", "V34_FULL_TEST_RUN_START", block, "## Results At A Glance")

    nav_line = (
        f"| [`{rel}`]({rel}README.md) | April 29 V34 full AIME-2026 run: 29/30, full figures, per-question reports, raw export copy |\n"
    )
    nav_path = REPO_DIR / "NAVIGATION.md"
    nav_text = nav_path.read_text(encoding="utf-8", errors="replace")
    if rel not in nav_text:
        insert_after = "| [`revisions/2026-04-29-artifact-05-q17-q27-transcript-diagnostics/`](revisions/2026-04-29-artifact-05-q17-q27-transcript-diagnostics/) | April 29 Q17/Q27 transcript diagnostics and comparison figures |\n"
        if insert_after in nav_text:
            nav_text = nav_text.replace(insert_after, insert_after + nav_line, 1)
        else:
            nav_text += "\n" + nav_line
        nav_path.write_text(nav_text, encoding="utf-8")

    rev_path = REPO_DIR / "revisions" / "README.md"
    rev_text = rev_path.read_text(encoding="utf-8", errors="replace")
    row = (
        f"| 06 | [`2026-04-29-artifact-06-v34-full-test-run/`](2026-04-29-artifact-06-v34-full-test-run/) | "
        f"{metrics['correct']}/{metrics['cases']} | {fmt_pct(metrics['accuracy'])} | "
        f"{fmt_int(round(metrics['mean_total_tokens']))} | V34 answer-aware Runtime-at-Boot repair full run |\n"
    )
    if "2026-04-29-artifact-06-v34-full-test-run" not in rev_text:
        target = "| 05 | [`2026-04-29-artifact-05-q17-q27-transcript-diagnostics/`](2026-04-29-artifact-05-q17-q27-transcript-diagnostics/) | 2/3 selected slice | 66.67% | ~2.21M on Q17 | Q17/Q27 transcript diagnostic; Q27 recovered, Q17 false-confidence miss |\n"
        if target in rev_text:
            rev_text = rev_text.replace(target, target + row, 1)
        else:
            rev_text += "\n" + row
        note = (
            "\nArtifact 06 is the April 29 V34 full test run. It is the highest-scoring artifact in the ledger "
            "at 29/30, but it is answer-aware because V34 adds repair rows for known AIME-2026 misses. "
            "Use it as architecture and Runtime-at-Boot repair evidence, not as a blind benchmark claim.\n"
        )
        rev_text += note
        rev_path.write_text(rev_text, encoding="utf-8")

    docs_path = REPO_DIR / "docs" / "index.md"
    docs_block = (
        "<!-- V34_FULL_TEST_RUN_START -->\n"
        "## V34 Full Test Run\n\n"
        f"Latest evidence package: [{metrics['correct']}/{metrics['cases']} V34 full AIME-2026 run](../{rel}README.md), "
        "with full figures, per-question reports, Runtime-at-Boot analysis, and raw export evidence.\n"
        "<!-- V34_FULL_TEST_RUN_END -->"
    )
    update_text_file_once(docs_path, "V34_FULL_TEST_RUN_START", docs_block, "## Results Snapshot")


def main() -> None:
    if not RUN_DIR.exists():
        raise FileNotFoundError(RUN_DIR)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "data").mkdir(exist_ok=True)
    (OUT_DIR / "visualizations").mkdir(exist_ok=True)
    scripts_dir = OUT_DIR / "scripts"
    scripts_dir.mkdir(exist_ok=True)
    shutil.copy2(Path(__file__).resolve(), scripts_dir / "analyze_v34_full_run.py")

    source_manifest = copy_raw_export()
    score_summary = read_json(RUN_DIR / "AIME-2026_dataset_score_summary.json")
    attached_summary = read_json(RUN_DIR / "attached_test_summary.json")
    boot_summary = read_json(RUN_DIR / "runtime_at_boot_summary.json")
    prior_rows, prior_by_key = build_prior_rows()
    problem_rows, role_rows, turn_rows, payloads_by_idx = build_run_rows()
    _ = payloads_by_idx
    slices = build_slices(problem_rows)
    comparison_rows, summary_rows = build_comparison_rows(prior_rows, prior_by_key, problem_rows)
    boot_table = boot_rows(boot_summary)

    write_csv(OUT_DIR / "data" / "v34_problem_results.csv", problem_rows)
    write_csv(OUT_DIR / "data" / "v34_role_runtime_by_question.csv", role_rows)
    write_csv(OUT_DIR / "data" / "v34_turn_timing_long.csv", turn_rows)
    write_csv(OUT_DIR / "data" / "v34_summary_and_slices.csv", slices)
    write_csv(OUT_DIR / "data" / "v34_vs_prior_artifacts_q1_q30.csv", comparison_rows)
    write_csv(OUT_DIR / "data" / "v34_artifact_comparison_summary.csv", summary_rows)
    write_csv(OUT_DIR / "data" / "v34_runtime_at_boot_summary.csv", boot_table)

    figures: list[FigureRecord] = []
    make_figures(problem_rows, role_rows, comparison_rows, summary_rows, boot_table, figures)
    write_question_reports(problem_rows, role_rows, comparison_rows)
    write_visual_index(figures)
    metrics = write_main_report(
        problem_rows,
        slices,
        comparison_rows,
        summary_rows,
        boot_table,
        score_summary,
        attached_summary,
        boot_summary,
        source_manifest,
    )
    write_repro_and_manifest(source_manifest, metrics)
    update_repo_navigation(metrics)
    print(json.dumps({"artifact_dir": str(OUT_DIR), "metrics": metrics}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

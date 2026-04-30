from __future__ import annotations

import csv
import html
import json
import math
from pathlib import Path
from statistics import mean

REVISIONS = Path(__file__).resolve().parents[1]
ROOT = REVISIONS.parent
DATA = REVISIONS / "data"
VIS = REVISIONS / "visualizations"
V34 = REVISIONS / "2026-04-29-artifact-06-v34-full-test-run"
V34_DATA = V34 / "data"
VIS.mkdir(parents=True, exist_ok=True)
DATA.mkdir(parents=True, exist_ok=True)

RUNS = [
    {"key": "frozen", "label": "Artifact 01 frozen pruned", "short": "Frozen", "color": "#6b7280", "claim": "blind/pruned baseline"},
    {"key": "unrestricted", "label": "Artifact 02 unrestricted", "short": "Unrestricted", "color": "#2563eb", "claim": "high-budget reference"},
    {"key": "current", "label": "Artifact 03 Apr27 benchmarkgrade", "short": "Apr27 benchmark", "color": "#7e22ce", "claim": "compact benchmarkgrade"},
    {"key": "official", "label": "Artifact 04 Apr28 RAB v33", "short": "Apr28 RAB v33", "color": "#ea580c", "claim": "Runtime-at-Boot negative diagnostic"},
    {"key": "v34", "label": "Artifact 06 V34 answer-aware replay", "short": "V34 answer-aware", "color": "#16a34a", "claim": "answer-aware context-recall replay"},
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def b(value: object) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def f(value: object) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0


def i(value: object) -> int:
    try:
        return int(float(str(value)))
    except Exception:
        return 0


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def fmt_int(value: float) -> str:
    return f"{int(round(value)):,}"


def svg_text(x: float, y: float, text: object, *, size: int = 12, weight: str = "400", fill: str = "#0f172a", anchor: str = "start") -> str:
    return f'<text x="{x:.1f}" y="{y:.1f}" font-family="Inter,Segoe UI,Arial,sans-serif" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(text)}</text>'


def svg_rect(x: float, y: float, w: float, h: float, *, fill: str, rx: float = 3, stroke: str | None = None) -> str:
    stroke_attr = f' stroke="{stroke}"' if stroke else ""
    return f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx:.1f}" fill="{fill}"{stroke_attr}/>'


def svg_doc(width: int, height: int, body: list[str]) -> str:
    return "\n".join([
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
        *body,
        '</svg>',
        '',
    ])


def load_rows() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    four_rows = read_csv(DATA / "artifact_comparison_q1_q30.csv")
    v34_rows = {i(row["idx"]): row for row in read_csv(V34_DATA / "v34_vs_prior_artifacts_q1_q30.csv")}
    long_rows: list[dict[str, object]] = []
    wide_rows: list[dict[str, object]] = []
    for row in four_rows:
        idx = i(row["idx"])
        vrow = v34_rows[idx]
        wide = {"idx": idx, "expected_answer": row["expected_answer"]}
        for run in RUNS:
            key = run["key"]
            source = vrow if key == "v34" else row
            answer = source.get(f"{key}_answer", "")
            correct = b(source.get(f"{key}_correct", ""))
            tokens = f(source.get(f"{key}_tokens", ""))
            seconds = f(source.get(f"{key}_seconds", ""))
            long_rows.append({
                "run_key": key,
                "run_label": run["label"],
                "run_short_label": run["short"],
                "claim_class": run["claim"],
                "idx": idx,
                "expected_answer": row["expected_answer"],
                "submitted_answer": answer,
                "correct": correct,
                "total_tokens": int(tokens),
                "seconds": seconds,
            })
            wide[f"{key}_answer"] = answer
            wide[f"{key}_correct"] = correct
            wide[f"{key}_tokens"] = int(tokens)
            wide[f"{key}_seconds"] = round(seconds, 4)
        official = b(wide["official_correct"])
        v34c = b(wide["v34_correct"])
        if official and v34c:
            delta = "same_correct"
        elif (not official) and v34c:
            delta = "v34_fix_vs_artifact04"
        elif official and (not v34c):
            delta = "v34_regression_vs_artifact04"
        else:
            delta = "same_miss"
        wide["v34_vs_artifact04"] = delta
        wide_rows.append(wide)

    summary_rows: list[dict[str, object]] = []
    by_run = {run["key"]: [] for run in RUNS}
    for row in long_rows:
        by_run[row["run_key"]].append(row)
    for run in RUNS:
        rows = by_run[run["key"]]
        correct = sum(1 for row in rows if row["correct"] is True)
        total_tokens = sum(f(row["total_tokens"]) for row in rows)
        total_seconds = sum(f(row["seconds"]) for row in rows)
        summary_rows.append({
            "run_key": run["key"],
            "run_label": run["label"],
            "run_short_label": run["short"],
            "claim_class": run["claim"],
            "cases": len(rows),
            "correct": correct,
            "incorrect": len(rows) - correct,
            "accuracy": round(correct / len(rows), 6),
            "mean_total_tokens": round(total_tokens / len(rows), 1),
            "total_tokens": int(total_tokens),
            "mean_seconds": round(total_seconds / len(rows), 3),
            "total_seconds": round(total_seconds, 3),
            "tokens_per_correct": round(total_tokens / correct, 1) if correct else "",
        })
    return long_rows, wide_rows, summary_rows


def draw_scoreboard(summary_rows: list[dict[str, object]]) -> None:
    width, height = 1120, 470
    body: list[str] = []
    body.append(svg_text(34, 46, "AIME 2026 Five-Full-Run Scoreboard", size=26, weight="700"))
    body.append(svg_text(34, 72, "Artifact 05 is omitted here because it is a 2/3 selected-slice diagnostic; V34 is answer-aware replay, not blind benchmark.", size=13, fill="#475569"))
    x_label, x_bar, bar_w, row_h, y0 = 34, 285, 620, 65, 112
    for n, row in enumerate(summary_rows):
        run = next(r for r in RUNS if r["key"] == row["run_key"])
        y = y0 + n * row_h
        body.append(svg_text(x_label, y + 23, run["short"], size=14, weight="600"))
        body.append(svg_text(x_label, y + 42, run["claim"], size=11, fill="#64748b"))
        body.append(svg_rect(x_bar, y, bar_w, 30, fill="#eff6ff", rx=4))
        body.append(svg_rect(x_bar, y, bar_w * f(row["correct"]) / 30.0, 30, fill=run["color"], rx=4))
        body.append(svg_text(x_bar + bar_w + 24, y + 22, f"{row['correct']}/30", size=18, weight="700"))
        meta = f"avg tokens {fmt_int(f(row['mean_total_tokens']))} | avg seconds {f(row['mean_seconds']):.1f} | tokens/correct {fmt_int(f(row['tokens_per_correct']))}"
        body.append(svg_text(x_bar, y + 49, meta, size=11, fill="#475569"))
    (VIS / "five_run_scoreboard_q1_q30.svg").write_text(svg_doc(width, height, body), encoding="utf-8")


def draw_result_grid(wide_rows: list[dict[str, object]]) -> None:
    width, height = 1220, 360
    body: list[str] = []
    body.append(svg_text(34, 42, "Q1-Q30 Five-Full-Run Result Grid", size=25, weight="700"))
    body.append(svg_text(34, 66, "Green = correct, red = missed. Numbers inside cells are submitted answers. V34 row is answer-aware replay.", size=13, fill="#475569"))
    x0, y0, cell, gap, row_h = 230, 104, 26, 5, 44
    for idx in range(1, 31):
        x = x0 + (idx - 1) * (cell + gap) + cell / 2
        body.append(svg_text(x, y0 - 12, idx, size=10, fill="#334155", anchor="middle"))
    for r, run in enumerate(RUNS):
        y = y0 + r * row_h
        body.append(svg_text(34, y + 18, run["short"], size=13, weight="600"))
        for idx, row in enumerate(wide_rows, start=1):
            x = x0 + (idx - 1) * (cell + gap)
            correct = b(row[f"{run['key']}_correct"])
            fill = "#1f8f3a" if correct else "#dc2626"
            body.append(svg_rect(x, y, cell, 26, fill=fill, rx=3))
            answer = str(row[f"{run['key']}_answer"])
            size = 8 if len(answer) <= 3 else 7
            body.append(svg_text(x + cell / 2, y + 17, answer, size=size, weight="700", fill="#ffffff", anchor="middle"))
    (VIS / "q1_q30_five_run_result_grid.svg").write_text(svg_doc(width, height, body), encoding="utf-8")


def draw_token_efficiency(summary_rows: list[dict[str, object]]) -> None:
    width, height = 1120, 455
    body: list[str] = []
    body.append(svg_text(34, 44, "Token Efficiency And Score Across Five Full Runs", size=25, weight="700"))
    body.append(svg_text(34, 68, "Bar width is log-scaled by mean tokens/problem so V34's high-compute replay can share the same frame.", size=13, fill="#475569"))
    max_log = max(math.log10(f(row["mean_total_tokens"])) for row in summary_rows)
    min_log = min(math.log10(f(row["mean_total_tokens"])) for row in summary_rows)
    x_label, x_bar, bar_w, row_h, y0 = 34, 285, 620, 65, 112
    for n, row in enumerate(summary_rows):
        run = next(r for r in RUNS if r["key"] == row["run_key"])
        y = y0 + n * row_h
        log_value = math.log10(f(row["mean_total_tokens"]))
        scaled = 0.12 + 0.88 * ((log_value - min_log) / (max_log - min_log if max_log > min_log else 1.0))
        body.append(svg_text(x_label, y + 23, run["short"], size=14, weight="600"))
        body.append(svg_rect(x_bar, y, bar_w, 30, fill="#eff6ff", rx=4))
        body.append(svg_rect(x_bar, y, bar_w * scaled, 30, fill=run["color"], rx=4))
        body.append(svg_text(x_bar + bar_w + 24, y + 21, f"{fmt_int(f(row['mean_total_tokens']))} avg tokens", size=14, weight="600"))
        detail = f"score {row['correct']}/30 | tokens/correct {fmt_int(f(row['tokens_per_correct']))} | avg seconds {f(row['mean_seconds']):.1f}"
        body.append(svg_text(x_bar, y + 49, detail, size=11, fill="#475569"))
    (VIS / "token_efficiency_five_run.svg").write_text(svg_doc(width, height, body), encoding="utf-8")


def draw_v34_delta(wide_rows: list[dict[str, object]]) -> None:
    width, height = 1120, 210
    body: list[str] = []
    body.append(svg_text(34, 42, "V34 vs Artifact 04: Problem-Level Delta", size=25, weight="700"))
    body.append(svg_text(34, 66, "Blue = V34 fixed an Artifact 04 miss, red = V34 lost an Artifact 04 win, green = unchanged win, gray = unchanged miss.", size=13, fill="#475569"))
    x0, y0, cell, gap = 108, 104, 28, 6
    fixes, regressions, unchanged_miss = [], [], []
    for idx in range(1, 31):
        x = x0 + (idx - 1) * (cell + gap) + cell / 2
        body.append(svg_text(x, y0 - 14, idx, size=10, fill="#334155", anchor="middle"))
    for idx, row in enumerate(wide_rows, start=1):
        delta = row["v34_vs_artifact04"]
        if delta == "v34_fix_vs_artifact04":
            fill, label = "#2563eb", "FIX"
            fixes.append(idx)
        elif delta == "v34_regression_vs_artifact04":
            fill, label = "#dc2626", "LOST"
            regressions.append(idx)
        elif delta == "same_correct":
            fill, label = "#15803d", "WIN"
        else:
            fill, label = "#94a3b8", "MISS"
            unchanged_miss.append(idx)
        x = x0 + (idx - 1) * (cell + gap)
        body.append(svg_rect(x, y0, cell, 32, fill=fill, rx=4))
        body.append(svg_text(x + cell / 2, y0 + 20, label, size=8, weight="700", fill="#ffffff", anchor="middle"))
    body.append(svg_text(34, 170, f"V34 fixes vs Artifact 04: {', '.join('Q' + str(x) for x in fixes) or 'none'}. V34 regressions: {', '.join('Q' + str(x) for x in regressions) or 'none'}. Unchanged misses: {', '.join('Q' + str(x) for x in unchanged_miss) or 'none'}.", size=12, fill="#334155"))
    body.append(svg_text(34, 190, "Interpretation caveat: V34 is answer-aware context-recall replay, so fixes are architectural/memory evidence, not blind-solve evidence.", size=12, fill="#b45309"))
    (VIS / "v34_vs_artifact04_delta.svg").write_text(svg_doc(width, height, body), encoding="utf-8")


def main() -> None:
    long_rows, wide_rows, summary_rows = load_rows()
    write_csv(DATA / "all_five_full_run_artifacts_q1_q30_long.csv", long_rows, [
        "run_key", "run_label", "run_short_label", "claim_class", "idx", "expected_answer", "submitted_answer", "correct", "total_tokens", "seconds",
    ])
    wide_fields = ["idx", "expected_answer"]
    for run in RUNS:
        wide_fields.extend([f"{run['key']}_answer", f"{run['key']}_correct", f"{run['key']}_tokens", f"{run['key']}_seconds"])
    wide_fields.append("v34_vs_artifact04")
    write_csv(DATA / "five_full_run_artifact_comparison_q1_q30.csv", wide_rows, wide_fields)
    write_csv(DATA / "five_full_run_summary_q1_q30.csv", summary_rows, [
        "run_key", "run_label", "run_short_label", "claim_class", "cases", "correct", "incorrect", "accuracy", "mean_total_tokens", "total_tokens", "mean_seconds", "total_seconds", "tokens_per_correct",
    ])
    draw_scoreboard(summary_rows)
    draw_result_grid(wide_rows)
    draw_token_efficiency(summary_rows)
    draw_v34_delta(wide_rows)
    summary = {
        "event": "five_full_run_summary_generated",
        "runs": [row["run_key"] for row in summary_rows],
        "figures": [
            "revisions/visualizations/five_run_scoreboard_q1_q30.svg",
            "revisions/visualizations/q1_q30_five_run_result_grid.svg",
            "revisions/visualizations/token_efficiency_five_run.svg",
            "revisions/visualizations/v34_vs_artifact04_delta.svg",
        ],
        "data": [
            "revisions/data/all_five_full_run_artifacts_q1_q30_long.csv",
            "revisions/data/five_full_run_artifact_comparison_q1_q30.csv",
            "revisions/data/five_full_run_summary_q1_q30.csv",
        ],
        "caveat": "Artifact 05 omitted because selected-slice diagnostic; V34 included as answer-aware context-recall replay, not blind benchmark.",
    }
    (DATA / "five_full_run_summary_manifest.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
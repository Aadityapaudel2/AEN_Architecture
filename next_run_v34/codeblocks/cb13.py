"""## 13 - Score, Package, and Download Files

CB13 packages the transcript artifacts written by CB11/CB12. It is now
route-aware:

- prompt-only CB12 runs package correctly;
- dataset-only CB12 runs score exactly the selected dataset rows;
- prompt+dataset CB12 runs package/score both route artifact directories.

If an answer key is available, CB13 scores strictly. If no key is available
for a prompt route, CB13 still produces private/public transcript packages and
marks the route as unscored instead of failing before packaging.
"""

from __future__ import annotations

import json
import re
import shutil
import time
from pathlib import Path
from typing import Any

import pandas as pd


CB13_GENERIC_SCORE_REVISION = "2026-04-29-cb13-route-aware-score-package-r2"

BENCHMARK_NAME = str(globals().get("BENCHMARK_NAME", "benchmark") or "benchmark")
SAFE_BENCHMARK_NAME = re.sub(r"[^A-Za-z0-9._-]+", "_", BENCHMARK_NAME).strip("_") or "benchmark"

ANSWER_MIN = int(globals().get("ANSWER_MIN", 0))
ANSWER_MAX = int(globals().get("ANSWER_MAX", 99999))
PRIVATE_KEY_PATH = str(globals().get("PRIVATE_KEY_PATH", "") or "").strip()
CB13_REQUIRE_ANSWER_KEY = bool(globals().get("CB13_REQUIRE_ANSWER_KEY", False))
CB13_SCORE_MODE = str(globals().get("CB13_SCORE_MODE", "integer_or_exact") or "integer_or_exact").strip().lower()
CB13_PACKAGE_ROOT = Path(str(globals().get("CB13_PACKAGE_ROOT", "/content") or "/content"))
if not CB13_PACKAGE_ROOT.exists():
    CB13_PACKAGE_ROOT = Path(str(globals().get("TRANSCRIPT_ARTIFACT_DIR", ".") or ".")).expanduser().parent


def _cb13_slug(value: Any, fallback: str = "benchmark") -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", str(value or "").strip()).strip("_")
    return text or str(fallback)


def _cb13_route_summaries() -> list[dict[str, Any]]:
    explicit_dirs = list(globals().get("CB13_ARTIFACT_DIRS", []) or [])
    if explicit_dirs:
        return [
            {
                "route_name": f"artifact_{index}",
                "artifact_dir": str(path),
                "summary": {},
            }
            for index, path in enumerate(explicit_dirs, start=1)
            if str(path or "").strip()
        ]

    summaries = list(globals().get("CB12_ROUTE_SUMMARIES", []) or [])
    route_summaries: list[dict[str, Any]] = []
    for index, raw_summary in enumerate(summaries, start=1):
        summary = dict(raw_summary or {})
        artifact_dir = str(summary.get("artifact_dir", "") or dict(summary.get("summary") or {}).get("artifact_dir", "") or "").strip()
        if artifact_dir:
            route_summaries.append(
                {
                    "route_name": str(summary.get("route_name", f"route_{index}") or f"route_{index}"),
                    "artifact_dir": str(artifact_dir),
                    "summary": dict(summary.get("summary") or {}),
                }
            )

    if route_summaries:
        return route_summaries

    artifact_dir = str(globals().get("TRANSCRIPT_ARTIFACT_DIR", "") or "").strip()
    if artifact_dir:
        return [{"route_name": "default", "artifact_dir": artifact_dir, "summary": {}}]

    raise ValueError(
        "CB13 could not find an artifact directory. Run CB12 first, set "
        "TRANSCRIPT_ARTIFACT_DIR, or set CB13_ARTIFACT_DIRS."
    )


def normalize_integer_answer(value: Any) -> str:
    text = str(value or "").strip()
    if not re.fullmatch(r"\d+", text):
        return ""
    number = int(text)
    if ANSWER_MIN <= number <= ANSWER_MAX:
        return str(number)
    return ""


def normalize_exact_answer(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def _cb13_answers_equal(model_answer: Any, expected_answer: Any) -> bool:
    expected_raw = str(expected_answer or "").strip()
    model_raw = str(model_answer or "").strip()
    if not expected_raw:
        return False
    expected_integer = normalize_integer_answer(expected_raw)
    model_integer = normalize_integer_answer(model_raw)
    if expected_integer:
        return bool(model_integer and model_integer == expected_integer)
    if CB13_SCORE_MODE in {"exact", "integer_or_exact", "generic"}:
        return bool(model_raw and normalize_exact_answer(model_raw) == normalize_exact_answer(expected_raw))
    return False


def _cb13_load_route_rows(artifact_dir: Path, route_name: str) -> list[dict[str, Any]]:
    rows_by_artifact = globals().get("CB12_ROUTE_ROWS_BY_ARTIFACT_DIR", {})
    if isinstance(rows_by_artifact, dict):
        for key in [str(artifact_dir), str(artifact_dir.resolve())]:
            rows = rows_by_artifact.get(key)
            if rows:
                return [dict(row or {}) for row in list(rows)]

    rows_by_route = globals().get("CB12_ROUTE_ROWS_BY_ROUTE_NAME", {})
    if isinstance(rows_by_route, dict):
        rows = rows_by_route.get(str(route_name))
        if rows:
            return [dict(row or {}) for row in list(rows)]

    test_rows = list(globals().get("TEST_ROWS", []) or [])
    if test_rows:
        return [dict(row or {}) for row in test_rows]
    return []


def _cb13_key_from_rows(rows: list[dict[str, Any]], attempted_ids: set[str]) -> tuple[pd.DataFrame, str]:
    payload_rows: list[dict[str, Any]] = []
    for row in rows:
        row_id = str(row.get("id") or row.get("question_id") or "").strip()
        if not row_id or row_id not in attempted_ids:
            continue
        if "answer" not in row and "expected_answer" not in row:
            continue
        expected = str(row.get("answer", row.get("expected_answer", "")) or "").strip()
        if not expected:
            continue
        payload_rows.append(
            {
                "id": row_id,
                "expected_answer": expected,
                "problem_idx": str(row.get("problem_idx", "")),
            }
        )
    return pd.DataFrame(payload_rows).fillna(""), "CB12 route rows"


def _cb13_key_from_results(results_df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    if "expected_answer" not in results_df.columns:
        return pd.DataFrame(), ""
    id_col = "question_id" if "question_id" in results_df.columns else "id"
    if id_col not in results_df.columns:
        return pd.DataFrame(), ""
    key_df = results_df[[id_col, "expected_answer"]].rename(columns={id_col: "id"}).copy()
    key_df["expected_answer"] = key_df["expected_answer"].astype(str).str.strip()
    key_df = key_df[key_df["expected_answer"].astype(str).str.len() > 0].copy()
    return key_df.fillna(""), "attached_test_full_log.expected_answer"


def _cb13_key_from_private_path() -> tuple[pd.DataFrame, str]:
    if not PRIVATE_KEY_PATH:
        return pd.DataFrame(), ""
    private_key_path = Path(PRIVATE_KEY_PATH).expanduser()
    if not private_key_path.exists():
        raise FileNotFoundError(f"Missing PRIVATE_KEY_PATH: {private_key_path}")
    key_df = pd.read_csv(private_key_path, dtype=str).fillna("")
    if "KEY" in key_df.columns and "answer" not in key_df.columns:
        key_df = key_df.rename(columns={"KEY": "answer"})
    if "answer" in key_df.columns and "expected_answer" not in key_df.columns:
        key_df = key_df.rename(columns={"answer": "expected_answer"})
    return key_df.fillna(""), str(private_key_path)


def _cb13_resolve_key(
    *,
    route_rows: list[dict[str, Any]],
    attempted_ids: set[str],
    results_df: pd.DataFrame,
) -> tuple[pd.DataFrame, str, str]:
    key_candidates = [
        _cb13_key_from_rows(route_rows, attempted_ids),
        _cb13_key_from_results(results_df),
        _cb13_key_from_private_path(),
    ]
    for key_df, source in key_candidates:
        if key_df is None or key_df.empty:
            continue
        if "answer" in key_df.columns and "expected_answer" not in key_df.columns:
            key_df = key_df.rename(columns={"answer": "expected_answer"})
        missing_cols = {"id", "expected_answer"} - set(key_df.columns)
        if missing_cols:
            continue
        key_df = key_df.copy().fillna("")
        key_df["id"] = key_df["id"].astype(str).str.strip()
        key_df["expected_answer"] = key_df["expected_answer"].astype(str).str.strip()
        key_df = key_df[(key_df["id"].astype(str).str.len() > 0) & (key_df["expected_answer"].astype(str).str.len() > 0)].copy()
        if key_df.empty:
            continue
        if key_df["id"].duplicated().any():
            duplicate_ids = key_df.loc[key_df["id"].duplicated(), "id"].astype(str).tolist()
            raise ValueError({"event": "cb13_duplicate_key_ids", "ids": duplicate_ids, "key_source": source})
        missing_key_ids = sorted(attempted_ids - set(key_df["id"].astype(str)))
        if missing_key_ids:
            # A partial key is not safe for strict scoring. Try the next source.
            continue
        return key_df, str(source), ""

    message = "No complete answer key was available for this artifact."
    if CB13_REQUIRE_ANSWER_KEY:
        raise ValueError(
            {
                "event": "cb13_missing_answer_key",
                "message": message,
                "hint": "Provide TEST_ROWS/CB12 route rows with answer values, or set PRIVATE_KEY_PATH.",
            }
        )
    return pd.DataFrame(), "", message


def _cb13_validate_artifact(artifact_dir: Path) -> tuple[Path, Path, Path]:
    submission_path = artifact_dir / "attached_test_submission.csv"
    results_path = artifact_dir / "attached_test_full_log.csv"
    summary_path = artifact_dir / "attached_test_summary.json"

    if not artifact_dir.exists():
        raise FileNotFoundError(f"Missing artifact dir: {artifact_dir}")
    if not submission_path.exists():
        raise FileNotFoundError(f"Missing submission CSV: {submission_path}")
    if not results_path.exists():
        raise FileNotFoundError(f"Missing full log CSV: {results_path}")
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing summary JSON: {summary_path}")
    return submission_path, results_path, summary_path


def _cb13_score_one_route(route_info: dict[str, Any]) -> dict[str, Any]:
    route_name = str(route_info.get("route_name", "default") or "default")
    artifact_dir = Path(str(route_info.get("artifact_dir", "") or "")).expanduser()
    submission_path, results_path, summary_path = _cb13_validate_artifact(artifact_dir)

    summary_json = json.loads(summary_path.read_text(encoding="utf-8"))
    summary_artifact_dir = str(summary_json.get("artifact_dir", "") or "").strip()
    if summary_artifact_dir and Path(summary_artifact_dir).expanduser() != artifact_dir:
        raise ValueError(
            {
                "event": "cb13_artifact_dir_mismatch",
                "expected_artifact_dir": str(artifact_dir),
                "summary_artifact_dir": summary_artifact_dir,
            }
        )

    submission_df = pd.read_csv(submission_path, dtype=str).fillna("")
    results_df = pd.read_csv(results_path, dtype=str).fillna("")

    missing_submission_cols = {"id", "answer"} - set(submission_df.columns)
    if missing_submission_cols:
        raise ValueError(f"Submission missing columns: {sorted(missing_submission_cols)}")
    if submission_df["id"].duplicated().any():
        duplicate_ids = submission_df.loc[submission_df["id"].duplicated(), "id"].astype(str).tolist()
        raise ValueError({"event": "cb13_duplicate_submission_ids", "ids": duplicate_ids})

    route_rows = _cb13_load_route_rows(artifact_dir, route_name)
    summary_cases = int(summary_json.get("cases", 0) or 0)
    expected_rows = int(len(route_rows) or summary_cases or len(submission_df))
    if len(submission_df) != expected_rows:
        raise ValueError(
            {
                "event": "cb13_submission_row_count_mismatch",
                "route_name": route_name,
                "expected_rows": expected_rows,
                "actual_rows": int(len(submission_df)),
            }
        )

    attempted_ids = set(submission_df["id"].astype(str))
    key_df, key_source, unscored_reason = _cb13_resolve_key(
        route_rows=route_rows,
        attempted_ids=attempted_ids,
        results_df=results_df,
    )
    scored = bool(not key_df.empty)

    scored_df = submission_df.copy()
    scored_df["model_answer_raw"] = scored_df["answer"].astype(str).str.strip()
    scored_df["model_answer_normalized"] = scored_df["model_answer_raw"].map(normalize_integer_answer)
    scored_df["valid_answer"] = scored_df["model_answer_raw"].map(lambda value: bool(str(value).strip()))

    extra_key_ids: list[str] = []
    if scored:
        key_df = key_df.copy().fillna("")
        key_df["expected_answer_normalized"] = key_df["expected_answer"].map(normalize_integer_answer)
        key_ids = set(key_df["id"].astype(str))
        extra_key_ids = sorted(key_ids - attempted_ids)
        merge_cols = ["id", "expected_answer", "expected_answer_normalized"]
        if "problem_idx" in key_df.columns:
            merge_cols.append("problem_idx")
        scored_df = scored_df.merge(key_df[merge_cols], on="id", how="left")
        scored_df["correct"] = scored_df.apply(
            lambda row: _cb13_answers_equal(row.get("model_answer_raw", ""), row.get("expected_answer", "")),
            axis=1,
        )
    else:
        scored_df["expected_answer"] = ""
        scored_df["expected_answer_normalized"] = ""
        scored_df["correct"] = ""

    telemetry_df = results_df.rename(columns={"question_id": "id"}).copy()
    if "id" in telemetry_df.columns:
        telemetry_df = telemetry_df.drop(
            columns=[col for col in telemetry_df.columns if col in scored_df.columns and col != "id"],
            errors="ignore",
        )
        scored_df = scored_df.merge(telemetry_df, on="id", how="left")

    rows = int(len(scored_df))
    correct = int(scored_df["correct"].sum()) if scored else None
    invalid = int((~scored_df["valid_answer"]).sum())
    incorrect = int(rows - int(correct)) if scored and correct is not None else None

    route_safe_name = _cb13_slug(route_name, "route")
    private_csv = artifact_dir / f"{SAFE_BENCHMARK_NAME}_{route_safe_name}_PRIVATE_FULL.csv"
    public_csv = artifact_dir / f"{SAFE_BENCHMARK_NAME}_{route_safe_name}_public_certification.csv"
    summary_json_path = artifact_dir / f"{SAFE_BENCHMARK_NAME}_{route_safe_name}_score_summary.json"

    score_summary = {
        "event": "benchmark_scored",
        "revision": CB13_GENERIC_SCORE_REVISION,
        "benchmark_name": BENCHMARK_NAME,
        "route_name": route_name,
        "artifact_dir": str(artifact_dir),
        "key_source": key_source,
        "scored": bool(scored),
        "unscored_reason": str(unscored_reason),
        "expected_rows": int(expected_rows),
        "rows": rows,
        "correct": correct,
        "incorrect": incorrect,
        "invalid": invalid,
        "accuracy": float(correct / rows) if scored and rows and correct is not None else None,
        "accuracy_percent": round(float(correct / rows) * 100.0, 4) if scored and rows and correct is not None else None,
        "correct_ids": scored_df.loc[scored_df["correct"] == True, "id"].astype(str).tolist() if scored else [],
        "incorrect_ids": scored_df.loc[scored_df["correct"] == False, "id"].astype(str).tolist() if scored else [],
        "extra_key_ids_ignored": extra_key_ids,
        "runtime_at_boot_passed": bool(summary_json.get("runtime_at_boot_passed", False)),
        "transcript_dir": str(artifact_dir / "transcripts"),
        "result_payload_dir": str(artifact_dir / "result_payloads"),
        "packaged_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    scored_df.to_csv(private_csv, index=False)
    summary_json_path.write_text(json.dumps(score_summary, indent=2), encoding="utf-8")

    public_df = pd.DataFrame(
        {
            "id": scored_df["id"].astype(str),
            "model_answer": scored_df["model_answer_normalized"].where(
                scored_df["model_answer_normalized"].astype(str).str.len() > 0,
                scored_df["model_answer_raw"],
            ),
            "scored": bool(scored),
            "correct": scored_df["correct"] if scored else "",
        }
    )
    public_df.to_csv(public_csv, index=False)

    public_dir = artifact_dir / "public_shareable"
    public_dir.mkdir(exist_ok=True)
    public_df.to_csv(public_dir / public_csv.name, index=False)
    (public_dir / summary_json_path.name).write_text(json.dumps(score_summary, indent=2), encoding="utf-8")

    stamp = time.strftime("%Y%m%d-%H%M%S")
    CB13_PACKAGE_ROOT.mkdir(parents=True, exist_ok=True)
    private_zip = Path(
        shutil.make_archive(
            str(CB13_PACKAGE_ROOT / f"{SAFE_BENCHMARK_NAME}_{route_safe_name}_PRIVATE_FULL_{expected_rows}q_{stamp}"),
            "zip",
            root_dir=str(artifact_dir.parent),
            base_dir=artifact_dir.name,
        )
    )
    public_zip = Path(
        shutil.make_archive(
            str(CB13_PACKAGE_ROOT / f"{SAFE_BENCHMARK_NAME}_{route_safe_name}_PUBLIC_CERTIFICATION_{expected_rows}q_{stamp}"),
            "zip",
            root_dir=str(public_dir.parent),
            base_dir=public_dir.name,
        )
    )

    route_done = {
        "event": "cb13_route_done",
        "route_name": route_name,
        "summary": score_summary,
        "private_csv": str(private_csv),
        "public_csv": str(public_csv),
        "summary_json": str(summary_json_path),
        "private_zip": str(private_zip),
        "public_zip": str(public_zip),
    }
    print(json.dumps(route_done, ensure_ascii=False, separators=(",", ":")), flush=True)
    return route_done


route_infos = _cb13_route_summaries()
CB13_ROUTE_RESULTS = [_cb13_score_one_route(dict(route_info)) for route_info in route_infos]

CB13_RUN_SUMMARY = {
    "event": "cb13_done",
    "revision": CB13_GENERIC_SCORE_REVISION,
    "benchmark_name": BENCHMARK_NAME,
    "routes": [
        {
            "route_name": str(result.get("route_name", "")),
            "artifact_dir": str(dict(result.get("summary") or {}).get("artifact_dir", "")),
            "scored": bool(dict(result.get("summary") or {}).get("scored", False)),
            "rows": int(dict(result.get("summary") or {}).get("rows", 0) or 0),
            "correct": dict(result.get("summary") or {}).get("correct"),
            "accuracy_percent": dict(result.get("summary") or {}).get("accuracy_percent"),
            "private_zip": str(result.get("private_zip", "")),
            "public_zip": str(result.get("public_zip", "")),
        }
        for result in CB13_ROUTE_RESULTS
    ],
}
globals()["CB13_ROUTE_RESULTS"] = list(CB13_ROUTE_RESULTS)
globals()["CB13_RUN_SUMMARY"] = dict(CB13_RUN_SUMMARY)
globals()["SCORE_SUMMARY"] = dict(CB13_ROUTE_RESULTS[-1].get("summary", {})) if CB13_ROUTE_RESULTS else {}

print(json.dumps(CB13_RUN_SUMMARY, ensure_ascii=False, separators=(",", ":")), flush=True)

try:
    display(pd.DataFrame(CB13_RUN_SUMMARY["routes"]))
except Exception:
    print(pd.DataFrame(CB13_RUN_SUMMARY["routes"]))

try:
    from google.colab import files

    for route_result in CB13_ROUTE_RESULTS:
        files.download(str(route_result.get("private_zip", "")))
        files.download(str(route_result.get("public_zip", "")))
except Exception as exc:
    print(
        {
            "event": "download_not_started",
            "error": str(exc),
            "zips": [
                {
                    "route_name": str(route_result.get("route_name", "")),
                    "private_zip": str(route_result.get("private_zip", "")),
                    "public_zip": str(route_result.get("public_zip", "")),
                }
                for route_result in CB13_ROUTE_RESULTS
            ],
        }
    )

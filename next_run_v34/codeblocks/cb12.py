"""## 12 - Prompt or Dataset Runner

**Purpose:** Run the already-booted AEN controller against either:

- a single pasted prompt, using the notebook-friendly triple-quoted prompt box; or
- a generic tabular benchmark source, with AIME-2026 kept as the default preset.

Route contract:

- `CB12_PROMPT_ROUTE_ENABLED=True` searches for a prompt and runs it first.
- `CB12_DATASET_ROUTE_ENABLED=True` loads and runs the configured dataset.
- If both are true, CB12 runs prompt route first, then dataset route.

CB12 still emits rows in the CB11 attached-test contract: `id` and `problem`
are required; extra fields such as `answer`, `problem_idx`, and `source_url`
are preserved for downstream analysis.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import pandas as pd


CB12_GENERIC_HF_REVISION = "2026-04-29-cb12-prompt-or-dataset-route-r2"


# ---------------------------------------------------------------------------
# Route knobs
# ---------------------------------------------------------------------------

# Prompt route: paste a problem, VoE prompt, theorem-check prompt, etc. in the
# triple-quoted box below. This avoids inline "\n" escaping.
CB12_PROMPT_ROUTE_ENABLED = bool(globals().get("CB12_PROMPT_ROUTE_ENABLED", False))
CB12_DATASET_ROUTE_ENABLED = bool(globals().get("CB12_DATASET_ROUTE_ENABLED", True))

CB12_PROMPT_ID = str(globals().get("CB12_PROMPT_ID", "manual_prompt_001") or "manual_prompt_001").strip()
CB12_PROMPT_EXPECTED_ANSWER = str(globals().get("CB12_PROMPT_EXPECTED_ANSWER", "") or "").strip()
CB12_PROMPT_PATH = str(globals().get("CB12_PROMPT_PATH", "") or "").strip()

CB12_PROMPT_TEXT = r"""

""".strip()

# Optional external override. Use this when another cell has already prepared
# the prompt string and you do not want to paste it into the box above.
CB12_PROMPT_TEXT = str(globals().get("CB12_PROMPT_TEXT_OVERRIDE", CB12_PROMPT_TEXT) or "").strip()


# Dataset route defaults. AIME-2026 remains the baseline, but this can now be
# any readable CSV/Parquet/JSON/JSONL source or a Hugging Face dataset repo.
BENCHMARK_NAME = str(globals().get("BENCHMARK_NAME", "AIME-2026") or "AIME-2026").strip()
BENCHMARK_DATASET_ID = str(globals().get("BENCHMARK_DATASET_ID", "MathArena/aime_2026") or "").strip()
BENCHMARK_DATASET_REVISION = str(globals().get("BENCHMARK_DATASET_REVISION", "main") or "main").strip()
BENCHMARK_DATASET_FILE = str(globals().get("BENCHMARK_DATASET_FILE", "data/train-00000-of-00001.parquet") or "").strip()
BENCHMARK_DATASET_SOURCE = str(
    globals().get(
        "BENCHMARK_DATASET_SOURCE",
        globals().get(
            "BENCHMARK_HF_PARQUET_PATH",
            "hf://datasets/MathArena/aime_2026@main/data/train-00000-of-00001.parquet",
        ),
    )
    or ""
).strip()

# Backward-compatible alias used by older notebooks.
BENCHMARK_HF_PARQUET_PATH = str(BENCHMARK_DATASET_SOURCE)

# Column hints. If the named column is absent, CB12 tries common alternatives.
BENCHMARK_ID_COLUMN = str(globals().get("BENCHMARK_ID_COLUMN", "") or "").strip()
BENCHMARK_PROBLEM_INDEX_COLUMN = str(globals().get("BENCHMARK_PROBLEM_INDEX_COLUMN", "problem_idx") or "problem_idx").strip()
BENCHMARK_PROBLEM_COLUMN = str(globals().get("BENCHMARK_PROBLEM_COLUMN", "problem") or "problem").strip()
BENCHMARK_ANSWER_COLUMN = str(globals().get("BENCHMARK_ANSWER_COLUMN", "answer") or "answer").strip()
BENCHMARK_ID_PREFIX = str(globals().get("BENCHMARK_ID_PREFIX", "") or "").strip()

# Selection contract.
# Problem indices are 1-based values from `BENCHMARK_PROBLEM_INDEX_COLUMN` when
# that column exists. Otherwise they are 1-based dataframe row numbers.
BENCHMARK_PROBLEM_INDICES = list(globals().get("BENCHMARK_PROBLEM_INDICES", []) or [])
BENCHMARK_START_PROBLEM_INDEX = int(globals().get("BENCHMARK_START_PROBLEM_INDEX", 1) or 1)
BENCHMARK_QUESTION_COUNT = int(globals().get("BENCHMARK_QUESTION_COUNT", 0) or 0)

ANSWER_MIN, ANSWER_MAX = 0, 999

CB12_OUTPUT_ROOT = str(
    globals().get(
        "CB12_OUTPUT_ROOT",
        "/content/drive/MyDrive/AthenaV5_colab/outputs",
    )
    or "/content/drive/MyDrive/AthenaV5_colab/outputs"
).rstrip("/")


def _cb12_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() not in {"0", "false", "no", "off", ""}
    return bool(value)


def _cb12_clean(value: Any) -> str:
    cleaner = globals().get("clean_dialogue_text") or globals().get("clean_text")
    if callable(cleaner):
        try:
            return str(cleaner(value)).strip()
        except Exception:
            pass
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def _cb12_slug(value: Any, fallback: str = "benchmark") -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "_", str(value or "").strip().lower()).strip("_")
    return text or str(fallback)


def _cb12_source_suffix(source: str) -> str:
    lowered = str(source or "").split("?", 1)[0].split("#", 1)[0].lower()
    for suffix in [".parquet", ".csv", ".jsonl", ".ndjson", ".json"]:
        if lowered.endswith(suffix):
            return suffix
    return ""


def _cb12_hf_repo_from_url(source: str) -> tuple[str, str, str]:
    """Return `(repo_id, revision, file_path)` for HF dataset links when possible."""

    parsed = urlparse(str(source or "").strip())
    if parsed.netloc.lower() != "huggingface.co":
        return "", "", ""
    path = parsed.path.strip("/")
    prefix = "datasets/"
    if not path.startswith(prefix):
        return "", "", ""
    rest = path[len(prefix) :]
    for marker in ["/blob/", "/resolve/"]:
        if marker in rest:
            repo_id, tail = rest.split(marker, 1)
            if "/" in tail:
                revision, file_path = tail.split("/", 1)
            else:
                revision, file_path = tail, ""
            return repo_id.strip("/"), revision.strip("/") or "main", file_path.strip("/")
    return rest.strip("/"), "main", ""


def _cb12_discover_hf_dataset_file(repo_id: str, revision: str) -> str:
    preferred_suffixes = (".parquet", ".csv", ".jsonl", ".ndjson", ".json")
    try:
        from huggingface_hub import list_repo_files  # type: ignore

        files = list_repo_files(repo_id=repo_id, repo_type="dataset", revision=revision or "main")
    except Exception as exc:
        raise ValueError(
            "CB12 could not discover a file inside the Hugging Face dataset repo. "
            "Set BENCHMARK_DATASET_FILE to a CSV/Parquet/JSON/JSONL file path."
        ) from exc

    ranked: list[str] = []
    for folder_prefix in ["data/", ""]:
        for suffix in preferred_suffixes:
            ranked.extend(
                [
                    str(path)
                    for path in files
                    if str(path).startswith(folder_prefix) and str(path).lower().endswith(suffix)
                ]
            )
    seen: set[str] = set()
    deduped = [path for path in ranked if not (path in seen or seen.add(path))]
    if not deduped:
        raise ValueError(
            f"CB12 found no supported tabular files in Hugging Face dataset repo {repo_id!r}."
        )
    return str(deduped[0])


def _cb12_resolve_dataset_source() -> str:
    source = str(BENCHMARK_DATASET_SOURCE or "").strip()
    dataset_file = str(BENCHMARK_DATASET_FILE or "").strip()
    revision = str(BENCHMARK_DATASET_REVISION or "main").strip() or "main"

    repo_from_url, rev_from_url, file_from_url = _cb12_hf_repo_from_url(source)
    if repo_from_url:
        chosen_file = dataset_file or file_from_url
        chosen_revision = revision or rev_from_url or "main"
        if not chosen_file:
            chosen_file = _cb12_discover_hf_dataset_file(repo_from_url, chosen_revision)
        return f"hf://datasets/{repo_from_url}@{chosen_revision}/{chosen_file}"

    if source.startswith("hf://"):
        return source

    # A bare "namespace/repo" source is treated as a Hugging Face dataset repo.
    if (
        source
        and "://" not in source
        and not Path(source).suffix
        and len(source.split("/")) == 2
    ):
        chosen_file = dataset_file or _cb12_discover_hf_dataset_file(source, revision)
        return f"hf://datasets/{source}@{revision}/{chosen_file}"

    if source:
        return source

    if BENCHMARK_DATASET_ID:
        chosen_file = dataset_file or _cb12_discover_hf_dataset_file(BENCHMARK_DATASET_ID, revision)
        return f"hf://datasets/{BENCHMARK_DATASET_ID}@{revision}/{chosen_file}"

    raise ValueError("CB12 dataset route is enabled, but no dataset source was configured.")


def _cb12_read_dataframe(source: str) -> pd.DataFrame:
    suffix = _cb12_source_suffix(source)
    if suffix == ".parquet":
        df = pd.read_parquet(source)
    elif suffix == ".csv":
        df = pd.read_csv(source)
    elif suffix in {".jsonl", ".ndjson"}:
        df = pd.read_json(source, lines=True)
    elif suffix == ".json":
        df = pd.read_json(source)
    else:
        # Keep the error explicit. Silent format guessing makes notebook runs
        # painful when a Hugging Face page URL was pasted instead of a data file.
        raise ValueError(
            "CB12 does not know how to read this dataset source. "
            "Use a .parquet, .csv, .jsonl, .ndjson, or .json file/link, "
            "or set BENCHMARK_DATASET_FILE for a Hugging Face dataset repo."
        )
    return df.fillna("").reset_index(drop=True)


def _cb12_pick_column(df: pd.DataFrame, preferred: str, candidates: list[str]) -> str:
    columns = [str(col) for col in df.columns]
    if preferred and preferred in columns:
        return preferred
    lowered = {str(col).lower(): str(col) for col in columns}
    for candidate in candidates:
        if candidate in columns:
            return candidate
        if candidate.lower() in lowered:
            return lowered[candidate.lower()]
    return ""


def _cb12_select_dataframe(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, str, str]:
    index_col = _cb12_pick_column(
        raw_df,
        BENCHMARK_PROBLEM_INDEX_COLUMN,
        ["problem_idx", "problem_index", "index", "idx", "number", "question_number"],
    )
    working_df = raw_df.copy()
    selector_col = index_col
    selector_label = "problem_index"

    if selector_col:
        working_df[selector_col] = working_df[selector_col].astype(int)
        working_df = working_df.sort_values(selector_col).reset_index(drop=True)
    else:
        selector_col = "_cb12_row_number"
        selector_label = "row_number"
        working_df[selector_col] = list(range(1, len(working_df) + 1))

    if BENCHMARK_PROBLEM_INDICES:
        wanted = [int(x) for x in BENCHMARK_PROBLEM_INDICES]
        selected_df = working_df[working_df[selector_col].isin(wanted)].copy()
        selected_df = selected_df.set_index(selector_col).loc[wanted].reset_index()
        selection_mode = f"explicit_{selector_label}s"
    elif int(BENCHMARK_QUESTION_COUNT) > 0:
        start_idx = int(BENCHMARK_START_PROBLEM_INDEX)
        stop_idx = start_idx + int(BENCHMARK_QUESTION_COUNT) - 1
        selected_df = working_df[
            (working_df[selector_col] >= start_idx)
            & (working_df[selector_col] <= stop_idx)
        ].copy()
        selection_mode = f"{selector_label}_start_count"
    else:
        selected_df = working_df.copy()
        selection_mode = "full_dataset"

    if int(BENCHMARK_QUESTION_COUNT) > 0 and len(selected_df) != int(BENCHMARK_QUESTION_COUNT):
        raise ValueError(
            {
                "event": "cb12_selection_count_mismatch",
                "expected": int(BENCHMARK_QUESTION_COUNT),
                "actual": int(len(selected_df)),
                "selection_mode": selection_mode,
            }
        )
    if len(selected_df) <= 0:
        raise ValueError({"event": "cb12_empty_selection"})
    return selected_df.reset_index(drop=True), selection_mode, selector_col


def _cb12_dataset_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    resolved_source = _cb12_resolve_dataset_source()
    raw_df = _cb12_read_dataframe(resolved_source)
    selected_df, selection_mode, selector_col = _cb12_select_dataframe(raw_df)

    problem_col = _cb12_pick_column(
        selected_df,
        BENCHMARK_PROBLEM_COLUMN,
        ["problem", "question", "prompt", "statement", "input", "text"],
    )
    if not problem_col:
        raise ValueError(
            {
                "event": "cb12_missing_problem_column",
                "preferred_problem_column": BENCHMARK_PROBLEM_COLUMN,
                "available_columns": sorted(str(col) for col in selected_df.columns),
            }
        )

    answer_col = _cb12_pick_column(
        selected_df,
        BENCHMARK_ANSWER_COLUMN,
        ["answer", "expected_answer", "target", "label", "final_answer"],
    )
    id_col = _cb12_pick_column(
        selected_df,
        BENCHMARK_ID_COLUMN,
        ["id", "question_id", "problem_id", "instance_id"],
    )
    id_prefix = BENCHMARK_ID_PREFIX or _cb12_slug(BENCHMARK_NAME, "benchmark")

    rows: list[dict[str, Any]] = []
    for ordinal, row in enumerate(selected_df.itertuples(index=False), start=1):
        row_dict = dict(zip([str(col) for col in selected_df.columns], row))
        selector_value = int(row_dict.get(selector_col, ordinal) or ordinal)
        row_id = str(row_dict.get(id_col, "") or "").strip() if id_col else ""
        if not row_id:
            row_id = f"{id_prefix}_{selector_value:02d}"
        problem_text = _cb12_clean(row_dict.get(problem_col, ""))
        if not problem_text:
            raise ValueError(f"CB12 selected row {ordinal} has an empty problem text.")
        payload = dict(row_dict)
        payload.update(
            {
                "id": str(row_id),
                "question_id": str(row_id),
                "problem_idx": int(selector_value),
                "question": str(problem_text),
                "problem": str(problem_text),
                "answer": str(row_dict.get(answer_col, "") or "").strip() if answer_col else "",
                "source_url": str(resolved_source),
            }
        )
        rows.append(payload)

    report = {
        "event": "cb12_dataset_loaded",
        "revision": CB12_GENERIC_HF_REVISION,
        "benchmark_name": BENCHMARK_NAME,
        "dataset_id": BENCHMARK_DATASET_ID,
        "dataset_source": str(resolved_source),
        "selection_mode": selection_mode,
        "expected_test_rows": int(len(rows)),
        "selector_column": str(selector_col),
        "problem_column": str(problem_col),
        "answer_column": str(answer_col),
        "id_column": str(id_col),
        "problem_indices": [int(row["problem_idx"]) for row in rows],
        "first_id": rows[0]["id"],
        "last_id": rows[-1]["id"],
    }
    return rows, report


def _cb12_resolve_prompt_text() -> tuple[str, str]:
    prompt_path = str(CB12_PROMPT_PATH or "").strip()
    if prompt_path:
        path = Path(prompt_path).expanduser()
        if path.exists():
            return _cb12_clean(path.read_text(encoding="utf-8", errors="replace")), str(path.resolve())
        raise FileNotFoundError(f"CB12_PROMPT_PATH does not exist: {path}")

    candidates = [
        ("CB12_PROMPT_TEXT", CB12_PROMPT_TEXT),
        ("CB12_PROMPT", globals().get("CB12_PROMPT")),
        ("PROMPT_TEXT", globals().get("PROMPT_TEXT")),
        ("MANUAL_PROMPT", globals().get("MANUAL_PROMPT")),
        ("PROBLEM_PROMPT", globals().get("PROBLEM_PROMPT")),
        ("problem_prompt", globals().get("problem_prompt")),
    ]
    for source_label, value in candidates:
        text = _cb12_clean(value)
        if text:
            return text, source_label
    return "", "not_found"


def _cb12_prompt_rows() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    prompt_text, prompt_source = _cb12_resolve_prompt_text()
    if not prompt_text:
        return [], {
            "event": "cb12_prompt_route_skipped",
            "revision": CB12_GENERIC_HF_REVISION,
            "status": "empty_prompt",
            "prompt_source": str(prompt_source),
        }
    row_id = _cb12_slug(CB12_PROMPT_ID, "manual_prompt_001")
    row = {
        "id": str(row_id),
        "question_id": str(row_id),
        "problem_idx": 1,
        "question": str(prompt_text),
        "problem": str(prompt_text),
        "answer": str(CB12_PROMPT_EXPECTED_ANSWER),
        "source_url": str(prompt_source),
    }
    report = {
        "event": "cb12_prompt_loaded",
        "revision": CB12_GENERIC_HF_REVISION,
        "prompt_id": str(row_id),
        "prompt_source": str(prompt_source),
        "prompt_chars": int(len(prompt_text)),
        "has_expected_answer": bool(str(CB12_PROMPT_EXPECTED_ANSWER).strip()),
    }
    return [row], report


def _cb12_run_route(
    *,
    route_name: str,
    rows: list[dict[str, Any]],
    loaded_report: dict[str, Any],
    artifact_dir: str,
) -> dict[str, Any]:
    rows_by_artifact = globals().setdefault("CB12_ROUTE_ROWS_BY_ARTIFACT_DIR", {})
    if isinstance(rows_by_artifact, dict):
        rows_by_artifact[str(artifact_dir)] = [dict(row) for row in rows]
    rows_by_route = globals().setdefault("CB12_ROUTE_ROWS_BY_ROUTE_NAME", {})
    if isinstance(rows_by_route, dict):
        rows_by_route[str(route_name)] = [dict(row) for row in rows]

    print(json.dumps(dict(loaded_report), ensure_ascii=False, separators=(",", ":")), flush=True)
    summary = dict(
        run_attached_test_dataset_export(
            test_dataset=list(rows),
            limit=None,
            artifact_dir=artifact_dir,
            submission_csv_path=f"{artifact_dir}/attached_test_submission.csv",
            results_csv_path=f"{artifact_dir}/attached_test_full_log.csv",
        )
        or {}
    )
    route_summary = {
        "event": "cb12_route_completed",
        "revision": CB12_GENERIC_HF_REVISION,
        "route_name": str(route_name),
        "case_count": int(len(rows)),
        "artifact_dir": str(artifact_dir),
        "summary": dict(summary),
    }
    print(json.dumps(route_summary, ensure_ascii=False, separators=(",", ":")), flush=True)
    return route_summary


def run_cb12_routes() -> dict[str, Any]:
    prompt_enabled = _cb12_bool(CB12_PROMPT_ROUTE_ENABLED)
    dataset_enabled = _cb12_bool(CB12_DATASET_ROUTE_ENABLED)
    if not prompt_enabled and not dataset_enabled:
        raise ValueError(
            "CB12 has no enabled route. Set CB12_PROMPT_ROUTE_ENABLED=True, "
            "CB12_DATASET_ROUTE_ENABLED=True, or both."
        )

    run_stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    route_summaries: list[dict[str, Any]] = []
    skipped_routes: list[dict[str, Any]] = []
    globals()["CB12_ROUTE_ROWS_BY_ARTIFACT_DIR"] = {}
    globals()["CB12_ROUTE_ROWS_BY_ROUTE_NAME"] = {}

    if prompt_enabled:
        prompt_rows, prompt_report = _cb12_prompt_rows()
        if prompt_rows:
            prompt_artifact_dir = (
                f"{CB12_OUTPUT_ROOT}/"
                f"{_cb12_slug(BENCHMARK_NAME)}_prompt_{_cb12_slug(CB12_PROMPT_ID)}_{run_stamp}"
            )
            route_summaries.append(
                _cb12_run_route(
                    route_name="prompt",
                    rows=prompt_rows,
                    loaded_report=prompt_report,
                    artifact_dir=prompt_artifact_dir,
                )
            )
            if not dataset_enabled:
                globals()["TEST_ROWS"] = list(prompt_rows)
                globals()["EXPECTED_TEST_ROWS"] = int(len(prompt_rows))
        elif dataset_enabled:
            skipped_routes.append(dict(prompt_report))
            print(json.dumps(prompt_report, ensure_ascii=False, separators=(",", ":")), flush=True)
        else:
            raise ValueError(
                "CB12 prompt route is enabled, but no prompt was supplied. "
                "Paste text into CB12_PROMPT_TEXT, set CB12_PROMPT_TEXT_OVERRIDE, "
                "or set CB12_PROMPT_PATH."
            )

    if dataset_enabled:
        dataset_rows, dataset_report = _cb12_dataset_rows()
        globals()["TEST_ROWS"] = list(dataset_rows)
        globals()["EXPECTED_TEST_ROWS"] = int(len(dataset_rows))
        globals()["BENCHMARK_SELECTION_MODE"] = str(dataset_report.get("selection_mode", ""))
        dataset_artifact_dir = (
            f"{CB12_OUTPUT_ROOT}/"
            f"{_cb12_slug(BENCHMARK_NAME)}_export_"
            f"{dataset_report.get('selection_mode', 'dataset')}_"
            f"{len(dataset_rows)}q_{run_stamp}"
        )
        globals()["TRANSCRIPT_ARTIFACT_DIR"] = str(dataset_artifact_dir)
        route_summaries.append(
            _cb12_run_route(
                route_name="dataset",
                rows=dataset_rows,
                loaded_report=dataset_report,
                artifact_dir=dataset_artifact_dir,
            )
        )
    elif route_summaries:
        globals()["TRANSCRIPT_ARTIFACT_DIR"] = str(route_summaries[-1].get("artifact_dir", ""))

    summary = {
        "event": "cb12_routes_summary",
        "revision": CB12_GENERIC_HF_REVISION,
        "prompt_route_enabled": bool(prompt_enabled),
        "dataset_route_enabled": bool(dataset_enabled),
        "route_order": ["prompt", "dataset"],
        "routes_completed": [str(row.get("route_name", "")) for row in route_summaries],
        "routes_skipped": list(skipped_routes),
        "route_summaries": list(route_summaries),
    }
    globals()["CB12_ROUTE_SUMMARIES"] = list(route_summaries)
    globals()["CB12_RUN_SUMMARY"] = dict(summary)
    # Backward-compatible alias: old notebooks expected BENCHMARK_RUN_SUMMARY.
    globals()["BENCHMARK_RUN_SUMMARY"] = dict(route_summaries[-1].get("summary", {})) if route_summaries else dict(summary)
    print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")), flush=True)
    return dict(summary)


CB12_RUN_SUMMARY = run_cb12_routes()

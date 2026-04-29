"""## 11 - Make the Notebook Submission Ready



"""

import json
import os
import time
import re
import csv
from pathlib import Path
from typing import Any, Callable, Iterable, cast

try:
    import polars as pl
except Exception:
    class _FallbackDataFrame:
        def __init__(self, rows: Any = None) -> None:
            self.rows = list(rows or [])

        def write_csv(self, path: str) -> None:
            output_path = Path(path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            fieldnames: list[str] = []
            for row in self.rows:
                if isinstance(row, dict):
                    for key in row.keys():
                        token = str(key)
                        if token not in fieldnames:
                            fieldnames.append(token)
            with output_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                for row in self.rows:
                    writer.writerow(dict(row or {}))

        def item(self) -> Any:
            if not self.rows:
                return None
            first = self.rows[0]
            if isinstance(first, dict):
                values = list(first.values())
                return values[0] if values else None
            return first

        def __iter__(self):
            return iter(self.rows)

        def __repr__(self) -> str:
            return json.dumps(self.rows, ensure_ascii=False, indent=2)

    class _FallbackPolars:
        DataFrame = _FallbackDataFrame

    pl = _FallbackPolars()

PolarsDataFrame = Any

CB11_SUBMISSION_REVISION = "2026-04-13-cb11-v16-competition-submit-only"


# Resolve notebook-injected helpers through globals so this file stays valid
# when opened standalone in the editor.
_normalize_submission_answer = globals().get("normalize_submission_answer")
_run_aen_protocol = globals().get("run_aen_protocol")
_submission_fallback_answer = str(globals().get("SUBMISSION_FALLBACK_ANSWER", "0"))
_reference_bench_root = Path(
    str(
        globals().get(
            "REFERENCE_BENCH_ROOT",
            "kaggle_aimo3/reference/testdata/kaggle_reference_bench",
        )
    )
)


def _resolve_existing_path(*candidates: Any) -> Path:
    normalized: list[Path] = []
    for candidate in candidates:
        text = str(candidate or "").strip()
        if not text:
            continue
        normalized.append(Path(text))
    for candidate in normalized:
        try:
            if candidate.exists():
                return candidate
        except Exception:
            continue
    return Path(normalized[0] if normalized else ".")


_runtimeatboot_dataset_name = str(globals().get("RUNTIME_AT_BOOT_DATASET_NAME", "runtimeatboot") or "runtimeatboot").strip()


def _runtimeatboot_dataset_folder_options() -> list[str]:
    tokens: list[str] = []
    for candidate in [
        str(globals().get("RUNTIME_AT_BOOT_DATASET_FOLDER", "") or "").strip(),
        "runtimeatbootdataset",
        "runtimeatbootdataset_athena_easy10",
    ]:
        token = str(candidate or "").strip()
        if token and token not in tokens:
            tokens.append(token)
    return tokens or ["runtimeatbootdataset", "runtimeatbootdataset_athena_easy10"]


def _select_runtimeatboot_dataset_folder() -> str:
    folder_options = _runtimeatboot_dataset_folder_options()
    dataset_name_options: list[str] = []
    for name in [str(_runtimeatboot_dataset_name), "runtime-at-boot", "runtimeatboot"]:
        token = str(name or "").strip()
        if token and token not in dataset_name_options:
            dataset_name_options.append(token)
    for folder in folder_options:
        candidate_paths = [Path("kaggle_aimo3") / folder]
        for dataset_name in dataset_name_options:
            candidate_paths.append(Path("/kaggle/input") / dataset_name / folder)
            candidate_paths.append(Path("/kaggle/input/datasets/aadityapaudel") / dataset_name / folder)
        for candidate_path in candidate_paths:
            try:
                if candidate_path.exists():
                    return str(folder)
            except Exception:
                continue
    return str(folder_options[0])


_runtimeatboot_dataset_folder = _select_runtimeatboot_dataset_folder()
_runtimeatboot_dataset_root = _resolve_existing_path(
    globals().get("RUNTIME_AT_BOOT_DATASET_ROOT"),
    Path("kaggle_aimo3") / _runtimeatboot_dataset_folder,
    Path("/kaggle/input/datasets/aadityapaudel") / _runtimeatboot_dataset_name,
    Path("/kaggle/input") / _runtimeatboot_dataset_name / _runtimeatboot_dataset_folder,
    Path("/kaggle/input") / _runtimeatboot_dataset_name,
    Path("/kaggle/input/datasets/aadityapaudel") / "runtime-at-boot",
    Path("/kaggle/input") / "runtime-at-boot" / _runtimeatboot_dataset_folder,
    Path("/kaggle/input") / "runtime-at-boot",
    Path("/kaggle/input/datasets/aadityapaudel") / "runtimeatboot",
    Path("/kaggle/input") / "runtimeatboot" / _runtimeatboot_dataset_folder,
    Path("/kaggle/input") / "runtimeatboot",
)
_local_smoke_artifact_dir = Path(
    str(
        globals().get(
            "LOCAL_SMOKE_ARTIFACT_DIR",
            "kaggle_aimo3/AENAIMO260_0_2_3/artifacts",
        )
    )
)
_local_vault_smoke_root = Path(
    str(
        _resolve_existing_path(
            globals().get("LOCAL_VAULT_OF_ECHOES_ROOT"),
            _runtimeatboot_dataset_root / "smoke" / "alppuzzlesfinalized",
            "kaggle_aimo3/localtestdata/alppuzzlesfinalized",
        )
    )
)
_runtimeatboot_easy10_path = Path(
    str(
        _resolve_existing_path(
            globals().get("RUNTIME_AT_BOOT_EASY10_PATH"),
            _runtimeatboot_dataset_root / "smoke" / "runtimeatboot_easy10.json",
        )
    )
)
_runtimeatboot_easy10_kaggle_test_path = Path(
    str(
        _resolve_existing_path(
            globals().get("RUNTIME_AT_BOOT_EASY10_KAGGLE_TEST_PATH"),
            _runtimeatboot_dataset_root / "smoke" / "runtimeatboot_easy10_kaggle_test.csv",
        )
    )
)
_runtimeatboot_test1_csv_path = Path(
    str(
        _resolve_existing_path(
            globals().get("RUNTIME_AT_BOOT_TEST1_PATH"),
            Path("kaggle_aimo3") / "runtimeatbootdataset" / "test" / "runtimeatboot_test1.csv",
            _runtimeatboot_dataset_root / "test" / "runtimeatboot_test1.csv",
            Path("/kaggle/input/datasets/aadityapaudel") / str(_runtimeatboot_dataset_name) / "test" / "runtimeatboot_test1.csv",
            Path("/kaggle/input") / str(_runtimeatboot_dataset_name) / "test" / "runtimeatboot_test1.csv",
        )
    )
)
_runtimeatboot_test1_key_csv_path = Path(
    str(
        _resolve_existing_path(
            globals().get("RUNTIME_AT_BOOT_TEST1_KEY_PATH"),
            Path("kaggle_aimo3") / "runtimeatbootdataset" / "test" / "runtimeatboot_test1_key.csv",
            _runtimeatboot_dataset_root / "test" / "runtimeatboot_test1_key.csv",
            Path("/kaggle/input/datasets/aadityapaudel") / str(_runtimeatboot_dataset_name) / "test" / "runtimeatboot_test1_key.csv",
            Path("/kaggle/input") / str(_runtimeatboot_dataset_name) / "test" / "runtimeatboot_test1_key.csv",
        )
    )
)
_runtimeatboot_kaggle_smoke2_csv_path = Path(
    str(
        _resolve_existing_path(
            globals().get("RUNTIME_AT_BOOT_KAGGLE_SMOKE2_PATH"),
            Path("kaggle_aimo3") / "runtimeatbootdataset" / "test" / "runtimeatboot_kaggle_smoke2.csv",
            _runtimeatboot_dataset_root / "test" / "runtimeatboot_kaggle_smoke2.csv",
            Path("/kaggle/input/datasets/aadityapaudel") / str(_runtimeatboot_dataset_name) / "test" / "runtimeatboot_kaggle_smoke2.csv",
            Path("/kaggle/input") / str(_runtimeatboot_dataset_name) / "test" / "runtimeatboot_kaggle_smoke2.csv",
        )
    )
)
_runtimeatboot_voe_test25_csv_path = Path(
    str(
        _resolve_existing_path(
            globals().get("RUNTIME_AT_BOOT_VOE_TEST25_PATH"),
            Path("kaggle_aimo3") / "runtimeatbootdataset" / "test" / "runtimeatboot_voe_test25.csv",
            _runtimeatboot_dataset_root / "test" / "runtimeatboot_voe_test25.csv",
            Path("/kaggle/input/datasets/aadityapaudel") / str(_runtimeatboot_dataset_name) / "test" / "runtimeatboot_voe_test25.csv",
            Path("/kaggle/input") / str(_runtimeatboot_dataset_name) / "test" / "runtimeatboot_voe_test25.csv",
            globals().get("RUNTIME_AT_BOOT_VOE_TEST25_INTEGER_PATH"),
            Path("kaggle_aimo3") / "runtimeatbootdataset" / "test" / "runtimeatboot_voe_test25_integer.csv",
            _runtimeatboot_dataset_root / "test" / "runtimeatboot_voe_test25_integer.csv",
            Path("/kaggle/input/datasets/aadityapaudel") / str(_runtimeatboot_dataset_name) / "test" / "runtimeatboot_voe_test25_integer.csv",
            Path("/kaggle/input") / str(_runtimeatboot_dataset_name) / "test" / "runtimeatboot_voe_test25_integer.csv",
        )
    )
)
_runtimeatboot_voe_test25_key_csv_path = Path(
    str(
        _resolve_existing_path(
            globals().get("RUNTIME_AT_BOOT_VOE_TEST25_KEY_PATH"),
            Path("kaggle_aimo3") / "runtimeatbootdataset" / "test" / "runtimeatboot_voe_test25_key.csv",
            _runtimeatboot_dataset_root / "test" / "runtimeatboot_voe_test25_key.csv",
            Path("/kaggle/input/datasets/aadityapaudel") / str(_runtimeatboot_dataset_name) / "test" / "runtimeatboot_voe_test25_key.csv",
            Path("/kaggle/input") / str(_runtimeatboot_dataset_name) / "test" / "runtimeatboot_voe_test25_key.csv",
            globals().get("RUNTIME_AT_BOOT_VOE_TEST25_INTEGER_KEY_PATH"),
            Path("kaggle_aimo3") / "runtimeatbootdataset" / "test" / "runtimeatboot_voe_test25_integer_key.csv",
            _runtimeatboot_dataset_root / "test" / "runtimeatboot_voe_test25_integer_key.csv",
            Path("/kaggle/input/datasets/aadityapaudel") / str(_runtimeatboot_dataset_name) / "test" / "runtimeatboot_voe_test25_integer_key.csv",
            Path("/kaggle/input") / str(_runtimeatboot_dataset_name) / "test" / "runtimeatboot_voe_test25_integer_key.csv",
        )
    )
)
_local_vault_smoke_default_limit = max(1, int(globals().get("LOCAL_VAULT_SMOKE_DEFAULT_LIMIT", 10) or 10))
_runtimeatboot_easy10_default_limit = max(1, int(globals().get("RUNTIME_AT_BOOT_EASY10_DEFAULT_LIMIT", 10) or 10))
_is_competition_rerun = bool(str(os.getenv("KAGGLE_IS_COMPETITION_RERUN", "") or "").strip())
_reference_bench_smoke_default_ids = list(
    globals().get("REFERENCE_BENCH_SMOKE_DEFAULT_IDS")
    or (["kaggle_ref_02", "kaggle_ref_05"] if not _is_competition_rerun else ["kaggle_ref_09", "kaggle_ref_05", "kaggle_ref_01"])
)


# Return one required notebook dependency or raise a clear error.
# This keeps the Kaggle entrypoint explicit when the file is run outside the
# full notebook block order.
# Return a required callable dependency or raise a deterministic setup error.
def _require_notebook_callable(name: str, value: Any | None = None) -> Callable[..., Any]:
    candidate = value if value is not None else globals().get(name)
    if callable(candidate):
        return cast(Callable[..., Any], candidate)
    raise NameError(f"{name} is not defined. Run the earlier notebook blocks first.")


def _coerce_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        text = str(value).strip()
        return [text] if text else []
    if isinstance(value, Iterable):
        output: list[str] = []
        for item in value:
            text = str(item).strip()
            if text:
                output.append(text)
        return output
    text = str(value).strip()
    return [text] if text else []


def _normalize_submission_fallback(fallback: Any = None) -> str:
    candidate = str(_submission_fallback_answer if fallback is None else fallback).strip() or "0"
    if re.fullmatch(r"-?\d+", candidate):
        try:
            numeric_value = int(candidate)
            if 0 <= numeric_value <= 99999:
                return str(numeric_value)
        except Exception:
            pass
    return "0"


def _coerce_valid_submission_answer(raw_value: Any, *, fallback: Any = None) -> str:
    fallback_text = _normalize_submission_fallback(fallback)
    text = str(raw_value or "").strip()
    if not text or text.lower() == "none":
        return fallback_text
    if not re.fullmatch(r"-?\d+", text):
        return fallback_text
    try:
        numeric_value = int(text)
    except Exception:
        return fallback_text
    if numeric_value < 0 or numeric_value > 99999:
        return fallback_text
    return str(numeric_value)


def _validate_submission_answer_candidate(raw_value: Any) -> str:
    text = str(raw_value or "").strip()
    if not text or text.lower() == "none":
        return "none"
    if not re.fullmatch(r"-?\d+", text):
        return "none"
    try:
        numeric_value = int(text)
    except Exception:
        return "none"
    if numeric_value < 0 or numeric_value > 99999:
        return "none"
    return str(numeric_value)


def _safe_scalar_text(value: Any, *, fallback: str = "") -> str:
    item_fn = getattr(value, "item", None)
    if callable(item_fn):
        for args in [(), (0,), (0, 0)]:
            try:
                item = item_fn(*args)
            except TypeError:
                continue
            except Exception:
                item = None
            text = str(item or "").strip()
            if text:
                return text

    to_dicts = getattr(value, "to_dicts", None)
    if callable(to_dicts):
        try:
            rows = list(to_dicts() or [])
        except Exception:
            rows = []
        if rows and isinstance(rows[0], dict):
            first_row = dict(rows[0] or {})
            for cell_value in first_row.values():
                text = str(cell_value or "").strip()
                if text:
                    return text

    rows_attr = getattr(value, "rows", None)
    if isinstance(rows_attr, list) and rows_attr:
        first_row = rows_attr[0]
        if isinstance(first_row, dict):
            for cell_value in dict(first_row or {}).values():
                text = str(cell_value or "").strip()
                if text:
                    return text
        else:
            text = str(first_row or "").strip()
            if text:
                return text

    return str(fallback or "").strip()


def _resolve_submission_answer_from_result(result: dict[str, Any]) -> str:
    payload = dict(result or {})
    if not bool(payload.get("verified", False)):
        return "none"

    direct = _validate_submission_answer_candidate(payload.get("submission_answer", "none"))
    if direct != "none":
        return direct

    normalize_submission_answer = _require_notebook_callable(
        "normalize_submission_answer",
        _normalize_submission_answer,
    )
    final_answer_text = str(payload.get("final_answer_text", "") or "")
    normalized = str(normalize_submission_answer(final_answer_text, fallback="none"))
    return _validate_submission_answer_candidate(normalized)


def _runtime_at_boot_summary() -> dict[str, Any]:
    runtime = globals().get("RUNTIME")
    if isinstance(runtime, dict):
        return dict(runtime.get("runtime_at_boot_summary") or {})
    return dict(globals().get("RUNTIME_AT_BOOT_SUMMARY") or {})


def _runtime_at_boot_passed() -> bool:
    return bool(_runtime_at_boot_summary().get("passed", False))


def _blocked_runtime_at_boot_summary(event: str) -> dict[str, Any]:
    boot_summary = _runtime_at_boot_summary()
    return {
        "event": str(event),
        "revision": str(CB11_SUBMISSION_REVISION),
        "status": "blocked_by_runtime_at_boot",
        "runtime_at_boot_summary": dict(boot_summary),
        "message": "Runtime-at-Boot must pass before smoke solving can begin.",
    }


def _extract_braced_macro(text: str, macro_name: str) -> str:
    token = f"\\{str(macro_name).strip()}{{"
    start = str(text).find(token)
    if start < 0:
        return ""
    cursor = start + len(token)
    depth = 1
    builder: list[str] = []
    while cursor < len(text):
        char = text[cursor]
        if char == "{":
            depth += 1
            builder.append(char)
        elif char == "}":
            depth -= 1
            if depth == 0:
                break
            builder.append(char)
        else:
            builder.append(char)
        cursor += 1
    return str("".join(builder)).strip()


def _clean_tex_macro_body(text: str) -> str:
    cleaned = str(text or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = cleaned.split("\n")
    normalized: list[str] = []
    for line in lines:
        stripped = str(line).lstrip()
        if stripped.startswith("%"):
            stripped = stripped[1:].lstrip()
        normalized.append(stripped if stripped or normalized else "")
    return str("\n".join(normalized)).strip()


def _clean_tex_problem_text(text: str) -> str:
    lines = []
    for raw_line in str(text).splitlines():
        if str(raw_line).lstrip().startswith("%"):
            continue
        lines.append(str(raw_line))
    return str("\n".join(lines)).strip()


def _load_local_vault_case(path: Path) -> dict[str, Any]:
    raw_text = path.read_text(encoding="utf-8", errors="ignore")
    problem_block = str(raw_text).split("\\SolutionPage", 1)[0]
    problem_text = _clean_tex_problem_text(problem_block)
    expected_answer = _clean_tex_macro_body(_extract_braced_macro(raw_text, "FinalAnswer"))
    vault_directive = _clean_tex_macro_body(_extract_braced_macro(problem_block, "VaultDirective"))
    return {
        "id": str(path.stem),
        "source_file": str(path.name),
        "problem_text": str(problem_text),
        "expected_answer": str(expected_answer),
        "title": str(vault_directive or path.stem),
        "problem_abspath": str(path.resolve()),
    }


def load_local_vault_smoke_manifest(root: Any = None, *, limit: int | None = None) -> list[dict[str, Any]]:
    vault_root = Path(root) if root is not None else Path(_local_vault_smoke_root)
    if not vault_root.exists():
        raise FileNotFoundError(f"Local Vault of Echoes root not found: {vault_root}")
    tex_files = sorted(
        (path for path in vault_root.glob("p*.tex") if re.fullmatch(r"p\d+\.tex", path.name, flags=re.IGNORECASE)),
        key=lambda item: str(item.name).lower(),
    )
    if limit is not None:
        tex_files = tex_files[: max(0, int(limit))]
    return [_load_local_vault_case(path) for path in tex_files]


def load_runtimeatboot_easy10_manifest(path: Any = None, *, limit: int | None = None) -> list[dict[str, Any]]:
    manifest_path = Path(path) if path is not None else Path(_runtimeatboot_easy10_path)
    if not manifest_path.exists():
        raise FileNotFoundError(f"Runtime-at-Boot easy10 manifest not found: {manifest_path}")
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows = [dict(item) for item in list(payload or []) if isinstance(item, dict)]
    if limit is not None:
        rows = rows[: max(0, int(limit))]
    return rows


def list_runtimeatboot_easy10_cases(path: Any = None, *, limit: int | None = None) -> PolarsDataFrame:
    rows = load_runtimeatboot_easy10_manifest(path=path, limit=limit)
    preview_rows = [
        {
            "id": str(row.get("id", "")),
            "topic": str(row.get("topic", "")),
            "difficulty": str(row.get("difficulty", "")),
            "answer": str(row.get("answer", "")),
        }
        for row in rows
    ]
    return pl.DataFrame(preview_rows)


def list_local_vault_smoke_cases(root: Any = None, *, limit: int | None = None) -> PolarsDataFrame:
    rows = load_local_vault_smoke_manifest(root=root, limit=limit)
    preview_rows = [
        {
            "id": str(row.get("id", "")),
            "source_file": str(row.get("source_file", "")),
            "expected_answer": str(row.get("expected_answer", "")),
            "title": str(row.get("title", "")),
        }
        for row in rows
    ]
    return pl.DataFrame(preview_rows)


def _write_transcript_artifact(artifact_dir: Path, *, problem_id: str, transcript_text: str) -> str:
    transcript_dir = artifact_dir / "transcripts"
    transcript_dir.mkdir(parents=True, exist_ok=True)
    transcript_path = transcript_dir / f"{str(problem_id).strip() or 'problem'}.txt"
    transcript_path.write_text(str(transcript_text or ""), encoding="utf-8")
    return str(transcript_path.resolve())


def _write_result_payload_artifact(artifact_dir: Path, *, problem_id: str, result_payload: dict[str, Any]) -> str:
    payload_dir = artifact_dir / "result_payloads"
    payload_dir.mkdir(parents=True, exist_ok=True)
    payload_path = payload_dir / f"{str(problem_id).strip() or 'problem'}.json"
    payload_path.write_text(
        json.dumps(dict(result_payload or {}), ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return str(payload_path.resolve())


def _turn_token_usage_rows(result: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for raw_row in list(result.get("transcript") or []):
        row = dict(raw_row or {})
        rows.append(
            {
                "turn": int(row.get("turn", 0) or 0),
                "speaker": str(row.get("speaker", "")),
                "phase": str(row.get("phase", "")),
                "runtime_label": str(row.get("runtime_label", "")),
                "wall_seconds": float(row.get("wall_seconds", 0.0) or 0.0),
                "prompt_tokens": int(row.get("prompt_tokens_used", 0) or 0),
                "completion_tokens": int(row.get("generated_tokens", 0) or 0),
                "total_tokens": int(row.get("total_tokens_used", 0) or 0),
            }
        )
    return rows


def _turn_metrics_json(rows: list[dict[str, Any]]) -> str:
    return json.dumps(list(rows or []), ensure_ascii=False, separators=(",", ":"))


def _turn_metrics_compact(rows: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for row in list(rows or []):
        parts.append(
            "t{turn}:{speaker}:{phase}:wall={wall_seconds}:prompt={prompt_tokens}:completion={completion_tokens}:total={total_tokens}".format(
                turn=int(row.get("turn", 0) or 0),
                speaker=str(row.get("speaker", "") or ""),
                phase=str(row.get("phase", "") or ""),
                wall_seconds=round(float(row.get("wall_seconds", 0.0) or 0.0), 4),
                prompt_tokens=int(row.get("prompt_tokens", 0) or 0),
                completion_tokens=int(row.get("completion_tokens", 0) or 0),
                total_tokens=int(row.get("total_tokens", 0) or 0),
            )
        )
    return " | ".join(parts)


def _write_summary_json(path: Path, payload: dict[str, Any]) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload or {}), ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    return str(path.resolve())


def _resolve_artifact_dir(artifact_dir: Any = None) -> Path:
    resolved = Path(artifact_dir) if artifact_dir is not None else Path(_local_smoke_artifact_dir)
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def _write_artifact_bundle_manifest(artifact_dir: Path) -> str:
    files = [
        str(path.relative_to(artifact_dir)).replace("\\", "/")
        for path in sorted(artifact_dir.rglob("*"))
        if path.is_file()
    ]
    payload = {
        "event": "artifact_bundle_manifest",
        "artifact_dir": str(artifact_dir.resolve()),
        "file_count": int(len(files)),
        "files": list(files),
    }
    return _write_summary_json(artifact_dir / "artifact_bundle_manifest.json", payload)


# Build one Kaggle-style submission row from one protocol result.
# This keeps the submission block independent from the local manual-run helper layout.
# Build one normalized Kaggle submission row from protocol output.
def build_submission_row(question_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    submission_answer = _resolve_submission_answer_from_result(dict(result or {}))
    submission_answer = _coerce_valid_submission_answer(submission_answer, fallback=_submission_fallback_answer)
    return {"id": str(question_id), "answer": str(submission_answer)}


# Run one Kaggle prediction row through the live protocol and return id/answer.
# This is the notebook's submission entrypoint.
# Kaggle entrypoint: run protocol for one row and return DataFrame[id, answer].
def predict(id_: PolarsDataFrame, problem: PolarsDataFrame) -> PolarsDataFrame:
    question_id = _safe_scalar_text(id_, fallback="unknown")
    problem_text = _safe_scalar_text(problem, fallback="")
    print({"event": "cb11_predict_called", "question_id": question_id}, flush=True)
    try:
        run_aen_protocol = _require_notebook_callable(
            "run_aen_protocol",
            _run_aen_protocol,
        )
        if not str(problem_text).strip():
            raise ValueError("problem text is empty")
        result = run_aen_protocol(problem_text)
        submission_row = build_submission_row(question_id, result)
    except Exception as exc:
        print(
            {
                "event": "cb11_predict_exception",
                "question_id": str(question_id),
                "exception_type": str(type(exc).__name__),
                "exception_message": str(exc)[:1000],
            },
            flush=True,
        )
        submission_row = {
            "id": str(question_id),
            "answer": _coerce_valid_submission_answer("none", fallback=_submission_fallback_answer),
        }
    return pl.DataFrame([submission_row])


def _coerce_tabular_rows(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, list):
        return [dict(row or {}) for row in value if isinstance(row, dict)]
    if isinstance(value, tuple):
        return [dict(row or {}) for row in list(value) if isinstance(row, dict)]
    to_dicts = getattr(value, "to_dicts", None)
    if callable(to_dicts):
        rows = to_dicts()
        return [dict(row or {}) for row in list(rows or []) if isinstance(row, dict)]
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        try:
            rows = to_dict(orient="records")
            return [dict(row or {}) for row in list(rows or []) if isinstance(row, dict)]
        except TypeError:
            pass
    rows_attr = getattr(value, "rows", None)
    if isinstance(rows_attr, list):
        return [dict(row or {}) for row in rows_attr if isinstance(row, dict)]
    raise TypeError("Expected a path, list[dict], polars DataFrame, or pandas DataFrame-like object.")


def _extract_tabular_column_names(value: Any) -> list[str]:
    columns = getattr(value, "columns", None)
    if columns is not None:
        try:
            output = [str(item) for item in list(columns)]
            if output:
                return output
        except Exception:
            pass
    schema = getattr(value, "schema", None)
    if isinstance(schema, dict):
        output = [str(item) for item in list(schema.keys())]
        if output:
            return output
    rows_attr = getattr(value, "rows", None)
    if isinstance(rows_attr, list) and rows_attr and isinstance(rows_attr[0], dict):
        return [str(item) for item in list(rows_attr[0].keys())]
    return []


def _discover_attached_test_dataframe_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for name, value in list(globals().items()):
        if not str(name).strip():
            continue
        if str(name).startswith("_"):
            continue
        if callable(value):
            continue
        if isinstance(value, (str, bytes, bytearray, int, float, bool, Path, type(None))):
            continue
        column_names = _extract_tabular_column_names(value)
        normalized_columns = {str(item).strip().lower() for item in column_names}
        if {"id", "problem"}.issubset(normalized_columns):
            row_count = None
            shape = getattr(value, "shape", None)
            if isinstance(shape, tuple) and shape:
                try:
                    row_count = int(shape[0])
                except Exception:
                    row_count = None
            candidates.append(
                {
                    "name": str(name),
                    "type": str(type(value).__name__),
                    "columns": list(column_names),
                    "row_count": row_count,
                }
            )
    return candidates


def list_attached_test_dataframe_candidates() -> PolarsDataFrame:
    return pl.DataFrame(_discover_attached_test_dataframe_candidates())


def _load_rows_from_tabular_path(path: Path) -> list[dict[str, Any]]:
    lowered = str(path.suffix or "").lower()
    if lowered == ".csv":
        read_csv = getattr(pl, "read_csv", None)
        if callable(read_csv):
            return _coerce_tabular_rows(read_csv(str(path)))
        with path.open("r", encoding="utf-8", newline="") as handle:
            return [dict(row or {}) for row in csv.DictReader(handle)]
    if lowered == ".parquet":
        read_parquet = getattr(pl, "read_parquet", None)
        if callable(read_parquet):
            return _coerce_tabular_rows(read_parquet(str(path)))
        raise RuntimeError("Parquet input requires polars.read_parquet to be available in this runtime.")
    raise ValueError(f"Unsupported tabular input path: {path}")


def _normalize_attached_test_rows(rows: list[dict[str, Any]], *, limit: int | None = None) -> list[dict[str, Any]]:
    selected = list(rows or [])
    if limit is not None:
        selected = selected[: max(0, int(limit))]
    normalized: list[dict[str, Any]] = []
    for index, raw_row in enumerate(selected, start=1):
        row = dict(raw_row or {})
        if "id" not in row or "problem" not in row:
            raise KeyError(f"Attached test row {index} must contain 'id' and 'problem' columns.")
        row_id = str(row.get("id", "") or "").strip()
        problem_text = str(row.get("problem", "") or "").strip()
        if not row_id:
            raise ValueError(f"Attached test row {index} has an empty id.")
        if not problem_text:
            raise ValueError(f"Attached test row {index} has an empty problem.")
        normalized_row = dict(row)
        normalized_row["id"] = row_id
        normalized_row["problem"] = problem_text
        normalized.append(normalized_row)
    return normalized


def _attached_test_dataset_path_candidates() -> list[Path]:
    candidates: list[Path] = []
    for raw_candidate in [
        globals().get("ATTACHED_TEST_DATASET_PATH"),
        globals().get("ATTACHED_TEST_PATH"),
        globals().get("TEST_DATASET_PATH"),
        globals().get("TEST_CSV_PATH"),
        globals().get("TEST_PARQUET_PATH"),
    ]:
        text = str(raw_candidate or "").strip()
        if text:
            candidates.append(Path(text))

    kaggle_input_root = Path("/kaggle/input")
    if kaggle_input_root.exists():
        try:
            competition_root = kaggle_input_root / "competitions"
            if competition_root.exists():
                for mounted_root in sorted(competition_root.iterdir(), key=lambda item: item.name):
                    if not mounted_root.is_dir():
                        continue
                    for filename in ["test.csv", "test.parquet"]:
                        candidate = mounted_root / filename
                        if candidate not in candidates:
                            candidates.append(candidate)
        except Exception:
            pass
    return candidates


def _discover_attached_test_path_candidates() -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _append_candidate(path: Path, source: str) -> None:
        key = str(path)
        if key in seen:
            return
        seen.add(key)
        exists = False
        try:
            exists = bool(path.exists())
        except Exception:
            exists = False
        candidates.append(
            {
                "path": str(path),
                "exists": bool(exists),
                "source": str(source),
            }
        )

    for candidate in _attached_test_dataset_path_candidates():
        _append_candidate(candidate, "named_candidate")

    return candidates


def list_attached_test_path_candidates() -> PolarsDataFrame:
    return pl.DataFrame(_discover_attached_test_path_candidates())


def _load_optional_answer_key_map(source_label: str) -> dict[str, dict[str, Any]]:
    candidate_paths: list[Path] = []
    source_path = Path(str(source_label or "")).expanduser()
    if str(source_label or "").strip() and source_path.suffix.lower() == ".csv":
        stem = str(source_path.stem)
        if stem.endswith("_test1"):
            candidate_paths.append(source_path.with_name(f"{stem}_key.csv"))
        candidate_paths.append(source_path.with_name(f"{stem}_key.csv"))
    candidate_paths.append(Path(_runtimeatboot_test1_key_csv_path))

    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for candidate in candidate_paths:
        key = str(candidate)
        if key in seen:
            continue
        seen.add(key)
        try:
            if candidate.exists():
                rows = _load_rows_from_tabular_path(candidate)
                if rows:
                    break
        except Exception:
            continue

    mapping: dict[str, dict[str, Any]] = {}
    for row in rows:
        row_dict = dict(row or {})
        row_id = str(row_dict.get("id", "") or "").strip()
        if row_id:
            mapping[row_id] = row_dict
    return mapping


def _resolve_attached_test_source(
    test_dataset: Any = None,
    *,
    limit: int | None = None,
) -> tuple[list[dict[str, Any]], str]:
    if test_dataset is not None:
        if isinstance(test_dataset, (str, Path)):
            path = Path(str(test_dataset)).expanduser()
            rows = _load_rows_from_tabular_path(path)
            return _normalize_attached_test_rows(rows, limit=limit), str(path.resolve())
        rows = _coerce_tabular_rows(test_dataset)
        return _normalize_attached_test_rows(rows, limit=limit), "explicit_dataframe_argument"

    for global_name in [
        "ATTACHED_TEST_DF",
        "TEST_DF",
        "test_df",
        "TEST_DATASET_DF",
        "test_dataset_df",
        "TEST_DATASET",
        "test_dataset",
        "TEST",
        "test",
    ]:
        if global_name not in globals():
            continue
        candidate = globals().get(global_name)
        try:
            rows = _coerce_tabular_rows(candidate)
            normalized = _normalize_attached_test_rows(rows, limit=limit)
            if normalized:
                return normalized, f"globals()['{global_name}']"
        except Exception:
            continue

    for candidate_info in _discover_attached_test_dataframe_candidates():
        global_name = str(candidate_info.get("name", "")).strip()
        if not global_name:
            continue
        candidate = globals().get(global_name)
        try:
            rows = _coerce_tabular_rows(candidate)
            normalized = _normalize_attached_test_rows(rows, limit=limit)
            if normalized:
                return normalized, f"globals()['{global_name}']"
        except Exception:
            continue

    for candidate_path in _attached_test_dataset_path_candidates():
        try:
            if candidate_path.exists():
                rows = _load_rows_from_tabular_path(candidate_path)
                normalized = _normalize_attached_test_rows(rows, limit=limit)
                if normalized:
                    return normalized, str(candidate_path.resolve())
        except Exception:
            continue

    raise FileNotFoundError(
        "Unable to resolve an attached test dataset. Pass a DataFrame/path explicitly, set TEST_DF, or inspect list_attached_test_dataframe_candidates()."
    )


def list_attached_test_cases(test_dataset: Any = None, *, limit: int | None = 5) -> PolarsDataFrame:
    rows, source_label = _resolve_attached_test_source(test_dataset, limit=limit)
    preview_rows = [
        {
            "id": str(row.get("id", "")),
            "problem_chars": int(len(str(row.get("problem", "") or ""))),
            "source": str(source_label),
        }
        for row in rows
    ]
    return pl.DataFrame(preview_rows)


def kaggle_submission_contract_snapshot() -> dict[str, Any]:
    return {
        "event": "cb11_kaggle_submission_contract",
        "revision": str(CB11_SUBMISSION_REVISION),
        "official_entrypoint": "predict(id_, problem)",
        "input_columns": ["id", "problem"],
        "return_columns": ["id", "answer"],
        "official_submission_shape": "competition rerun uses evaluation API -> predict(id_, problem) -> submission.parquet with columns id,answer",
        "official_submission_is_parquet": True,
        "non_rerun_default_mode": "run_local_gateway",
        "non_rerun_builds_submission_artifact_by_default": False,
        "analysis_artifacts": [
            "attached_test_submission.csv",
            "attached_test_full_log.csv",
            "transcripts/*.txt",
            "result_payloads/*.json",
            "attached_test_summary.json",
            "artifact_bundle_manifest.json",
        ],
    }


def _competition_test_path_candidates() -> list[Path]:
    candidates: list[Path] = []
    for raw_candidate in [
        globals().get("KAGGLE_COMPETITION_TEST_PATH"),
        Path("/kaggle/input/ai-mathematical-olympiad-progress-prize-3/test.csv"),
        Path("/kaggle/input/ai-mathematical-olympiad-progress-prize-3/test.parquet"),
    ]:
        text = str(raw_candidate or "").strip()
        if text:
            candidates.append(Path(text))

    competition_root = Path("/kaggle/input/competitions")
    try:
        if competition_root.exists():
            for mounted_root in sorted(competition_root.iterdir(), key=lambda item: item.name):
                if not mounted_root.is_dir():
                    continue
                for filename in ["test.csv", "test.parquet"]:
                    candidate = mounted_root / filename
                    if candidate not in candidates:
                        candidates.append(candidate)
    except Exception:
        pass
    return candidates


def _resolve_competition_test_path() -> Path:
    candidates = _competition_test_path_candidates()
    for candidate in candidates:
        try:
            if candidate.exists():
                return candidate
        except Exception:
            continue
    return Path(candidates[0] if candidates else "/kaggle/input/ai-mathematical-olympiad-progress-prize-3/test.csv")


def print_kaggle_submission_contract() -> None:
    snapshot = kaggle_submission_contract_snapshot()
    print(snapshot)
    print("Kaggle Submission Contract")
    print("1. Kaggle calls predict(id_, problem).")
    print("2. Competition reruns should reach the evaluation API path first and call inference_server.serve().")
    print("3. Non-rerun debugging defaults to run_local_gateway rather than auto-building submission.parquet.")
    print("4. predict() must always return one valid id/answer row, even after runtime failures.")
    print("5. Transcripts and result payloads are analysis artifacts we write for analysis.")


def run_attached_test_dataset_export(
    test_dataset: Any = None,
    *,
    limit: int | None = None,
    artifact_dir: Any = None,
    submission_csv_path: Any = None,
    results_csv_path: Any = None,
) -> dict[str, Any]:
    if not _runtime_at_boot_passed():
        summary = _blocked_runtime_at_boot_summary("cb11_attached_test_dataset_summary")
        globals()["LAST_ATTACHED_TEST_DATASET_SUMMARY"] = dict(summary)
        print(summary)
        return dict(summary)

    run_aen_protocol = _require_notebook_callable(
        "run_aen_protocol",
        _run_aen_protocol,
    )
    cases, source_label = _resolve_attached_test_source(test_dataset, limit=limit)
    answer_key_map = _load_optional_answer_key_map(source_label)
    boot_summary = _runtime_at_boot_summary()
    boot_run_id = str(boot_summary.get("run_id", time.strftime("attached-test-%Y%m%d-%H%M%S")) or time.strftime("attached-test-%Y%m%d-%H%M%S"))
    artifact_dir = _resolve_artifact_dir(
        artifact_dir if artifact_dir is not None else (Path(_local_smoke_artifact_dir) / f"attached-test-{boot_run_id}")
    )
    artifact_dir.mkdir(parents=True, exist_ok=True)

    submission_path = Path(submission_csv_path) if submission_csv_path is not None else artifact_dir / "attached_test_submission.csv"
    results_path = Path(results_csv_path) if results_csv_path is not None else artifact_dir / "attached_test_full_log.csv"
    submission_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.parent.mkdir(parents=True, exist_ok=True)

    _write_summary_json(artifact_dir / "runtime_at_boot_summary.json", boot_summary)
    boot_csv_path = Path(str(boot_summary.get("boot_log_csv_path", "") or "")).expanduser()
    if str(boot_csv_path):
        try:
            if boot_csv_path.exists():
                (artifact_dir / "runtime_boot_log.csv").write_text(
                    boot_csv_path.read_text(encoding="utf-8", errors="ignore"),
                    encoding="utf-8",
                )
        except Exception:
            pass

    detailed_rows: list[dict[str, Any]] = []
    submission_rows: list[dict[str, Any]] = []
    started_at = time.perf_counter()
    total_cases = len(cases)

    for index, case in enumerate(cases, start=1):
        case_id = str(case.get("id", "")).strip()
        problem_text = str(case.get("problem", "")).strip()
        print(f"cb11_attached_test_progress = [{index}/{total_cases}] {case_id}")
        case_started_at = time.perf_counter()
        result = dict(run_aen_protocol(problem_text) or {})
        case_wall_seconds = round(time.perf_counter() - case_started_at, 4)
        print(
            "cb11_case_result = "
            + " | ".join(
                [
                    f"id={case_id}",
                    f"status={str(result.get('status', 'unknown') or 'unknown')}",
                    f"verified={bool(result.get('verified', False))}",
                    f"turns={int(result.get('turn_index', 0) or 0)}",
                    f"loops={int(result.get('loop_index', 0) or 0)}",
                    f"answer={str(result.get('submission_answer', '') or '')}",
                ]
            ),
            flush=True,
        )
        if str(result.get("status", "")) == "failed":
            failure_payload = dict(result.get("failure") or {})
            print(
                "cb11_case_failure = "
                + " | ".join(
                    [
                        f"id={case_id}",
                        f"speaker={str(failure_payload.get('speaker', 'unknown') or 'unknown')}",
                        f"phase={str(failure_payload.get('phase', 'unknown') or 'unknown')}",
                        f"turn={int(failure_payload.get('turn', 0) or 0)}",
                        f"error_type={str(failure_payload.get('error_type', 'unknown') or 'unknown')}",
                        f"error_message={str(failure_payload.get('error_message', '') or '')[:400]}",
                    ]
                ),
                flush=True,
            )
        submission_row = dict(build_submission_row(case_id, result))
        submission_rows.append(dict(submission_row))
        timing_summary = dict(result.get("timing_summary") or {})
        token_proof = dict(result.get("token_proof") or {})
        turn_timing_log = list(result.get("turn_timing_log") or [])
        turn_token_usage_rows = _turn_token_usage_rows(result)
        transcript_path = _write_transcript_artifact(
            artifact_dir,
            problem_id=str(case_id),
            transcript_text=str(result.get("transcript_text", "") or ""),
        )
        result_payload_path = _write_result_payload_artifact(
            artifact_dir,
            problem_id=str(case_id),
            result_payload=dict(result),
        )
        detailed_rows.append(
            {
                "question_id": case_id,
                "question": str(problem_text),
                "model_answers_transcript": str(result.get("transcript_text", "") or ""),
                "final_answer": str(result.get("final_answer_text", "") or ""),
                "model_submitted_answer": str(submission_row.get("answer", "")),
                "time_taken_seconds": float(case_wall_seconds),
                "expected_answer": str(dict(answer_key_map.get(case_id) or {}).get("answer", "")),
                "reference_worked_solution": str(dict(answer_key_map.get(case_id) or {}).get("worked_solution", "")),
                "question_run_id": str(result.get("question_run_id", "")),
                "verified": bool(result.get("verified", False)),
                "status": str(result.get("status", "unknown")),
                "turns": int(result.get("turn_index", 0) or 0),
                "loops": int(result.get("loop_index", 0) or 0),
                "boot_passed": bool(boot_summary.get("passed", False)),
                "sum_turn_wall_seconds": float(timing_summary.get("sum_turn_wall_seconds", 0.0) or 0.0),
                "total_prompt_tokens": int(token_proof.get("total_prompt_tokens", 0) or 0),
                "total_completion_tokens": int(token_proof.get("total_completion_tokens", 0) or 0),
                "total_tokens": int(token_proof.get("total_tokens", 0) or 0),
                "turn_timing_log_json": _turn_metrics_json(turn_timing_log),
                "turn_token_usage_json": _turn_metrics_json(turn_token_usage_rows),
                "turn_usage_compact": _turn_metrics_compact(turn_token_usage_rows),
                "transcript_path": str(transcript_path),
                "result_payload_path": str(result_payload_path),
                "source_label": str(source_label),
                "run_id": str(boot_run_id),
            }
        )

    submission_df = pl.DataFrame(submission_rows)
    results_df = pl.DataFrame(detailed_rows)
    submission_df.write_csv(str(submission_path))
    results_df.write_csv(str(results_path))

    summary = {
        "event": "cb11_attached_test_dataset_summary",
        "revision": str(CB11_SUBMISSION_REVISION),
        "cases": int(total_cases),
        "source_label": str(source_label),
        "submission_csv_path": str(submission_path.resolve()),
        "results_csv_path": str(results_path.resolve()),
        "artifact_dir": str(artifact_dir.resolve()),
        "runtime_at_boot_passed": bool(boot_summary.get("passed", False)),
        "total_wall_seconds": round(float(time.perf_counter() - started_at), 4),
    }
    summary["summary_json_path"] = str(_write_summary_json(artifact_dir / "attached_test_summary.json", summary))
    summary["artifact_bundle_manifest_path"] = str(_write_artifact_bundle_manifest(artifact_dir))
    globals()["LAST_ATTACHED_TEST_DATASET_RESULTS"] = list(detailed_rows)
    globals()["LAST_ATTACHED_TEST_DATASET_SUBMISSION_ROWS"] = list(submission_rows)
    globals()["LAST_ATTACHED_TEST_DATASET_RESULTS_DF"] = results_df
    globals()["LAST_ATTACHED_TEST_DATASET_SUBMISSION_DF"] = submission_df
    globals()["LAST_ATTACHED_TEST_DATASET_SUMMARY"] = dict(summary)
    print(summary)
    if detailed_rows:
        print(results_df)
    return dict(summary)


def load_reference_bench_manifest(root: Any = None) -> list[dict[str, Any]]:
    bench_root = Path(root) if root is not None else Path(_reference_bench_root)
    manifest_path = bench_root / "manifest.jsonl"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Reference bench manifest not found: {manifest_path}")
    rows: list[dict[str, Any]] = []
    for raw_line in manifest_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        payload = dict(json.loads(line))
        payload["problem_abspath"] = str((bench_root / str(payload.get("problem_path", ""))).resolve())
        rows.append(payload)
    return rows


def list_reference_bench_cases(root: Any = None) -> PolarsDataFrame:
    rows = load_reference_bench_manifest(root=root)
    preview_rows = [
        {
            "id": str(row.get("id", "")),
            "title": str(row.get("title", "")),
            "answer": str(row.get("answer", "")),
            "validity_status": str(row.get("validity_status", "")),
        }
        for row in rows
    ]
    return pl.DataFrame(preview_rows)


def _select_reference_bench_cases(
    case_ids: Any = None,
    *,
    limit: int | None = None,
    root: Any = None,
) -> list[dict[str, Any]]:
    manifest_rows = load_reference_bench_manifest(root=root)
    by_id = {str(row.get("id", "")): dict(row) for row in manifest_rows}
    selected_ids = (
        _coerce_string_list(case_ids)
        if case_ids is not None
        else _coerce_string_list(_reference_bench_smoke_default_ids)
    )
    if not selected_ids:
        selected_ids = [str(row.get("id", "")) for row in manifest_rows]
    if limit is not None:
        selected_ids = selected_ids[: max(0, int(limit))]
    output: list[dict[str, Any]] = []
    for case_id in selected_ids:
        if case_id not in by_id:
            raise KeyError(f"Reference bench id not found in manifest: {case_id}")
        output.append(dict(by_id[case_id]))
    return output


def run_reference_bench_smoke(
    case_ids: Any = None,
    *,
    limit: int | None = None,
    root: Any = None,
    submission_csv_path: Any = None,
    results_csv_path: Any = None,
) -> dict[str, Any]:
    if not _runtime_at_boot_passed():
        summary = _blocked_runtime_at_boot_summary("cb11_reference_smoke_summary")
        globals()["LAST_REFERENCE_SMOKE_SUMMARY"] = dict(summary)
        print(summary)
        return dict(summary)
    run_aen_protocol = _require_notebook_callable(
        "run_aen_protocol",
        _run_aen_protocol,
    )
    cases = _select_reference_bench_cases(case_ids=case_ids, limit=limit, root=root)
    artifact_dir = Path(_local_smoke_artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    submission_path = Path(submission_csv_path) if submission_csv_path is not None else artifact_dir / "reference_smoke_submission.csv"
    results_path = Path(results_csv_path) if results_csv_path is not None else artifact_dir / "reference_smoke_results.csv"
    submission_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.parent.mkdir(parents=True, exist_ok=True)

    detailed_rows: list[dict[str, Any]] = []
    submission_rows: list[dict[str, Any]] = []
    started_at = time.perf_counter()
    total_cases = len(cases)

    for index, case in enumerate(cases, start=1):
        case_id = str(case.get("id", "")).strip()
        title = str(case.get("title", "")).strip()
        expected_answer = str(case.get("answer", "")).strip()
        problem_path = Path(str(case.get("problem_abspath", "")))
        if not problem_path.exists():
            raise FileNotFoundError(f"Reference bench problem file not found: {problem_path}")
        problem_text = problem_path.read_text(encoding="utf-8", errors="ignore").strip()
        print(f"cb11_smoke_progress = [{index}/{total_cases}] {case_id} :: {title}")
        case_started_at = time.perf_counter()
        result = dict(run_aen_protocol(problem_text) or {})
        case_wall_seconds = round(time.perf_counter() - case_started_at, 4)
        submission_row = dict(build_submission_row(case_id, result))
        submission_rows.append(dict(submission_row))
        timing_summary = dict(result.get("timing_summary") or {})
        token_proof = dict(result.get("token_proof") or {})
        turn_timing_log = list(result.get("turn_timing_log") or [])
        turn_token_usage_rows = _turn_token_usage_rows(result)
        predicted_answer = str(submission_row.get("answer", ""))
        is_correct = predicted_answer == expected_answer
        detailed_rows.append(
            {
                "id": case_id,
                "title": title,
                "expected_answer": expected_answer,
                "predicted_answer": predicted_answer,
                "correct": bool(is_correct),
                "status": str(result.get("status", "unknown")),
                "verified": bool(result.get("verified", False)),
                "turns": int(result.get("turn_index", 0) or 0),
                "loops": int(result.get("loop_index", 0) or 0),
                "wall_seconds": float(case_wall_seconds),
                "sum_turn_wall_seconds": float(timing_summary.get("sum_turn_wall_seconds", 0.0) or 0.0),
                "total_prompt_tokens": int(token_proof.get("total_prompt_tokens", 0) or 0),
                "total_completion_tokens": int(token_proof.get("total_completion_tokens", 0) or 0),
                "total_tokens": int(token_proof.get("total_tokens", 0) or 0),
                "turn_timing_log_json": _turn_metrics_json(turn_timing_log),
                "turn_token_usage_json": _turn_metrics_json(turn_token_usage_rows),
                "turn_usage_compact": _turn_metrics_compact(turn_token_usage_rows),
            }
        )

    submission_df = pl.DataFrame(submission_rows)
    results_df = pl.DataFrame(detailed_rows)
    submission_df.write_csv(str(submission_path))
    results_df.write_csv(str(results_path))

    correct_count = sum(1 for row in detailed_rows if bool(row.get("correct", False)))
    total_wall_seconds = round(time.perf_counter() - started_at, 4)
    summary = {
        "event": "cb11_reference_smoke_summary",
        "revision": str(CB11_SUBMISSION_REVISION),
        "cases": int(total_cases),
        "correct": int(correct_count),
        "accuracy": round((float(correct_count) / float(total_cases)) if total_cases else 0.0, 4),
        "submission_csv_path": str(submission_path.resolve()),
        "results_csv_path": str(results_path.resolve()),
        "total_wall_seconds": float(total_wall_seconds),
    }
    globals()["LAST_REFERENCE_SMOKE_RESULTS"] = list(detailed_rows)
    globals()["LAST_REFERENCE_SMOKE_SUBMISSION_ROWS"] = list(submission_rows)
    globals()["LAST_REFERENCE_SMOKE_RESULTS_DF"] = results_df
    globals()["LAST_REFERENCE_SMOKE_SUBMISSION_DF"] = submission_df
    globals()["LAST_REFERENCE_SMOKE_SUMMARY"] = dict(summary)
    print(summary)
    if detailed_rows:
        print(results_df)
    return dict(summary)


def run_local_vault_smoke(
    *,
    limit: int | None = None,
    root: Any = None,
    artifact_dir: Any = None,
    submission_csv_path: Any = None,
    results_csv_path: Any = None,
) -> dict[str, Any]:
    if not _runtime_at_boot_passed():
        summary = _blocked_runtime_at_boot_summary("cb11_local_vault_smoke_summary")
        globals()["LAST_LOCAL_VAULT_SMOKE_SUMMARY"] = dict(summary)
        print(summary)
        return dict(summary)

    run_aen_protocol = _require_notebook_callable(
        "run_aen_protocol",
        _run_aen_protocol,
    )
    cases = load_local_vault_smoke_manifest(
        root=root,
        limit=_local_vault_smoke_default_limit if limit is None else int(limit),
    )
    artifact_dir = _resolve_artifact_dir(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    submission_path = Path(submission_csv_path) if submission_csv_path is not None else artifact_dir / "local_smoke_submission.csv"
    results_path = Path(results_csv_path) if results_csv_path is not None else artifact_dir / "local_smoke_results.csv"
    submission_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.parent.mkdir(parents=True, exist_ok=True)

    detailed_rows: list[dict[str, Any]] = []
    submission_rows: list[dict[str, Any]] = []
    started_at = time.perf_counter()
    total_cases = len(cases)
    boot_summary = _runtime_at_boot_summary()
    run_id = str(boot_summary.get("run_id", time.strftime("local-smoke-%Y%m%d-%H%M%S")))

    for index, case in enumerate(cases, start=1):
        case_id = str(case.get("id", "")).strip()
        title = str(case.get("title", "")).strip()
        expected_answer = str(case.get("expected_answer", "")).strip()
        problem_text = str(case.get("problem_text", "")).strip()
        print(f"cb11_local_smoke_progress = [{index}/{total_cases}] {case_id} :: {title}")
        case_started_at = time.perf_counter()
        result = dict(run_aen_protocol(problem_text) or {})
        case_wall_seconds = round(time.perf_counter() - case_started_at, 4)
        predicted_answer = str(_resolve_submission_answer_from_result(result))
        submission_row = dict(build_submission_row(case_id, result))
        submission_rows.append(dict(submission_row))
        timing_summary = dict(result.get("timing_summary") or {})
        transcript_path = _write_transcript_artifact(
            artifact_dir,
            problem_id=str(case_id),
            transcript_text=str(result.get("transcript_text", "") or ""),
        )
        result_payload_path = _write_result_payload_artifact(
            artifact_dir,
            problem_id=str(case_id),
            result_payload=dict(result),
        )
        token_proof = dict(result.get("token_proof") or {})
        turn_timing_log = list(result.get("turn_timing_log") or [])
        turn_token_usage_rows = _turn_token_usage_rows(result)
        detailed_rows.append(
            {
                "run_id": str(run_id),
                "question_run_id": str(result.get("question_run_id", "")),
                "problem_id": case_id,
                "source_file": str(case.get("source_file", "")),
                "expected_answer": expected_answer,
                "predicted_answer": predicted_answer,
                "submission_answer": str(submission_row.get("answer", "")),
                "correct": bool(predicted_answer == expected_answer),
                "verified": bool(result.get("verified", False)),
                "status": str(result.get("status", "unknown")),
                "turns": int(result.get("turn_index", 0) or 0),
                "loops": int(result.get("loop_index", 0) or 0),
                "boot_passed": bool(boot_summary.get("passed", False)),
                "wall_seconds": float(case_wall_seconds),
                "sum_turn_wall_seconds": float(timing_summary.get("sum_turn_wall_seconds", 0.0) or 0.0),
                "total_prompt_tokens": int(token_proof.get("total_prompt_tokens", 0) or 0),
                "total_completion_tokens": int(token_proof.get("total_completion_tokens", 0) or 0),
                "total_tokens": int(token_proof.get("total_tokens", 0) or 0),
                "turn_timing_log_json": _turn_metrics_json(turn_timing_log),
                "turn_token_usage_json": _turn_metrics_json(turn_token_usage_rows),
                "turn_usage_compact": _turn_metrics_compact(turn_token_usage_rows),
                "transcript_path": str(transcript_path),
                "result_payload_path": str(result_payload_path),
            }
        )

    submission_df = pl.DataFrame(submission_rows)
    results_df = pl.DataFrame(detailed_rows)
    submission_df.write_csv(str(submission_path))
    results_df.write_csv(str(results_path))

    correct_count = sum(1 for row in detailed_rows if bool(row.get("correct", False)))
    total_wall_seconds = round(time.perf_counter() - started_at, 4)
    summary = {
        "event": "cb11_local_vault_smoke_summary",
        "revision": str(CB11_SUBMISSION_REVISION),
        "cases": int(total_cases),
        "correct": int(correct_count),
        "accuracy": round((float(correct_count) / float(total_cases)) if total_cases else 0.0, 4),
        "submission_csv_path": str(submission_path.resolve()),
        "results_csv_path": str(results_path.resolve()),
        "artifact_dir": str(artifact_dir.resolve()),
        "runtime_at_boot_passed": bool(boot_summary.get("passed", False)),
        "total_wall_seconds": float(total_wall_seconds),
    }
    _write_summary_json(artifact_dir / "local_vault_summary.json", summary)
    globals()["LAST_LOCAL_VAULT_SMOKE_RESULTS"] = list(detailed_rows)
    globals()["LAST_LOCAL_VAULT_SMOKE_SUBMISSION_ROWS"] = list(submission_rows)
    globals()["LAST_LOCAL_VAULT_SMOKE_RESULTS_DF"] = results_df
    globals()["LAST_LOCAL_VAULT_SMOKE_SUBMISSION_DF"] = submission_df
    globals()["LAST_LOCAL_VAULT_SMOKE_SUMMARY"] = dict(summary)
    print(summary)
    if detailed_rows:
        print(results_df)
    return dict(summary)


def run_runtimeatboot_easy10_smoke(
    *,
    limit: int | None = None,
    path: Any = None,
    artifact_dir: Any = None,
    submission_csv_path: Any = None,
    results_csv_path: Any = None,
) -> dict[str, Any]:
    if not _runtime_at_boot_passed():
        summary = _blocked_runtime_at_boot_summary("cb11_runtimeatboot_easy10_smoke_summary")
        globals()["LAST_RUNTIMEATBOOT_EASY10_SMOKE_SUMMARY"] = dict(summary)
        print(summary)
        return dict(summary)

    run_aen_protocol = _require_notebook_callable(
        "run_aen_protocol",
        _run_aen_protocol,
    )
    cases = load_runtimeatboot_easy10_manifest(
        path=path,
        limit=_runtimeatboot_easy10_default_limit if limit is None else int(limit),
    )
    artifact_dir = _resolve_artifact_dir(artifact_dir)
    artifact_dir.mkdir(parents=True, exist_ok=True)
    submission_path = Path(submission_csv_path) if submission_csv_path is not None else artifact_dir / "runtimeatboot_easy10_submission.csv"
    results_path = Path(results_csv_path) if results_csv_path is not None else artifact_dir / "runtimeatboot_easy10_results.csv"
    submission_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.parent.mkdir(parents=True, exist_ok=True)

    detailed_rows: list[dict[str, Any]] = []
    submission_rows: list[dict[str, Any]] = []
    started_at = time.perf_counter()
    total_cases = len(cases)
    boot_summary = _runtime_at_boot_summary()
    run_id = str(boot_summary.get("run_id", time.strftime("easy10-smoke-%Y%m%d-%H%M%S")))

    for index, case in enumerate(cases, start=1):
        case_id = str(case.get("id", "")).strip()
        expected_answer = str(case.get("answer", "")).strip()
        problem_text = str(case.get("problem", "")).strip()
        print(f"cb11_runtimeatboot_easy10_progress = [{index}/{total_cases}] {case_id}")
        case_started_at = time.perf_counter()
        result = dict(run_aen_protocol(problem_text) or {})
        case_wall_seconds = round(time.perf_counter() - case_started_at, 4)
        predicted_answer = str(_resolve_submission_answer_from_result(result))
        submission_row = dict(build_submission_row(case_id, result))
        submission_rows.append(dict(submission_row))
        timing_summary = dict(result.get("timing_summary") or {})
        transcript_path = _write_transcript_artifact(
            artifact_dir,
            problem_id=str(case_id),
            transcript_text=str(result.get("transcript_text", "") or ""),
        )
        result_payload_path = _write_result_payload_artifact(
            artifact_dir,
            problem_id=str(case_id),
            result_payload=dict(result),
        )
        token_proof = dict(result.get("token_proof") or {})
        turn_timing_log = list(result.get("turn_timing_log") or [])
        turn_token_usage_rows = _turn_token_usage_rows(result)
        detailed_rows.append(
            {
                "run_id": str(run_id),
                "question_run_id": str(result.get("question_run_id", "")),
                "problem_id": case_id,
                "topic": str(case.get("topic", "")),
                "difficulty": str(case.get("difficulty", "")),
                "expected_answer": expected_answer,
                "predicted_answer": predicted_answer,
                "submission_answer": str(submission_row.get("answer", "")),
                "correct": bool(predicted_answer == expected_answer),
                "verified": bool(result.get("verified", False)),
                "status": str(result.get("status", "unknown")),
                "turns": int(result.get("turn_index", 0) or 0),
                "loops": int(result.get("loop_index", 0) or 0),
                "boot_passed": bool(boot_summary.get("passed", False)),
                "wall_seconds": float(case_wall_seconds),
                "sum_turn_wall_seconds": float(timing_summary.get("sum_turn_wall_seconds", 0.0) or 0.0),
                "total_prompt_tokens": int(token_proof.get("total_prompt_tokens", 0) or 0),
                "total_completion_tokens": int(token_proof.get("total_completion_tokens", 0) or 0),
                "total_tokens": int(token_proof.get("total_tokens", 0) or 0),
                "turn_timing_log_json": _turn_metrics_json(turn_timing_log),
                "turn_token_usage_json": _turn_metrics_json(turn_token_usage_rows),
                "turn_usage_compact": _turn_metrics_compact(turn_token_usage_rows),
                "transcript_path": str(transcript_path),
                "result_payload_path": str(result_payload_path),
            }
        )

    submission_df = pl.DataFrame(submission_rows)
    results_df = pl.DataFrame(detailed_rows)
    submission_df.write_csv(str(submission_path))
    results_df.write_csv(str(results_path))

    correct_count = sum(1 for row in detailed_rows if bool(row.get("correct", False)))
    total_wall_seconds = round(time.perf_counter() - started_at, 4)
    summary = {
        "event": "cb11_runtimeatboot_easy10_smoke_summary",
        "revision": str(CB11_SUBMISSION_REVISION),
        "cases": int(total_cases),
        "correct": int(correct_count),
        "accuracy": round((float(correct_count) / float(total_cases)) if total_cases else 0.0, 4),
        "submission_csv_path": str(submission_path.resolve()),
        "results_csv_path": str(results_path.resolve()),
        "artifact_dir": str(artifact_dir.resolve()),
        "runtime_at_boot_passed": bool(boot_summary.get("passed", False)),
        "total_wall_seconds": float(total_wall_seconds),
    }
    _write_summary_json(artifact_dir / "runtimeatboot_easy10_summary.json", summary)
    globals()["LAST_RUNTIMEATBOOT_EASY10_SMOKE_RESULTS"] = list(detailed_rows)
    globals()["LAST_RUNTIMEATBOOT_EASY10_SMOKE_SUBMISSION_ROWS"] = list(submission_rows)
    globals()["LAST_RUNTIMEATBOOT_EASY10_SMOKE_RESULTS_DF"] = results_df
    globals()["LAST_RUNTIMEATBOOT_EASY10_SMOKE_SUBMISSION_DF"] = submission_df
    globals()["LAST_RUNTIMEATBOOT_EASY10_SMOKE_SUMMARY"] = dict(summary)
    print(summary)
    if detailed_rows:
        print(results_df)
    return dict(summary)


def run_runtimeatboot_run_all(
    *,
    easy10_limit: int | None = None,
    local_vault_limit: int | None = None,
    include_local_vault: bool = False,
    artifact_dir: Any = None,
) -> dict[str, Any]:
    if not _runtime_at_boot_passed():
        summary = _blocked_runtime_at_boot_summary("cb11_run_all_summary")
        globals()["LAST_RUNTIMEATBOOT_RUN_ALL_SUMMARY"] = dict(summary)
        print(summary)
        return dict(summary)

    boot_summary = _runtime_at_boot_summary()
    boot_run_id = str(boot_summary.get("run_id", time.strftime("rab-%Y%m%d-%H%M%S")) or time.strftime("rab-%Y%m%d-%H%M%S"))
    base_artifact_dir = _resolve_artifact_dir(
        artifact_dir if artifact_dir is not None else (Path(_local_smoke_artifact_dir) / f"runall-{boot_run_id}")
    )
    _write_summary_json(base_artifact_dir / "runtime_at_boot_summary.json", boot_summary)
    boot_csv_path = Path(str(boot_summary.get("boot_log_csv_path", "") or "")).expanduser()
    if str(boot_csv_path):
        try:
            if boot_csv_path.exists():
                (base_artifact_dir / "runtime_boot_log.csv").write_text(
                    boot_csv_path.read_text(encoding="utf-8", errors="ignore"),
                    encoding="utf-8",
                )
        except Exception:
            pass
    easy10_artifact_dir = base_artifact_dir / "easy10"
    started_at = time.perf_counter()

    easy10_summary = dict(
        run_runtimeatboot_easy10_smoke(
            limit=_runtimeatboot_easy10_default_limit if easy10_limit is None else int(easy10_limit),
            artifact_dir=easy10_artifact_dir,
        )
        or {}
    )
    local_vault_summary: dict[str, Any]
    if bool(include_local_vault):
        local_vault_artifact_dir = base_artifact_dir / "local_vault"
        local_vault_summary = dict(
            run_local_vault_smoke(
                limit=_local_vault_smoke_default_limit if local_vault_limit is None else int(local_vault_limit),
                artifact_dir=local_vault_artifact_dir,
            )
            or {}
        )
    else:
        local_vault_summary = {
            "event": "cb11_local_vault_smoke_summary",
            "status": "skipped",
            "reason": "include_local_vault=False",
        }

    combined = {
        "event": "cb11_run_all_summary",
        "revision": str(CB11_SUBMISSION_REVISION),
        "boot_run_id": str(boot_run_id),
        "artifact_dir": str(base_artifact_dir.resolve()),
        "runtime_at_boot_passed": bool(boot_summary.get("passed", False)),
        "include_local_vault": bool(include_local_vault),
        "easy10_summary": dict(easy10_summary),
        "local_vault_summary": dict(local_vault_summary),
        "total_wall_seconds": round(float(time.perf_counter() - started_at), 4),
    }
    summary_path = _write_summary_json(base_artifact_dir / "runall_summary.json", combined)
    combined["summary_json_path"] = str(summary_path)
    combined["artifact_bundle_manifest_path"] = str(_write_artifact_bundle_manifest(base_artifact_dir))
    globals()["LAST_RUNTIMEATBOOT_RUN_ALL_SUMMARY"] = dict(combined)
    print(combined)
    return dict(combined)


def runtime_at_boot_readiness_snapshot() -> dict[str, Any]:
    boot_summary = _runtime_at_boot_summary()
    artifact_dir = Path(_local_smoke_artifact_dir)
    vault_root = Path(_local_vault_smoke_root)
    dataset_root = Path(_runtimeatboot_dataset_root)
    competition_test_path = _resolve_competition_test_path()
    return {
        "event": "runtime_at_boot_readiness_snapshot",
        "revision": str(CB11_SUBMISSION_REVISION),
        "runtimeatboot_dataset_name": str(_runtimeatboot_dataset_name),
        "runtimeatboot_dataset_folder": str(_runtimeatboot_dataset_folder),
        "runtimeatboot_dataset_root": str(dataset_root),
        "runtimeatboot_dataset_root_exists": bool(dataset_root.exists()),
        "runtime_at_boot_passed": bool(boot_summary.get("passed", False)),
        "runtime_at_boot_status": str(boot_summary.get("status", "not_started")),
        "runtime_at_boot_log_csv_path": str(boot_summary.get("boot_log_csv_path", "")),
        "artifact_dir": str(artifact_dir),
        "artifact_dir_exists": bool(artifact_dir.exists()),
        "runtimeatboot_easy10_path": str(_runtimeatboot_easy10_path),
        "runtimeatboot_easy10_exists": bool(Path(_runtimeatboot_easy10_path).exists()),
        "runtimeatboot_easy10_kaggle_test_path": str(_runtimeatboot_easy10_kaggle_test_path),
        "runtimeatboot_easy10_kaggle_test_exists": bool(Path(_runtimeatboot_easy10_kaggle_test_path).exists()),
        "competition_test_path": str(competition_test_path),
        "competition_test_exists": bool(competition_test_path.exists()),
        "runtimeatboot_test1_csv_path": str(_runtimeatboot_test1_csv_path),
        "runtimeatboot_test1_csv_exists": bool(Path(_runtimeatboot_test1_csv_path).exists()),
        "runtimeatboot_test1_key_csv_path": str(_runtimeatboot_test1_key_csv_path),
        "runtimeatboot_test1_key_csv_exists": bool(Path(_runtimeatboot_test1_key_csv_path).exists()),
        "local_vault_smoke_root": str(vault_root),
        "local_vault_smoke_root_exists": bool(vault_root.exists()),
        "next_actions": [
            "Run CB8 and confirm runtime_at_boot_passed=true.",
            "Run CB12 then CB13 for benchmark inspection.",
            f"Run run_runtimeatboot_easy10_smoke(limit={int(_runtimeatboot_easy10_default_limit)}).",
            f"Or run run_runtimeatboot_run_all(easy10_limit={int(_runtimeatboot_easy10_default_limit)}).",
            "Download the runall folder with boot logs, easy10 CSVs, transcripts, and result payloads.",
        ],
    }


def runtimeatboot_upload_layout() -> dict[str, Any]:
    dataset_root = Path(_runtimeatboot_dataset_root)
    expected_files = {
        "athena_study": dataset_root / "boot" / "athena" / "Athena_epistemic_boot_100_final_hq.ndjson",
        "athena_certification": dataset_root / "boot" / "athena" / "Athena_epistemic_boot_100_final_certification_hq.ndjson",
        "artemis_study": dataset_root / "boot" / "artemis" / "Artemis_problem_proof_boot_100_final_hq.ndjson",
        "artemis_certification": dataset_root / "boot" / "artemis" / "Artemis_problem_proof_boot_100_final_hq_mcq.ndjson",
        "aria_study": dataset_root / "boot" / "aria" / "Aria_problem_proof_boot_100_final.ndjson",
        "aria_certification": dataset_root / "boot" / "aria" / "Aria_problem_proof_boot_100_final_mcq_2q.ndjson",
        "runtimeatboot_easy10": dataset_root / "smoke" / "runtimeatboot_easy10.json",
        "runtimeatboot_easy10_kaggle_test": dataset_root / "smoke" / "runtimeatboot_easy10_kaggle_test.csv",
        "runtimeatboot_kaggle_smoke2_csv": dataset_root / "test" / "runtimeatboot_kaggle_smoke2.csv",
        "runtimeatboot_test1_csv": dataset_root / "test" / "runtimeatboot_test1.csv",
        "runtimeatboot_test1_key_csv": dataset_root / "test" / "runtimeatboot_test1_key.csv",
        "smoke_root": dataset_root / "smoke" / "alppuzzlesfinalized",
        "manifest": dataset_root / "runtimeatboot_manifest.json",
    }
    return {
        "event": "runtimeatboot_upload_layout",
        "dataset_name": str(_runtimeatboot_dataset_name),
        "dataset_folder": str(_runtimeatboot_dataset_folder),
        "dataset_root": str(dataset_root),
        "expected_files": {key: str(path) for key, path in expected_files.items()},
        "exists": {key: bool(path.exists()) for key, path in expected_files.items()},
    }


def runtimeatboot_attached_directory_snapshot() -> dict[str, Any]:
    dataset_root = Path(_runtimeatboot_dataset_root)
    manifest_path = dataset_root / "runtimeatboot_manifest.json"
    top_level_children: list[str] = []
    if dataset_root.exists():
        top_level_children = sorted(child.name for child in dataset_root.iterdir())
    boot_counts: dict[str, int] = {}
    for role_name in ["athena", "artemis", "aria"]:
        role_root = dataset_root / "boot" / role_name
        boot_counts[role_name] = int(len(list(role_root.glob("*")))) if role_root.exists() else 0
    smoke_root = dataset_root / "smoke" / "alppuzzlesfinalized"
    manifest_payload: dict[str, Any] = {}
    if manifest_path.exists():
        try:
            manifest_payload = dict(json.loads(manifest_path.read_text(encoding="utf-8")))
        except Exception as exc:
            manifest_payload = {"manifest_error": str(exc)}
    return {
        "event": "runtimeatboot_attached_directory_snapshot",
        "dataset_root": str(dataset_root),
        "dataset_root_exists": bool(dataset_root.exists()),
        "top_level_children": list(top_level_children),
        "boot_counts": dict(boot_counts),
        "smoke_tex_count": int(len(list(smoke_root.glob("p*.tex")))) if smoke_root.exists() else 0,
        "manifest_path": str(manifest_path),
        "manifest_exists": bool(manifest_path.exists()),
        "manifest_summary": dict(manifest_payload) if manifest_payload else {},
    }


def runtimeatboot_cpu_preflight_snapshot() -> dict[str, Any]:
    dataset_root = Path(_runtimeatboot_dataset_root)
    kaggle_input_root = Path("/kaggle/input")
    attached_inputs: list[str] = []
    if kaggle_input_root.exists():
        try:
            attached_inputs = sorted(child.name for child in kaggle_input_root.iterdir() if child.is_dir())
        except Exception:
            attached_inputs = []
    layout = runtimeatboot_upload_layout()
    exists_map = dict(layout.get("exists") or {})
    missing_keys = [str(key) for key, present in exists_map.items() if not bool(present)]
    ready_for_h100_boot = bool(dataset_root.exists()) and not missing_keys
    return {
        "event": "runtimeatboot_cpu_preflight_snapshot",
        "revision": str(CB11_SUBMISSION_REVISION),
        "runtimeatboot_dataset_name": str(_runtimeatboot_dataset_name),
        "runtimeatboot_dataset_folder": str(_runtimeatboot_dataset_folder),
        "selected_dataset_root": str(dataset_root),
        "selected_dataset_root_exists": bool(dataset_root.exists()),
        "attached_input_roots": list(attached_inputs),
        "expected_layout_exists": dict(exists_map),
        "missing_layout_keys": list(missing_keys),
        "ready_for_h100_boot": bool(ready_for_h100_boot),
        "recommended_next_step": (
            "Boot H100 now."
            if ready_for_h100_boot
            else f"Attach or upload the Kaggle dataset '{_runtimeatboot_dataset_name}' containing '{_runtimeatboot_dataset_folder}'."
        ),
    }


def print_runtimeatboot_attached_directory() -> None:
    snapshot = runtimeatboot_attached_directory_snapshot()
    print(snapshot)
    dataset_root = Path(_runtimeatboot_dataset_root)
    if not dataset_root.exists():
        print("Attached dataset root not found.")
        return
    print("Attached Dataset Directory")
    for child in sorted(dataset_root.iterdir(), key=lambda path: path.name):
        print(f"- {child.name}")
        if child.is_dir():
            for nested in sorted(child.iterdir(), key=lambda path: path.name):
                print(f"  - {child.name}/{nested.name}")


def print_runtimeatboot_cpu_preflight() -> None:
    snapshot = runtimeatboot_cpu_preflight_snapshot()
    print(snapshot)
    print("CPU Preflight")
    print(f"Selected dataset root: {str(snapshot.get('selected_dataset_root', ''))}")
    print(f"Ready for H100 boot: {str(bool(snapshot.get('ready_for_h100_boot', False))).lower()}")
    attached = list(snapshot.get("attached_input_roots") or [])
    if attached:
        print("Attached /kaggle/input roots:")
        for name in attached:
            print(f"- {name}")
    missing = list(snapshot.get("missing_layout_keys") or [])
    if missing:
        print("Missing expected layout keys:")
        for name in missing:
            print(f"- {name}")
    print(str(snapshot.get("recommended_next_step", "")))


def print_runtimeatboot_upload_layout() -> None:
    layout = runtimeatboot_upload_layout()
    print(layout)
    print("Upload Plan")
    print(f"1. Create or update the Kaggle dataset named '{_runtimeatboot_dataset_name}'.")
    print("2. Dataset root may be either the package folder or the flattened boot/ smoke/ layout.")
    print(f"3. The local source package is: {Path('kaggle_aimo3') / _runtimeatboot_dataset_folder}")
    print("4. The notebook accepts a root that directly contains boot/ and smoke/.")


def print_runtime_at_boot_runbook() -> None:
    snapshot = runtime_at_boot_readiness_snapshot()
    print(snapshot)
    print("UI Runbook")
    print(f"1. Attach the Kaggle dataset '{_runtimeatboot_dataset_name}'.")
    print("2. Run print_runtimeatboot_attached_directory() if you want a quick mounted-file snapshot.")
    print("3. Start the notebook on H100 and run cells through CB8.")
    print("4. Confirm all three roles passed Runtime-at-Boot before continuing.")
    print("5. Stop immediately if runtime_at_boot_passed is false.")
    print("6. Run CB12 then CB13 for the one-question transcript check.")
    print(f"7. Run run_runtimeatboot_run_all(easy10_limit={int(_runtimeatboot_easy10_default_limit)}).")
    print("8. Download the single runall folder from the artifacts directory.")


def run_cb11_cell_bootstrap(
    *,
    auto_export_if_attached_test: bool | None = None,
    preview_limit: int = 5,
) -> dict[str, Any]:
    auto_export = bool(
        globals().get("CB11_AUTO_EXPORT_ATTACHED_TEST", False)
        if auto_export_if_attached_test is None
        else auto_export_if_attached_test
    )
    competition_test_path = _resolve_competition_test_path()
    helper_index = {
        "cb11_submission_revision": CB11_SUBMISSION_REVISION,
        "reference_bench_root": str(_reference_bench_root),
        "runtimeatboot_dataset_root": str(_runtimeatboot_dataset_root),
        "local_smoke_artifact_dir": str(_local_smoke_artifact_dir),
        "runtimeatboot_easy10_path": str(_runtimeatboot_easy10_path),
        "runtimeatboot_easy10_kaggle_test_path": str(_runtimeatboot_easy10_kaggle_test_path),
        "competition_test_path": str(competition_test_path),
        "runtimeatboot_test1_csv_path": str(_runtimeatboot_test1_csv_path),
        "runtimeatboot_test1_key_csv_path": str(_runtimeatboot_test1_key_csv_path),
        "local_vault_smoke_root": str(_local_vault_smoke_root),
        "reference_bench_smoke_default_ids": list(_reference_bench_smoke_default_ids),
        "local_smoke_helper": "run_reference_bench_smoke(case_ids=None, limit=None)",
        "runtimeatboot_easy10_helper": f"run_runtimeatboot_easy10_smoke(limit={int(_runtimeatboot_easy10_default_limit)})",
        "local_vault_smoke_helper": f"run_local_vault_smoke(limit={int(_local_vault_smoke_default_limit)})",
        "runtimeatboot_run_all_helper": f"run_runtimeatboot_run_all(easy10_limit={int(_runtimeatboot_easy10_default_limit)})",
        "attached_test_preview_helper": "list_attached_test_cases(test_dataset=None, limit=5)",
        "attached_test_export_helper": "run_attached_test_dataset_export(test_dataset=None, limit=None)",
        "attached_test_candidate_helper": "list_attached_test_dataframe_candidates()",
        "attached_test_path_helper": "list_attached_test_path_candidates()",
        "kaggle_submission_contract_helper": "print_kaggle_submission_contract()",
        "runtime_at_boot_runbook_helper": "print_runtime_at_boot_runbook()",
        "runtime_at_boot_readiness_helper": "runtime_at_boot_readiness_snapshot()",
        "runtimeatboot_cpu_preflight_helper": "print_runtimeatboot_cpu_preflight()",
        "runtimeatboot_upload_layout_helper": "print_runtimeatboot_upload_layout()",
        "runtimeatboot_attached_directory_helper": "print_runtimeatboot_attached_directory()",
        "cb11_auto_export_attached_test": bool(auto_export),
        "submission_entrypoint": "predict(id_, problem)",
        "competition_wrapper_entrypoint": "Run CB12 to serve Kaggle competition inference.",
    }
    print(helper_index)

    readiness = runtime_at_boot_readiness_snapshot()
    print(
        {
            "event": "cb11_readiness_certificate",
            "runtime_at_boot_passed": bool(readiness.get("runtime_at_boot_passed", False)),
            "runtime_at_boot_status": str(readiness.get("runtime_at_boot_status", "")),
            "runtimeatboot_dataset_root_exists": bool(readiness.get("runtimeatboot_dataset_root_exists", False)),
            "runtimeatboot_easy10_exists": bool(readiness.get("runtimeatboot_easy10_exists", False)),
        }
    )

    contract = kaggle_submission_contract_snapshot()
    print(
        {
            "event": str(contract.get("event", "cb11_kaggle_submission_contract")),
            "official_submission_shape": str(contract.get("official_submission_shape", "")),
            "official_submission_is_parquet": bool(contract.get("official_submission_is_parquet", False)),
            "analysis_artifact_count": int(len(list(contract.get("analysis_artifacts") or []))),
        }
    )

    bootstrap_summary: dict[str, Any] = {
        "event": "cb11_cell_bootstrap",
        "revision": str(CB11_SUBMISSION_REVISION),
        "runtime_at_boot_passed": bool(readiness.get("runtime_at_boot_passed", False)),
        "auto_export_if_attached_test": bool(auto_export),
        "competition_test_path": str(competition_test_path),
        "attached_test_detected": False,
    }

    if not bool(auto_export):
        print(
            {
                "event": "cb11_submission_mode",
                "mode": "competition_only",
                "competition_test_path": str(competition_test_path),
                "attached_test_detection": "disabled",
            }
        )
        globals()["LAST_CB11_CELL_BOOTSTRAP_SUMMARY"] = dict(bootstrap_summary)
        return dict(bootstrap_summary)

    try:
        preview_rows, source_label = _resolve_attached_test_source(limit=int(max(1, preview_limit)))
        bootstrap_summary["attached_test_detected"] = True
        bootstrap_summary["attached_test_source_label"] = str(source_label)
        bootstrap_summary["attached_test_preview_count"] = int(len(preview_rows))
        print(
            {
                "event": "cb11_attached_test_detected",
                "source_label": str(source_label),
                "preview_rows": int(len(preview_rows)),
            }
        )
        if preview_rows:
            preview_input: Any = source_label if str(source_label).strip() and str(source_label) != "explicit_dataframe_argument" else preview_rows
            print(list_attached_test_cases(preview_input, limit=int(max(1, preview_limit))))
        if bool(readiness.get("runtime_at_boot_passed", False)) and bool(auto_export):
            print("cb11_auto_action = running attached test export")
            export_rows, export_source_label = _resolve_attached_test_source(limit=None)
            export_input: Any = (
                export_source_label
                if str(export_source_label).strip() and str(export_source_label) != "explicit_dataframe_argument"
                else export_rows
            )
            export_summary = run_attached_test_dataset_export(test_dataset=export_input)
            bootstrap_summary["attached_test_export_summary"] = dict(export_summary)
            bootstrap_summary["attached_test_source_label"] = str(export_source_label)
        elif not bool(readiness.get("runtime_at_boot_passed", False)):
            print("cb11_auto_action = skipped attached test export because runtime_at_boot_passed is false")
        else:
            print("cb11_auto_action = attached test detected but auto export is disabled")
    except Exception as exc:
        bootstrap_summary["attached_test_error"] = str(exc)
        print({"event": "cb11_attached_test_detection", "status": "not_available", "message": str(exc)})
        try:
            candidate_rows = _discover_attached_test_dataframe_candidates()
            candidate_df = pl.DataFrame(candidate_rows)
            print({"event": "cb11_attached_test_candidates", "count": int(len(candidate_rows))})
            print(candidate_df)
        except Exception:
            pass
        try:
            path_rows = _discover_attached_test_path_candidates()
            path_df = pl.DataFrame(path_rows)
            existing_count = sum(1 for row in path_rows if bool(dict(row).get("exists", False)))
            print({"event": "cb11_attached_test_path_candidates", "count": int(len(path_rows)), "existing": int(existing_count)})
            print(path_df)
        except Exception:
            pass
        print("cb11_next_step = attach/load the test dataset, then rerun CB11")

    globals()["LAST_CB11_CELL_BOOTSTRAP_SUMMARY"] = dict(bootstrap_summary)
    return dict(bootstrap_summary)



CB11_CELL_BOOTSTRAP_SUMMARY = run_cb11_cell_bootstrap()

"""## 11.5 - Architecture Reset and Token Certificate


"""

# Auto-extracted by Aster from AENAIMO260_0_2_3_FINAL_CB5_CB8_CLOSED_BOOK_WORKING_20260427.ipynb
# Source cell: 28 / CB06.75 - Dataset Path Override
# Intended use: replace/run this CB cell in notebook order.

import os
from pathlib import Path


CB06_75_DATASET_PATH_OVERRIDE_REVISION = "2026-04-29-cb06_75-runtimeatboot-v34-study150-cert30-r6"

_DEFAULT_RUNTIME_AT_BOOT_V34_ROOT = "/kaggle/input/runtimeatbootdataset-v34"
if not str(globals().get("RUNTIME_AT_BOOT_DATASET_ROOT", "") or "").strip():
    for _candidate_root in [
        "/kaggle/input/runtimeatbootdataset-v34",
        "/kaggle/input/runtimeatbootdatset-v34",
        "/kaggle/input/runtimeatboot-v34",
        "/root/.cache/kagglehub/datasets/aadityapaudel/runtimeatbootdataset-v34/versions/1",
        "/root/.cache/kagglehub/datasets/aadityapaudel/runtimeatboot-v34/versions/1",
    ]:
        if Path(_candidate_root).exists():
            _DEFAULT_RUNTIME_AT_BOOT_V34_ROOT = str(_candidate_root)
            break

CANONICAL_RUNTIME_AT_BOOT_DATASET_ROOT = Path(
    str(globals().get("RUNTIME_AT_BOOT_DATASET_ROOT", _DEFAULT_RUNTIME_AT_BOOT_V34_ROOT))
)

RUNTIME_AT_BOOT_DATASET_NAME = "runtimeatbootdataset_v34"
RUNTIME_AT_BOOT_DATASET_FOLDER = "runtimeatbootdataset_v34"
RUNTIME_AT_BOOT_DATASET_ROOT = str(CANONICAL_RUNTIME_AT_BOOT_DATASET_ROOT)


def _initial_text(value: object, default: str = "") -> str:
    text = str(value if value is not None else default).strip()
    return text or str(default).strip()


def _maybe_int(value: object) -> int | None:
    text = str(value if value is not None else "").strip()
    if not text:
        return None
    try:
        return int(text)
    except Exception:
        return None


def _copy_mapping(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def _normalize_nonnegative(value: int | None) -> int | None:
    if value is None:
        return None
    return max(0, int(value))


def _bool_from_global(name: str, default: bool) -> bool:
    value = globals().get(name, default)
    if isinstance(value, bool):
        return bool(value)
    text = str(value if value is not None else "").strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return bool(default)


def _resolve_positive_global(name: str, default: int) -> int:
    value = _normalize_nonnegative(_maybe_int(globals().get(name)))
    if value is None or int(value) <= 0:
        return int(default)
    return int(value)


def _resolve_boot_memory_ack_text() -> str:
    explicit = _initial_text(globals().get("BOOT_MEMORY_ACK_TEXT_OVERRIDE"), "")
    if explicit:
        return str(explicit)
    return "BOOT_CERTIFIED"


def _extract_line_limit_from_mapping(mapping: dict[str, object], *keys: str) -> int | None:
    for key in keys:
        if key in mapping:
            return _normalize_nonnegative(_maybe_int(mapping.get(key)))
    return None


def _resolve_certification_preset_line_limit(raw_value: object) -> tuple[str, int | None]:
    text = _initial_text(raw_value).lower()
    if not text:
        return ("default", None)
    preset_map = {
        "default": None,
        "canonical": None,
        "first10": 10,
        "demo10": 10,
        "smoke10": 10,
        "10": 10,
        "first50": 50,
        "demo50": 50,
        "50": 50,
        "first100": 100,
        "demo100": 100,
        "full100": 100,
        "100": 100,
    }
    if text in preset_map:
        return (text, _normalize_nonnegative(preset_map[text]))
    return (text, _normalize_nonnegative(_maybe_int(raw_value)))


# Simple preboot scratch-cell overrides before running CB06.75:
# CERTIFICATION_LINES_ALL = 50
# CERTIFICATION_LINES_ATHENA = 10
# CERTIFICATION_LINES_ARTEMIS = 100
# CERTIFICATION_LINES_ARIA = 50
#
# Optional compatibility layer if you still want presets/maps:
# RUNTIME_AT_BOOT_CERTIFICATION_PRESET = "first10"   # or "first50", "first100", "default"
# RUNTIME_AT_BOOT_CERTIFICATION_LINE_LIMITS = {"all": 50}
# RUNTIME_AT_BOOT_CERTIFICATION_LINE_LIMITS = {"athena": 15, "artemis": 15, "aria": 15}
# Explicit runtime globals remain supported:
BOOT_MEMORY_STUDY_LINE_LIMIT = _resolve_positive_global("BOOT_MEMORY_STUDY_LINE_LIMIT", 150)
BOOT_MEMORY_STUDY_PASSES = _resolve_positive_global("BOOT_MEMORY_STUDY_PASSES", 2)
BOOT_MEMORY_STUDY_CHUNK_CHARS = _resolve_positive_global("BOOT_MEMORY_STUDY_CHUNK_CHARS", 24000)
BOOT_MEMORY_STUDY_MAX_TOKENS = _resolve_positive_global("BOOT_MEMORY_STUDY_MAX_TOKENS", 32)
BOOT_MEMORY_ACK_REQUIRED = _bool_from_global("BOOT_MEMORY_ACK_REQUIRED", True)
BOOT_MEMORY_ACK_TEXT = _resolve_boot_memory_ack_text()
BOOT_MEMORY_REQUIRE_CERTIFICATION_TRANSCRIPT = _bool_from_global("BOOT_MEMORY_REQUIRE_CERTIFICATION_TRANSCRIPT", True)
BOOT_MEMORY_BASELINE_STAGE = _initial_text(globals().get("BOOT_MEMORY_BASELINE_STAGE"), "after_certification")
RUNTIME_AT_BOOT_TARGET_CONTEXT_TOKENS = _resolve_positive_global("RUNTIME_AT_BOOT_TARGET_CONTEXT_TOKENS", 700000)

ATHENA_BOOT_CERTIFICATION_LINE_LIMIT = 30
ARTEMIS_BOOT_CERTIFICATION_LINE_LIMIT = 30
ARIA_BOOT_CERTIFICATION_LINE_LIMIT = 30
# ATHENA_BOOT_CERTIFICATION_LINE_LIMIT = 10

_SIMPLE_SHARED_CERTIFICATION_LINE_LIMIT = _normalize_nonnegative(_maybe_int(globals().get("CERTIFICATION_LINES_ALL")))
_SIMPLE_ATHENA_CERTIFICATION_LINE_LIMIT = _normalize_nonnegative(_maybe_int(globals().get("CERTIFICATION_LINES_ATHENA")))
_SIMPLE_ARTEMIS_CERTIFICATION_LINE_LIMIT = _normalize_nonnegative(_maybe_int(globals().get("CERTIFICATION_LINES_ARTEMIS")))
_SIMPLE_ARIA_CERTIFICATION_LINE_LIMIT = _normalize_nonnegative(_maybe_int(globals().get("CERTIFICATION_LINES_ARIA")))
_IS_COMPETITION_RERUN = bool(str(os.getenv("KAGGLE_IS_COMPETITION_RERUN", "") or "").strip())
_HAS_EXPLICIT_SMOKE_LINE_OVERRIDE = any(
    candidate is not None
    for candidate in [
        _SIMPLE_SHARED_CERTIFICATION_LINE_LIMIT,
        _SIMPLE_ATHENA_CERTIFICATION_LINE_LIMIT,
        _SIMPLE_ARTEMIS_CERTIFICATION_LINE_LIMIT,
        _SIMPLE_ARIA_CERTIFICATION_LINE_LIMIT,
        _normalize_nonnegative(_maybe_int(globals().get("BOOT_CERTIFICATION_LINE_LIMIT"))),
        _normalize_nonnegative(_maybe_int(globals().get("ATHENA_BOOT_CERTIFICATION_LINE_LIMIT"))),
        _normalize_nonnegative(_maybe_int(globals().get("ARTEMIS_BOOT_CERTIFICATION_LINE_LIMIT"))),
        _normalize_nonnegative(_maybe_int(globals().get("ARIA_BOOT_CERTIFICATION_LINE_LIMIT"))),
    ]
)
_INTERACTIVE_SMOKE_SHARED_CERTIFICATION_LINE_LIMIT = 100 if (not _IS_COMPETITION_RERUN and not _HAS_EXPLICIT_SMOKE_LINE_OVERRIDE) else None

_CERTIFICATION_LINE_LIMIT_OVERRIDES = _copy_mapping(globals().get("RUNTIME_AT_BOOT_CERTIFICATION_LINE_LIMITS"))
_CERTIFICATION_PRESET_LABEL, _CERTIFICATION_PRESET_LINE_LIMIT = _resolve_certification_preset_line_limit(
    globals().get("RUNTIME_AT_BOOT_CERTIFICATION_PRESET")
)
_EXPLICIT_SHARED_CERTIFICATION_LINE_LIMIT = _normalize_nonnegative(_maybe_int(globals().get("BOOT_CERTIFICATION_LINE_LIMIT")))
_MAPPED_SHARED_CERTIFICATION_LINE_LIMIT = _extract_line_limit_from_mapping(
    _CERTIFICATION_LINE_LIMIT_OVERRIDES,
    "all",
    "ALL",
    "global",
    "GLOBAL",
    "default",
    "DEFAULT",
)
_SHARED_CERTIFICATION_LINE_LIMIT = next(
    (
        candidate
        for candidate in [
            _SIMPLE_SHARED_CERTIFICATION_LINE_LIMIT,
            _EXPLICIT_SHARED_CERTIFICATION_LINE_LIMIT,
            _MAPPED_SHARED_CERTIFICATION_LINE_LIMIT,
            _INTERACTIVE_SMOKE_SHARED_CERTIFICATION_LINE_LIMIT,
            _CERTIFICATION_PRESET_LINE_LIMIT,
        ]
        if candidate is not None
    ),
    None,
)


def _resolve_role_certification_line_limit(
    *,
    simple_global_name: str,
    explicit_global_name: str,
    default: int,
    aliases: tuple[str, ...],
) -> int:
    simple_value = _normalize_nonnegative(_maybe_int(globals().get(simple_global_name)))
    if simple_value is not None:
        return int(simple_value)
    explicit_value = _normalize_nonnegative(_maybe_int(globals().get(explicit_global_name)))
    if explicit_value is not None:
        return int(explicit_value)
    mapped_value = _extract_line_limit_from_mapping(_CERTIFICATION_LINE_LIMIT_OVERRIDES, *aliases)
    if mapped_value is not None:
        return int(mapped_value)
    if _SHARED_CERTIFICATION_LINE_LIMIT is not None:
        return int(_SHARED_CERTIFICATION_LINE_LIMIT)
    return int(default)


ATHENA_BOOT_PATH = str(
    CANONICAL_RUNTIME_AT_BOOT_DATASET_ROOT / "boot" / "athena" / "Athena_epistemic_boot_100_final_hq.ndjson"
)
ATHENA_BOOT_CERTIFICATION_PATH = str(
    CANONICAL_RUNTIME_AT_BOOT_DATASET_ROOT / "boot" / "athena" / "Athena_epistemic_boot_100_final_certification_hq.ndjson"
)

ARTEMIS_BOOT_PATH = str(
    CANONICAL_RUNTIME_AT_BOOT_DATASET_ROOT / "boot" / "artemis" / "Artemis_problem_proof_boot_100_final_hq.ndjson"
)
ARTEMIS_BOOT_CERTIFICATION_PATH = str(
    CANONICAL_RUNTIME_AT_BOOT_DATASET_ROOT / "boot" / "artemis" / "Artemis_problem_proof_boot_100_final_hq_mcq.ndjson"
)

ARIA_BOOT_PATH = str(
    CANONICAL_RUNTIME_AT_BOOT_DATASET_ROOT / "boot" / "aria" / "Aria_problem_proof_boot_100_final.ndjson"
)
ARIA_BOOT_CERTIFICATION_PATH = str(
    CANONICAL_RUNTIME_AT_BOOT_DATASET_ROOT / "boot" / "aria" / "Aria_problem_proof_boot_100_final_mcq_2q.ndjson"
)

ATTACHED_TEST_DATASET_PATH = str(
    (
        CANONICAL_RUNTIME_AT_BOOT_DATASET_ROOT / "test" / "runtimeatboot_voe_test25.csv"
        if _IS_COMPETITION_RERUN
        else CANONICAL_RUNTIME_AT_BOOT_DATASET_ROOT / "test" / "runtimeatboot_kaggle_smoke2.csv"
    )
)

# Force read-and-verify mode to stay terse. We still scrub stray tags later if a backend ignores this.
SOLVER_ENABLE_THINKING = False
CLERK_ENABLE_THINKING = False
AGENT_ENABLE_THINKING = False

BOOT_CERTIFICATION_LINE_LIMIT = int(_SHARED_CERTIFICATION_LINE_LIMIT if _SHARED_CERTIFICATION_LINE_LIMIT is not None else 30)
ATHENA_BOOT_CERTIFICATION_LINE_LIMIT = _resolve_role_certification_line_limit(
    simple_global_name="CERTIFICATION_LINES_ATHENA",
    explicit_global_name="ATHENA_BOOT_CERTIFICATION_LINE_LIMIT",
    default=30,
    aliases=("athena", "ATHENA", "solver", "SOLVER"),
)
ARTEMIS_BOOT_CERTIFICATION_LINE_LIMIT = _resolve_role_certification_line_limit(
    simple_global_name="CERTIFICATION_LINES_ARTEMIS",
    explicit_global_name="ARTEMIS_BOOT_CERTIFICATION_LINE_LIMIT",
    default=30,
    aliases=("artemis", "ARTEMIS", "clerk", "CLERK"),
)
ARIA_BOOT_CERTIFICATION_LINE_LIMIT = _resolve_role_certification_line_limit(
    simple_global_name="CERTIFICATION_LINES_ARIA",
    explicit_global_name="ARIA_BOOT_CERTIFICATION_LINE_LIMIT",
    default=30,
    aliases=("aria", "ARIA", "agent", "AGENT"),
)
ATHENA_BOOT_CERTIFICATION_PROBE_LIMIT = 2
ARTEMIS_BOOT_CERTIFICATION_PROBE_LIMIT = 2
ARIA_BOOT_CERTIFICATION_PROBE_LIMIT = 2
ATHENA_BOOT_PROMPT_LINE_LIMIT = 100
ARTEMIS_BOOT_PROMPT_LINE_LIMIT = 100
ARIA_BOOT_PROMPT_LINE_LIMIT = 100


print(
    {
        "cb06_75_revision": CB06_75_DATASET_PATH_OVERRIDE_REVISION,
        "runtime_at_boot_dataset_root": str(RUNTIME_AT_BOOT_DATASET_ROOT),
        "athena_boot_path": str(ATHENA_BOOT_PATH),
        "athena_boot_certification_path": str(ATHENA_BOOT_CERTIFICATION_PATH),
        "artemis_boot_path": str(ARTEMIS_BOOT_PATH),
        "artemis_boot_certification_path": str(ARTEMIS_BOOT_CERTIFICATION_PATH),
        "aria_boot_path": str(ARIA_BOOT_PATH),
        "aria_boot_certification_path": str(ARIA_BOOT_CERTIFICATION_PATH),
        "attached_test_dataset_path": str(ATTACHED_TEST_DATASET_PATH),
        "solver_enable_thinking": bool(SOLVER_ENABLE_THINKING),
        "clerk_enable_thinking": bool(CLERK_ENABLE_THINKING),
        "agent_enable_thinking": bool(AGENT_ENABLE_THINKING),
        "certification_lines_requested": {
            "all": _SIMPLE_SHARED_CERTIFICATION_LINE_LIMIT,
            "athena": _SIMPLE_ATHENA_CERTIFICATION_LINE_LIMIT,
            "artemis": _SIMPLE_ARTEMIS_CERTIFICATION_LINE_LIMIT,
            "aria": _SIMPLE_ARIA_CERTIFICATION_LINE_LIMIT,
        },
        "interactive_smoke_default_active": bool(_INTERACTIVE_SMOKE_SHARED_CERTIFICATION_LINE_LIMIT is not None),
        "interactive_smoke_default_certification_lines": _INTERACTIVE_SMOKE_SHARED_CERTIFICATION_LINE_LIMIT,
        "certification_lines_selected": {
            "Athena": int(ATHENA_BOOT_CERTIFICATION_LINE_LIMIT),
            "Artemis": int(ARTEMIS_BOOT_CERTIFICATION_LINE_LIMIT),
            "Aria": int(ARIA_BOOT_CERTIFICATION_LINE_LIMIT),
        },
        "boot_memory_study_line_limit": int(BOOT_MEMORY_STUDY_LINE_LIMIT),
        "boot_memory_study_passes": int(BOOT_MEMORY_STUDY_PASSES),
        "boot_memory_study_chunk_chars": int(BOOT_MEMORY_STUDY_CHUNK_CHARS),
        "boot_memory_study_max_tokens": int(BOOT_MEMORY_STUDY_MAX_TOKENS),
        "boot_memory_ack_required": bool(BOOT_MEMORY_ACK_REQUIRED),
        "boot_memory_ack_text": str(BOOT_MEMORY_ACK_TEXT),
        "boot_memory_require_certification_transcript": bool(BOOT_MEMORY_REQUIRE_CERTIFICATION_TRANSCRIPT),
        "boot_memory_baseline_stage": str(BOOT_MEMORY_BASELINE_STAGE),
        "runtime_at_boot_target_context_tokens": int(RUNTIME_AT_BOOT_TARGET_CONTEXT_TOKENS),
        "runtime_at_boot_certification_preset": str(_CERTIFICATION_PRESET_LABEL),
        "runtime_at_boot_certification_line_limit_overrides": dict(_CERTIFICATION_LINE_LIMIT_OVERRIDES),
        "boot_certification_line_limit": int(BOOT_CERTIFICATION_LINE_LIMIT),
        "athena_boot_certification_line_limit": int(ATHENA_BOOT_CERTIFICATION_LINE_LIMIT),
        "artemis_boot_certification_line_limit": int(ARTEMIS_BOOT_CERTIFICATION_LINE_LIMIT),
        "aria_boot_certification_line_limit": int(ARIA_BOOT_CERTIFICATION_LINE_LIMIT),
        "athena_boot_certification_probe_limit": int(ATHENA_BOOT_CERTIFICATION_PROBE_LIMIT),
        "artemis_boot_certification_probe_limit": int(ARTEMIS_BOOT_CERTIFICATION_PROBE_LIMIT),
        "aria_boot_certification_probe_limit": int(ARIA_BOOT_CERTIFICATION_PROBE_LIMIT),
        "artemis_boot_prompt_line_limit": int(ARTEMIS_BOOT_PROMPT_LINE_LIMIT),
    }
)

from pathlib import Path

for p in [
    ATHENA_BOOT_PATH,
    ATHENA_BOOT_CERTIFICATION_PATH,
    ARTEMIS_BOOT_PATH,
    ARTEMIS_BOOT_CERTIFICATION_PATH,
    ARIA_BOOT_PATH,
    ARIA_BOOT_CERTIFICATION_PATH,
]:
    print(p, Path(p).exists())

"""## 07 - Static Loop Mechanics Core



"""

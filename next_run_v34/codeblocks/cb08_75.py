"""## 08.75 - Knobs


"""
from typing import Any, Callable, cast


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

BOOT_MEMORY_STUDY_LINE_LIMIT = int(globals().get("BOOT_MEMORY_STUDY_LINE_LIMIT", 150) or 150)
BOOT_MEMORY_STUDY_CHUNK_CHARS = int(globals().get("BOOT_MEMORY_STUDY_CHUNK_CHARS", 24000) or 24000)

GLOBAL_SHOW_STREAMING = False
GLOBAL_PRINT_PROGRESS_LINES = True
GLOBAL_ENABLE_TOKEN_STREAMING = True
GLOBAL_STREAM_PRINT_ROLE_PREFIX = True
GLOBAL_STREAM_TOKEN_MODE = "word"



def _copy_mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


MAX_BIG_LOOPS = int(GLOBAL_MAX_BIG_LOOPS)
MIN_BIG_LOOP_FOR_CLOSEOUT = int(GLOBAL_MIN_BIG_LOOP_FOR_CLOSEOUT)
INNER_TOTAL_EXCHANGES = int(GLOBAL_INNER_TOTAL_EXCHANGES)
INNER_REASONING_EXCHANGES = int(INNER_TOTAL_EXCHANGES)
PER_TURN_MAX_TOKENS = int(GLOBAL_MAX_TURN_TOKENS)
LOCK_CONFIDENCE_PCT = int(GLOBAL_CLOSEOUT_CONFIDENCE_PCT)
BOXED_CONFIDENCE_GATE_PCT = int(GLOBAL_CLOSEOUT_CONFIDENCE_PCT)
STRICT_AEN_CLOSEOUT_ENABLED = True
if int(GLOBAL_MAX_TURN_TOKENS) > 0:
    ATHENA_MAX_TOKENS = int(GLOBAL_MAX_TURN_TOKENS)
    ARIA_MAX_TOKENS = int(GLOBAL_MAX_TURN_TOKENS)
    ARTEMIS_MAX_TOKENS = int(GLOBAL_MAX_TURN_TOKENS)
    ATHENA_OPEN_MAX_TOKENS = int(GLOBAL_MAX_TURN_TOKENS)
    ATHENA_SYNTHESIS_MAX_TOKENS = int(GLOBAL_MAX_TURN_TOKENS)
    ATHENA_FINAL_MAX_TOKENS = int(GLOBAL_MAX_TURN_TOKENS)
    PEER_EXCHANGE_MAX_TOKENS = int(GLOBAL_MAX_TURN_TOKENS)
    PEER_REPORT_MAX_TOKENS = int(GLOBAL_MAX_TURN_TOKENS)
    ARIA_EXCHANGE_MAX_TOKENS = int(GLOBAL_MAX_TURN_TOKENS)
    ARTEMIS_EXCHANGE_MAX_TOKENS = int(GLOBAL_MAX_TURN_TOKENS)
    ARIA_REPORT_MAX_TOKENS = int(GLOBAL_MAX_TURN_TOKENS)
    ARTEMIS_REPORT_MAX_TOKENS = int(GLOBAL_MAX_TURN_TOKENS)
SOLVER_MAX_TURN_TOKENS = max(int(ATHENA_MAX_TOKENS), int(ATHENA_OPEN_MAX_TOKENS), int(ATHENA_SYNTHESIS_MAX_TOKENS), int(ATHENA_FINAL_MAX_TOKENS))
CLERK_MAX_TURN_TOKENS = max(int(ARTEMIS_MAX_TOKENS), int(ARTEMIS_EXCHANGE_MAX_TOKENS), int(ARTEMIS_REPORT_MAX_TOKENS))
AGENT_MAX_TURN_TOKENS = max(int(ARIA_MAX_TOKENS), int(ARIA_EXCHANGE_MAX_TOKENS), int(ARIA_REPORT_MAX_TOKENS))
PER_TURN_MAX_TOKENS = max(int(PER_TURN_MAX_TOKENS), int(SOLVER_MAX_TURN_TOKENS), int(CLERK_MAX_TURN_TOKENS), int(AGENT_MAX_TURN_TOKENS))
TRACE_CHARS = 1100
REPORT_TRACE_CHARS = 700
PEER_REPORT_STATE_CHARS = 700
ATHENA_PEER_REPORT_CHARS = 900
SHOW_STREAMING = bool(GLOBAL_SHOW_STREAMING)
PRINT_PROGRESS_LINES = bool(GLOBAL_PRINT_PROGRESS_LINES)
SILENT_CONTROLLER_STREAM = not bool(SHOW_STREAMING)
ENABLE_TOKEN_STREAMING = bool(GLOBAL_ENABLE_TOKEN_STREAMING)
STREAM_PRINT_ROLE_PREFIX = bool(GLOBAL_STREAM_PRINT_ROLE_PREFIX)
STREAM_TOKEN_MODE = str(GLOBAL_STREAM_TOKEN_MODE or "word").strip().lower()
if STREAM_TOKEN_MODE not in {"chunk", "word", "char"}:
    STREAM_TOKEN_MODE = "word"


_normalize_generation_profile_raw = globals().get("normalize_generation_profile")
if callable(_normalize_generation_profile_raw):
    _normalize_generation_profile = cast(Callable[..., dict[str, Any]], _normalize_generation_profile_raw)
    solver_generation = _copy_mapping(
        _normalize_generation_profile(
            globals().get("SOLVER_GENERATION"),
            default_max_tokens=int(SOLVER_MAX_TURN_TOKENS),
            role_name="solver",
        )
    )
    clerk_generation = _copy_mapping(
        _normalize_generation_profile(
            globals().get("CLERK_GENERATION"),
            default_max_tokens=int(CLERK_MAX_TURN_TOKENS),
            role_name="clerk",
        )
    )
    agent_generation = _copy_mapping(
        _normalize_generation_profile(
            globals().get("AGENT_GENERATION"),
            default_max_tokens=int(AGENT_MAX_TURN_TOKENS),
            role_name="agent",
        )
    )
    solver_generation["max_tokens"] = int(SOLVER_MAX_TURN_TOKENS)
    clerk_generation["max_tokens"] = int(CLERK_MAX_TURN_TOKENS)
    agent_generation["max_tokens"] = int(AGENT_MAX_TURN_TOKENS)
    SOLVER_GENERATION = _copy_mapping(solver_generation)
    CLERK_GENERATION = _copy_mapping(clerk_generation)
    AGENT_GENERATION = _copy_mapping(agent_generation)
    SOLVER_SOLVE_GENERATION = _copy_mapping(
        _normalize_generation_profile(
            globals().get("SOLVER_SOLVE_GENERATION") or SOLVER_GENERATION,
            default_max_tokens=int(SOLVER_MAX_TURN_TOKENS),
            role_name="solver",
        )
    )
    CLERK_PATCH_GENERATION = _copy_mapping(
        _normalize_generation_profile(
            globals().get("CLERK_PATCH_GENERATION") or CLERK_GENERATION,
            default_max_tokens=int(CLERK_MAX_TURN_TOKENS),
            role_name="clerk",
        )
    )
    AGENT_REVIEW_GENERATION = _copy_mapping(
        _normalize_generation_profile(
            globals().get("AGENT_REVIEW_GENERATION") or AGENT_GENERATION,
            default_max_tokens=int(AGENT_MAX_TURN_TOKENS),
            role_name="agent",
        )
    )
    SOLVER_SOLVE_GENERATION["max_tokens"] = int(SOLVER_MAX_TURN_TOKENS)
    CLERK_PATCH_GENERATION["max_tokens"] = int(CLERK_MAX_TURN_TOKENS)
    AGENT_REVIEW_GENERATION["max_tokens"] = int(AGENT_MAX_TURN_TOKENS)


_build_loop_mechanics_config_raw = globals().get("build_loop_mechanics_config")
if callable(_build_loop_mechanics_config_raw):
    _build_loop_mechanics_config = cast(Callable[..., dict[str, Any]], _build_loop_mechanics_config_raw)
    LOOP_MECHANICS = _copy_mapping(_build_loop_mechanics_config(globals()))
    MAX_BIG_LOOPS = int(LOOP_MECHANICS.get("max_big_loops", MAX_BIG_LOOPS))
    MIN_BIG_LOOP_FOR_CLOSEOUT = int(LOOP_MECHANICS.get("min_big_loop_for_closeout", MIN_BIG_LOOP_FOR_CLOSEOUT))
    INNER_TOTAL_EXCHANGES = int(LOOP_MECHANICS.get("inner_total_exchanges", INNER_TOTAL_EXCHANGES))
    INNER_REASONING_EXCHANGES = int(LOOP_MECHANICS.get("inner_reasoning_exchanges", INNER_REASONING_EXCHANGES))
    LOCK_CONFIDENCE_PCT = int(LOOP_MECHANICS.get("lock_confidence_pct", LOCK_CONFIDENCE_PCT))
    BOXED_CONFIDENCE_GATE_PCT = int(LOOP_MECHANICS.get("boxed_confidence_gate_pct", BOXED_CONFIDENCE_GATE_PCT))
    ATHENA_MAX_TOKENS = int(LOOP_MECHANICS.get("athena_max_tokens", ATHENA_MAX_TOKENS))
    ARIA_MAX_TOKENS = int(LOOP_MECHANICS.get("aria_max_tokens", ARIA_MAX_TOKENS))
    ARTEMIS_MAX_TOKENS = int(LOOP_MECHANICS.get("artemis_max_tokens", ARTEMIS_MAX_TOKENS))
    ATHENA_OPEN_MAX_TOKENS = int(LOOP_MECHANICS.get("athena_open_max_tokens", ATHENA_MAX_TOKENS))
    PEER_EXCHANGE_MAX_TOKENS = int(LOOP_MECHANICS.get("peer_exchange_max_tokens", max(ARIA_MAX_TOKENS, ARTEMIS_MAX_TOKENS)))
    PEER_REPORT_MAX_TOKENS = int(LOOP_MECHANICS.get("peer_report_max_tokens", PEER_REPORT_MAX_TOKENS))
    ATHENA_SYNTHESIS_MAX_TOKENS = int(LOOP_MECHANICS.get("athena_synthesis_max_tokens", ATHENA_SYNTHESIS_MAX_TOKENS))
    ATHENA_FINAL_MAX_TOKENS = int(LOOP_MECHANICS.get("athena_final_max_tokens", ATHENA_MAX_TOKENS))
    ARIA_EXCHANGE_MAX_TOKENS = int(LOOP_MECHANICS.get("aria_exchange_max_tokens", ARIA_MAX_TOKENS))
    ARIA_REPORT_MAX_TOKENS = int(LOOP_MECHANICS.get("aria_report_max_tokens", ARIA_MAX_TOKENS))
    ARTEMIS_EXCHANGE_MAX_TOKENS = int(LOOP_MECHANICS.get("artemis_exchange_max_tokens", ARTEMIS_MAX_TOKENS))
    ARTEMIS_REPORT_MAX_TOKENS = int(LOOP_MECHANICS.get("artemis_report_max_tokens", ARTEMIS_MAX_TOKENS))
    TRACE_CHARS = int(LOOP_MECHANICS.get("trace_chars", TRACE_CHARS))
    REPORT_TRACE_CHARS = int(LOOP_MECHANICS.get("report_trace_chars", REPORT_TRACE_CHARS))
    PEER_REPORT_STATE_CHARS = int(LOOP_MECHANICS.get("peer_report_state_chars", PEER_REPORT_STATE_CHARS))
    ATHENA_PEER_REPORT_CHARS = int(LOOP_MECHANICS.get("athena_peer_report_chars", ATHENA_PEER_REPORT_CHARS))


print(
    {
        "cb08_75_knobs": "ready",
        "global_max_big_loops": int(GLOBAL_MAX_BIG_LOOPS),
        "global_min_big_loop_for_closeout": int(GLOBAL_MIN_BIG_LOOP_FOR_CLOSEOUT),
        "global_closeout_confidence_pct": int(GLOBAL_CLOSEOUT_CONFIDENCE_PCT),
        "global_inner_total_exchanges": int(GLOBAL_INNER_TOTAL_EXCHANGES),
        "global_max_turn_tokens": int(GLOBAL_MAX_TURN_TOKENS),
        "show_streaming": bool(SHOW_STREAMING),
        "print_progress_lines": bool(PRINT_PROGRESS_LINES),
        "silent_controller_stream": bool(SILENT_CONTROLLER_STREAM),
        "enable_token_streaming": bool(ENABLE_TOKEN_STREAMING),
        "stream_print_role_prefix": bool(STREAM_PRINT_ROLE_PREFIX),
        "stream_token_mode": str(STREAM_TOKEN_MODE),
        "athena_open_max_tokens": int(ATHENA_OPEN_MAX_TOKENS),
        "athena_synthesis_max_tokens": int(ATHENA_SYNTHESIS_MAX_TOKENS),
        "athena_final_max_tokens": int(ATHENA_FINAL_MAX_TOKENS),
        "aria_exchange_max_tokens": int(ARIA_EXCHANGE_MAX_TOKENS),
        "artemis_exchange_max_tokens": int(ARTEMIS_EXCHANGE_MAX_TOKENS),
        "aria_report_max_tokens": int(ARIA_REPORT_MAX_TOKENS),
        "artemis_report_max_tokens": int(ARTEMIS_REPORT_MAX_TOKENS),
    }
)

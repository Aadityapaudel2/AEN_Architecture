# Auto-extracted by Aster from AENAIMO260_0_2_3_FINAL_CB5_CB8_CLOSED_BOOK_WORKING_20260427.ipynb
# Source cell: 24 / CB06.5 - Sampling Parameters
# Intended use: replace/run this CB cell in notebook order.

"""## 06.5 - Sampling Parameters

Controller-stable decoding defaults for routed AEN protocol turns.
"""

from __future__ import annotations


CB06_5_SAMPLING_REVISION = "2026-04-27-cb065-v1.4.3-question-routing-stable-decoding"


def coerce_int(value: object, default: int) -> int:
    if value is None:
        return int(default)
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, int):
        return int(value)
    text = str(value).strip()
    if not text:
        return int(default)
    try:
        return int(text)
    except Exception:
        return int(default)


def coerce_float(value: object, default: float) -> float:
    if value is None:
        return float(default)
    if isinstance(value, bool):
        return float(int(value))
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return float(default)
    try:
        return float(text)
    except Exception:
        return float(default)


def derive_default_per_turn_tokens() -> tuple[int, int]:
    contexts: list[int] = []
    for key in (
        "SOLVER_RUNTIME_CONTEXT_WINDOW_TOKENS",
        "CLERK_RUNTIME_CONTEXT_WINDOW_TOKENS",
        "AGENT_RUNTIME_CONTEXT_WINDOW_TOKENS",
    ):
        value = coerce_int(globals().get(key), 0)
        if value > 0:
            contexts.append(value)
    if not contexts:
        return 1024, 0
    minimum = min(contexts)
    if minimum <= 2048:
        return 512, minimum
    if minimum <= 8192:
        return 1024, minimum
    return 2048, minimum


def role_sampling_profile(*, role_name: str) -> dict[str, float | int]:
    # Low-variance but not identical: stable enough for strict scaffolds,
    # with tiny role offsets to avoid collapsed peer reports.
    base: dict[str, float | int] = {
        "temperature": 0.24,
        "top_p": 0.78,
        "top_k": 40,
        "min_p": 0.0,
        "presence_penalty": 0.0,
        "frequency_penalty": 0.0,
        "repetition_penalty": 1.12,
    }
    role = str(role_name or "").strip().lower()
    if role in {"solver", "athena"}:
        base["temperature"] = 0.26
        base["top_p"] = 0.80
    elif role in {"clerk", "artemis"}:
        base["temperature"] = 0.22
        base["top_p"] = 0.76
        base["repetition_penalty"] = 1.14
    elif role in {"agent", "aria"}:
        base["temperature"] = 0.24
        base["top_p"] = 0.78
        base["top_k"] = 32
    return base


def normalize_generation_profile(
    config: dict | None,
    *,
    default_max_tokens: int,
    role_name: str,
) -> dict:
    base = dict(role_sampling_profile(role_name=str(role_name)))
    incoming = dict(config or {})
    profile = dict(base)
    profile.update(incoming)
    profile["max_tokens"] = max(1, coerce_int(profile.get("max_tokens"), int(default_max_tokens)))
    profile["temperature"] = max(0.0, coerce_float(profile.get("temperature"), float(base["temperature"])))
    profile["top_p"] = min(1.0, max(0.0, coerce_float(profile.get("top_p"), float(base["top_p"]))))
    profile["top_k"] = max(-1, coerce_int(profile.get("top_k"), int(base["top_k"])))
    profile["min_p"] = min(1.0, max(0.0, coerce_float(profile.get("min_p"), float(base["min_p"]))))
    profile["presence_penalty"] = coerce_float(profile.get("presence_penalty"), float(base["presence_penalty"]))
    profile["frequency_penalty"] = coerce_float(profile.get("frequency_penalty"), float(base["frequency_penalty"]))
    profile["repetition_penalty"] = max(
        0.0,
        coerce_float(profile.get("repetition_penalty"), float(base["repetition_penalty"])),
    )
    return profile


_default_per_turn_tokens, RUNTIME_MIN_CONTEXT_TOKENS = derive_default_per_turn_tokens()
PER_TURN_MAX_TOKENS = max(
    1,
    coerce_int(globals().get("PER_TURN_MAX_TOKENS"), int(_default_per_turn_tokens)),
)
SOLVER_MAX_TURN_TOKENS = max(1, coerce_int(globals().get("SOLVER_MAX_TURN_TOKENS"), int(PER_TURN_MAX_TOKENS)))
CLERK_MAX_TURN_TOKENS = max(1, coerce_int(globals().get("CLERK_MAX_TURN_TOKENS"), int(PER_TURN_MAX_TOKENS)))
AGENT_MAX_TURN_TOKENS = max(1, coerce_int(globals().get("AGENT_MAX_TURN_TOKENS"), int(PER_TURN_MAX_TOKENS)))

SAMPLING_POLICY_LABEL = "question_routing_stable_v1"
globals()["SAMPLING_POLICY_LABEL"] = str(SAMPLING_POLICY_LABEL)

SOLVER_GENERATION = dict(
    normalize_generation_profile(
        globals().get("SOLVER_GENERATION"),
        default_max_tokens=SOLVER_MAX_TURN_TOKENS,
        role_name="solver",
    )
)
CLERK_GENERATION = dict(
    normalize_generation_profile(
        globals().get("CLERK_GENERATION"),
        default_max_tokens=CLERK_MAX_TURN_TOKENS,
        role_name="clerk",
    )
)
AGENT_GENERATION = dict(
    normalize_generation_profile(
        globals().get("AGENT_GENERATION"),
        default_max_tokens=AGENT_MAX_TURN_TOKENS,
        role_name="agent",
    )
)
SOLVER_SOLVE_GENERATION = dict(
    normalize_generation_profile(
        globals().get("SOLVER_SOLVE_GENERATION") or SOLVER_GENERATION,
        default_max_tokens=SOLVER_MAX_TURN_TOKENS,
        role_name="solver",
    )
)
CLERK_PATCH_GENERATION = dict(
    normalize_generation_profile(
        globals().get("CLERK_PATCH_GENERATION") or CLERK_GENERATION,
        default_max_tokens=CLERK_MAX_TURN_TOKENS,
        role_name="clerk",
    )
)
AGENT_REVIEW_GENERATION = dict(
    normalize_generation_profile(
        globals().get("AGENT_REVIEW_GENERATION") or AGENT_GENERATION,
        default_max_tokens=AGENT_MAX_TURN_TOKENS,
        role_name="agent",
    )
)

"""## 06.625 Upload dataset


"""

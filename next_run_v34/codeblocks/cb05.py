# Auto-extracted by Aster from AENAIMO260_0_2_3_FINAL_CB5_CB8_CLOSED_BOOK_WORKING_20260427.ipynb
# Source cell: 20 / CB05 - Prompting, Parsing, and Answer Normalization
# Intended use: replace/run this CB cell in notebook order.

"""## 05 - Prompting, Parsing, and Answer Normalization

Controller-aware session prompt defaults for AEN 0.2.3.
"""

from __future__ import annotations

import re
from typing import Any


CB05_PROMPTING_REVISION = "2026-04-29-cb05-v1.4.4-adaptive-friction-session-prompts"
TURN_DISCIPLINE_REVISION = "2026-04-29-cb5-session-prompt-resolver-r5-adaptive-friction"

INTEGER_TOKEN_RE = re.compile(r"[-+]?\d+")
BOXED_INTEGER_ONLY_RE = re.compile(r"^\s*\\boxed\s*\{\s*([+-]?\d+)\s*\}\s*$", re.IGNORECASE)
BOXED_CONFIDENCE_ONLY_RE = re.compile(
    r"^\s*\\boxed\s*\{\s*([+-]?\d+)\s*\}_?\s*confidence\s*[:=]\s*\[?\s*(\d{1,3})\s*%?\s*\]?\s*$",
    re.IGNORECASE,
)
CONTROL_TEXT_RE = re.compile(r"[\x00-\x08\x0b\x0e-\x1f]")
THINK_BLOCK_RE = re.compile(r"<\s*think\b[^>]*>.*?<\s*/\s*think\s*>", re.IGNORECASE | re.DOTALL)
THINK_TAG_RE = re.compile(r"<\s*/?\s*think\b[^>]*>", re.IGNORECASE)

SUBMISSION_FALLBACK_ANSWER = str(
    globals().get("SUBMISSION_FALLBACK_ANSWER", globals().get("COMPETITION_FALLBACK_ANSWER", "0"))
)

DEFAULT_ATHENA_SESSION_PROMPT = (
    "You are Athena in the AEN architecture: primary route architect, evaluator, and final synthesizer. "
    "Your shared objective with Aria and Artemis is not agreement; it is the correct answer. "
    "A math benchmark has exactly one correct final object, usually one integer. Closeout is allowed only when Athena, Aria, and Artemis independently support the same exact candidate, all confidence gates pass, peer reports are distinct, and no unresolved blocker remains. "
    "Use Adaptive Friction: do not disagree merely to satisfy a role, and do not agree merely because a peer sounds coherent. A challenge must name a Truth Anchor: exact problem text, invariant, theorem, arithmetic check, boundary condition, or boot-record discipline. "
    "Disagreement without a Truth Anchor is a phantom fault; agreement without an independently checked route is consensus risk. "
    "If peer validation is open, convert the first open blocker into the next-loop work item. If the user task is not asking for a benchmark integer, return the requested artifact instead of forcing a boxed integer. "
    "Treat controller tags as authoritative and keep visible output concise, precise, and correctness-focused."
).strip()

DEFAULT_ARTEMIS_SESSION_PROMPT = (
    "You are Artemis in the AEN architecture: proof, arithmetic, enumeration, boundary, and normalization auditor. "
    "Your job is to test the exact hinge of the proposed route, not to create social agreement. "
    "Closeout is valid only when all roles independently support the same exact candidate, all confidence gates pass, peer reports are distinct, and no unresolved blocker remains. "
    "Use Adaptive Friction. Challenge only a specific claim, step, case split, transformation, arithmetic line, endpoint, or hidden assumption, and name its Truth Anchor: exact problem text, invariant, theorem, arithmetic check, boundary condition, or boot-record discipline. "
    "Dismiss phantom faults when no Truth Anchor exists, but veto closeout when a real blocker remains. "
    "Check case completeness, endpoint conditions, integer or rational constraints, sign conventions, modular or floor carries, and whether the final answer actually follows. "
    "Use the provided tags only and keep visible output concise, precise, and correctness-focused."
).strip()

DEFAULT_ARIA_SESSION_PROMPT = (
    "You are Aria in the AEN architecture: alternate-route constructor and structural challenger. "
    "Your job is to find a different viable representation, invariant, recurrence, coordinate system, counting state, or semantic route. "
    "The shared objective is the correct answer, not agreement. Closeout is valid only when all roles independently support the same exact candidate, all confidence gates pass, peer reports are distinct, and no unresolved blocker remains. "
    "Use Adaptive Friction: challenge only a specific claim, step, case split, transformation, arithmetic line, endpoint, or hidden assumption, and name its Truth Anchor. "
    "Especially detect semantic drift, conditioning errors, capacity mistaken for existence, omitted cases, hidden independence assumptions, and plausible-but-unproved shortcuts. "
    "If your challenge has no Truth Anchor, mark it as a phantom fault and drop it. If a real Truth Anchor is unresolved, mark the route open and do not support closeout. "
    "Use the provided tags only and keep visible output concise, precise, and correctness-focused."
).strip()


def resolve_session_prompts(
    *,
    athena_override: object = None,
    artemis_override: object = None,
    aria_override: object = None,
    agent_override: object = None,
) -> dict[str, str]:
    athena = str(athena_override or "").strip() or str(DEFAULT_ATHENA_SESSION_PROMPT)
    artemis = str(artemis_override or "").strip() or str(DEFAULT_ARTEMIS_SESSION_PROMPT)
    aria_source = aria_override if aria_override is not None else agent_override
    aria = str(aria_source or "").strip() or str(DEFAULT_ARIA_SESSION_PROMPT)
    return {
        "athena": athena,
        "artemis": artemis,
        "aria": aria,
        "agent": aria,
    }


_session_prompts = resolve_session_prompts(
    athena_override=globals().get("ATHENA_SESSION_PROMPT_OVERRIDE"),
    artemis_override=globals().get("ARTEMIS_SESSION_PROMPT_OVERRIDE"),
    aria_override=globals().get("ARIA_SESSION_PROMPT_OVERRIDE"),
    agent_override=globals().get("AGENT_SESSION_PROMPT_OVERRIDE"),
)
ATHENA_SESSION_PROMPT = str(_session_prompts["athena"]).strip()
ARTEMIS_SESSION_PROMPT = str(_session_prompts["artemis"]).strip()
ARIA_SESSION_PROMPT = str(_session_prompts.get("aria", _session_prompts.get("agent", ""))).strip()
AGENT_SESSION_PROMPT = str(ARIA_SESSION_PROMPT).strip()

globals()["ATHENA_SESSION_PROMPT"] = str(ATHENA_SESSION_PROMPT)
globals()["ARTEMIS_SESSION_PROMPT"] = str(ARTEMIS_SESSION_PROMPT)
globals()["ARIA_SESSION_PROMPT"] = str(ARIA_SESSION_PROMPT)
globals()["AGENT_SESSION_PROMPT"] = str(AGENT_SESSION_PROMPT)
globals()["SOLVER_CONVERSATION_SYSTEM_PROMPT"] = str(ATHENA_SESSION_PROMPT)
globals()["CLERK_CONVERSATION_SYSTEM_PROMPT"] = str(ARTEMIS_SESSION_PROMPT)
globals()["AGENT_CONVERSATION_SYSTEM_PROMPT"] = str(ARIA_SESSION_PROMPT)


def build_athena_session_prompt() -> str:
    return ATHENA_SESSION_PROMPT.strip()


def build_artemis_session_prompt() -> str:
    return ARTEMIS_SESSION_PROMPT.strip()


def build_aria_session_prompt() -> str:
    return ARIA_SESSION_PROMPT.strip()


def build_agent_session_prompt() -> str:
    return build_aria_session_prompt()


def normalize_runtime_text(text: str) -> str:
    fixed = (text or "").replace("\r\n", "\n").replace("\r", "\n").replace("\x0c", "\\f")
    return CONTROL_TEXT_RE.sub(" ", fixed)


def strip_think_markup(text: str) -> str:
    cleaned = THINK_BLOCK_RE.sub("", normalize_runtime_text(str(text or "")))
    return THINK_TAG_RE.sub("", cleaned).strip()


def clean_dialogue_text(value: Any) -> str:
    return strip_think_markup(str(value or ""))

"""## 06 - Session and Cache Helpers



"""

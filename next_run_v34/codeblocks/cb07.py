# Auto-extracted by Aster from AENAIMO260_0_2_3_FINAL_CB5_CB8_CLOSED_BOOK_WORKING_20260427.ipynb
# Source cell: 30 / CB07 - Static Loop Mechanics Core
# Intended use: replace/run this CB cell in notebook order.

"""
Finalized CB07 loop mechanics.

This module is intentionally standalone and notebook-safe: no IPython syntax, no
runtime boot side effects, and no hidden dependency on the exported monolith.

Expected session interface:
    session.execute_user_turn(prompt: str, generation_profile: dict) -> dict

The response dict may contain any of:
    visible_text, raw_text, output_text, response_text, text

Optional session method:
    session.reset_session()
"""

from __future__ import annotations

import json
import re
import time
from difflib import SequenceMatcher
from typing import Any


CB07_FINAL_REVISION = "2026-04-27-cb07-controller-section-wrapper-v1.5.1-closed-book-confidence"

# ---------------------------------------------------------------------------
# Static loop mechanics core (CB7)
# ---------------------------------------------------------------------------

ROLE_ALIASES = {
    "athena": "Athena",
    "solver": "Athena",
    "aria": "Aria",
    "agent": "Aria",
    "artemis": "Artemis",
    "clerk": "Artemis",
}

ROLE_TAGS = {"Athena": "athena", "Aria": "aria", "Artemis": "artemis"}


BOXED_CONFIDENCE_ONLY_RE = re.compile(
    r"^\s*\\boxed\s*\{\s*([+-]?\d+)\s*\}\s*_?\s*confidence\s*[:=]\s*\[?\s*(\d{1,3})\s*%?\s*\]?\s*$",
    re.IGNORECASE,
)
BOXED_CONFIDENCE_ANYWHERE_RE = re.compile(
    r"\\boxed\s*\{\s*([+-]?\d+)\s*\}\s*_?\s*confidence\s*[:=]\s*\[?\s*(\d{1,3})\s*%?\s*\]?",
    re.IGNORECASE,
)
BOXED_INTEGER_ANYWHERE_RE = re.compile(r"\\boxed\s*\{\s*([+-]?\d+)\s*\}", re.IGNORECASE)
REPORT_VERDICT_LINE_RE = re.compile(r"^\s*Report\s+Verdict\s*:\s*(.+?)\s*$", re.IGNORECASE)
CONFIDENCE_VALUE_RE = re.compile(r"\bconfidence\s*[:=]\s*\[?\s*(\d{1,3})\s*%?\s*\]?", re.IGNORECASE)
INTEGER_RE = re.compile(r"[-+]?\d+")
PROMPT_HEADER_RE = re.compile(
    r"^\s*(?:#+\s*)?(Problem|Role|Phase|State|Instructions|Output|Trace|"
    r"HOW_I_WILL_PROCEED|Previous|Athena Context|Peer Reports|Finalization|"
    r"ROLE|PROBLEM|STATE|ROUTE|INSTRUCTIONS|OUTPUT_CONTRACT|SYSTEM|DEVELOPER|USER)\s*:?\s*$",
    re.IGNORECASE,
)
SECTION_RE = re.compile(
    r"<(?P<name>[a-z0-9_]+)(?:\s+max_chars=\"(?P<max>\d+)\")?\s*>(?P<body>.*?)</(?P=name)>",
    re.IGNORECASE | re.DOTALL,
)
VISIBLE_THINK_TAG_RE = re.compile(r"</?\s*think(?:ing)?\b[^>]*>", re.IGNORECASE)

UNSUPPORTED_ROUTE_PHRASES = (
    "let's guess",
    "i will guess",
    "best guess",
    "usually",
    "often these problems",
    "problem design",
    "partial enumeration",
    "partial count",
    "verified subset",
    "lower bound",
    "not fully enumerated",
    "unexecuted computation",
    "not verified",
    "heuristic only",
)

HARD_BLOCKER_PHRASES = (
    "trusting the candidate_answer",
    "trusting candidate_answer",
    "trusting the input state",
    "trust the input state",
    "assume the question implies",
    "i will assert",
    "time constraints",
    "most plausible",
    "not fully",
    "not verified",
    "where does",
    "contradicts",
    "unless",
    "might reveal",
    "given the complexity",
    "i will proceed with the assumption",
    "select the most plausible",
)

QUESTION_PHASE_FORBIDDEN_PHRASES = (
    "final answer",
    "a+b+c+d",
    "\\boxed",
    "<solve_problem_now",
    "candidate_answer:",
)

UNKNOWN_SLOT_VALUES = {"", "unknown", "none", "n/a", "na", "tbd", "pending"}

ANSWER_FORMAT_CONTRADICTION_PHRASES = (
    "format conflict",
    "answer format conflict",
    "positive integer format",
    "integer format conflict",
    "not a positive integer",
    "not an integer",
    "not an exact integer",
    "contradicts the requested format",
    "contradicts the answer format",
    "does not match the requested answer format",
    "does not fit the requested answer format",
    "problem promises a positive integer",
    "problem promises an integer",
)

OPEN_BLOCKER_PHRASES = (
    "blocker remains",
    "gap remains",
    "still open",
    "unresolved",
    "not closed",
    "do not close",
    "cannot support",
    "unproved",
    "missing proof",
    "failed audit",
    "partial_only",
)

NEGATED_OPEN_BLOCKER_PHRASES = (
    "no blocker remains",
    "no blockers remain",
    "no gap remains",
    "no gaps remain",
    "no open blocker",
    "no unresolved blocker",
    "no missing proof",
    "not unresolved",
)


DEFAULT_CONFIG = {
    "max_big_loops": 1,
    "inner_total_exchanges": 3,
    "min_big_loop_for_closeout": 1,
    "closeout_confidence_pct": 90,
    "reset_session_each_turn": True,
    "answer_min": 0,
    "answer_max": 999,
    "athena_open_max_tokens": 4200,
    "peer_exchange_max_tokens": 2600,
    "peer_report_max_tokens": 1200,
    "athena_synthesis_max_tokens": 2600,
    "athena_final_max_tokens": 768,
}

DEFAULT_GENERATION = {
    "Athena": {"temperature": 0.2, "top_p": 0.95},
    "Aria": {"temperature": 0.2, "top_p": 0.95},
    "Artemis": {"temperature": 0.2, "top_p": 0.95},
}


# ---------------------------------------------------------------------------
# Text helpers and sanitization
# ---------------------------------------------------------------------------

def clean_text(value: Any) -> str:
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def canonical_role_name(value: str) -> str:
    token = clean_text(value).lower()
    if token in ROLE_ALIASES:
        return ROLE_ALIASES[token]
    if clean_text(value) in ROLE_TAGS:
        return clean_text(value)
    raise KeyError(f"unknown CB07 role: {value!r}")


def role_payload_tag(role_name: str) -> str:
    return ROLE_TAGS[canonical_role_name(role_name)]


def role_setup_yaml(role_name: str) -> str:
    role = canonical_role_name(role_name)
    if role != "Athena":
        return ""
    fallback = f"schema_id: {_role_metadata_schema_token(role)}\nrole: {role}\n"
    return str(globals().get("ATHENA_SETUP_YAML") or fallback)


def truncate_text(value: Any, max_chars: int) -> str:
    text = clean_text(value)
    limit = max(80, int(max_chars))
    if len(text) <= limit:
        return text
    return f"{text[: limit - 3].rstrip()}..."


def _has_any_phrase(value: Any, phrases: tuple[str, ...]) -> bool:
    lower = clean_text(value).lower()
    return bool(lower) and any(phrase in lower for phrase in phrases)


def has_unsupported_route_language(value: Any) -> bool:
    return _has_any_phrase(value, UNSUPPORTED_ROUTE_PHRASES)


def hard_blocker_hits(value: Any) -> list[str]:
    lower = clean_text(value).lower()
    if not lower:
        return []
    return [phrase for phrase in HARD_BLOCKER_PHRASES if phrase in lower]


def has_hard_blocker_language(value: Any) -> bool:
    return bool(hard_blocker_hits(value))


def has_answer_format_contradiction(value: Any) -> bool:
    return _has_any_phrase(value, ANSWER_FORMAT_CONTRADICTION_PHRASES)


def has_open_blocker_language(value: Any) -> bool:
    lower = clean_text(value).lower()
    if not lower:
        return False
    scrubbed = str(lower)
    for phrase in NEGATED_OPEN_BLOCKER_PHRASES:
        scrubbed = scrubbed.replace(phrase, " ")
    return any(phrase in scrubbed for phrase in OPEN_BLOCKER_PHRASES)


def strip_pseudo_system_text(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    text = re.sub(r"(?im)^\s*```\s*[a-z0-9_-]*\s*$", "", text)
    if re.match(r"(?is)^\s*(?:SYSTEM|DEVELOPER|USER|ASSISTANT)\s*:", text):
        return ""
    cut = re.search(r"(?im)^\s*(?:SYSTEM|DEVELOPER|USER|ASSISTANT)\s*:", text)
    if cut:
        text = text[: cut.start()]
    text = re.sub(r"</?\s*(system_summary|think|final_answer)\b[^>]*>", " ", text, flags=re.IGNORECASE)
    return clean_text(text)


def strip_prompt_echo_sections(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    lines = [str(line or "") for line in text.split("\n")]
    header_indices = [idx for idx, line in enumerate(lines) if PROMPT_HEADER_RE.match(line)]
    if len(header_indices) >= 2:
        first_header = int(header_indices[0])
        prefix = clean_text("\n".join(lines[:first_header]))
        if prefix and not PROMPT_HEADER_RE.search(prefix):
            return prefix
        boxed = BOXED_CONFIDENCE_ANYWHERE_RE.search(text)
        if boxed:
            return clean_text(boxed.group(0))
        return ""
    kept = [line for line in lines if not PROMPT_HEADER_RE.match(line)]
    return clean_text("\n".join(kept))


def sanitize_model_visible_text(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return ""
    text = strip_pseudo_system_text(text)
    text = strip_prompt_echo_sections(text)
    text = re.sub(r"</?\s*(athena|aria|artemis)\s*>", " ", text, flags=re.IGNORECASE)
    return clean_text(text)


sanitize_transcript_visible_text = sanitize_model_visible_text


def has_visible_think_tags(value: Any) -> bool:
    return bool(VISIBLE_THINK_TAG_RE.search(str(value or "")))


def clamp_int(value: Any, lower: int, upper: int, default: int = 0) -> int:
    try:
        parsed = int(value)
    except Exception:
        parsed = int(default)
    return max(int(lower), min(int(upper), int(parsed)))


def clamp_confidence_pct(value: Any, *, default: int = 0, upper: int = 100) -> int:
    text = clean_text(value).rstrip("%")
    if not text:
        return int(default)
    try:
        if "." in text:
            parsed_float = float(text)
            parsed = int(round(parsed_float * 100)) if 0 <= parsed_float <= 1 else int(round(parsed_float))
        else:
            parsed = int(text)
    except Exception:
        parsed = int(default)
    return max(0, min(int(upper), int(parsed)))


def normalize_explicit_integer_answer(value: Any) -> str:
    text = clean_text(value)
    if not text or text.lower() in UNKNOWN_SLOT_VALUES:
        return "none"
    if re.fullmatch(r"[+-]?\d+", text):
        return str(int(text))
    return "none"


def integer_from_abcd_slots(slots: dict[str, str]) -> str:
    values: list[int] = []
    for key in ["a_value", "b_value", "c_value", "d_value"]:
        token = normalize_explicit_integer_answer(dict(slots or {}).get(key, "none"))
        if token == "none":
            return "none"
        values.append(int(token))
    return str(sum(values))


def parse_controller_sections(text: Any) -> dict[str, dict[str, Any]]:
    sections: dict[str, dict[str, Any]] = {}
    for match in SECTION_RE.finditer(clean_text(text)):
        name = clean_text(match.group("name")).lower()
        if not name:
            continue
        sections[name] = {
            "name": name,
            "body": clean_text(match.group("body")),
            "max_chars": clamp_int(match.group("max") or 0, 0, 100000, 0),
        }
    return sections


def parse_key_value_slots(text: Any) -> dict[str, str]:
    slots: dict[str, str] = {}
    for raw_line in clean_text(text).split("\n"):
        line = clean_text(raw_line)
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key_token = clean_text(key).lower().replace(" ", "_")
        if key_token:
            slots[key_token] = clean_text(value)
    return slots


def section_body(sections: dict[str, dict[str, Any]], name: str) -> str:
    return clean_text(dict(sections.get(clean_text(name).lower()) or {}).get("body", ""))


def required_sections_for(role_name: str, phase: str) -> list[str]:
    role = canonical_role_name(role_name)
    phase_key = clean_text(phase).lower()
    if role == "Athena" and phase_key in {"athena_open", "open", "question", "question_athena"}:
        return ["canon_problem_yaml", "given_ask_route_map", "questions_for_aria", "questions_for_artemis"]
    if role == "Athena" and phase_key in {"athena_synthesis", "synthesis"}:
        return ["parsed_peer_artifacts", "route_alignment", "resolved_objections", "remaining_objections", "synthesis_reasoning", "selected_candidate"]
    if role == "Aria" and phase_key in {"peer_exchange_1", "aria_question_answer", "question_answer"}:
        return ["aria_canon_yaml", "answers_to_athena", "proposed_solution_route", "route_confidence_and_risks", "request_to_artemis"]
    if role == "Artemis" and phase_key in {"peer_exchange_1", "artemis_question_answer", "question_answer"}:
        return ["artemis_canon_yaml", "answers_to_athena", "answers_to_aria", "route_validation", "route_feedback_for_aria"]
    if role == "Aria" and phase_key in {"peer_report", "report"}:
        return ["report_slots", "report"]
    if role == "Artemis" and phase_key in {"peer_report", "report"}:
        return ["report_slots", "report"]
    if role == "Artemis" and phase_key in {"forced_solve", "artemis_forced_solve"}:
        return ["entry_status_slots", "case_contribution_table", "normalization_work", "remaining_blocker_if_any", "solve_problem_now", "final_status_slots"]
    if role == "Artemis":
        return ["aria_claim_audit", "confidence_backing", "corrections", "solution_continuation", "request_to_aria", "final_status_slots"]
    if role == "Aria":
        return ["route_agreement_status", "confidence_map", "solution_continuation", "open_uncertainties", "request_to_artemis", "final_status_slots"]
    return []


def section_contract_diagnostics(role_name: str, phase: str, text: Any) -> dict[str, Any]:
    role = canonical_role_name(role_name)
    phase_key = clean_text(phase).lower()
    sections = parse_controller_sections(text)
    required = required_sections_for(role, phase)
    missing = [name for name in required if name not in sections or not section_body(sections, name)]
    think_tags = has_visible_think_tags(text)
    unknown_sections: list[str] = []
    forbidden_hits: list[str] = []
    if phase_key in {"athena_open", "open", "question", "question_athena", "peer_exchange_1", "aria_question_answer", "artemis_question_answer", "question_answer"}:
        for name in required:
            body = section_body(sections, name)
            if not body or body.strip().lower() in UNKNOWN_SLOT_VALUES:
                unknown_sections.append(str(name))
        lower = clean_text(text).lower()
        for phrase in QUESTION_PHASE_FORBIDDEN_PHRASES:
            if phrase in lower:
                if phrase == "candidate_answer:" and "candidate_answer: none" in lower:
                    continue
                forbidden_hits.append(str(phrase))
    return {
        "role": role,
        "phase": clean_text(phase),
        "valid": bool(not missing and not unknown_sections and not forbidden_hits and not think_tags),
        "missing_sections": list(missing),
        "unknown_sections": list(unknown_sections),
        "forbidden_question_phase_hits": list(forbidden_hits),
        "think_tags_detected": bool(think_tags),
        "sections_present": sorted(sections.keys()),
    }


def section_contract_valid(role_name: str, phase: str, text: Any) -> tuple[bool, list[str]]:
    payload = section_contract_diagnostics(role_name, phase, text)
    return bool(payload.get("valid")), list(payload.get("missing_sections") or [])


def render_section_scaffold(role_name: str, phase: str) -> str:
    role = canonical_role_name(role_name)
    phase_key = clean_text(phase).lower()
    canon_yaml = clean_text(globals().get("ATHENA_SETUP_YAML")) or "schema_id: distillator_dsl.math.v2.1\nschema_version: 1"
    if role == "Athena" and phase_key in {"athena_open", "open", "question"}:
        return f"""<canon_problem_yaml max_chars="4200">
{canon_yaml}
</canon_problem_yaml>
<given_ask_route_map max_chars="1400">
given:
  - unknown
ask:
  - unknown
potential_solution_routes:
  - route: unknown
    why_viable: unknown
route_risks:
  - unknown
solution_attempt_status: not_started
</given_ask_route_map>
<questions_for_aria max_chars="1000">
</questions_for_aria>
<questions_for_artemis max_chars="1000">
</questions_for_artemis>
"""
    if role == "Athena" and phase_key in {"athena_synthesis", "synthesis"}:
        return """<parsed_peer_artifacts max_chars="900">
</parsed_peer_artifacts>
<route_alignment max_chars="900">
</route_alignment>
<resolved_objections max_chars="900">
</resolved_objections>
<remaining_objections max_chars="900">
</remaining_objections>
<synthesis_reasoning max_chars="3200">
</synthesis_reasoning>
<selected_candidate max_chars="300">
candidate_answer_integer: none
candidate_confidence: 0
selection_basis: pending_final_answer_turn
</selected_candidate>"""
    if role == "Aria" and phase_key in {"peer_report", "report"}:
        return """<report_slots max_chars="220">
candidate_answer_integer: none
candidate_confidence: 0
status: open
open_blockers: unknown
</report_slots>
<report max_chars="700">
Report to Athena:
</report>"""
    if role == "Artemis" and phase_key in {"peer_report", "report"}:
        return """<report_slots max_chars="220">
candidate_answer_integer: none
candidate_confidence: 0
status: open
open_blockers: unknown
</report_slots>
<report max_chars="700">
Report to Athena:
</report>"""
    if role == "Aria" and phase_key in {"peer_exchange_1", "aria_question_answer", "question_answer"}:
        return """<aria_canon_yaml max_chars="3600">
schema_id: distillator_dsl.math.v2.1
schema_version: 1
role_view: Aria proof-route breakdown
</aria_canon_yaml>
<answers_to_athena max_chars="1000">
</answers_to_athena>
<proposed_solution_route max_chars="1200">
</proposed_solution_route>
<route_confidence_and_risks max_chars="900">
confident:
  - unknown
uncertain:
  - unknown
</route_confidence_and_risks>
<request_to_artemis max_chars="700">
</request_to_artemis>"""
    if role == "Artemis" and phase_key in {"peer_exchange_1", "artemis_question_answer", "question_answer"}:
        return """<artemis_canon_yaml max_chars="3600">
schema_id: distillator_dsl.math.v2.1
schema_version: 1
role_view: Artemis audit-route breakdown
</artemis_canon_yaml>
<answers_to_athena max_chars="900">
</answers_to_athena>
<answers_to_aria max_chars="900">
</answers_to_aria>
<route_validation max_chars="1200">
</route_validation>
<route_feedback_for_aria max_chars="900">
</route_feedback_for_aria>"""
    if role == "Artemis" and phase_key in {"forced_solve", "artemis_forced_solve"}:
        return """<entry_status_slots max_chars="450">
source_alignment_status: unknown
case_partition_status: unknown
arithmetic_status: unknown
normalization_status: unknown
sum_expression: none
a_value: none
b_value: none
c_value: none
d_value: none
candidate_answer_integer: none
candidate_confidence: 0
first_blocker: unknown
</entry_status_slots>
<case_contribution_table max_chars="2600">
branch | m_range | equation | valid_roots | contribution
</case_contribution_table>
<normalization_work max_chars="1800">
</normalization_work>
<remaining_blocker_if_any max_chars="900">
</remaining_blocker_if_any>
<solve_problem_now max_chars="4200">
</solve_problem_now>
<final_status_slots max_chars="450">
source_alignment_status: unknown
case_partition_status: unknown
arithmetic_status: unknown
normalization_status: unknown
sum_expression: none
a_value: none
b_value: none
c_value: none
d_value: none
candidate_answer_integer: none
candidate_confidence: 0
first_blocker: unknown
</final_status_slots>"""
    if role == "Artemis":
        return """<aria_claim_audit max_chars="1200">
</aria_claim_audit>
<confidence_backing max_chars="900">
</confidence_backing>
<corrections max_chars="1200">
</corrections>
<solution_continuation max_chars="3200">
</solution_continuation>
<request_to_aria max_chars="700">
</request_to_aria>
<final_status_slots max_chars="450">
source_alignment_status: unknown
route_status: unknown
arithmetic_status: unknown
normalization_status: unknown
candidate_answer_integer: none
candidate_confidence: 0
first_blocker: unknown
</final_status_slots>"""
    if role == "Aria":
        return """<route_agreement_status max_chars="700">
</route_agreement_status>
<confidence_map max_chars="900">
confident:
  - unknown
uncertain:
  - unknown
</confidence_map>
<solution_continuation max_chars="3200">
</solution_continuation>
<open_uncertainties max_chars="900">
</open_uncertainties>
<request_to_artemis max_chars="700">
</request_to_artemis>
<final_status_slots max_chars="450">
source_alignment_status: unknown
route_status: unknown
proof_status: unknown
answer_form_status: unknown
candidate_answer_integer: none
candidate_confidence: 0
first_blocker: unknown
</final_status_slots>"""
    return ""


def wrap_role_body(role_name: str, body: Any) -> str:
    tag = role_payload_tag(role_name)
    return f"<{tag}>{clean_text(body) or '[empty]'}</{tag}>"


# ---------------------------------------------------------------------------
# Candidate and report parsing
# ---------------------------------------------------------------------------

def normalize_candidate_answer(value: Any) -> str:
    text = clean_text(value)
    if not text:
        return "none"
    match = INTEGER_RE.search(text)
    if not match:
        return "none"
    return str(int(match.group(0)))


def answer_satisfies_contract(answer: Any, config: dict[str, Any] | None = None) -> bool:
    token = normalize_candidate_answer(answer)
    if token == "none":
        return True
    cfg = {**DEFAULT_CONFIG, **dict(config or {})}
    value = int(token)
    lower = cfg.get("answer_min")
    upper = cfg.get("answer_max")
    if lower is not None and value < int(lower):
        return False
    if upper is not None and value > int(upper):
        return False
    return True


def emit_final(answer: Any, *, confidence_pct: Any = 0) -> str:
    token = normalize_candidate_answer(answer)
    if token == "none":
        return "none"
    confidence = max(0, min(100, int(confidence_pct or 0)))
    return f"\\boxed{{{token}}}_confidence:{confidence}"


def parse_final_closeout(text: Any, config: dict[str, Any] | None = None) -> dict[str, Any]:
    cleaned = clean_text(text)
    match = BOXED_CONFIDENCE_ONLY_RE.fullmatch(cleaned)
    if not match:
        return {"answer": "none", "confidence_pct": 0, "valid": False}
    answer = str(int(match.group(1)))
    confidence = max(0, min(100, int(match.group(2))))
    contract_valid = answer_satisfies_contract(answer, config)
    return {
        "answer": answer,
        "confidence_pct": confidence if contract_valid else 0,
        "valid": bool(contract_valid),
        "answer_contract_valid": bool(contract_valid),
    }


def boxed_confidence_count(text: Any) -> int:
    return len(list(BOXED_CONFIDENCE_ANYWHERE_RE.finditer(clean_text(text))))


def strip_boxed_confidence_from_report_sections(text: Any) -> str:
    def _strip(match: re.Match[str]) -> str:
        body = BOXED_CONFIDENCE_ANYWHERE_RE.sub("", match.group("body"))
        body = clean_text(body)
        return f"{match.group(1)}\n{body}\n{match.group(3)}"

    return re.sub(
        r"(<report[^>]*>)(?P<body>[\s\S]*?)(</report>)",
        _strip,
        str(text or ""),
        count=0,
        flags=re.IGNORECASE,
    )


def extract_report_verdict(text: Any) -> dict[str, Any]:
    for raw_line in clean_text(text).split("\n")[:12]:
        line = clean_text(raw_line)
        match = REPORT_VERDICT_LINE_RE.fullmatch(line)
        if not match:
            continue
        payload = clean_text(match.group(1))
        answer_match = re.search(
            r"\banswer\s*[:=]\s*([+-]?\d+|none|open|unresolved|unknown)\b",
            payload,
            flags=re.IGNORECASE,
        )
        confidence_match = re.search(r"\bconfidence\s*[:=]\s*(\d{1,3})\b", payload, flags=re.IGNORECASE)
        status_match = re.search(r"\bstatus\s*[:=]\s*([a-z_ -]+)\b", payload, flags=re.IGNORECASE)
        answer = normalize_candidate_answer(answer_match.group(1) if answer_match else "none")
        confidence = max(0, min(100, int(confidence_match.group(1)))) if confidence_match else 0
        status = clean_text(status_match.group(1)).lower() if status_match else ""
        status_open = any(token in status for token in ["open", "block", "unresolved", "fragile", "unknown"])
        return {
            "answer": answer,
            "confidence_pct": confidence,
            "valid": bool(answer != "none" and confidence_match is not None),
            "status": status,
            "status_open": bool(status_open),
            "line": line,
        }
    return {"answer": "none", "confidence_pct": 0, "valid": False, "status": "", "status_open": False, "line": ""}


def strip_structured_lines(text: Any) -> str:
    body: list[str] = []
    for raw_line in clean_text(text).split("\n"):
        line = clean_text(raw_line)
        if not line:
            continue
        if BOXED_CONFIDENCE_ONLY_RE.fullmatch(line):
            continue
        if REPORT_VERDICT_LINE_RE.fullmatch(line):
            continue
        body.append(line)
    return clean_text("\n".join(body))


LEGACY_METADATA_HEADER_RE = re.compile(r"(?im)^\s*(?:#+\s*)?LEGACY[_ -]?METADATA\s*:?\s*$")


def _role_metadata_schema_token(role_name: str) -> str:
    role = canonical_role_name(role_name)
    schema_keys = {
        "Athena": ("ATHENA_SCHEMA_ID", "distillator_dsl.math.v2.1"),
        "Aria": ("ARIA_SCHEMA_ID", "prooflineage_dsl.v2.2"),
        "Artemis": ("ARTEMIS_CONTRACT_ID", "auditlineage_dsl.v2.3"),
    }
    key, fallback = schema_keys[role]
    return str(globals().get(str(key)) or fallback)


def _has_role_yaml_metadata(text: Any, *, role_name: str) -> bool:
    cleaned = clean_text(text)
    if not cleaned:
        return False
    schema_token = _role_metadata_schema_token(role_name)
    return bool(LEGACY_METADATA_HEADER_RE.search(cleaned) and schema_token and schema_token in cleaned)


def report_quality(text: Any, *, role_name: str) -> dict[str, Any]:
    role = canonical_role_name(role_name)
    body = clean_text(re.sub(r"^\s*REPORT TO ATHENA\s*:\s*", "", strip_structured_lines(text), flags=re.IGNORECASE))
    lower = body.lower()
    body_lines = [line for line in body.split("\n") if clean_text(line)]
    missing: list[str] = []
    if len(body) < 80:
        missing.append("report_body")
    if role == "Aria" and not any(token in lower for token in ["proof", "lineage", "lemma", "route", "gap", "invariant", "therefore"]):
        missing.append("proof_substance")
    if role == "Artemis" and not any(token in lower for token in ["audit", "check", "arithmetic", "case", "edge", "boundary", "decomposition", "normalization"]):
        missing.append("audit_substance")
    open_blocker = has_open_blocker_language(body)
    unsupported = has_unsupported_route_language(body)
    format_contradiction = has_answer_format_contradiction(body)
    hard_hits = hard_blocker_hits(body)
    if unsupported:
        open_blocker = True
        missing.append("unsupported_guess_or_partial_route")
    if format_contradiction:
        open_blocker = True
        missing.append("answer_format_contradiction")
    if hard_hits:
        open_blocker = True
        missing.append("hard_blocker_language")
    boxed_only = bool(BOXED_CONFIDENCE_ANYWHERE_RE.search(clean_text(text))) and not body
    if boxed_only:
        missing.append("boxed_only")
    unique_missing = list(dict.fromkeys(missing))
    return {
        "body": body,
        "body_chars": len(body),
        "body_line_count": len(body_lines),
        "boxed_only": bool(boxed_only),
        "hard_invalid": bool(boxed_only or len(body) < 40),
        "open_blocker": bool(open_blocker),
        "unsupported_guess_language": bool(unsupported),
        "answer_format_contradiction": bool(format_contradiction),
        "hard_blocker_hits": list(hard_hits),
        "missing_fields": unique_missing,
        "schema_valid": bool(not boxed_only and not unique_missing),
        "yaml_metadata_present": bool(_has_role_yaml_metadata(text, role_name=role)) if role in {"Aria", "Artemis"} else True,
    }

def parse_role_text(text: Any, *, role_name: str) -> str:
    cleaned = clean_text(text)
    tag = role_payload_tag(role_name)
    match = re.search(rf"<\s*{re.escape(tag)}\s*>(.*?)<\s*/\s*{re.escape(tag)}\s*>", cleaned, re.I | re.S)
    if match:
        cleaned = clean_text(match.group(1))
    return sanitize_model_visible_text(cleaned)


def parse_peer_turn(text: Any, *, role_name: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    role = canonical_role_name(role_name)
    role_text = parse_role_text(text, role_name=role)
    role_text = re.sub(r"^\s*REPORT TO ATHENA\s*:\s*", "", role_text, flags=re.IGNORECASE)
    sections = parse_controller_sections(role_text)
    if role in {"Aria", "Artemis"} and "report_slots" in sections:
        report_slots = parse_key_value_slots(section_body(sections, "report_slots"))
        slot_candidate = normalize_explicit_integer_answer(report_slots.get("candidate_answer_integer", "none"))
        if slot_candidate == "none":
            slot_candidate = integer_from_abcd_slots(report_slots)
        if slot_candidate == "none":
            slot_candidate = normalize_explicit_integer_answer(report_slots.get("candidate_answer", "none"))
        slot_confidence = clamp_confidence_pct(report_slots.get("candidate_confidence", 0), upper=92)
        status = clean_text(report_slots.get("status", "open")).lower()
        blockers = clean_text(report_slots.get("open_blockers", "unknown")).lower()
        required_sections = ["report"]
        missing = [name for name in required_sections if not section_body(sections, name)]
        report_body = section_body(sections, "report")
        report_boxed_count = int(boxed_confidence_count(report_body))
        total_boxed_count = int(boxed_confidence_count(role_text))
        boxed_integer_count = len(list(BOXED_INTEGER_ANYWHERE_RE.finditer(role_text)))
        candidate = str(slot_candidate)
        confidence = int(slot_confidence if candidate != "none" else 0)
        body = clean_text(report_body)
        hard_hits = hard_blocker_hits(body)
        extraction_issues: list[str] = []
        if report_boxed_count:
            extraction_issues.append("boxed_confidence_forbidden_in_peer_report")
        if total_boxed_count:
            extraction_issues.append("peer_report_boxed_confidence_present")
        if boxed_integer_count:
            extraction_issues.append("peer_report_boxed_answer_present")
        open_blocker = bool(
            status != "closed"
            or blockers not in {"none", "no", "closed"}
            or missing
            or hard_hits
            or extraction_issues
        )
        if candidate == "none" or not answer_satisfies_contract(candidate, config):
            candidate = "none"
            confidence = 0
        elif open_blocker:
            confidence = min(int(confidence), 74 if hard_hits else int(confidence))
        canonical_closeout = emit_final(candidate, confidence_pct=confidence) if candidate != "none" else "none"
        boxed_matches_slots = True
        missing_headers = list(missing) + list(extraction_issues)
        if hard_hits:
            missing_headers.append("hard_blocker_language")
        return {
            "role": role,
            "role_text": role_text,
            "body": body,
            "sections": dict(sections),
            "report_slots": dict(report_slots),
            "candidate_answer": candidate,
            "confidence_pct": confidence,
            "explicit_closeout_valid": bool(candidate != "none"),
            "explicit_closeout_answer": str(candidate),
            "explicit_closeout_confidence_pct": int(confidence),
            "explicit_closeout_location": "report_slots",
            "report_verdict_line": "",
            "report_verdict_status_open": bool(open_blocker),
            "report_schema_valid": bool(not missing and not hard_hits and not extraction_issues),
            "report_open_blocker": bool(open_blocker),
            "report_answer_format_contradiction": False,
            "hard_blocker_hits": list(hard_hits),
            "boxed_matches_slots": bool(boxed_matches_slots),
            "slot_candidate_answer": str(slot_candidate),
            "slot_confidence_pct": int(slot_confidence),
            "final_block_valid": False,
            "report_boxed_confidence_count": int(report_boxed_count),
            "final_block_boxed_confidence_count": 0,
            "role_boxed_confidence_count": int(total_boxed_count),
            "answer_extraction_issues": list(extraction_issues),
            "missing_headers": list(dict.fromkeys(missing_headers)),
            "canonical_closeout": "" if canonical_closeout == "none" else canonical_closeout,
        }
    verdict = extract_report_verdict(role_text) if role in {"Aria", "Artemis"} else {"valid": False, "status_open": False, "line": ""}
    explicit = parse_final_closeout(role_text, config)
    candidate = str(explicit.get("answer", "none") or "none")
    confidence = int(explicit.get("confidence_pct", 0) or 0)
    explicit_valid = bool(explicit.get("valid"))
    inferred_from = "boxed" if explicit_valid else "none"

    if not explicit_valid and bool(verdict.get("valid")):
        candidate = str(verdict.get("answer", "none") or "none")
        confidence = int(verdict.get("confidence_pct", 0) or 0)
        explicit_valid = True
        inferred_from = "report_verdict"
    elif not explicit_valid:
        boxed_confidence = BOXED_CONFIDENCE_ANYWHERE_RE.search(role_text)
        boxed = [str(int(match.group(1))) for match in BOXED_INTEGER_ANYWHERE_RE.finditer(role_text)]
        if boxed_confidence:
            candidate = str(int(boxed_confidence.group(1)))
            confidence = int(boxed_confidence.group(2))
            explicit_valid = answer_satisfies_contract(candidate, config)
            inferred_from = "loose_boxed_confidence"
        elif len(set(boxed)) == 1:
            candidate = str(boxed[0])
            confidence_match = CONFIDENCE_VALUE_RE.search(role_text)
            confidence = int(confidence_match.group(1)) if confidence_match else 0
            explicit_valid = answer_satisfies_contract(candidate, config)
            inferred_from = "loose_boxed"

    missing: list[str] = []
    quality = (
        report_quality(role_text, role_name=role)
        if role in {"Aria", "Artemis"}
        else {"body": strip_structured_lines(role_text), "schema_valid": True, "missing_fields": [], "open_blocker": False}
    )
    body = clean_text(quality.get("body") or strip_structured_lines(role_text))
    if role in {"Aria", "Artemis"}:
        if not clean_text(verdict.get("line", "")):
            missing.append("report_verdict")
        missing.extend(str(item) for item in list(quality.get("missing_fields") or []))
        if candidate != "none" and (
            bool(quality.get("hard_invalid"))
            or bool(quality.get("answer_format_contradiction"))
            or not bool(answer_satisfies_contract(candidate, config))
        ):
            candidate = "none"
            confidence = 0
        elif candidate != "none" and (bool(quality.get("open_blocker")) or bool(verdict.get("status_open"))):
            confidence = min(confidence, 58 if bool(quality.get("unsupported_guess_language")) else 74)

    canonical_closeout = emit_final(candidate, confidence_pct=confidence) if candidate != "none" else ""
    return {
        "role": role,
        "role_text": role_text,
        "body": body,
        "candidate_answer": candidate,
        "confidence_pct": confidence,
        "explicit_closeout_valid": bool(explicit_valid),
        "explicit_closeout_answer": str(candidate),
        "explicit_closeout_confidence_pct": int(confidence),
        "explicit_closeout_location": inferred_from,
        "report_verdict_line": str(verdict.get("line", "") or ""),
        "report_verdict_status_open": bool(verdict.get("status_open", False)),
        "report_schema_valid": bool(quality.get("schema_valid", True)) and not missing,
        "report_open_blocker": bool(quality.get("open_blocker", False)) or bool(verdict.get("status_open", False)),
        "report_answer_format_contradiction": bool(quality.get("answer_format_contradiction", False)),
        "hard_blocker_hits": list(quality.get("hard_blocker_hits") or []),
        "missing_headers": list(dict.fromkeys(missing)),
        "canonical_closeout": canonical_closeout,
    }


def parse_athena_turn(
    text: Any,
    *,
    loop_no: int | None = None,
    config: dict[str, Any] | None = None,
    require_final_block: bool = False,
) -> dict[str, Any]:
    _ = loop_no
    parsed = parse_peer_turn(text, role_name="Athena", config=config)
    body = clean_text(parsed.get("body", ""))
    sections = parse_controller_sections(str(parsed.get("role_text", "")))
    candidate_section_name = "selected_candidate" if "selected_candidate" in sections else "current_candidate"
    candidate_slots = parse_key_value_slots(section_body(sections, candidate_section_name)) if candidate_section_name in sections else {}
    candidate = str(parsed.get("candidate_answer", "none") or "none")
    confidence = int(parsed.get("confidence_pct", 0) or 0)
    candidate_source = "parsed_body"
    current_candidate_answer = "none"
    if candidate_slots:
        candidate = normalize_explicit_integer_answer(candidate_slots.get("candidate_answer_integer", "none"))
        if candidate == "none":
            candidate = normalize_explicit_integer_answer(candidate_slots.get("candidate_answer", "none"))
        current_candidate_answer = str(candidate)
        confidence = clamp_confidence_pct(candidate_slots.get("candidate_confidence", 0), upper=99) if candidate != "none" else 0
        candidate_source = str(candidate_section_name)
    final_block = section_body(sections, "final_answer_block")
    final_block_closeout = parse_final_closeout(final_block, config) if final_block else {"valid": False}
    final_block_valid = bool(final_block_closeout.get("valid"))
    if bool(final_block_valid):
        candidate = str(final_block_closeout.get("answer", "none") or "none")
        confidence = int(final_block_closeout.get("confidence_pct", 0) or 0)
        candidate_source = "final_answer_block"
    elif bool(require_final_block):
        candidate = "none"
        confidence = 0
        candidate_source = "missing_required_final_answer_block"
    unsupported = has_unsupported_route_language(body)
    format_contradiction = has_answer_format_contradiction(body)
    if candidate != "none" and not body:
        confidence = min(confidence, 55)
    if candidate != "none" and unsupported:
        confidence = min(confidence, 74)
    if candidate != "none" and format_contradiction:
        confidence = min(confidence, 58)
    parsed.update(
        {
            "confidence_pct": confidence,
            "candidate_answer": str(candidate),
            "explicit_closeout_answer": str(candidate),
            "explicit_closeout_confidence_pct": int(confidence),
            "sections": dict(sections),
            "current_candidate_slots": dict(candidate_slots),
            "current_candidate_answer": str(current_candidate_answer),
            "athena_candidate_section": str(candidate_section_name),
            "athena_candidate_source": str(candidate_source),
            "athena_final_block_valid": bool(final_block_valid),
            "athena_final_block_closeout": dict(final_block_closeout),
            "athena_require_final_block": bool(require_final_block),
            "athena_body_chars": len(body),
            "athena_unsupported_guess_language": bool(unsupported),
            "athena_answer_format_contradiction": bool(format_contradiction),
        }
    )
    return parsed


# ---------------------------------------------------------------------------
# CB7 compact prompt bridge
# ---------------------------------------------------------------------------

def render_state(state: dict[str, Any], *, max_report_chars: int = 420) -> str:
    peer_reports = dict(state.get("peer_reports") or {})
    fields = [
        f"loop: {int(state.get('loop_no', 0) or 0)}",
        f"athena_candidate: {state.get('athena_candidate_answer', 'none')}",
        f"athena_confidence: {int(state.get('athena_confidence_pct', 0) or 0)}",
        f"peer_validation: {state.get('peer_validation_status', 'not_started')}",
    ]
    objections = [clean_text(item) for item in list(state.get("open_objections") or []) if clean_text(item)]
    if objections:
        fields.append(f"open_objection: {truncate_text(objections[0], 160)}")
    if clean_text(peer_reports.get("Aria")):
        fields.append(f"aria_report: {truncate_text(peer_reports.get('Aria'), max_report_chars)}")
    if clean_text(peer_reports.get("Artemis")):
        fields.append(f"artemis_report: {truncate_text(peer_reports.get('Artemis'), max_report_chars)}")
    return "\n".join(f"- {item}" for item in fields)


def build_role_prompt(
    *,
    problem_text: str,
    role_name: str,
    phase: str,
    state: dict[str, Any],
    athena_context: str = "",
    counterpart_last: str = "",
    counterpart_context: str = "",
    trace_text: str = "",
) -> str:
    role = canonical_role_name(role_name)
    phase_name = clean_text(phase).lower()
    if counterpart_context and not counterpart_last:
        counterpart_last = str(counterpart_context)
    build_payload_prompt_fn = globals().get("build_model_payload_prompt")
    make_prompt_state_fn = globals().get("make_prompt_state")
    build_config_fn = globals().get("build_loop_mechanics_config")
    if callable(build_payload_prompt_fn):
        if role == "Athena" and phase_name == "synthesis":
            route = {"role": "Athena", "stage": "synthesis", "phase": "athena_synthesis", "loop_no": int(state.get("loop_no", 0) or 0)}
        elif role == "Athena":
            route = {"role": "Athena", "stage": "solve", "phase": "athena_open", "loop_no": int(state.get("loop_no", 0) or 0)}
        elif phase_name in {"report", "peer_report"}:
            route = {
                "role": role,
                "stage": "peer_report",
                "phase": "peer_report",
                "loop_no": int(state.get("loop_no", 0) or 0),
                "completed_reasoning_exchanges": int(dict(state.get("config") or {}).get("inner_total_exchanges", 0) or 0),
                "inner_total_exchanges": int(dict(state.get("config") or {}).get("inner_total_exchanges", 0) or 0),
                "athena_message": str(athena_context or state.get("athena_last_message", "")),
                "counterpart_last": str(counterpart_last),
            }
        else:
            route = {
                "role": role,
                "stage": "peer_reasoning",
                "phase": "peer_exchange",
                "loop_no": int(state.get("loop_no", 0) or 0),
                "exchange_no": int(state.get("exchange_no", 0) or 0),
                "inner_total_exchanges": int(dict(state.get("config") or {}).get("inner_total_exchanges", 0) or 0),
                "athena_message": str(athena_context or state.get("athena_last_message", "")),
                "counterpart_last": str(counterpart_last),
            }
        prompt_state_view = (
            make_prompt_state_fn(dict(state), build_config_fn(globals()))
            if callable(make_prompt_state_fn) and callable(build_config_fn)
            else dict(state)
        )
        return build_payload_prompt_fn(
            problem_text=str(problem_text),
            prompt_state=prompt_state_view,
            route=dict(route),
            trace_text=str(trace_text),
        )

    lines = [
        "ROLE",
        role,
        "",
        "STATE",
        render_state(dict(state), max_report_chars=360),
        "",
        "INSTRUCTIONS",
        "Complete the supplied tags in order. Keep each section concise.",
        "",
        "CONTEXT",
        "PROBLEM\n" + (clean_text(problem_text) or "[empty]"),
        "",
        "OUTPUT",
        wrap_role_body(role, render_section_scaffold(role, phase_name)),
    ]
    return "\n".join(lines).strip()


def build_final_prompt(
    *,
    problem_text: str,
    state: dict[str, Any] | None = None,
    prompt_state: dict[str, Any] | None = None,
    chosen_answer: str = "",
) -> str:
    _ = problem_text
    active_state = dict(state if state is not None else prompt_state or {})
    selected = normalize_candidate_answer(clean_text(chosen_answer) or "none")
    selected_confidence = clamp_confidence_pct(
        dict(active_state.get("closeout_resolution") or {}).get(
            "confidence_pct",
            active_state.get("athena_confidence_pct", active_state.get("confidence_pct", 0)),
        ),
        default=0,
    )
    state_renderer = globals().get("_render_state_for_prompt")
    state_text = (
        state_renderer(active_state)
        if callable(state_renderer)
        else render_state(active_state, max_report_chars=360)
    )
    if selected == "none":
        synthesis_text = clean_text(active_state.get("athena_last_message", ""))
        synthesis_tail = synthesis_text[-2200:].strip() if len(synthesis_text) > 2200 else synthesis_text
        return "\n".join(
            [
                "ROLE",
                "Athena",
                "",
                "PHASE",
                "finalization",
                "",
                "STATE",
                state_text,
                "",
                "SYNTHESIS_TAIL",
                synthesis_tail or "none",
                "",
                "FINALIZATION_CONTRACT",
                CLOSED_BOOK_REASONING_CONTRACT,
                "Mandatory final answer turn. Re-adjudicate from source facts, peer reports, and the synthesis tail.",
                "Decide from source facts, the first mathematical divergence, and corrected arithmetic.",
                "Choose final confidence from the visible adjudication; do not copy a prior controller/rubric confidence by default.",
                "Return only these two sections:",
                "<final_answer_block max_chars=\"80\">",
                "\\boxed{<integer>}_confidence:<0-100 integer>",
                "</final_answer_block>",
                "<adjudication_certificate max_chars=\"500\">",
                "first divergence; corrected check; rejected candidates",
                "</adjudication_certificate>",
            ]
        ).strip()
    return "\n".join(
        [
            "ROLE",
            "Athena",
            "",
            "PHASE",
            "finalization",
            "",
            "STATE",
            state_text,
            "",
            "FINALIZATION_CONTRACT",
            CLOSED_BOOK_REASONING_CONTRACT,
            "Mandatory final answer turn. Use the selected integer unless the adjudication certificate finds a concrete contradiction.",
            "Choose final confidence from the visible decisive check; do not copy prior controller confidence by default.",
            "Return only these two sections:",
            "<final_answer_block max_chars=\"80\">",
            "\\boxed{<integer>}_confidence:<0-100 integer>",
            "</final_answer_block>",
            "<adjudication_certificate max_chars=\"500\">",
            "selected candidate; decisive check; rejected alternatives if any",
            "</adjudication_certificate>",
            f"selected_candidate: {selected}",
            f"prior_controller_confidence: {int(selected_confidence)}",
            f"Required final integer: {selected}",
        ]
    ).strip()

def build_config(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = {**DEFAULT_CONFIG, **dict(overrides or {})}
    for key in [
        "max_big_loops",
        "inner_total_exchanges",
        "min_big_loop_for_closeout",
        "closeout_confidence_pct",
        "athena_open_max_tokens",
        "peer_exchange_max_tokens",
        "peer_report_max_tokens",
        "athena_synthesis_max_tokens",
        "athena_final_max_tokens",
    ]:
        cfg[key] = int(cfg[key])
    return cfg


def new_controller_state(problem_text: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "problem_text": clean_text(problem_text),
        "config": build_config(config),
        "loop_no": 0,
        "athena_last_message": "",
        "athena_candidate_answer": "none",
        "athena_confidence_pct": 0,
        "peer_reports": {"Aria": "", "Artemis": ""},
        "peer_report_meta": {"Aria": {}, "Artemis": {}},
        "peer_reasoning_log": [],
        "recent_summary": [],
        "peer_validation_status": "not_started",
        "open_objections": ["Peer validation has not started."],
        "closeout_resolution": {},
    }


def report_signature(text: str) -> str:
    lowered = clean_text(text).lower()
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return " ".join(lowered.split())


def report_similarity(left: str, right: str) -> float:
    a = report_signature(left)
    b = report_signature(right)
    if not a or not b:
        return 0.0
    return float(SequenceMatcher(None, a, b).ratio())


def peer_report_meta(role_name: str, report_text: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    parsed = parse_peer_turn(report_text, role_name=role_name, config=config)
    candidate = str(parsed.get("candidate_answer", "none") or "none")
    schema_valid = bool(parsed.get("report_schema_valid", False))
    open_blocker = bool(parsed.get("report_open_blocker", False))
    if not schema_valid or open_blocker:
        candidate = "none"
    return {
        "role": canonical_role_name(role_name),
        "text": clean_text(report_text),
        "candidate_exact_integer": candidate,
        "candidate_is_exact_integer": bool(candidate != "none"),
        "confidence_pct": int(parsed.get("confidence_pct", 0) or 0) if candidate != "none" else 0,
        "schema_valid": bool(schema_valid),
        "open_blocker": bool(open_blocker),
        "answer_format_contradiction": bool(parsed.get("report_answer_format_contradiction", False)),
        "missing_headers": list(parsed.get("missing_headers") or []),
        "verdict_line": str(parsed.get("report_verdict_line", "") or ""),
        "signature": report_signature(report_text),
    }


def refresh_peer_validation_state(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = build_config(config or state.get("config"))
    reports = dict(state.get("peer_reports") or {})
    aria = peer_report_meta("Aria", str(reports.get("Aria", "")), cfg)
    artemis = peer_report_meta("Artemis", str(reports.get("Artemis", "")), cfg)
    aria_answer = str(aria.get("candidate_exact_integer", "none") or "none")
    artemis_answer = str(artemis.get("candidate_exact_integer", "none") or "none")
    athena_answer = normalize_candidate_answer(state.get("athena_candidate_answer", "none"))
    peers_align = bool(aria_answer != "none" and aria_answer == artemis_answer)
    trio_align = bool(peers_align and athena_answer == aria_answer)
    min_peer_conf = min(int(aria.get("confidence_pct", 0) or 0), int(artemis.get("confidence_pct", 0) or 0))
    reports_distinct = bool(aria.get("signature")) and bool(artemis.get("signature")) and report_similarity(
        str(aria.get("text", "")), str(artemis.get("text", ""))
    ) < 0.90
    schemas_valid = bool(aria.get("schema_valid")) and bool(artemis.get("schema_valid"))
    objections: list[str] = []
    for label, meta in [("Aria", aria), ("Artemis", artemis)]:
        if not clean_text(meta.get("text")):
            objections.append(f"{label} report is missing.")
        if bool(meta.get("missing_headers")):
            objections.append(f"{label} report missing: {', '.join(list(meta.get('missing_headers') or []))}.")
        if bool(meta.get("open_blocker")):
            objections.append(f"{label} report has an open blocker.")
        if bool(meta.get("answer_format_contradiction")):
            objections.append(f"{label} report flags an answer-format contradiction.")
    if not reports_distinct:
        objections.append("Peer reports are not distinct enough for independent validation.")
    if not peers_align:
        objections.append("Aria and Artemis do not agree on a validated exact integer.")
    elif not trio_align:
        objections.append("Athena has not reconciled to the peer-validated exact integer.")
    if min_peer_conf < int(cfg["closeout_confidence_pct"]):
        objections.append(f"Peer confidence is below {int(cfg['closeout_confidence_pct'])}.")
    validation_status = "confidence_aligned" if trio_align and schemas_valid and reports_distinct and not objections else "open"
    state["peer_report_meta"] = {"Aria": aria, "Artemis": artemis}
    state["peer_validation_status"] = validation_status
    state["open_objections"] = objections
    return {
        "aria_meta": aria,
        "artemis_meta": artemis,
        "peers_align": bool(peers_align),
        "trio_align": bool(trio_align),
        "reports_distinct": bool(reports_distinct),
        "schemas_valid": bool(schemas_valid),
        "peer_min_confidence": int(min_peer_conf),
        "submission_ready": bool(validation_status == "confidence_aligned"),
        "open_objections": list(objections),
    }


def strict_closeout_ready(state: dict[str, Any], config: dict[str, Any] | None = None) -> dict[str, Any]:
    cfg = build_config(config or state.get("config"))
    outcome = refresh_peer_validation_state(state, cfg)
    candidate = normalize_candidate_answer(state.get("athena_candidate_answer", "none"))
    confidence = int(state.get("athena_confidence_pct", 0) or 0)
    ready = bool(
        candidate != "none"
        and outcome.get("submission_ready")
        and confidence >= int(cfg["closeout_confidence_pct"])
        and answer_satisfies_contract(candidate, cfg)
    )
    return {
        "ready": bool(ready),
        "answer": candidate if ready else "none",
        "confidence_pct": confidence if ready else 0,
        "reason": "strict_consensus" if ready else "not_strict_consensus",
        "outcome": outcome,
    }


def parse_solve_turn(text: Any, *, role_name: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    role = canonical_role_name(role_name)
    role_text = parse_role_text(text, role_name=role)
    sections = parse_controller_sections(role_text)
    slots = parse_key_value_slots(section_body(sections, "final_status_slots"))
    if not slots:
        slots = parse_key_value_slots(section_body(sections, "entry_status_slots"))
    if not slots:
        slots = parse_key_value_slots(section_body(sections, "status_slots"))
    candidate = normalize_explicit_integer_answer(slots.get("candidate_answer_integer", "none"))
    if candidate == "none":
        candidate = integer_from_abcd_slots(slots)
    if candidate == "none":
        candidate = normalize_explicit_integer_answer(slots.get("candidate_answer", "none"))
    confidence = clamp_confidence_pct(slots.get("candidate_confidence", 0), upper=92) if candidate != "none" else 0
    status_values = [clean_text(value).lower() for key, value in slots.items() if key.endswith("_status")]
    first_blocker = clean_text(slots.get("first_blocker", "unknown")).lower()
    body = clean_text("\n\n".join(section_body(sections, name) for name in sections if section_body(sections, name)))
    hard_hits = hard_blocker_hits(body)
    open_blocker = bool(
        candidate == "none"
        or first_blocker not in {"none", "no", "closed"}
        or any(value in {"unknown", "open", "pending", "failed"} for value in status_values)
        or bool(hard_hits)
    )
    if open_blocker or not answer_satisfies_contract(candidate, config):
        candidate = "none"
        confidence = 0
    diagnostic_text = "\n".join(
        section_body(sections, name)
        for name in ["normalization_work", "normalization_check", "solve_problem_now", "case_contribution_table"]
        if section_body(sections, name)
    )
    diagnostic_candidate = "none"
    for pattern in [
        r"a_plus_b_plus_c_plus_d\s*:\s*([+-]?\d+)",
        r"Final\s+Calculation\s*:.*?=\s*([+-]?\d+)",
        r"Final\s+Answer\s*:.*?([+-]?\d+)\s*$",
    ]:
        match = re.search(pattern, diagnostic_text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if match:
            diagnostic_candidate = normalize_candidate_answer(match.group(1))
            if diagnostic_candidate != "none":
                break
    return {
        "role": role,
        "role_text": role_text,
        "sections": dict(sections),
        "status_slots": dict(slots),
        "sum_expression": clean_text(slots.get("sum_expression", "none")) or "none",
        "a_value": normalize_explicit_integer_answer(slots.get("a_value", "none")),
        "b_value": normalize_explicit_integer_answer(slots.get("b_value", "none")),
        "c_value": normalize_explicit_integer_answer(slots.get("c_value", "none")),
        "d_value": normalize_explicit_integer_answer(slots.get("d_value", "none")),
        "candidate_answer_integer": str(candidate),
        "candidate_answer": str(candidate),
        "confidence_pct": int(confidence),
        "diagnostic_candidate_answer": str(diagnostic_candidate),
        "hard_blocker_hits": list(hard_hits),
        "open_blocker": bool(open_blocker),
        "body": body,
    }


def parse_peer_report(text: Any, *, role_name: str, config: dict[str, Any] | None = None) -> str:
    parsed = dict(parse_peer_turn(text, role_name=role_name, config=config))
    rebuilt: list[str] = []
    body = clean_text(parsed.get("body", ""))
    body = re.sub(r"^\s*REPORT TO ATHENA\s*:\s*", "", body, flags=re.IGNORECASE)
    if body:
        rebuilt.append(body)
    return clean_text("\n".join(rebuilt))


def format_controller_report(text: Any, *, role_name: str) -> str:
    if parse_controller_sections(text):
        return clean_text(text)
    payload = parse_peer_report(text, role_name=role_name)
    payload = clean_text(payload) or "[missing report payload]"
    return str(payload)


def parse_final_token(text: Any) -> str:
    parsed = dict(parse_final_closeout(text))
    token = normalize_candidate_answer(parsed.get("answer", "none"))
    return str(token if token != "none" else "none")


def classify_peer_report(text: Any) -> dict[str, Any]:
    cleaned = clean_text(text)
    lowered = cleaned.lower()
    challenge_hits = sum(
        1
        for token in ["objection", "challenge", "reject", "fail", "invalid", "contradiction", "error", "blocker"]
        if token in lowered
    )
    support_hits = sum(
        1
        for token in ["closed", "confirmed", "consistent", "resolved", "validated", "supports"]
        if token in lowered
    )
    if challenge_hits > support_hits:
        return {"stance": "challenge", "score": -1}
    if support_hits > challenge_hits:
        return {"stance": "support", "score": 1}
    return {"stance": "neutral", "score": 0}


def _session_for_role(sessions: dict[str, Any], role_name: str) -> Any:
    role = canonical_role_name(role_name)
    for key in [role, role.lower(), {"Athena": "solver", "Aria": "agent", "Artemis": "clerk"}[role]]:
        if key in sessions:
            return sessions[key]
    raise KeyError(f"missing session for {role}")


def _response_text(payload: dict[str, Any]) -> str:
    for key in ["visible_text", "raw_text", "output_text", "response_text", "text"]:
        value = clean_text(payload.get(key))
        if value:
            return value
    return ""


def safe_generation_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    allowed_keys = [
        "usage",
        "prompt_tokens_used",
        "generated_tokens",
        "total_tokens_used",
        "finish_reason",
        "think_tags_detected",
    ]
    for key in allowed_keys:
        if key in payload:
            safe[key] = payload.get(key)
    if "usage" not in safe:
        usage = {
            key: payload.get(key)
            for key in ["prompt_tokens", "completion_tokens", "total_tokens"]
            if key in payload
        }
        if usage:
            safe["usage"] = usage
    return safe


def run_model_turn(
    *,
    role_name: str,
    phase: str,
    session: Any,
    prompt: str,
    generation_profile: dict[str, Any],
    turn_no: int,
    reset_session_each_turn: bool = True,
) -> dict[str, Any]:
    started = time.perf_counter()
    if reset_session_each_turn and hasattr(session, "reset_session"):
        session.reset_session()
    payload = dict(session.execute_user_turn(str(prompt), dict(generation_profile or {})) or {})
    raw = _response_text(payload)
    think_tags = has_visible_think_tags(raw)
    visible = clean_text(raw) if think_tags else (sanitize_model_visible_text(raw) or "[controller-suppressed prompt echo]")
    return {
        "turn": int(turn_no),
        "speaker": canonical_role_name(role_name),
        "phase": clean_text(phase),
        "ok": True,
        "prompt_chars": int(len(str(prompt))),
        "raw_visible_chars": int(len(raw)),
        "visible_text": visible,
        "prompt_echo_suppressed": bool(clean_text(raw) != clean_text(visible)),
        "no_think_violation": bool(think_tags),
        "generation_metadata": {**safe_generation_metadata(payload), "think_tags_detected": bool(think_tags)},
        "wall_seconds": round(float(time.perf_counter() - started), 4),
    }


def _generation_for(role_name: str, generation_profiles: dict[str, Any], max_tokens: int) -> dict[str, Any]:
    role = canonical_role_name(role_name)
    generation = {**DEFAULT_GENERATION.get(role, {}), **dict(generation_profiles.get(role, {}) or {})}
    generation["max_tokens"] = min(int(generation.get("max_tokens", max_tokens) or max_tokens), int(max_tokens))
    stop = generation.get("stop")
    stop_values = [stop] if isinstance(stop, str) else [str(item) for item in list(stop or []) if str(item)]
    generation["stop"] = list(dict.fromkeys([*stop_values, "\nSystem:", "\nDeveloper:", "\nUser:", "\n<final_answer>"]))
    return generation


def run_cb07_protocol(
    problem_text: str,
    *,
    sessions: dict[str, Any],
    generation_profiles: dict[str, Any] | None = None,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cfg = build_config(config)
    generations = dict(generation_profiles or {})
    state = new_controller_state(problem_text, cfg)
    transcript: list[dict[str, Any]] = []
    turn_no = 0
    status = "loop_exhausted_without_strict_consensus"
    final_answer_text = "none"
    submission_answer = "none"

    for loop_no in range(1, int(cfg["max_big_loops"]) + 1):
        state["loop_no"] = int(loop_no)
        state["peer_reports"] = {"Aria": "", "Artemis": ""}

        athena_prompt = build_role_prompt(problem_text=problem_text, role_name="Athena", phase="open", state=state)
        turn_no += 1
        turn = run_model_turn(
            role_name="Athena",
            phase="athena_open",
            session=_session_for_role(sessions, "Athena"),
            prompt=athena_prompt,
            generation_profile=_generation_for("Athena", generations, int(cfg["athena_open_max_tokens"])),
            turn_no=turn_no,
            reset_session_each_turn=bool(cfg["reset_session_each_turn"]),
        )
        transcript.append(turn)
        parsed = parse_athena_turn(turn["visible_text"], config=cfg)
        state["athena_last_message"] = str(parsed.get("role_text", ""))
        if str(parsed.get("candidate_answer", "none")) != "none":
            state["athena_candidate_answer"] = str(parsed.get("candidate_answer"))
            state["athena_confidence_pct"] = int(parsed.get("confidence_pct", 0) or 0)

        last_peer = {"Aria": "", "Artemis": ""}
        for exchange_no in range(1, int(cfg["inner_total_exchanges"]) + 1):
            for role in ["Aria", "Artemis"]:
                counterpart = "Artemis" if role == "Aria" else "Aria"
                prompt = build_role_prompt(
                    problem_text=problem_text,
                    role_name=role,
                    phase=f"peer_exchange_{exchange_no}",
                    state=state,
                    athena_context=str(state.get("athena_last_message", "")),
                    counterpart_context=str(last_peer.get(counterpart, "")),
                    trace_text="\n".join(
                        f"{row.get('speaker')}: {truncate_text(row.get('text'), 600)}"
                        for row in list(state.get("peer_reasoning_log") or [])[-8:]
                    ),
                )
                turn_no += 1
                turn = run_model_turn(
                    role_name=role,
                    phase=f"{role.lower()}_exchange_{exchange_no}",
                    session=_session_for_role(sessions, role),
                    prompt=prompt,
                    generation_profile=_generation_for(role, generations, int(cfg["peer_exchange_max_tokens"])),
                    turn_no=turn_no,
                    reset_session_each_turn=bool(cfg["reset_session_each_turn"]),
                )
                transcript.append(turn)
                last_peer[role] = str(turn["visible_text"])
                state["peer_reasoning_log"].append(
                    {"speaker": role, "exchange": int(exchange_no), "text": str(turn["visible_text"])}
                )

        for role in ["Aria", "Artemis"]:
            prompt = build_role_prompt(
                problem_text=problem_text,
                role_name=role,
                phase="peer_report",
                state=state,
                athena_context=str(state.get("athena_last_message", "")),
                counterpart_context=str(last_peer.get("Artemis" if role == "Aria" else "Aria", "")),
                trace_text="\n".join(
                    f"{row.get('speaker')}: {truncate_text(row.get('text'), 600)}"
                    for row in list(state.get("peer_reasoning_log") or [])[-10:]
                ),
            )
            turn_no += 1
            turn = run_model_turn(
                role_name=role,
                phase=f"{role.lower()}_report",
                session=_session_for_role(sessions, role),
                prompt=prompt,
                generation_profile=_generation_for(role, generations, int(cfg["peer_report_max_tokens"])),
                turn_no=turn_no,
                reset_session_each_turn=bool(cfg["reset_session_each_turn"]),
            )
            transcript.append(turn)
            state["peer_reports"][role] = str(turn["visible_text"])

        refresh_peer_validation_state(state, cfg)

        synth_prompt = build_role_prompt(problem_text=problem_text, role_name="Athena", phase="synthesis", state=state)
        turn_no += 1
        turn = run_model_turn(
            role_name="Athena",
            phase="athena_synthesis",
            session=_session_for_role(sessions, "Athena"),
            prompt=synth_prompt,
            generation_profile=_generation_for("Athena", generations, int(cfg["athena_synthesis_max_tokens"])),
            turn_no=turn_no,
            reset_session_each_turn=bool(cfg["reset_session_each_turn"]),
        )
        transcript.append(turn)
        parsed = parse_athena_turn(turn["visible_text"], config=cfg, require_final_block=True)
        if str(parsed.get("candidate_answer", "none")) != "none":
            state["athena_candidate_answer"] = str(parsed.get("candidate_answer"))
            state["athena_confidence_pct"] = int(parsed.get("confidence_pct", 0) or 0)
        refresh_peer_validation_state(state, cfg)

        gate = strict_closeout_ready(state, cfg)
        if bool(gate.get("ready")):
            final_answer_text = emit_final(gate["answer"], confidence_pct=gate["confidence_pct"])
            submission_answer = str(gate["answer"])
            status = "closed_out_exact_integer_consensus_strict_confidence_controller_slots"
            state["closeout_resolution"] = {
                "mode": "strict_consensus",
                "answer": submission_answer,
                "confidence_pct": int(gate["confidence_pct"]),
                "supporting_roles": ["Athena", "Aria", "Artemis"],
            }
            break

        state["recent_summary"] = list(state.get("recent_summary") or [])[-12:]
        state["peer_reasoning_log"] = list(state.get("peer_reasoning_log") or [])[-6:]

    transcript_text = "\n\n".join(
        f"<{role_payload_tag(row['speaker'])}>\n{row['visible_text']}\n</{role_payload_tag(row['speaker'])}>"
        for row in transcript
    )
    return {
        "revision": CB07_FINAL_REVISION,
        "status": status,
        "verified": bool(status.startswith("closed_out_")),
        "submission_answer": submission_answer,
        "final_answer_text": final_answer_text,
        "turn_index": int(turn_no),
        "loop_index": int(state.get("loop_no", 0) or 0),
        "peer_validation_ready": bool(state.get("peer_validation_status") == "confidence_aligned"),
        "state": state,
        "transcript": transcript,
        "transcript_text": transcript_text,
    }


__all__ = [
    "CB07_FINAL_REVISION",
    "ATHENA_SETUP_YAML",
    "build_config",
    "new_controller_state",
    "build_role_prompt",
    "build_final_prompt",
    "run_cb07_protocol",
    "sanitize_model_visible_text",
    "sanitize_transcript_visible_text",
    "has_visible_think_tags",
    "hard_blocker_hits",
    "has_hard_blocker_language",
    "parse_controller_sections",
    "parse_key_value_slots",
    "section_body",
    "required_sections_for",
    "section_contract_diagnostics",
    "section_contract_valid",
    "render_section_scaffold",
    "wrap_role_body",
    "parse_peer_report",
    "format_controller_report",
    "parse_solve_turn",
    "parse_final_token",
    "classify_peer_report",
    "parse_peer_turn",
    "parse_athena_turn",
    "parse_final_closeout",
    "emit_final",
    "refresh_peer_validation_state",
    "strict_closeout_ready",
    "normalize_candidate_answer",
    "normalize_explicit_integer_answer",
    "integer_from_abcd_slots",
    "answer_satisfies_contract",
]

"""## 07.25 Turn Discipline Schemas

"""

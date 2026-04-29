# Auto-extracted by Aster from AENAIMO260_0_2_3_FINAL_CB5_CB8_CLOSED_BOOK_WORKING_20260427.ipynb
# Source cell: 34 / CB07.5 - Dynamic Turn Discipline
# Intended use: replace/run this CB cell in notebook order.

"""## 07.5 - Dynamic Turn Discipline

All mutable, phase-specific prompt construction lives here. CB7 keeps parser and
controller invariants; CB7.25 keeps immutable schema contracts. This block owns
turn discipline, bounded context, role handoffs, and finalization prompts.

"""

from __future__ import annotations

import json
import re
import time
from difflib import SequenceMatcher
from typing import Any


CB07_5_DYNAMIC_REVISION = "2026-04-29-cb075-strict-confidence-loop-closeout-v1.5.2"

MAX_BIG_LOOPS_DEFAULT = 3
MIN_BIG_LOOP_FOR_CLOSEOUT_DEFAULT = 1
INNER_TOTAL_EXCHANGES_DEFAULT = 3
INNER_REASONING_EXCHANGES_DEFAULT = 3
BOXED_CONFIDENCE_GATE_PCT_DEFAULT = 85
ATHENA_OPEN_MAX_TOKENS_DEFAULT = 5200
PEER_EXCHANGE_MAX_TOKENS_DEFAULT = 3400
PEER_REPORT_MAX_TOKENS_DEFAULT = 1500
ATHENA_SYNTHESIS_MAX_TOKENS_DEFAULT = 3800
ATHENA_FINAL_MAX_TOKENS_DEFAULT = 768
ATHENA_REPAIR_ATTEMPTS_DEFAULT = 1
PEER_REPAIR_ATTEMPTS_DEFAULT = 1
FINAL_REPAIR_ATTEMPTS_DEFAULT = 1
TRACE_CHARS_DEFAULT = 1100
REPORT_TRACE_CHARS_DEFAULT = 700
PEER_REPORT_STATE_CHARS_DEFAULT = 700
ATHENA_PEER_REPORT_CHARS_DEFAULT = 900

CLOSED_BOOK_REASONING_CONTRACT = (
    "This is a closed-book reasoning run. Do not request or claim Python, calculators, web search, "
    "external tools, scripts, or hidden computation. If verification is needed, perform it visibly "
    "by hand inside the transcript."
)


ROLE_ALIASES_LOCAL = {
    "athena": "Athena",
    "solver": "Athena",
    "aria": "Aria",
    "agent": "Aria",
    "artemis": "Artemis",
    "clerk": "Artemis",
}

ROLE_TAGS_LOCAL = {"Athena": "athena", "Aria": "aria", "Artemis": "artemis"}

VISIBLE_THINK_TAG_RE_LOCAL = re.compile(r"</?\s*think(?:ing)?\b[^>]*>", re.IGNORECASE)
LEGACY_METADATA_HEADER_RE_LOCAL = re.compile(r"(?im)^\s*(?:#+\s*)?LEGACY[_ -]?METADATA\s*:?\s*$")


def clean_text(value: Any) -> str:
    cleaner = globals().get("clean_dialogue_text")
    if callable(cleaner):
        try:
            return str(cleaner(str(value or ""))).strip()
        except Exception:
            pass
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def canonical_role_name(value: str) -> str:
    resolver = globals().get("role_name_for_runtime_label")
    if callable(resolver):
        try:
            resolved = clean_text(resolver(str(value), default=""))
            if resolved in ROLE_TAGS_LOCAL:
                return resolved
        except Exception:
            pass
    token = clean_text(value).lower()
    if token in ROLE_ALIASES_LOCAL:
        return ROLE_ALIASES_LOCAL[token]
    cleaned = clean_text(value)
    if cleaned in ROLE_TAGS_LOCAL:
        return cleaned
    display_names = globals().get("ROLE_DISPLAY_NAMES")
    if isinstance(display_names, dict):
        for runtime_label, display_name in display_names.items():
            if token == str(runtime_label).lower() or cleaned == str(display_name):
                return str(display_name)
    raise KeyError(f"unknown CB07 role: {value!r}")


def _role_metadata_schema_token(role_name: str) -> str:
    role = canonical_role_name(role_name)
    schema_keys = {
        "Athena": ("ATHENA_SCHEMA_ID", "distillator_dsl.math.v2.1"),
        "Aria": ("ARIA_SCHEMA_ID", "prooflineage_dsl.v2.2"),
        "Artemis": ("ARTEMIS_CONTRACT_ID", "auditlineage_dsl.v2.3"),
    }
    key, fallback = schema_keys.get(role, ("", "unknown_schema"))
    return str(globals().get(key) or fallback)


def has_visible_think_tags(value: Any) -> bool:
    return bool(VISIBLE_THINK_TAG_RE_LOCAL.search(str(value or "")))


def safe_generation_metadata(payload: dict[str, Any]) -> dict[str, Any]:
    data = dict(payload or {})
    safe: dict[str, Any] = {}
    for key in [
        "usage",
        "prompt_tokens_used",
        "generated_tokens",
        "total_tokens_used",
        "finish_reason",
        "think_tags_detected",
    ]:
        if key in data:
            safe[key] = data.get(key)
    if "usage" not in safe:
        usage = {
            key: data.get(key)
            for key in ["prompt_tokens", "completion_tokens", "total_tokens"]
            if key in data
        }
        if usage:
            safe["usage"] = usage
    return safe


def _has_role_yaml_metadata(text: Any, *, role_name: str) -> bool:
    cleaned = clean_text(text)
    if not cleaned:
        return False
    schema_token = _role_metadata_schema_token(role_name)
    return bool(LEGACY_METADATA_HEADER_RE_LOCAL.search(cleaned) and schema_token in cleaned)


def render_state(state: dict[str, Any], *, max_report_chars: int = 420) -> str:
    st = dict(state or {})
    peer_reports = dict(st.get("peer_reports") or {})
    fields = [
        f"loop: {int(st.get('loop_no', 0) or 0)}",
        f"athena_candidate: {st.get('athena_candidate_answer', 'none')}",
        f"athena_confidence: {int(st.get('athena_confidence_pct', 0) or 0)}",
        f"peer_validation: {st.get('peer_validation_status', 'not_started')}",
    ]
    objections = [clean_text(item) for item in list(st.get("open_objections") or []) if clean_text(item)]
    if objections:
        fields.append(f"open_objection: {_truncate_prompt_text(objections[0], max_chars=160)}")
    for role in ["Aria", "Artemis"]:
        report = clean_text(peer_reports.get(role))
        if report:
            fields.append(f"{role.lower()}_report: {_truncate_prompt_text(report, max_chars=max_report_chars)}")
    return "\n".join(f"- {item}" for item in fields)


def _clamp_int(value: Any, low: int, high: int, default: int) -> int:
    try:
        parsed = int(value)
    except Exception:
        parsed = int(default)
    return max(int(low), min(int(high), int(parsed)))


def _coerce_int_local(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return int(default)


def _truncate_prompt_text(value: Any, *, max_chars: int) -> str:
    text = clean_text(value)
    limit = max(0, int(max_chars))
    if limit <= 0 or len(text) <= limit:
        return text
    if limit <= 16:
        return text[:limit]
    return text[: max(0, limit - 15)].rstrip() + " ... [trimmed]"


def _section_body_from_text(text: Any, section_name: str) -> str:
    cleaned = clean_text(text)
    if not cleaned:
        return ""
    section_parser = globals().get("parse_controller_sections")
    section_getter = globals().get("section_body")
    if callable(section_parser) and callable(section_getter):
        try:
            sections = dict(section_parser(cleaned) or {})
            value = clean_text(section_getter(sections, str(section_name)))
            if value:
                return value
        except Exception:
            pass
    pattern = rf"<\s*{re.escape(str(section_name))}\b[^>]*>([\s\S]*?)<\s*/\s*{re.escape(str(section_name))}\s*>"
    match = re.search(pattern, cleaned, flags=re.IGNORECASE)
    return clean_text(match.group(1)) if match else ""


def _capture_athena_routing_loads(state: dict[str, Any], athena_text: Any) -> dict[str, Any]:
    canon_yaml = _section_body_from_text(athena_text, "canon_problem_yaml")
    given_ask_route_map = _section_body_from_text(athena_text, "given_ask_route_map")
    source_facts = _section_body_from_text(athena_text, "source_facts")
    answer_contract = _section_body_from_text(athena_text, "answer_contract")
    if not source_facts:
        source_facts = clean_text("\n".join([canon_yaml, given_ask_route_map]))
    if not answer_contract:
        answer_contract = clean_text(given_ask_route_map)
    questions_for_aria = _section_body_from_text(athena_text, "questions_for_aria")
    questions_for_artemis = _section_body_from_text(athena_text, "questions_for_artemis")
    routed = {
        "athena_canon_problem_yaml": str(canon_yaml),
        "athena_given_ask_route_map": str(given_ask_route_map),
        "athena_source_facts": str(source_facts),
        "athena_answer_contract": str(answer_contract),
        "athena_questions_for_aria": str(questions_for_aria),
        "athena_questions_for_artemis": str(questions_for_artemis),
        "athena_question_routing_ready": bool(questions_for_aria or questions_for_artemis),
    }
    state.update(dict(routed))
    return dict(routed)


def _role_contract_summary(role_name: str) -> str:
    role = canonical_role_name(role_name)
    contracts = globals().get("ROLE_STATIC_CONTRACTS")
    payload = dict(dict(contracts).get(role) or {}) if isinstance(contracts, dict) else {}
    schema = str(payload.get("schema_id") or payload.get("contract_id") or _role_metadata_schema_token(role))
    duty = str(payload.get("duty") or "role-specific validation")
    return f"{role}: {schema}; duty={duty}; immutable schema contract lives in CB7.25."


def build_loop_mechanics_config(global_state: dict[str, Any] | None = None) -> dict[str, Any]:
    gs = global_state if isinstance(global_state, dict) else {}
    global_turn_max = max(0, _coerce_int_local(gs.get("GLOBAL_MAX_TURN_TOKENS"), 0))
    if global_turn_max > 0:
        athena_open = athena_synthesis = max(64, global_turn_max)
        peer_exchange = peer_report = max(64, global_turn_max)
    else:
        athena_open = max(64, _coerce_int_local(gs.get("ATHENA_OPEN_MAX_TOKENS"), ATHENA_OPEN_MAX_TOKENS_DEFAULT))
        athena_synthesis = max(64, _coerce_int_local(gs.get("ATHENA_SYNTHESIS_MAX_TOKENS"), ATHENA_SYNTHESIS_MAX_TOKENS_DEFAULT))
        peer_exchange = max(64, _coerce_int_local(gs.get("PEER_EXCHANGE_MAX_TOKENS"), PEER_EXCHANGE_MAX_TOKENS_DEFAULT))
        peer_report = max(64, _coerce_int_local(gs.get("PEER_REPORT_MAX_TOKENS"), PEER_REPORT_MAX_TOKENS_DEFAULT))
    return {
        "max_big_loops": max(1, _coerce_int_local(gs.get("GLOBAL_MAX_BIG_LOOPS"), _coerce_int_local(gs.get("MAX_BIG_LOOPS"), MAX_BIG_LOOPS_DEFAULT))),
        "min_big_loop_for_closeout": max(1, _coerce_int_local(gs.get("GLOBAL_MIN_BIG_LOOP_FOR_CLOSEOUT"), MIN_BIG_LOOP_FOR_CLOSEOUT_DEFAULT)),
        "inner_total_exchanges": max(1, _coerce_int_local(gs.get("GLOBAL_INNER_TOTAL_EXCHANGES"), _coerce_int_local(gs.get("INNER_TOTAL_EXCHANGES"), INNER_TOTAL_EXCHANGES_DEFAULT))),
        "inner_reasoning_exchanges": max(1, _coerce_int_local(gs.get("INNER_REASONING_EXCHANGES"), INNER_REASONING_EXCHANGES_DEFAULT)),
        "lock_confidence_pct": _clamp_int(gs.get("GLOBAL_CLOSEOUT_CONFIDENCE_PCT"), 0, 100, BOXED_CONFIDENCE_GATE_PCT_DEFAULT),
        "boxed_confidence_gate_pct": _clamp_int(gs.get("GLOBAL_CLOSEOUT_CONFIDENCE_PCT"), 0, 100, BOXED_CONFIDENCE_GATE_PCT_DEFAULT),
        "athena_max_tokens": int(athena_open),
        "aria_max_tokens": int(peer_exchange),
        "artemis_max_tokens": int(peer_exchange),
        "athena_open_max_tokens": int(athena_open),
        "peer_exchange_max_tokens": int(peer_exchange),
        "peer_report_max_tokens": int(peer_report),
        "athena_synthesis_max_tokens": int(athena_synthesis),
        "athena_final_max_tokens": max(16, _coerce_int_local(gs.get("ATHENA_FINAL_MAX_TOKENS"), ATHENA_FINAL_MAX_TOKENS_DEFAULT)),
        "aria_exchange_max_tokens": max(64, _coerce_int_local(gs.get("ARIA_EXCHANGE_MAX_TOKENS"), int(peer_exchange))),
        "aria_report_max_tokens": max(64, _coerce_int_local(gs.get("ARIA_REPORT_MAX_TOKENS"), int(peer_report))),
        "artemis_exchange_max_tokens": max(64, _coerce_int_local(gs.get("ARTEMIS_EXCHANGE_MAX_TOKENS"), int(peer_exchange))),
        "artemis_report_max_tokens": max(64, _coerce_int_local(gs.get("ARTEMIS_REPORT_MAX_TOKENS"), int(peer_report))),
        "athena_repair_attempts": max(0, _coerce_int_local(gs.get("ATHENA_REPAIR_ATTEMPTS"), ATHENA_REPAIR_ATTEMPTS_DEFAULT)),
        "peer_repair_attempts": max(0, _coerce_int_local(gs.get("PEER_REPAIR_ATTEMPTS"), PEER_REPAIR_ATTEMPTS_DEFAULT)),
        "final_repair_attempts": max(0, _coerce_int_local(gs.get("FINAL_REPAIR_ATTEMPTS"), FINAL_REPAIR_ATTEMPTS_DEFAULT)),
        "trace_chars": max(300, _coerce_int_local(gs.get("TRACE_CHARS"), TRACE_CHARS_DEFAULT)),
        "report_trace_chars": max(500, _coerce_int_local(gs.get("REPORT_TRACE_CHARS"), REPORT_TRACE_CHARS_DEFAULT)),
        "peer_report_state_chars": max(240, _coerce_int_local(gs.get("PEER_REPORT_STATE_CHARS"), PEER_REPORT_STATE_CHARS_DEFAULT)),
        "athena_peer_report_chars": max(360, _coerce_int_local(gs.get("ATHENA_PEER_REPORT_CHARS"), ATHENA_PEER_REPORT_CHARS_DEFAULT)),
        "controller_routing_mode": "aenaimo260_0.2.3_role_question_routing_authoritative_synthesis",
        "warm_style_enabled": True,
    }


def make_prompt_state(st: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    peer_reports = dict(st.get("peer_reports") or {})
    report_chars = int(dict(config or {}).get("peer_report_state_chars", PEER_REPORT_STATE_CHARS_DEFAULT) or PEER_REPORT_STATE_CHARS_DEFAULT)
    return {
        "loop_no": int(st.get("loop_no", 0) or 0),
        "athena_stage": str(st.get("athena_stage", "solve") or "solve"),
        "athena_candidate_answer": str(st.get("athena_candidate_answer", "none") or "none"),
        "athena_exact_candidate_answer": str(st.get("athena_exact_candidate_answer", st.get("athena_candidate_answer", "none")) or "none"),
        "athena_confidence_pct": int(st.get("athena_confidence_pct", 0) or 0),
        "controller_confidence_ceiling": int(st.get("controller_confidence_ceiling", 0) or 0),
        "athena_confidence_rubric_band": str(st.get("athena_confidence_rubric_band", "unknown_or_unstable") or "unknown_or_unstable"),
        "athena_confidence_rubric_ceiling": int(st.get("athena_confidence_rubric_ceiling", 58) or 58),
        "athena_confidence_checklist": dict(st.get("athena_confidence_checklist") or {}),
        "athena_confidence_checklist_summary": str(st.get("athena_confidence_checklist_summary", "") or ""),
        "peer_validation_status": str(st.get("peer_validation_status", "not_started") or "not_started"),
        "open_objections": [str(item).strip() for item in list(st.get("open_objections") or []) if str(item).strip()][:3],
        "recent_summary": list(st.get("recent_summary") or [])[-4:],
        "peer_report_state_chars": int(report_chars),
        "athena_peer_report_chars": int(dict(config or {}).get("athena_peer_report_chars", ATHENA_PEER_REPORT_CHARS_DEFAULT) or ATHENA_PEER_REPORT_CHARS_DEFAULT),
        "peer_reports": {
            "Aria": _truncate_prompt_text(peer_reports.get("Aria", ""), max_chars=report_chars),
            "Artemis": _truncate_prompt_text(peer_reports.get("Artemis", ""), max_chars=report_chars),
        },
        "athena_source_facts": _truncate_prompt_text(st.get("athena_source_facts", ""), max_chars=900),
        "athena_answer_contract": _truncate_prompt_text(st.get("athena_answer_contract", ""), max_chars=500),
        "athena_canon_problem_yaml": _truncate_prompt_text(st.get("athena_canon_problem_yaml", ""), max_chars=1800),
        "athena_given_ask_route_map": _truncate_prompt_text(st.get("athena_given_ask_route_map", ""), max_chars=1000),
        "athena_questions_for_aria": _truncate_prompt_text(st.get("athena_questions_for_aria", ""), max_chars=900),
        "athena_questions_for_artemis": _truncate_prompt_text(st.get("athena_questions_for_artemis", ""), max_chars=900),
        "athena_question_routing_ready": bool(st.get("athena_question_routing_ready", False)),
        "peer_report_meta": dict(st.get("peer_report_meta") or {}),
        "latest_solve_meta": dict(st.get("latest_solve_meta") or {}),
        "closeout_resolution": dict(st.get("closeout_resolution") or {}),
        "turn_contract_damage": list(st.get("turn_contract_damage") or [])[-6:],
        "inner_total_exchanges": int(dict(config or {}).get("inner_total_exchanges", INNER_TOTAL_EXCHANGES_DEFAULT) or INNER_TOTAL_EXCHANGES_DEFAULT),
    }


def make_athena_open_route(st: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    loop_no = int(st.get("loop_no", 0) or 0)
    min_loop = int(dict(config or {}).get("min_big_loop_for_closeout", MIN_BIG_LOOP_FOR_CLOSEOUT_DEFAULT) or MIN_BIG_LOOP_FOR_CLOSEOUT_DEFAULT)
    stage = "decompose" if loop_no == 1 and min_loop > 1 else "solve"
    return {"role": "Athena", "stage": stage, "phase": "athena_open", "loop_no": int(loop_no)}


def make_peer_exchange_route(st: dict[str, Any], config: dict[str, Any], *, role_name: str, exchange_no: int, counterpart_last: str) -> dict[str, Any]:
    role = canonical_role_name(role_name)
    role_question_key = "athena_questions_for_aria" if role == "Aria" else "athena_questions_for_artemis"
    return {
        "role": role,
        "stage": "peer_reasoning",
        "phase": "peer_exchange",
        "loop_no": int(st.get("loop_no", 0) or 0),
        "exchange_no": int(exchange_no),
        "inner_total_exchanges": int(dict(config or {}).get("inner_total_exchanges", INNER_TOTAL_EXCHANGES_DEFAULT) or INNER_TOTAL_EXCHANGES_DEFAULT),
        "athena_message": "" if int(exchange_no) <= 1 else _truncate_prompt_text(st.get("athena_last_message", ""), max_chars=700),
        "athena_source_facts": _truncate_prompt_text(st.get("athena_source_facts", ""), max_chars=900),
        "athena_answer_contract": _truncate_prompt_text(st.get("athena_answer_contract", ""), max_chars=500),
        "athena_questions_for_this_role": _truncate_prompt_text(st.get(role_question_key, ""), max_chars=900),
        "counterpart_last": _truncate_prompt_text(counterpart_last, max_chars=700 if int(exchange_no) <= 1 else 900),
    }


def make_peer_report_route(st: dict[str, Any], config: dict[str, Any], *, role_name: str, completed_reasoning_exchanges: int) -> dict[str, Any]:
    role = canonical_role_name(role_name)
    role_question_key = "athena_questions_for_aria" if role == "Aria" else "athena_questions_for_artemis"
    return {
        "role": role,
        "stage": "peer_report",
        "phase": "peer_report",
        "loop_no": int(st.get("loop_no", 0) or 0),
        "completed_reasoning_exchanges": int(completed_reasoning_exchanges),
        "inner_total_exchanges": int(dict(config or {}).get("inner_total_exchanges", INNER_TOTAL_EXCHANGES_DEFAULT) or INNER_TOTAL_EXCHANGES_DEFAULT),
        "athena_message": _truncate_prompt_text(st.get("athena_last_message", ""), max_chars=900),
        "athena_source_facts": _truncate_prompt_text(st.get("athena_source_facts", ""), max_chars=700),
        "athena_answer_contract": _truncate_prompt_text(st.get("athena_answer_contract", ""), max_chars=420),
        "athena_questions_for_this_role": _truncate_prompt_text(st.get(role_question_key, ""), max_chars=700),
        "counterpart_last": "",
    }


def make_athena_synthesis_route(st: dict[str, Any], config: dict[str, Any]) -> dict[str, Any]:
    _ = config
    return {"role": "Athena", "stage": "synthesis", "phase": "athena_synthesis", "loop_no": int(st.get("loop_no", 0) or 0)}


def _render_state_for_prompt(prompt_state: dict[str, Any]) -> str:
    state = dict(prompt_state or {})
    peer_reports = dict(state.get("peer_reports") or {})
    lines = [
        f"- loop_no: {int(state.get('loop_no', 0) or 0)}",
        f"- athena_stage: {str(state.get('athena_stage', 'solve') or 'solve')}",
        f"- athena_candidate_answer: {str(state.get('athena_candidate_answer', 'none') or 'none')}",
        f"- athena_exact_candidate_answer: {str(state.get('athena_exact_candidate_answer', 'none') or 'none')}",
        f"- athena_confidence_pct: {int(state.get('athena_confidence_pct', 0) or 0)}",
        f"- controller_confidence_ceiling: {int(state.get('controller_confidence_ceiling', 0) or 0)}",
        f"- athena_rubric_band: {str(state.get('athena_confidence_rubric_band', 'unknown_or_unstable') or 'unknown_or_unstable')}",
        f"- athena_rubric_ceiling: {int(state.get('athena_confidence_rubric_ceiling', 58) or 58)}",
        f"- peer_validation_status: {str(state.get('peer_validation_status', 'not_started') or 'not_started')}",
    ]
    objections = [str(item).strip() for item in list(state.get("open_objections") or []) if str(item).strip()]
    for idx, objection in enumerate(objections[:3], start=1):
        lines.append(f"- open_objection_{idx}: {_truncate_prompt_text(objection, max_chars=180)}")
    if clean_text(peer_reports.get("Aria")):
        lines.append(f"- aria_report: {_truncate_prompt_text(peer_reports.get('Aria'), max_chars=int(state.get('peer_report_state_chars', 700) or 700))}")
    if clean_text(peer_reports.get("Artemis")):
        lines.append(f"- artemis_report: {_truncate_prompt_text(peer_reports.get('Artemis'), max_chars=int(state.get('peer_report_state_chars', 700) or 700))}")
    for idx, row in enumerate(list(state.get("recent_summary") or [])[-3:], start=1):
        try:
            rendered = json.dumps(dict(row or {}), ensure_ascii=False, separators=(",", ":"))
        except Exception:
            rendered = str(row)
        lines.append(f"- recent_{idx}: {_truncate_prompt_text(rendered, max_chars=240)}")
    return "\n".join(lines)


def _render_route_for_prompt(route: dict[str, Any]) -> str:
    payload = dict(route or {})
    lines = [
        f"- role: {str(payload.get('role', 'unknown') or 'unknown')}",
        f"- stage: {str(payload.get('stage', 'unknown') or 'unknown')}",
        f"- phase: {str(payload.get('phase', 'unknown') or 'unknown')}",
        f"- loop_no: {int(payload.get('loop_no', 0) or 0)}",
    ]
    if int(payload.get("exchange_no", 0) or 0):
        lines.append(f"- exchange_no: {int(payload.get('exchange_no', 0) or 0)}")
        lines.append(f"- inner_total_exchanges: {int(payload.get('inner_total_exchanges', 0) or 0)}")
    if int(payload.get("completed_reasoning_exchanges", 0) or 0):
        lines.append(f"- completed_reasoning_exchanges: {int(payload.get('completed_reasoning_exchanges', 0) or 0)}")
    return "\n".join(lines)


def _metadata_required_for_route(role: str, stage: str, phase: str, route: dict[str, Any]) -> bool:
    canonical = canonical_role_name(role)
    loop_no = int(dict(route or {}).get("loop_no", 0) or 0)
    exchange_no = int(dict(route or {}).get("exchange_no", 0) or 0)
    if canonical == "Athena":
        return bool(str(phase) == "athena_open" and loop_no <= 1)
    return False


def _problem_required_for_route(role: str, stage: str, phase: str, route: dict[str, Any]) -> bool:
    canonical = canonical_role_name(role)
    loop_no = int(dict(route or {}).get("loop_no", 0) or 0)
    exchange_no = int(dict(route or {}).get("exchange_no", 0) or 0)
    if canonical == "Athena":
        return bool(str(phase) == "athena_open" and loop_no <= 1)
    return bool(str(stage) == "peer_reasoning" and exchange_no == 1)


def _athena_turn_headers(stage: str, phase: str, loop_no: int) -> list[str]:
    if str(phase) == "athena_open" and int(loop_no or 0) <= 1:
        return ["canon_problem_yaml", "given_ask_route_map", "questions_for_aria", "questions_for_artemis"]
    if str(phase) == "athena_open":
        return ["canon_problem_yaml", "given_ask_route_map", "questions_for_aria", "questions_for_artemis"]
    if str(stage) == "synthesis":
        return ["route_alignment", "resolved_objections", "remaining_objections", "synthesis_reasoning", "selected_candidate"]
    return []


def _peer_turn_headers(role: str, stage: str, exchange_no: int) -> list[str]:
    canonical = canonical_role_name(role)
    first_exchange = bool(int(exchange_no or 0) == 1)
    if str(stage) == "peer_report":
        return ["report_slots", "report"]
    if canonical == "Aria":
        if first_exchange:
            return ["aria_canon_yaml", "answers_to_athena", "proposed_solution_route", "route_confidence_and_risks", "request_to_artemis"]
        return ["route_agreement_status", "confidence_map", "solution_continuation", "open_uncertainties", "request_to_artemis", "final_status_slots"]
    if first_exchange:
        return ["artemis_canon_yaml", "answers_to_athena", "answers_to_aria", "route_validation", "route_feedback_for_aria"]
    return ["aria_claim_audit", "confidence_backing", "corrections", "solution_continuation", "request_to_aria", "final_status_slots"]

def _report_template_for_prompt(role_name: str) -> str:
    role = canonical_role_name(role_name)
    scaffold = globals().get("render_section_scaffold")
    return str(scaffold(role, "peer_report")) if callable(scaffold) else ""


def _metadata_schema_for_route(role: str, stage: str, phase: str, route: dict[str, Any]) -> str:
    canonical = canonical_role_name(role)
    _ = stage, phase, route
    if canonical != "Athena":
        return ""
    setup = globals().get("role_setup_yaml")
    if callable(setup):
        return str(setup(canonical))
    return f"schema_id: {_role_metadata_schema_token(canonical)}\nrole: {canonical}\ncontroller_contract: section_wrapper\n"


def _dynamic_instruction_lines(role: str, stage: str, phase: str, route: dict[str, Any], prompt_state: dict[str, Any]) -> list[str]:
    role = canonical_role_name(role)
    stage = str(stage or "")
    phase = str(phase or "")
    loop_no = int(route.get("loop_no", 0) or 0)
    exchange_no = int(route.get("exchange_no", 0) or 0)
    total = int(route.get("inner_total_exchanges", prompt_state.get("inner_total_exchanges", INNER_TOTAL_EXCHANGES_DEFAULT)) or INNER_TOTAL_EXCHANGES_DEFAULT)
    ceiling = int(prompt_state.get("controller_confidence_ceiling", 0) or 0)
    peer_status = str(prompt_state.get("peer_validation_status", "not_started") or "not_started")

    _ = loop_no, total, ceiling, peer_status
    if role == "Athena" and phase == "athena_open":
        return ["Athena full Canon v2.1 problem breakdown, routed questions, no solution attempt."]
    if role == "Athena" and stage == "synthesis":
        return ["Athena synthesis scaffold; select candidate only, final answer block is a later turn."]
    if role == "Aria" and stage == "peer_reasoning" and exchange_no == 1:
        return ["Aria writes a proof-route Canon view, answers Athena, and proposes the route."]
    if role == "Artemis" and stage == "peer_reasoning" and exchange_no == 1:
        return ["Artemis writes an audit-route Canon view, answers Athena and Aria, and validates or rejects the route."]
    if role == "Aria" and stage == "peer_report":
        return ["Aria reports to Athena with no boxed answer-confidence text."]
    if role == "Artemis" and stage == "peer_report":
        return ["Artemis reports to Athena with no boxed answer-confidence text."]
    return [f"{role} solve scaffold."]

def _prefill_report_scaffold(role: str, scaffold: str, prompt_state: dict[str, Any]) -> str:
    latest = dict(dict(prompt_state or {}).get("latest_solve_meta") or {})
    role_meta = dict(latest.get(canonical_role_name(role)) or {})
    status_slots = dict(role_meta.get("status_slots") or {})

    def _slot(name: str, default: str = "none") -> str:
        value = role_meta.get(name, status_slots.get(name, default))
        text = clean_text(value)
        return text if text else str(default)

    answer = normalize_candidate_answer(str(_slot("candidate_answer_integer", "none")))
    if answer == "none":
        answer = normalize_candidate_answer(str(role_meta.get("candidate_answer", "none") or "none"))
    if answer == "none":
        answer = normalize_candidate_answer(str(role_meta.get("diagnostic_candidate_answer", "none") or "none"))
    confidence = int(role_meta.get("confidence_pct", 0) or 0)
    if answer == "none":
        diagnostic = normalize_candidate_answer(str(role_meta.get("diagnostic_candidate_answer", "none") or "none"))
        if diagnostic != "none":
            answer = diagnostic
            confidence = max(int(confidence), min(92, int(BOXED_CONFIDENCE_GATE_PCT) + 1))
    hard_hits = list(role_meta.get("hard_blocker_hits") or [])
    status = "closed" if answer != "none" and confidence >= int(BOXED_CONFIDENCE_GATE_PCT) and not hard_hits else "open"
    blockers = "none" if status == "closed" else "unknown"
    replacement = (
        '<report_slots max_chars="220">\n'
        f"candidate_answer_integer: {answer}\n"
        f"candidate_confidence: {int(confidence) if answer != 'none' else 0}\n"
        f"status: {status}\n"
        f"open_blockers: {blockers}\n"
        "</report_slots>"
    )
    updated = re.sub(
        r"<report_slots[\s\S]*?</report_slots>",
        lambda _match: replacement,
        str(scaffold),
        count=1,
        flags=re.IGNORECASE,
    )
    return str(updated)

def _peer_answer_from_report_meta(report_meta: dict[str, Any]) -> tuple[str, int, str]:
    payload = dict(report_meta or {})
    answer = normalize_candidate_answer(
        str(payload.get("answer_signal_integer", payload.get("candidate_exact_integer", "none")) or "none")
    )
    if answer == "none":
        answer = normalize_candidate_answer(str(payload.get("candidate_exact_integer", payload.get("candidate", "none")) or "none"))
    confidence = int(payload.get("answer_signal_confidence_pct", payload.get("confidence_pct", 0)) or 0)
    if confidence <= 0:
        confidence = int(payload.get("confidence_pct", 0) or 0)
    return str(answer), max(0, min(100, int(confidence))), str(payload.get("answer_signal_source", "peer_report") or "peer_report")


def _peer_report_disagreement(prompt_state: dict[str, Any]) -> bool:
    peer_meta = dict(dict(prompt_state or {}).get("peer_report_meta") or {})
    answers: list[str] = []
    for role in ["Aria", "Artemis"]:
        answer, _confidence, _source = _peer_answer_from_report_meta(dict(peer_meta.get(role) or {}))
        if answer != "none":
            answers.append(str(answer))
    return bool(len(answers) >= 2 and len(set(answers)) > 1)


def _peer_report_field_excerpt(report_meta: dict[str, Any], field_names: list[str], *, max_chars: int) -> str:
    fields = dict(dict(report_meta or {}).get("extracted_fields") or {})
    chunks: list[str] = []
    for field_name in list(field_names or []):
        value = _truncate_prompt_text(fields.get(str(field_name), ""), max_chars=max(120, int(max_chars) // 2))
        if value:
            chunks.append(f"{field_name}: {value}")
    return _truncate_prompt_text("\n".join(chunks), max_chars=int(max_chars))


def _build_peer_disagreement_adjudication_block(prompt_state: dict[str, Any]) -> str:
    peer_meta = dict(dict(prompt_state or {}).get("peer_report_meta") or {})
    role_rows: list[str] = []
    for role in ["Aria", "Artemis"]:
        meta = dict(peer_meta.get(role) or {})
        answer, confidence, source = _peer_answer_from_report_meta(meta)
        if answer == "none" and not clean_text(meta.get("text", "")):
            continue
        excerpt_fields = ["report_slots", "report"]
        excerpt = _peer_report_field_excerpt(meta, excerpt_fields, max_chars=900)
        role_rows.append(
            "\n".join(
                [
                    f"{role}: answer={answer}; confidence={int(confidence)}; source={source}",
                    excerpt,
                ]
            ).strip()
        )
    answers = [
        _peer_answer_from_report_meta(dict(peer_meta.get(role) or {}))[0]
        for role in ["Aria", "Artemis"]
        if _peer_answer_from_report_meta(dict(peer_meta.get(role) or {}))[0] != "none"
    ]
    if len(answers) < 2 or len(set(answers)) <= 1:
        return ""
    lines = [
        "Peer final answers disagree. Resolve by source-fact adjudication.",
        "Required adjudication:",
        "1. Restate the transformed variable, exact interval, and endpoint inclusivity from the source facts.",
        "2. Locate the first mathematical divergence between the peer derivations.",
        "3. For count/range disagreements, explicitly audit boundary values introduced by substitutions such as +1 or -1.",
        "4. Classify any disputed endpoint before counting exclusions or inclusions.",
        "5. Select the answer whose derivation survives this audit; if neither survives, recompute from source facts.",
        "6. In resolved_objections, name the rejected step and the corrected step.",
        "",
        "Peer report excerpts:",
        "\n\n".join(role_rows),
    ]
    return _truncate_prompt_text("\n".join(lines), max_chars=2400)


def _prefill_athena_synthesis_scaffold(scaffold: str, prompt_state: dict[str, Any]) -> str:
    latest = dict(dict(prompt_state or {}).get("latest_solve_meta") or {})
    peer_reports = dict(dict(prompt_state or {}).get("peer_reports") or {})
    peer_meta = dict(dict(prompt_state or {}).get("peer_report_meta") or {})
    lines: list[str] = []
    for role in ["Aria", "Artemis"]:
        report_meta = dict(peer_meta.get(role) or {})
        meta = dict(latest.get(role) or {})
        if report_meta:
            answer = normalize_candidate_answer(
                str(
                    report_meta.get(
                        "answer_signal_integer",
                        report_meta.get("candidate_exact_integer", report_meta.get("candidate", "none")),
                    )
                    or "none"
                )
            )
            if answer == "none":
                answer = normalize_candidate_answer(str(report_meta.get("candidate_exact_integer", "none") or "none"))
            confidence = int(
                report_meta.get(
                    "answer_signal_confidence_pct",
                    report_meta.get("confidence_pct", 0),
                )
                or 0
            )
            if confidence <= 0:
                confidence = int(report_meta.get("confidence_pct", 0) or 0)
            lines.append(
                f"{role}: candidate_integer={answer}; "
                f"signal_source={report_meta.get('answer_signal_source', 'peer_report')}; "
                f"confidence={int(confidence)}; schema_valid={bool(report_meta.get('schema_valid', False))}; "
                f"open_blocker={bool(report_meta.get('open_blocker', False))}; "
                f"hard_blockers={report_meta.get('hard_blocker_hits', [])}"
            )
        elif meta:
            lines.append(
                f"{role}: candidate_integer={meta.get('candidate_answer_integer', meta.get('candidate_answer', 'none'))}; "
                f"diagnostic={meta.get('diagnostic_candidate_answer', 'none')}; "
                f"confidence={meta.get('confidence_pct', 0)}; open_blocker={meta.get('open_blocker', True)}; "
                f"hard_blockers={meta.get('hard_blocker_hits', [])}"
            )
        elif clean_text(peer_reports.get(role)):
            lines.append(f"{role}: report_present")
        else:
            lines.append(f"{role}: no parsed artifact")
    artifact_text = "\n".join(lines)
    scaffold_text = re.sub(
        r"<parsed_peer_artifacts[^>]*>[\s\S]*?</parsed_peer_artifacts>",
        f'<parsed_peer_artifacts max_chars="900">\n{artifact_text}\n</parsed_peer_artifacts>',
        str(scaffold),
        count=1,
        flags=re.IGNORECASE,
    )
    peer_disagreement = bool(_peer_report_disagreement(dict(prompt_state or {})))
    if bool(peer_disagreement):
        scaffold_text = re.sub(
            r"(<remaining_objections[^>]*>)[\s\S]*?(</remaining_objections>)",
            lambda match: (
                f"{match.group(1)}\n"
                "Peer reports disagree on the final integer. Athena must adjudicate the first mathematical divergence before selecting a candidate.\n"
                f"{match.group(2)}"
            ),
            scaffold_text,
            count=1,
            flags=re.IGNORECASE,
        )
        scaffold_text = re.sub(
            r"(<selected_candidate[^>]*>)[\s\S]*?(</selected_candidate>)",
            lambda match: f"{match.group(1)}\ncandidate_answer_integer: none\ncandidate_confidence: 0\n{match.group(2)}",
            scaffold_text,
            count=1,
            flags=re.IGNORECASE,
        )
    final_candidate = normalize_candidate_answer(str(dict(prompt_state or {}).get("athena_exact_candidate_answer", dict(prompt_state or {}).get("athena_candidate_answer", "none"))))
    final_confidence = int(dict(prompt_state or {}).get("athena_confidence_pct", 0) or 0)
    if final_candidate == "none" and not bool(peer_disagreement):
        candidates: list[tuple[str, int]] = []
        for role in ["Aria", "Artemis"]:
            report_meta = dict(peer_meta.get(role) or {})
            answer, confidence, _source = _peer_answer_from_report_meta(report_meta)
            if answer != "none":
                candidates.append((str(answer), int(confidence)))
        if candidates:
            final_candidate, final_confidence = sorted(candidates, key=lambda item: int(item[1]), reverse=True)[0]
    selected_payload = (
        f"candidate_answer_integer: {final_candidate}\n"
        f"candidate_confidence: {int(final_confidence) if final_candidate != 'none' else 0}\n"
        "selection_basis: synthesis_only_final_answer_block_deferred"
    )
    return re.sub(
        r"<selected_candidate[^>]*>[\s\S]*?</selected_candidate>",
        lambda _match: f'<selected_candidate max_chars="300">\n{selected_payload}\n</selected_candidate>',
        scaffold_text,
        count=1,
        flags=re.IGNORECASE,
    )

def build_model_payload_prompt(*, problem_text: str, prompt_state: dict[str, Any], route: dict[str, Any], trace_text: str = "") -> str:
    role = canonical_role_name(str(route.get("role") or "Athena"))
    stage = str(route.get("stage") or "")
    phase = str(route.get("phase") or "")
    role_tag = role_payload_tag(role)
    route_view = dict(route or {})
    exchange_no = int(route_view.get("exchange_no", 0) or 0)
    athena_context = _truncate_prompt_text(route_view.get("athena_message", ""), max_chars=700)
    athena_source_facts = _truncate_prompt_text(
        route_view.get("athena_source_facts", dict(prompt_state or {}).get("athena_source_facts", "")),
        max_chars=900,
    )
    athena_answer_contract = _truncate_prompt_text(
        route_view.get("athena_answer_contract", dict(prompt_state or {}).get("athena_answer_contract", "")),
        max_chars=500,
    )
    athena_questions_for_this_role = _truncate_prompt_text(route_view.get("athena_questions_for_this_role", ""), max_chars=900)
    counterpart_context = _truncate_prompt_text(route_view.get("counterpart_last", ""), max_chars=900 if exchange_no > 1 else 700)
    trace_view = _truncate_prompt_text(trace_text, max_chars=REPORT_TRACE_CHARS_DEFAULT if stage == "peer_report" else TRACE_CHARS_DEFAULT)
    peer_disagreement_adjudication = (
        _build_peer_disagreement_adjudication_block(dict(prompt_state or {}))
        if role == "Athena" and stage == "synthesis"
        else ""
    )
    if role == "Athena" and stage == "synthesis":
        scaffold_phase = "athena_synthesis"
        turn_contract = (
            "Adjudicate peer evidence from source facts. When peer answers differ, locate the first mathematical "
            "divergence, recompute the contested step, and fill selected_candidate only. For finite counts, lists, "
            "case partitions, or arithmetic totals, show the visible hand check in synthesis_reasoning before "
            "selecting. Do not accept claimed verification without the visible check. Do not write a boxed answer; "
            "the final_answer_block is a separate mandatory next turn."
        )
    elif role == "Athena":
        scaffold_phase = "athena_open"
        turn_contract = (
            "Open with a full Canon DSL v2.1 YAML problem breakdown, a given/ask/route map, and routed questions "
            "for Aria and Artemis. Do not attempt the solution. Route requests toward visible hand checks, not tools."
        )
    elif stage == "peer_report":
        scaffold_phase = "peer_report"
        turn_contract = (
            "Write a compact paper-faithful report to Athena. Use report_slots for controller metadata and one concise "
            "<report> with the decisive reason/check. Do not write boxed answer-confidence text. Do not claim script, "
            "tool, Python, calculator, or empirical verification; report only visible hand reasoning."
        )
    elif role == "Aria" and exchange_no <= 1:
        scaffold_phase = "peer_exchange_1"
        turn_contract = (
            "Write Aria's Canon-style proof-route breakdown, answer Athena, propose the most valid solution route, "
            "explain why it is best, and request Artemis visible hand checks where useful. Keep final selection pending."
        )
    elif role == "Artemis" and exchange_no <= 1:
        scaffold_phase = "peer_exchange_1"
        turn_contract = (
            "Write Artemis's Canon-style audit-route breakdown, answer Athena, answer Aria, validate or disagree with "
            "Aria's proposed route, and send actionable route feedback to Aria. If asked for computation, provide a "
            "visible hand enumeration or arithmetic audit, not a tool/script request. Keep final selection pending."
        )
    elif role == "Artemis" and str(phase).lower() in {"forced_solve", "artemis_forced_solve"}:
        scaffold_phase = "forced_solve"
        turn_contract = (
            "Independently compute the audit ledger and normalization work in the provided sections. For bounded "
            "counts or casework, include a visible hand table/list sufficient to audit the total."
        )
    else:
        scaffold_phase = "solve"
        turn_contract = (
            "Continue the agreed route. Aria states confidence and uncertainty; Artemis audits Aria's confidence, "
            "corrects errors, and builds the solution. For bounded counts or arithmetic totals, show the visible "
            "hand check before candidate status. Put candidate status in final_status_slots."
        )
    scaffold_renderer = globals().get("render_section_scaffold")
    wrapper = globals().get("wrap_role_body")
    scaffold_inner = (
        scaffold_renderer(role, scaffold_phase)
        if callable(scaffold_renderer)
        else "\n".join([f"<solve_problem_now max_chars=\"4200\">\n</solve_problem_now>"])
    )
    if stage == "peer_report":
        scaffold_inner = _prefill_report_scaffold(role, str(scaffold_inner), dict(prompt_state or {}))
    if role == "Athena" and stage == "synthesis":
        scaffold_inner = _prefill_athena_synthesis_scaffold(str(scaffold_inner), dict(prompt_state or {}))
    controller_scaffold = (
        wrapper(role, scaffold_inner)
        if callable(wrapper)
        else f"<{role_tag}>{scaffold_inner}</{role_tag}>"
    )

    context_blocks: list[str] = []
    if _problem_required_for_route(role, stage, phase, route_view):
        context_blocks.append("PROBLEM\n" + (clean_text(problem_text) or "[empty]"))
    if athena_source_facts and role in {"Aria", "Artemis"}:
        context_blocks.append("ATHENA_SOURCE_FACTS\n" + athena_source_facts)
    if athena_answer_contract and role in {"Aria", "Artemis"}:
        context_blocks.append("ATHENA_ANSWER_CONTRACT\n" + athena_answer_contract)
    if athena_questions_for_this_role and role in {"Aria", "Artemis"}:
        context_blocks.append("ATHENA_QUESTIONS_FOR_THIS_ROLE\n" + athena_questions_for_this_role)
    if peer_disagreement_adjudication:
        context_blocks.append("PEER_DISAGREEMENT_TO_ADJUDICATE\n" + peer_disagreement_adjudication)
    if athena_context:
        context_blocks.append("ATHENA_CONTEXT\n" + athena_context)
    if counterpart_context:
        context_blocks.append("COUNTERPART_CONTEXT\nAddress one concrete counterpart claim in the relevant response section.\n" + counterpart_context)
    if trace_view:
        context_blocks.append("TRACE\n" + trace_view)
    lines = [
        "ROLE",
        role,
        "",
        "PHASE",
        f"{stage or phase}",
        "",
        "STATE",
        _render_state_for_prompt(dict(prompt_state or {})),
        "",
        "INSTRUCTIONS",
        CLOSED_BOOK_REASONING_CONTRACT,
        str(turn_contract),
        "Complete the supplied tags in order. Keep each section concise.",
    ]
    if context_blocks:
        lines.extend(["", "CONTEXT", "\n\n".join(context_blocks)])
    lines.extend(["", "OUTPUT", controller_scaffold])
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
    selected_confidence = int(
        dict(active_state.get("closeout_resolution") or {}).get(
            "confidence_pct",
            active_state.get("athena_confidence_pct", active_state.get("confidence_pct", 0)),
        )
        or 0
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

def format_trace(entries: list[dict[str, Any]], *, max_chars: int) -> str:
    rendered: list[str] = []
    for row in list(entries or [])[-6:]:
        speaker = clean_text(dict(row or {}).get("speaker")) or "Unknown"
        text = _truncate_prompt_text(dict(row or {}).get("text", ""), max_chars=320)
        if text:
            rendered.append(f"{speaker}: {text}")
    trace = "\n".join(rendered).strip()
    if len(trace) <= int(max_chars):
        return trace
    return trace[-int(max_chars):]


## Runtime Adapter - inside CB07.5 Dynamic Turn Discipline

import json
import re
import time
from difflib import SequenceMatcher
from typing import Any


CB07_CONTROLLER_REVISION = "2026-04-27-aenaimo260-0.2.3-turn-discipline-v1.5.1-closed-book-confidence"


def _require_from_globals(name: str) -> Any:
    if name in globals():
        return globals()[name]
    raise NameError(f"{name} is not available in notebook globals. Run CB7 before CB07.5.")


build_loop_mechanics_config = _require_from_globals("build_loop_mechanics_config")
build_model_payload_prompt = _require_from_globals("build_model_payload_prompt")
build_final_prompt = _require_from_globals("build_final_prompt")
make_prompt_state = _require_from_globals("make_prompt_state")
make_athena_open_route = _require_from_globals("make_athena_open_route")
make_peer_exchange_route = _require_from_globals("make_peer_exchange_route")
make_peer_report_route = _require_from_globals("make_peer_report_route")
make_athena_synthesis_route = _require_from_globals("make_athena_synthesis_route")
new_controller_state = _require_from_globals("new_controller_state")
parse_role_text = _require_from_globals("parse_role_text")
parse_peer_report = _require_from_globals("parse_peer_report")
format_controller_report = _require_from_globals("format_controller_report")
parse_peer_turn = _require_from_globals("parse_peer_turn")
parse_athena_turn = _require_from_globals("parse_athena_turn")
classify_peer_report = _require_from_globals("classify_peer_report")
normalize_candidate_answer = _require_from_globals("normalize_candidate_answer")
parse_final_closeout = _require_from_globals("parse_final_closeout")
parse_final_token = _require_from_globals("parse_final_token")
emit_final = _require_from_globals("emit_final")
role_payload_tag = _require_from_globals("role_payload_tag")
format_trace = _require_from_globals("format_trace")


def _coerce_int(value: Any, default: int) -> int:
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


def _clean_text(value: Any) -> str:
    cleaner = globals().get("clean_dialogue_text")
    if callable(cleaner):
        try:
            return str(cleaner(str(value or ""))).strip()
        except Exception:
            pass
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n").strip()


def resolve_runtime_label(role_or_alias: str, fallback: str) -> str:
    resolver = globals().get("runtime_label_for_role")
    if callable(resolver):
        try:
            label = str(resolver(str(role_or_alias), default=str(fallback))).strip()
            if label:
                return label
        except Exception:
            pass
    return str(fallback).strip() or str(role_or_alias).strip()


def resolve_role_name(runtime_label: str, fallback: str) -> str:
    resolver = globals().get("role_name_for_runtime_label")
    if callable(resolver):
        try:
            name = str(resolver(str(runtime_label), default=str(fallback))).strip()
            if name:
                return name
        except Exception:
            pass
    return str(fallback).strip() or str(runtime_label).strip()


LOOP_MECHANICS = dict(build_loop_mechanics_config(globals()))
MAX_BIG_LOOPS = int(LOOP_MECHANICS.get("max_big_loops", 5))
MIN_BIG_LOOP_FOR_CLOSEOUT = int(LOOP_MECHANICS.get("min_big_loop_for_closeout", 1))
INNER_TOTAL_EXCHANGES = int(LOOP_MECHANICS.get("inner_total_exchanges", 8))
INNER_REASONING_EXCHANGES = int(LOOP_MECHANICS.get("inner_reasoning_exchanges", 7))
BOXED_CONFIDENCE_GATE_PCT = int(LOOP_MECHANICS.get("boxed_confidence_gate_pct", 90))

ATHENA_OPEN_MAX_TOKENS = int(LOOP_MECHANICS.get("athena_open_max_tokens", 5200))
PEER_EXCHANGE_MAX_TOKENS = int(LOOP_MECHANICS.get("peer_exchange_max_tokens", 3400))
PEER_REPORT_MAX_TOKENS = int(LOOP_MECHANICS.get("peer_report_max_tokens", 1500))
ATHENA_SYNTHESIS_MAX_TOKENS = int(LOOP_MECHANICS.get("athena_synthesis_max_tokens", 3800))
ATHENA_FINAL_MAX_TOKENS = int(LOOP_MECHANICS.get("athena_final_max_tokens", 768))
ARIA_EXCHANGE_MAX_TOKENS = int(LOOP_MECHANICS.get("aria_exchange_max_tokens", PEER_EXCHANGE_MAX_TOKENS))
ARIA_REPORT_MAX_TOKENS = int(LOOP_MECHANICS.get("aria_report_max_tokens", PEER_REPORT_MAX_TOKENS))
ARTEMIS_EXCHANGE_MAX_TOKENS = int(LOOP_MECHANICS.get("artemis_exchange_max_tokens", PEER_EXCHANGE_MAX_TOKENS))
ARTEMIS_REPORT_MAX_TOKENS = int(LOOP_MECHANICS.get("artemis_report_max_tokens", PEER_REPORT_MAX_TOKENS))

ATHENA_REPAIR_ATTEMPTS = int(LOOP_MECHANICS.get("athena_repair_attempts", 1))
PEER_REPAIR_ATTEMPTS = int(LOOP_MECHANICS.get("peer_repair_attempts", 1))
FINAL_REPAIR_ATTEMPTS = int(LOOP_MECHANICS.get("final_repair_attempts", 1))
TRACE_CHARS = int(LOOP_MECHANICS.get("trace_chars", 1100))
REPORT_TRACE_CHARS = int(LOOP_MECHANICS.get("report_trace_chars", 700))

CONTROLLER_RESET_SESSION_EACH_TURN = bool(globals().get("CONTROLLER_RESET_SESSION_EACH_TURN", True))
SILENT_CONTROLLER_STREAM = bool(globals().get("SILENT_CONTROLLER_STREAM", True))
CONTROLLER_JSON_EVENTS = bool(
    globals().get("CONTROLLER_JSON_EVENTS", globals().get("PRINT_INTERMEDIATE_JSON", False))
)
AUTO_RECOVER_RUNTIME_ON_DEAD_SERVER = bool(globals().get("AUTO_RECOVER_RUNTIME_ON_DEAD_SERVER", True))
PRINT_PROGRESS_LINES = bool(globals().get("PRINT_PROGRESS_LINES", False))
PRINT_CB7_CONFIG_JSON = bool(globals().get("PRINT_CB7_CONFIG_JSON", False))
CB075_TIME_RECORD_ENABLED = bool(globals().get("CB075_TIME_RECORD_ENABLED", True))
CB075_TIME_RECORD_JSON = bool(globals().get("CB075_TIME_RECORD_JSON", True))
CB075_TIME_RECORD_GLOBAL_KEY = str(globals().get("CB075_TIME_RECORD_GLOBAL_KEY", "CB075_TURN_TIMING_LOG"))


def _refresh_live_controller_knobs() -> dict[str, Any]:
    global LOOP_MECHANICS
    global MAX_BIG_LOOPS
    global MIN_BIG_LOOP_FOR_CLOSEOUT
    global INNER_TOTAL_EXCHANGES
    global INNER_REASONING_EXCHANGES
    global BOXED_CONFIDENCE_GATE_PCT
    global ATHENA_OPEN_MAX_TOKENS
    global PEER_EXCHANGE_MAX_TOKENS
    global PEER_REPORT_MAX_TOKENS
    global ATHENA_SYNTHESIS_MAX_TOKENS
    global ATHENA_FINAL_MAX_TOKENS
    global ARIA_EXCHANGE_MAX_TOKENS
    global ARIA_REPORT_MAX_TOKENS
    global ARTEMIS_EXCHANGE_MAX_TOKENS
    global ARTEMIS_REPORT_MAX_TOKENS
    global ATHENA_REPAIR_ATTEMPTS
    global PEER_REPAIR_ATTEMPTS
    global FINAL_REPAIR_ATTEMPTS
    global TRACE_CHARS
    global REPORT_TRACE_CHARS
    global CONTROLLER_RESET_SESSION_EACH_TURN
    global SILENT_CONTROLLER_STREAM
    global CONTROLLER_JSON_EVENTS
    global AUTO_RECOVER_RUNTIME_ON_DEAD_SERVER
    global PRINT_PROGRESS_LINES
    global PRINT_CB7_CONFIG_JSON
    global CB075_TIME_RECORD_ENABLED
    global CB075_TIME_RECORD_JSON
    global CB075_TIME_RECORD_GLOBAL_KEY
    global SOLVER_SOLVE_GENERATION
    global CLERK_PATCH_GENERATION
    global AGENT_REVIEW_GENERATION

    LOOP_MECHANICS = dict(build_loop_mechanics_config(globals()))
    MAX_BIG_LOOPS = int(LOOP_MECHANICS.get("max_big_loops", 5))
    MIN_BIG_LOOP_FOR_CLOSEOUT = int(LOOP_MECHANICS.get("min_big_loop_for_closeout", 1))
    INNER_TOTAL_EXCHANGES = int(LOOP_MECHANICS.get("inner_total_exchanges", 8))
    INNER_REASONING_EXCHANGES = int(LOOP_MECHANICS.get("inner_reasoning_exchanges", 7))
    BOXED_CONFIDENCE_GATE_PCT = int(LOOP_MECHANICS.get("boxed_confidence_gate_pct", 90))
    ATHENA_OPEN_MAX_TOKENS = int(LOOP_MECHANICS.get("athena_open_max_tokens", 5200))
    PEER_EXCHANGE_MAX_TOKENS = int(LOOP_MECHANICS.get("peer_exchange_max_tokens", 3400))
    PEER_REPORT_MAX_TOKENS = int(LOOP_MECHANICS.get("peer_report_max_tokens", 1500))
    ATHENA_SYNTHESIS_MAX_TOKENS = int(LOOP_MECHANICS.get("athena_synthesis_max_tokens", 3800))
    ATHENA_FINAL_MAX_TOKENS = int(LOOP_MECHANICS.get("athena_final_max_tokens", 768))
    ARIA_EXCHANGE_MAX_TOKENS = int(LOOP_MECHANICS.get("aria_exchange_max_tokens", PEER_EXCHANGE_MAX_TOKENS))
    ARIA_REPORT_MAX_TOKENS = int(LOOP_MECHANICS.get("aria_report_max_tokens", PEER_REPORT_MAX_TOKENS))
    ARTEMIS_EXCHANGE_MAX_TOKENS = int(LOOP_MECHANICS.get("artemis_exchange_max_tokens", PEER_EXCHANGE_MAX_TOKENS))
    ARTEMIS_REPORT_MAX_TOKENS = int(LOOP_MECHANICS.get("artemis_report_max_tokens", PEER_REPORT_MAX_TOKENS))
    ATHENA_REPAIR_ATTEMPTS = int(LOOP_MECHANICS.get("athena_repair_attempts", 1))
    PEER_REPAIR_ATTEMPTS = int(LOOP_MECHANICS.get("peer_repair_attempts", 1))
    FINAL_REPAIR_ATTEMPTS = int(LOOP_MECHANICS.get("final_repair_attempts", 1))
    TRACE_CHARS = int(LOOP_MECHANICS.get("trace_chars", 1100))
    REPORT_TRACE_CHARS = int(LOOP_MECHANICS.get("report_trace_chars", 700))

    CONTROLLER_RESET_SESSION_EACH_TURN = bool(globals().get("CONTROLLER_RESET_SESSION_EACH_TURN", True))
    SILENT_CONTROLLER_STREAM = bool(globals().get("SILENT_CONTROLLER_STREAM", True))
    CONTROLLER_JSON_EVENTS = bool(
        globals().get("CONTROLLER_JSON_EVENTS", globals().get("PRINT_INTERMEDIATE_JSON", False))
    )
    AUTO_RECOVER_RUNTIME_ON_DEAD_SERVER = bool(globals().get("AUTO_RECOVER_RUNTIME_ON_DEAD_SERVER", True))
    PRINT_PROGRESS_LINES = bool(globals().get("PRINT_PROGRESS_LINES", True))
    PRINT_CB7_CONFIG_JSON = bool(globals().get("PRINT_CB7_CONFIG_JSON", False))
    CB075_TIME_RECORD_ENABLED = bool(globals().get("CB075_TIME_RECORD_ENABLED", True))
    CB075_TIME_RECORD_JSON = bool(globals().get("CB075_TIME_RECORD_JSON", True))
    CB075_TIME_RECORD_GLOBAL_KEY = str(globals().get("CB075_TIME_RECORD_GLOBAL_KEY", "CB075_TURN_TIMING_LOG"))

    SOLVER_SOLVE_GENERATION = require_generation_profile("SOLVER_SOLVE_GENERATION")
    CLERK_PATCH_GENERATION = require_generation_profile("CLERK_PATCH_GENERATION")
    AGENT_REVIEW_GENERATION = require_generation_profile("AGENT_REVIEW_GENERATION")
    SOLVER_SOLVE_GENERATION["max_tokens"] = max(int(ATHENA_OPEN_MAX_TOKENS), int(ATHENA_SYNTHESIS_MAX_TOKENS), int(ATHENA_FINAL_MAX_TOKENS))
    CLERK_PATCH_GENERATION["max_tokens"] = max(int(ARTEMIS_EXCHANGE_MAX_TOKENS), int(ARTEMIS_REPORT_MAX_TOKENS))
    AGENT_REVIEW_GENERATION["max_tokens"] = max(int(ARIA_EXCHANGE_MAX_TOKENS), int(ARIA_REPORT_MAX_TOKENS))

    return {
        "max_big_loops": int(MAX_BIG_LOOPS),
        "min_big_loop_for_closeout": int(MIN_BIG_LOOP_FOR_CLOSEOUT),
        "inner_total_exchanges": int(INNER_TOTAL_EXCHANGES),
        "inner_reasoning_exchanges": int(INNER_REASONING_EXCHANGES),
        "closeout_confidence_pct_strict_gt": int(BOXED_CONFIDENCE_GATE_PCT),
        "athena_open_max_tokens": int(ATHENA_OPEN_MAX_TOKENS),
        "peer_exchange_max_tokens": int(PEER_EXCHANGE_MAX_TOKENS),
        "peer_report_max_tokens": int(PEER_REPORT_MAX_TOKENS),
        "athena_synthesis_max_tokens": int(ATHENA_SYNTHESIS_MAX_TOKENS),
        "athena_final_max_tokens": int(ATHENA_FINAL_MAX_TOKENS),
        "aria_exchange_max_tokens": int(ARIA_EXCHANGE_MAX_TOKENS),
        "artemis_exchange_max_tokens": int(ARTEMIS_EXCHANGE_MAX_TOKENS),
        "aria_report_max_tokens": int(ARIA_REPORT_MAX_TOKENS),
        "artemis_report_max_tokens": int(ARTEMIS_REPORT_MAX_TOKENS),
        "solver_generation_max_tokens": int(SOLVER_SOLVE_GENERATION.get("max_tokens", 0) or 0),
        "agent_generation_max_tokens": int(AGENT_REVIEW_GENERATION.get("max_tokens", 0) or 0),
        "clerk_generation_max_tokens": int(CLERK_PATCH_GENERATION.get("max_tokens", 0) or 0),
    }


def emit_json_event(payload: dict[str, Any], *, force: bool = False) -> None:
    if bool(force) or bool(CONTROLLER_JSON_EVENTS):
        print(json.dumps(dict(payload or {}), ensure_ascii=False, separators=(",", ":")), flush=True)


def _time_log_ref() -> list[dict[str, Any]]:
    key = str(CB075_TIME_RECORD_GLOBAL_KEY or "CB075_TURN_TIMING_LOG")
    current = globals().get(key)
    if isinstance(current, list):
        return current
    created: list[dict[str, Any]] = []
    globals()[key] = created
    return created


def _record_turn_timing(payload: dict[str, Any]) -> None:
    if not bool(CB075_TIME_RECORD_ENABLED):
        return
    row = dict(payload or {})
    _time_log_ref().append(dict(row))
    if bool(CB075_TIME_RECORD_JSON):
        emit_json_event({"event": "cb075_turn_timing", **row}, force=False)


def require_generation_profile(name: str) -> dict[str, Any]:
    profile = globals().get(name)
    if isinstance(profile, dict) and profile:
        return dict(profile)
    raise RuntimeError(f"{name} is not defined in this kernel. Run CB6.5 first, then rerun CB7.")


def require_runtime_state() -> dict[str, Any]:
    runtime_state = globals().get("RUNTIME")
    if not isinstance(runtime_state, dict):
        raise RuntimeError("RUNTIME is not initialized in this kernel. Run CB8 first, then rerun CB7.")
    return runtime_state


SOLVER_RUNTIME_LABEL = resolve_runtime_label("solver", "solver")
CLERK_RUNTIME_LABEL = resolve_runtime_label("clerk", "clerk")
AGENT_RUNTIME_LABEL = resolve_runtime_label("agent", "agent")

SOLVER_DISPLAY_NAME = resolve_role_name(SOLVER_RUNTIME_LABEL, str(globals().get("SOLVER_ROLE_NAME", "Athena")))
CLERK_DISPLAY_NAME = resolve_role_name(CLERK_RUNTIME_LABEL, str(globals().get("CLERK_ROLE_NAME", "Artemis")))
AGENT_DISPLAY_NAME = resolve_role_name(AGENT_RUNTIME_LABEL, str(globals().get("AGENT_ROLE_NAME", "Aria")))

SOLVER_SOLVE_GENERATION = require_generation_profile("SOLVER_SOLVE_GENERATION")
CLERK_PATCH_GENERATION = require_generation_profile("CLERK_PATCH_GENERATION")
AGENT_REVIEW_GENERATION = require_generation_profile("AGENT_REVIEW_GENERATION")


def runtime_session_for_role(runtime_state: dict[str, Any], role_key: str) -> Any:
    runtime_label = resolve_runtime_label(role_key, role_key)
    runtime_sessions = runtime_state.get("runtime_sessions")
    if isinstance(runtime_sessions, dict) and runtime_label in runtime_sessions:
        return runtime_sessions[runtime_label]
    return runtime_state.get(f"{str(role_key).strip()}_session")


def _new_question_run_id() -> str:
    timestamp = time.strftime("qrun-%Y%m%d-%H%M%S")
    millis = int((time.time() % 1.0) * 1000.0)
    return f"{timestamp}-{millis:03d}"


def _reset_sessions_for_new_question(runtime_state: dict[str, Any]) -> dict[str, Any]:
    roles: list[dict[str, Any]] = []
    for role_key in ["solver", "clerk", "agent"]:
        runtime_label = resolve_runtime_label(str(role_key), str(role_key))
        session = runtime_session_for_role(runtime_state, str(role_key))
        payload = {
            "role_key": str(role_key),
            "runtime_label": str(runtime_label),
            "present": bool(session is not None),
            "reset": False,
            "error": "",
        }
        if session is not None:
            reset_fn = getattr(session, "reset_session", None)
            if callable(reset_fn):
                try:
                    reset_fn()
                    payload["reset"] = True
                except Exception as exc:
                    payload["error"] = str(exc)
        roles.append(dict(payload))
    return {
        "roles": list(roles),
        "all_reset": all(bool(row.get("reset")) for row in roles if bool(row.get("present"))),
    }


def _session_health(session: Any, *, runtime_label: str) -> dict[str, Any]:
    if session is None:
        return {
            "runtime_label": str(runtime_label),
            "present": False,
            "has_process": False,
            "process_alive": False,
            "poll_code": None,
            "reachable": False,
            "error": "missing_session",
        }
    process = getattr(session, "server_process", None)
    has_process = process is not None
    poll_code: int | None = None
    process_alive = True
    if has_process:
        try:
            poll_result = process.poll()
            poll_code = None if poll_result is None else int(poll_result)
            process_alive = poll_result is None
        except Exception:
            process_alive = False
    reachable = False
    reachable_error = ""
    try:
        client = getattr(session, "client", None)
        models_api = getattr(client, "models", None)
        list_fn = getattr(models_api, "list", None)
        if callable(list_fn):
            list_fn()
            reachable = True
        else:
            reachable_error = "missing_models_list"
    except Exception as exc:
        reachable_error = str(exc)[:500]
    return {
        "runtime_label": str(runtime_label),
        "present": True,
        "has_process": bool(has_process),
        "process_alive": bool(process_alive),
        "poll_code": poll_code,
        "reachable": bool(reachable),
        "error": str(reachable_error),
    }


def _runtime_health_report(runtime_state: dict[str, Any]) -> dict[str, Any]:
    labels = {
        "solver": str(SOLVER_RUNTIME_LABEL),
        "clerk": str(CLERK_RUNTIME_LABEL),
        "agent": str(AGENT_RUNTIME_LABEL),
    }
    roles: dict[str, Any] = {}
    any_dead = False
    for role_key, runtime_label in labels.items():
        session = runtime_session_for_role(runtime_state, role_key)
        health = _session_health(session, runtime_label=str(runtime_label))
        roles[str(role_key)] = dict(health)
        if not bool(health.get("present")):
            any_dead = True
        elif bool(health.get("has_process")) and not bool(health.get("process_alive")):
            any_dead = True
        elif not bool(health.get("reachable")):
            any_dead = True
    return {"roles": dict(roles), "any_dead": bool(any_dead)}


def _ensure_runtime_sessions_alive() -> dict[str, Any]:
    runtime_state = require_runtime_state()
    health_before = _runtime_health_report(runtime_state)
    if not bool(health_before.get("any_dead")):
        return runtime_state
    emit_json_event(
        {
            "event": "cb075_runtime_health_before_recovery",
            "roles": dict(health_before.get("roles") or {}),
        },
        force=False,
    )
    if not bool(AUTO_RECOVER_RUNTIME_ON_DEAD_SERVER):
        raise RuntimeError("runtime health check failed and auto-recovery is disabled.")
    starter = globals().get("start_aen_runtime")
    if not callable(starter):
        raise RuntimeError("runtime health check failed and start_aen_runtime is unavailable.")
    recovered = starter()
    if not isinstance(recovered, dict):
        raise RuntimeError("runtime recovery returned invalid runtime state.")
    globals()["RUNTIME"] = recovered
    health_after = _runtime_health_report(recovered)
    emit_json_event(
        {
            "event": "cb075_runtime_health_after_recovery",
            "roles": dict(health_after.get("roles") or {}),
            "recovered": not bool(health_after.get("any_dead")),
        },
        force=False,
    )
    if bool(health_after.get("any_dead")):
        raise RuntimeError("runtime recovery attempted but one or more sessions remain unavailable.")
    return recovered


def _wrap_role_content(*, speaker: str, text: str, as_report: bool = False) -> str:
    tag = role_payload_tag(str(speaker))
    body = _clean_text(text) or "[empty]"
    return f"<{tag}>{body}</{tag}>"


def _build_failure(*, phase: str, turn: int, speaker: str, prompt: str, error_message: str, session: Any | None = None) -> dict[str, Any]:
    tails = {"stdout_tail": "", "stderr_tail": ""}
    if session is not None:
        metadata = dict(getattr(session, "server_metadata", {}) or {})
        reader = globals().get("read_log_tail")
        if callable(reader):
            try:
                tails["stdout_tail"] = str(reader(metadata.get("stdout_log")))[-4000:]
            except Exception:
                tails["stdout_tail"] = ""
            try:
                tails["stderr_tail"] = str(reader(metadata.get("stderr_log")))[-4000:]
            except Exception:
                tails["stderr_tail"] = ""
    return {
        "event": "cb075_failure_diagnostic",
        "phase": str(phase),
        "turn": int(turn),
        "speaker": str(speaker),
        "error_type": "RuntimeError",
        "error_message": str(error_message),
        "prompt_chars": len(str(prompt or "")),
        "prompt_preview": "[redacted_controller_prompt]",
        "stdout_tail": str(tails["stdout_tail"]),
        "stderr_tail": str(tails["stderr_tail"]),
    }


def _prepare_generation(session: Any, prompt: str, generation_profile: dict[str, Any]) -> dict[str, Any]:
    generation = dict(generation_profile or {})
    preview_fn = globals().get("preview_session_turn_prompt")
    if not callable(preview_fn):
        return generation
    try:
        preview = preview_fn(
            session=session,
            prompt=str(prompt),
            requested_max_tokens=int(generation.get("max_tokens", 256) or 256),
        )
        if isinstance(preview, dict):
            resolved = int(preview.get("resolved_max_tokens", generation.get("max_tokens", 256)) or generation.get("max_tokens", 256))
            generation["max_tokens"] = max(1, int(resolved))
    except Exception:
        pass
    return generation


def _run_model_turn(*, speaker: str, phase: str, session: Any, prompt: str, generation: dict[str, Any], turn_number: int) -> dict[str, Any]:
    phase_name = str(phase or "").strip().lower()
    if bool(PRINT_PROGRESS_LINES):
        label = f"{speaker} turn {int(turn_number)}"
        if phase_name.endswith("_repair"):
            base_phase = phase_name[: -len("_repair")]
            if base_phase.endswith("_report"):
                label = f"{speaker} report repair turn {int(turn_number)}"
            elif base_phase == "athena_synthesis":
                label = f"{speaker} synthesis repair turn {int(turn_number)}"
            elif base_phase == "athena_finalization":
                label = f"{speaker} final repair turn {int(turn_number)}"
            else:
                label = f"{speaker} repair turn {int(turn_number)}"
        elif phase_name.endswith("_report"):
            label = f"{speaker} report turn {int(turn_number)}"
        elif phase_name == "athena_synthesis":
            label = f"{speaker} synthesis turn {int(turn_number)}"
        elif phase_name == "athena_finalization":
            label = f"{speaker} final turn {int(turn_number)}"
        print(f"cb075_progress = generating {label}", flush=True)
    previous_stream_flag = globals().get("ENABLE_TOKEN_STREAMING")
    previous_stream_prefix = globals().get("STREAM_PRINT_ROLE_PREFIX")
    started = time.perf_counter()
    try:
        if bool(CONTROLLER_RESET_SESSION_EACH_TURN):
            session.reset_session()
        if bool(SILENT_CONTROLLER_STREAM):
            globals()["ENABLE_TOKEN_STREAMING"] = False
            globals()["STREAM_PRINT_ROLE_PREFIX"] = False
        prepared_generation = _prepare_generation(session, str(prompt), dict(generation))
        result = session.execute_user_turn(str(prompt), dict(prepared_generation))
    except Exception as exc:
        wall_seconds = round(float(time.perf_counter() - started), 4)
        _record_turn_timing(
            {
                "turn": int(turn_number),
                "speaker": str(speaker),
                "phase": str(phase),
                "runtime_label": str(speaker),
                "ok": False,
                "wall_seconds": float(wall_seconds),
            }
        )
        return {
            "ok": False,
            "wall_seconds": float(wall_seconds),
            "failure": _build_failure(
                phase=str(phase),
                turn=int(turn_number),
                speaker=str(speaker),
                prompt=str(prompt),
                error_message=str(exc),
                session=session,
            ),
        }
    finally:
        if bool(SILENT_CONTROLLER_STREAM):
            if previous_stream_flag is None:
                globals().pop("ENABLE_TOKEN_STREAMING", None)
            else:
                globals()["ENABLE_TOKEN_STREAMING"] = previous_stream_flag
            if previous_stream_prefix is None:
                globals().pop("STREAM_PRINT_ROLE_PREFIX", None)
            else:
                globals()["STREAM_PRINT_ROLE_PREFIX"] = previous_stream_prefix

    metadata = dict(getattr(session, "server_metadata", {}) or {})
    effective_spec = dict(metadata.get("effective_spec") or {})
    runtime_label = str(effective_spec.get("runtime_label") or speaker)
    wall_seconds = round(float(time.perf_counter() - started), 4)
    _record_turn_timing(
        {
            "turn": int(turn_number),
            "speaker": str(speaker),
            "phase": str(phase),
            "runtime_label": str(runtime_label),
            "ok": True,
            "wall_seconds": float(wall_seconds),
        }
    )
    return {
        "ok": True,
        "turn": int(turn_number),
        "speaker": str(speaker),
        "phase": str(phase),
        "runtime_label": str(runtime_label),
        "wall_seconds": float(wall_seconds),
        "prompt": str(prompt),
        "visible": _clean_text(result.get("visible_text") or result.get("raw_text") or ""),
        "result": {**dict(result or {}), "think_tags_detected": bool(has_visible_think_tags(result.get("visible_text") or result.get("raw_text") or ""))} if callable(globals().get("has_visible_think_tags")) else dict(result or {}),
    }


def _commit_turn(*, turn_output: dict[str, Any], transcript: list[dict[str, Any]], canonical_visible: str = "") -> str:
    visible = str(turn_output.get("visible", ""))
    result_payload = dict(turn_output.get("result") or {})
    usage_payload = dict(result_payload.get("usage") or {})
    prompt_tokens_used = int(
        result_payload.get("prompt_tokens_used", usage_payload.get("prompt_tokens", 0) or 0) or 0
    )
    generated_tokens = int(
        result_payload.get("generated_tokens", usage_payload.get("completion_tokens", 0) or 0) or 0
    )
    total_tokens_used = int(
        usage_payload.get("total_tokens", prompt_tokens_used + generated_tokens) or (prompt_tokens_used + generated_tokens)
    )
    transcript.append(
        {
            "turn": int(turn_output.get("turn", 0) or 0),
            "speaker": str(turn_output.get("speaker", "Unknown")),
            "phase": str(turn_output.get("phase", "")),
            "runtime_label": str(turn_output.get("runtime_label", "")),
            "wall_seconds": float(turn_output.get("wall_seconds", 0.0) or 0.0),
            "text": str(canonical_visible or visible),
            "visible_text": str(canonical_visible or visible),
            "prompt_tokens_used": int(prompt_tokens_used),
            "generated_tokens": int(generated_tokens),
            "total_tokens_used": int(total_tokens_used),
            "usage": dict(usage_payload),
            "generation_metadata": dict(safe_generation_metadata(result_payload)) if callable(globals().get("safe_generation_metadata")) else {
                key: result_payload.get(key)
                for key in ["usage", "prompt_tokens_used", "generated_tokens", "total_tokens_used", "finish_reason", "think_tags_detected"]
                if key in result_payload
            },
        }
    )
    return str(visible)


def _render_transcript_text(transcript: list[dict[str, Any]]) -> str:
    builder = globals().get("build_transcript_text")
    if callable(builder):
        try:
            return str(builder(list(transcript or [])))
        except Exception:
            pass
    rendered: list[str] = []
    for row in list(transcript or []):
        speaker = str(row.get("speaker", "Unknown"))
        text = str(row.get("visible_text", row.get("text", ""))).strip() or "[empty]"
        rendered.append(f"{speaker}:\n{text}")
    return "\n\n".join(rendered)


def _summarize_token_proof(transcript: list[dict[str, Any]]) -> dict[str, Any]:
    totals = {
        "turns_with_usage": 0,
        "total_prompt_tokens": 0,
        "total_completion_tokens": 0,
        "total_tokens": 0,
        "roles": {},
    }
    role_rows: dict[str, dict[str, Any]] = {}
    for row in list(transcript or []):
        prompt_tokens = int(row.get("prompt_tokens_used", 0) or 0)
        completion_tokens = int(row.get("generated_tokens", 0) or 0)
        total_tokens = int(row.get("total_tokens_used", prompt_tokens + completion_tokens) or (prompt_tokens + completion_tokens))
        if prompt_tokens <= 0 and completion_tokens <= 0 and total_tokens <= 0:
            continue
        totals["turns_with_usage"] = int(totals.get("turns_with_usage", 0) or 0) + 1
        totals["total_prompt_tokens"] = int(totals.get("total_prompt_tokens", 0) or 0) + prompt_tokens
        totals["total_completion_tokens"] = int(totals.get("total_completion_tokens", 0) or 0) + completion_tokens
        totals["total_tokens"] = int(totals.get("total_tokens", 0) or 0) + total_tokens
        runtime_label = str(row.get("runtime_label", row.get("speaker", "unknown")) or "unknown").strip() or "unknown"
        speaker = str(row.get("speaker", runtime_label) or runtime_label)
        bucket = role_rows.setdefault(
            runtime_label,
            {
                "runtime_label": str(runtime_label),
                "speaker": str(speaker),
                "turns": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            },
        )
        bucket["turns"] = int(bucket.get("turns", 0) or 0) + 1
        bucket["prompt_tokens"] = int(bucket.get("prompt_tokens", 0) or 0) + prompt_tokens
        bucket["completion_tokens"] = int(bucket.get("completion_tokens", 0) or 0) + completion_tokens
        bucket["total_tokens"] = int(bucket.get("total_tokens", 0) or 0) + total_tokens
    totals["roles"] = {str(key): dict(value) for key, value in role_rows.items()}
    return dict(totals)


def _normalize_submission_answer_safe(raw_text: str) -> str:
    normalizer = globals().get("normalize_submission_answer")
    if callable(normalizer):
        try:
            return str(normalizer(str(raw_text), fallback="none"))
        except Exception:
            pass
    token = parse_final_token(str(raw_text))
    return str(token if token != "none" else "none")


def _resolve_protocol_verified_submission_answer(*, verified: bool, submission_answer: str, final_answer_text: str) -> str:
    direct = str(submission_answer or "none").strip()
    if not bool(verified):
        return "none"
    if direct and direct.lower() != "none":
        return direct
    recovered = _normalize_submission_answer_safe(str(final_answer_text))
    return str(recovered if recovered != "none" else "none")


def _observed_final_from_parsed(parsed: dict[str, Any]) -> str:
    payload = dict(parsed or {})
    observed = _clean_text(payload.get("observed_final_answer_text", "none"))
    if observed and str(observed).lower() != "none":
        return str(observed)
    candidate = normalize_candidate_answer(str(payload.get("candidate_answer", "none") or "none"))
    if candidate == "none":
        candidate = normalize_candidate_answer(str(payload.get("explicit_closeout_answer", "none") or "none"))
    if candidate == "none":
        return "none"
    confidence = int(payload.get("explicit_closeout_confidence_pct", payload.get("confidence_pct", 0)) or 0)
    return str(emit_final(candidate, confidence_pct=max(0, min(100, int(confidence)))))


def _role_turn_contract_ok(
    *,
    speaker: str,
    role_text: str,
    as_report: bool,
    phase: str = "",
    route: dict[str, Any] | None = None,
) -> tuple[bool, str]:
    # Controller is fail-open on stylistic/output-contract variance.
    # Extraction and downstream closeout logic decide usefulness; formatting alone never aborts a run.
    return True, ""


def _canonicalize_role_turn_body(
    *,
    speaker: str,
    role_text: str,
    as_report: bool,
    phase: str = "",
    route: dict[str, Any] | None = None,
) -> str:
    canonical_role = canonical_role_name(str(speaker))
    cleaned_role_text = str(role_text or "")
    section_parser = globals().get("parse_controller_sections")
    if callable(section_parser) and section_parser(cleaned_role_text):
        if bool(as_report):
            cleaned_role_text = strip_boxed_confidence_from_report_sections(cleaned_role_text)
            return str(cleaned_role_text)
        if canonical_role == "Athena" and str(dict(route or {}).get("stage", "")).lower() == "synthesis":
            parsed = dict(parse_athena_turn(cleaned_role_text, require_final_block=True))
            if not bool(parsed.get("athena_final_block_valid", False)):
                return str(cleaned_role_text)
            candidate = normalize_candidate_answer(str(parsed.get("candidate_answer", "none") or "none"))
            confidence = int(parsed.get("confidence_pct", 0) or 0)
            closeout = emit_final(candidate, confidence_pct=confidence) if candidate != "none" else "none"
            return re.sub(
                r"(<final_answer_block[^>]*>)[\s\S]*?(</final_answer_block>)",
                lambda match: f"{match.group(1)}\n{closeout}\n{match.group(2)}",
                str(cleaned_role_text),
                count=1,
                flags=re.IGNORECASE,
            )
        return str(cleaned_role_text)
    if bool(as_report):
        return str(parse_peer_report(cleaned_role_text, role_name=str(speaker)))
    phase_name = str(phase or "").strip().lower()
    loop_no = int(dict(route or {}).get("loop_no", 0) or 0)
    if canonical_role == "Athena" and phase_name == "athena_open" and int(loop_no) == 1:
        return str(cleaned_role_text)
    parsed = dict(parse_peer_turn(cleaned_role_text, role_name=str(speaker)))
    if not bool(parsed.get("explicit_closeout_valid")):
        return str(cleaned_role_text)
    canonical_closeout = _clean_text(parsed.get("canonical_closeout", ""))
    body = _clean_text(parsed.get("body", ""))
    if not canonical_closeout:
        return str(cleaned_role_text)
    if body:
        return _clean_text(f"{canonical_closeout}\n{body}")
    return str(canonical_closeout)


def _run_role_text_turn(
    *,
    speaker: str,
    phase: str,
    session: Any,
    problem_text: str,
    prompt_state: dict[str, Any],
    route: dict[str, Any],
    generation_base: dict[str, Any],
    token_limit: int,
    repair_attempts: int,
    turn_index: int,
    transcript: list[dict[str, Any]],
    trace_text: str = "",
    as_report: bool = False,
) -> tuple[int, dict[str, Any]]:
    def _contract_phase_for_turn() -> str:
        role = canonical_role_name(str(speaker))
        route_view = dict(route or {})
        stage = str(route_view.get("stage", ""))
        phase_value = str(route_view.get("phase", phase))
        exchange_no = int(route_view.get("exchange_no", 0) or 0)
        if role == "Athena" and stage == "synthesis":
            return "athena_synthesis"
        if role == "Athena":
            return "athena_open"
        if stage == "peer_report":
            return "peer_report"
        if role in {"Aria", "Artemis"} and exchange_no <= 1:
            return "peer_exchange_1"
        if role == "Artemis" and phase_value in {"forced_solve", "artemis_forced_solve"}:
            return "forced_solve"
        return "solve"

    prompt = build_model_payload_prompt(
        problem_text=str(problem_text),
        prompt_state=dict(prompt_state),
        route=dict(route),
        trace_text=str(trace_text),
    )
    if not _clean_text(prompt):
        raise RuntimeError(
            f"empty prompt generated for {speaker} during {phase}; "
            "rerun CB7 before CB07.5 and verify the active problem source is loaded"
        )
    generation = dict(generation_base)
    generation["max_tokens"] = min(int(generation.get("max_tokens", token_limit) or token_limit), int(token_limit))
    turn = _run_model_turn(
        speaker=str(speaker),
        phase=str(phase),
        session=session,
        prompt=str(prompt),
        generation=dict(generation),
        turn_number=int(turn_index) + 1,
    )
    if not bool(turn.get("ok")):
        return int(turn_index), {"ok": False, "failure": dict(turn.get("failure") or {})}

    turn_index += 1
    committed_turn = dict(turn)
    visible = str(turn.get("visible", ""))
    role_text = parse_role_text(str(visible), role_name=str(speaker)) or _clean_text(visible)
    contract_phase = _contract_phase_for_turn()
    diagnostics_fn = globals().get("section_contract_diagnostics")
    contract_diagnostics = (
        dict(diagnostics_fn(str(speaker), str(contract_phase), str(role_text)))
        if callable(diagnostics_fn)
        else {"valid": True, "missing_sections": [], "think_tags_detected": False}
    )
    think_detector = globals().get("has_visible_think_tags")
    if callable(think_detector) and bool(think_detector(str(visible))):
        contract_diagnostics["think_tags_detected"] = True
        contract_diagnostics["valid"] = False
    contract_valid = bool(contract_diagnostics.get("valid", True))
    if not contract_valid:
        canonical_body = _clean_text(role_text) or _clean_text(visible)
        canonical_visible = _wrap_role_content(speaker=str(speaker), text=canonical_body, as_report=bool(as_report))
        _commit_turn(turn_output=committed_turn, transcript=transcript, canonical_visible=canonical_visible)
        return int(turn_index), {
            "ok": True,
            "role_text": str(canonical_body),
            "report_text": str(canonical_body) if bool(as_report) else "",
            "visible": str(visible),
            "contract_valid": False,
            "contract_diagnostics": dict(contract_diagnostics),
        }
    canonical_body = _canonicalize_role_turn_body(
        speaker=str(speaker),
        role_text=str(role_text),
        as_report=bool(as_report),
        phase=str(phase),
        route=dict(route),
    )
    if not _clean_text(canonical_body):
        canonical_body = _clean_text(role_text) or _clean_text(visible)
    report_text = str(canonical_body) if bool(as_report) else ""

    canonical_visible = _wrap_role_content(speaker=str(speaker), text=canonical_body, as_report=bool(as_report))
    _commit_turn(turn_output=committed_turn, transcript=transcript, canonical_visible=canonical_visible)

    return int(turn_index), {
        "ok": True,
        "role_text": str(canonical_body),
        "report_text": str(report_text),
        "visible": str(visible),
        "contract_valid": True,
        "contract_diagnostics": dict(contract_diagnostics),
    }


def _run_final_turn(
    *,
    session: Any,
    problem_text: str,
    prompt_state: dict[str, Any],
    generation_base: dict[str, Any],
    chosen_answer: str,
    turn_index: int,
    transcript: list[dict[str, Any]],
) -> tuple[int, dict[str, Any]]:
    prompt = build_final_prompt(problem_text=str(problem_text), prompt_state=dict(prompt_state), chosen_answer=str(chosen_answer))
    generation = dict(generation_base)
    generation["max_tokens"] = min(
        int(generation.get("max_tokens", ATHENA_FINAL_MAX_TOKENS) or ATHENA_FINAL_MAX_TOKENS),
        int(ATHENA_FINAL_MAX_TOKENS),
    )
    turn = _run_model_turn(
        speaker=str(SOLVER_DISPLAY_NAME),
        phase="athena_finalization",
        session=session,
        prompt=str(prompt),
        generation=dict(generation),
        turn_number=int(turn_index) + 1,
    )
    if not bool(turn.get("ok")):
        return int(turn_index), {"ok": False, "failure": dict(turn.get("failure") or {})}

    turn_index += 1
    committed_turn = dict(turn)
    visible = str(turn.get("visible", ""))
    closeout = dict(parse_final_closeout(str(visible)))
    token = str(closeout.get("answer", "none") or "none")
    confidence_pct = int(closeout.get("confidence_pct", 0) or 0)

    if str(token) == "none":
        fallback = dict(parse_peer_turn(str(visible), role_name=str(SOLVER_DISPLAY_NAME)))
        fallback_answer = normalize_candidate_answer(str(fallback.get("explicit_closeout_answer", "none") or "none"))
        if fallback_answer == "none":
            fallback_answer = normalize_candidate_answer(str(fallback.get("candidate_answer", "none") or "none"))
        if fallback_answer == "none":
            fallback_answer = normalize_candidate_answer(str(visible))
        token = str(fallback_answer)
        confidence_pct = int(fallback.get("confidence_pct", confidence_pct) or confidence_pct)

    if str(token) != "none":
        if int(confidence_pct) <= 0:
            confidence_pct = int(
                dict(dict(prompt_state or {}).get("closeout_resolution") or {}).get(
                    "confidence_pct",
                    dict(prompt_state or {}).get("athena_confidence_pct", 0),
                )
                or 0
            )
        final_line = emit_final(str(token), confidence_pct=int(confidence_pct))
        canonical = _wrap_role_content(
            speaker=str(SOLVER_DISPLAY_NAME),
            text=str(final_line),
            as_report=False,
        )
        _commit_turn(turn_output=committed_turn, transcript=transcript, canonical_visible=canonical)
        return int(turn_index), {
            "ok": True,
            "answer": str(token),
            "confidence_pct": int(confidence_pct),
            "final_text": str(final_line),
        }
    fallback_text = _clean_text(visible) or "none"
    canonical = _wrap_role_content(
        speaker=str(SOLVER_DISPLAY_NAME),
        text=str(fallback_text),
        as_report=False,
    )
    _commit_turn(turn_output=committed_turn, transcript=transcript, canonical_visible=canonical)
    return int(turn_index), {
        "ok": True,
        "answer": "none",
        "confidence_pct": 0,
        "final_text": str(fallback_text),
    }


def _summarize_controller_metrics(transcript: list[dict[str, Any]], state: dict[str, Any]) -> dict[str, Any]:
    solver_turns = sum(1 for row in transcript if str(row.get("speaker")) == str(SOLVER_DISPLAY_NAME))
    clerk_turns = sum(1 for row in transcript if str(row.get("speaker")) == str(CLERK_DISPLAY_NAME))
    agent_turns = sum(1 for row in transcript if str(row.get("speaker")) == str(AGENT_DISPLAY_NAME))
    return {
        "solver_turns": int(solver_turns),
        "clerk_turns": int(clerk_turns),
        "agent_turns": int(agent_turns),
        "routing_mode": str(LOOP_MECHANICS.get("controller_routing_mode", "")),
        "max_big_loops": int(MAX_BIG_LOOPS),
        "inner_total_exchanges": int(INNER_TOTAL_EXCHANGES),
        "inner_reasoning_exchanges": int(INNER_REASONING_EXCHANGES),
    }


def _summarize_timing_metrics() -> dict[str, Any]:
    rows = list(_time_log_ref())
    total_turns = len(rows)
    ok_turns = sum(1 for row in rows if bool(row.get("ok")))
    failed_turns = int(total_turns - ok_turns)
    total_wall = round(sum(float(row.get("wall_seconds", 0.0) or 0.0) for row in rows), 4)

    by_speaker: dict[str, float] = {}
    by_runtime: dict[str, float] = {}
    for row in rows:
        if not bool(row.get("ok")):
            continue
        speaker = str(row.get("speaker", "unknown"))
        runtime_label = str(row.get("runtime_label", "unknown"))
        wall = float(row.get("wall_seconds", 0.0) or 0.0)
        by_speaker[speaker] = float(by_speaker.get(speaker, 0.0) + wall)
        by_runtime[runtime_label] = float(by_runtime.get(runtime_label, 0.0) + wall)

    return {
        "enabled": bool(CB075_TIME_RECORD_ENABLED),
        "total_turns_timed": int(total_turns),
        "ok_turns_timed": int(ok_turns),
        "failed_turns_timed": int(failed_turns),
        "sum_turn_wall_seconds": float(round(total_wall, 4)),
        "speaker_wall_seconds": {str(k): float(round(v, 4)) for k, v in by_speaker.items()},
        "runtime_wall_seconds": {str(k): float(round(v, 4)) for k, v in by_runtime.items()},
    }


def _refresh_athena_confidence_rubric_state(state: dict[str, Any], *, stage: str) -> dict[str, Any]:
    stage_name = str(stage or state.get("athena_stage", "solve") or "solve").strip().lower()
    peer_meta = dict(state.get("peer_report_meta") or {})
    aria_meta = dict(peer_meta.get("Aria") or {})
    artemis_meta = dict(peer_meta.get("Artemis") or {})
    athena_candidate = normalize_candidate_answer(str(state.get("athena_candidate_answer", "none")))
    athena_exact_candidate = normalize_candidate_answer(str(state.get("athena_exact_candidate_answer", athena_candidate)))
    exact_integer_candidate_exists = bool(athena_exact_candidate != "none")
    coherent_route_present = bool(_clean_text(state.get("athena_last_message", "")))
    peer_reports_present = bool(_clean_text(aria_meta.get("text", ""))) and bool(_clean_text(artemis_meta.get("text", "")))
    schemas_valid = bool(aria_meta.get("schema_valid")) and bool(artemis_meta.get("schema_valid"))
    aria_exact_candidate = str(aria_meta.get("candidate_exact_integer", "none") or "none")
    artemis_exact_candidate = str(artemis_meta.get("candidate_exact_integer", "none") or "none")
    aria_exact_candidate_matches = bool(exact_integer_candidate_exists and athena_exact_candidate == aria_exact_candidate and aria_exact_candidate != "none")
    artemis_exact_candidate_matches = bool(exact_integer_candidate_exists and athena_exact_candidate == artemis_exact_candidate and artemis_exact_candidate != "none")
    peers_exactly_align = bool(aria_exact_candidate != "none" and aria_exact_candidate == artemis_exact_candidate)
    report_similarity = _report_similarity_score(str(aria_meta.get("text", "")), str(artemis_meta.get("text", "")))
    shared_field_count = _shared_report_field_count(
        dict(aria_meta.get("extracted_fields") or {}),
        dict(artemis_meta.get("extracted_fields") or {}),
    )
    peer_reports_distinct = (
        bool(aria_meta.get("signature"))
        and bool(artemis_meta.get("signature"))
        and str(aria_meta.get("signature")) != str(artemis_meta.get("signature"))
        and float(report_similarity) < 0.88
        and int(shared_field_count) <= 2
    )
    trio_exact_alignment = bool(peers_exactly_align and aria_exact_candidate_matches and artemis_exact_candidate_matches)
    substantive_open_objections = []
    for item in list(state.get("open_objections") or []):
        objection = _clean_text(item)
        if not objection:
            continue
        lower = objection.lower()
        if "confidence strictly above" in lower or "validator confidence" in lower:
            continue
        substantive_open_objections.append(str(objection))
    main_objections_resolved = not bool(substantive_open_objections)
    phase_is_synthesis = bool(stage_name == "synthesis")
    phase_is_finalization = bool(stage_name == "finalization")
    pending_final_candidate_selected = bool(normalize_candidate_answer(str(state.get("pending_final_candidate", "none"))) != "none")

    if stage_name == "decompose":
        band = "decompose"
        ceiling = 0
    elif bool(phase_is_finalization):
        band = "finalization_only"
        ceiling = 99
    elif bool(pending_final_candidate_selected):
        band = "pending_finalization"
        ceiling = 95
    elif not bool(exact_integer_candidate_exists) or not bool(coherent_route_present):
        band = "unknown_or_unstable"
        ceiling = 58
    elif not bool(peer_reports_present):
        band = "candidate_only"
        ceiling = 68
    elif not bool(schemas_valid):
        band = "peer_schema_incomplete"
        ceiling = 72
    elif not bool(peers_exactly_align):
        band = "peer_disagreement_open"
        ceiling = 79 if bool(aria_exact_candidate_matches or artemis_exact_candidate_matches) else 74
    elif not bool(trio_exact_alignment):
        band = "peer_aligned_waiting_athena"
        ceiling = 84
    elif not bool(peer_reports_distinct):
        band = "aligned_reports_collapsed"
        ceiling = 84
    elif not bool(main_objections_resolved):
        band = "aligned_objections_open"
        ceiling = 87
    elif bool(phase_is_synthesis):
        band = "synthesis_pass_ready"
        ceiling = 92
    else:
        band = "aligned_pre_synthesis"
        ceiling = 89

    checklist = {
        "exact_integer_candidate_exists": bool(exact_integer_candidate_exists),
        "coherent_route_present": bool(coherent_route_present),
        "peer_reports_present": bool(peer_reports_present),
        "peer_reports_schema_valid": bool(schemas_valid),
        "aria_exact_candidate_matches": bool(aria_exact_candidate_matches),
        "artemis_exact_candidate_matches": bool(artemis_exact_candidate_matches),
        "peers_exactly_align": bool(peers_exactly_align),
        "peer_reports_distinct": bool(peer_reports_distinct),
        "main_objections_resolved": bool(main_objections_resolved),
        "phase_is_synthesis": bool(phase_is_synthesis),
        "phase_is_finalization": bool(phase_is_finalization),
        "pending_final_candidate_selected": bool(pending_final_candidate_selected),
    }
    checklist_summary = "; ".join(
        f"{key}={'yes' if bool(value) else 'no'}" for key, value in checklist.items()
    )

    state["athena_confidence_rubric_band"] = str(band)
    state["athena_confidence_rubric_ceiling"] = int(ceiling)
    state["athena_confidence_checklist"] = dict(checklist)
    state["athena_confidence_checklist_summary"] = str(checklist_summary)
    return {
        "band": str(band),
        "ceiling": int(ceiling),
        "checklist": dict(checklist),
        "checklist_summary": str(checklist_summary),
        "report_similarity": float(report_similarity),
        "shared_report_fields": int(shared_field_count),
        "substantive_open_objections": list(substantive_open_objections),
    }


def _update_athena_state(state: dict[str, Any], parsed: dict[str, Any], *, loop_no: int, stage: str) -> None:
    state["athena_last_message"] = str(parsed.get("role_text", ""))
    supplied_confidence = int(parsed.get("confidence_pct", state.get("athena_supplied_confidence_pct", 0)) or 0)
    parsed_confidence = int(supplied_confidence)
    if str(stage) == "decompose":
        supplied_confidence = 0
        parsed_confidence = 0
    candidate = str(parsed.get("candidate_answer", "none") or "none")
    exact_candidate = str(parsed.get("explicit_closeout_answer", "none") or "none")
    if exact_candidate == "none":
        exact_candidate = str(candidate)
    if candidate == "none" and str(stage) != "decompose":
        exact_candidate = "none"
        parsed_confidence = min(int(parsed_confidence), 35)
    state["athena_candidate_answer"] = str(candidate if candidate != "none" else state.get("athena_candidate_answer", "none"))
    state["athena_exact_candidate_answer"] = str(exact_candidate if exact_candidate != "none" else "none")
    state["athena_candidate_is_exact_integer"] = bool(str(state.get("athena_exact_candidate_answer", "none")) != "none")
    rubric = dict(_refresh_athena_confidence_rubric_state(state, stage=str(stage)))
    combined_ceiling = min(
        _coerce_int(state.get("controller_confidence_ceiling"), 100),
        int(rubric.get("ceiling", 100) or 100),
    )
    if str(stage) != "decompose":
        supplied_confidence = max(0, min(100, int(supplied_confidence)))
        parsed_confidence = min(int(parsed_confidence), int(combined_ceiling))
    state["athena_supplied_confidence_pct"] = int(supplied_confidence)
    state["athena_confidence_pct"] = int(parsed_confidence)
    state["recent_summary"] = list(state.get("recent_summary") or []) + [
        {
            "speaker": "Athena",
            "loop": int(loop_no),
            "stage": str(stage),
            "supplied_confidence_pct": int(state.get("athena_supplied_confidence_pct", 0) or 0),
            "confidence_pct": int(state.get("athena_confidence_pct", 0) or 0),
            "candidate_answer": str(state.get("athena_candidate_answer", "none")),
            "exact_candidate_answer": str(state.get("athena_exact_candidate_answer", "none")),
            "peer_validation_status": str(state.get("peer_validation_status", "not_started") or "not_started"),
            "controller_confidence_ceiling": int(state.get("controller_confidence_ceiling", 0) or 0),
            "athena_confidence_rubric_band": str(state.get("athena_confidence_rubric_band", "")),
            "athena_confidence_rubric_ceiling": int(state.get("athena_confidence_rubric_ceiling", 0) or 0),
        }
    ]


def _matches_report_header(line: str, label: str) -> re.Match[str] | None:
    return re.match(
        rf"^\s*(?:[-*]\s*)?(?:\*\*)?\s*{re.escape(str(label))}\s*:\s*(?:\*\*)?\s*(.*)$",
        str(line or ""),
        flags=re.IGNORECASE,
    )


def _extract_report_line(text: str, field_names: list[str] | tuple[str, ...] | str) -> str:
    cleaned = _clean_text(text)
    labels = [str(field_names)] if isinstance(field_names, str) else [str(item) for item in list(field_names or [])]
    stop_labels = list(dict.fromkeys([*_required_report_fields("Aria"), *_required_report_fields("Artemis"), "Lens"]))
    lines = str(cleaned).split("\n")
    for label in labels:
        for idx, raw_line in enumerate(lines):
            match = _matches_report_header(raw_line, str(label))
            if not match:
                continue
            collected: list[str] = []
            same_line_value = _clean_text(match.group(1))
            if same_line_value:
                collected.append(str(same_line_value))
            for follow_line in lines[idx + 1 :]:
                stripped = str(follow_line).strip()
                if not stripped:
                    if collected:
                        collected.append("")
                    continue
                if stripped.startswith("\\boxed{"):
                    break
                if any(
                    _matches_report_header(stripped, stop_label)
                    for stop_label in stop_labels
                    if str(stop_label).strip().lower() != str(label).strip().lower()
                ):
                    break
                collected.append(stripped)
            value = _clean_text("\n".join(collected))
            if value:
                return str(value)
    return ""


def _extract_exact_integer_field(text: str, field_names: list[str] | tuple[str, ...] | str) -> str:
    value = _extract_report_line(text, field_names)
    cleaned = _clean_text(value)
    if not cleaned:
        return "none"
    if not re.fullmatch(r"[+-]?\d+", cleaned):
        return "none"
    return str(int(cleaned))


def _required_report_fields(role_name: str) -> list[str]:
    role = canonical_role_name(role_name)
    if role == "Aria":
        return ["report_slots", "report"]
    if role == "Artemis":
        return ["report_slots", "report"]
    return []

def _normalize_report_signature(text: str) -> str:
    cleaned = _clean_text(text).lower()
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned)
    return " ".join(cleaned.split())


def _report_similarity_score(left_text: str, right_text: str) -> float:
    left = _normalize_report_signature(str(left_text))
    right = _normalize_report_signature(str(right_text))
    if not left or not right:
        return 0.0
    try:
        return float(SequenceMatcher(None, left, right).ratio())
    except Exception:
        return 0.0


def _shared_report_field_count(left_fields: dict[str, Any], right_fields: dict[str, Any]) -> int:
    shared = 0
    left_map = dict(left_fields or {})
    right_map = dict(right_fields or {})
    for key in sorted(set(left_map).intersection(set(right_map))):
        left_value = _normalize_report_signature(str(left_map.get(key, "")))
        right_value = _normalize_report_signature(str(right_map.get(key, "")))
        if left_value and right_value and left_value == right_value:
            shared += 1
    return int(shared)


def _extract_answer_signal(text: Any) -> dict[str, Any]:
    cleaned = _clean_text(text)
    candidate = "none"
    confidence = 0
    source = "none"
    sections: dict[str, Any] = {}
    section_parser = globals().get("parse_controller_sections")
    slot_parser = globals().get("parse_key_value_slots")
    section_getter = globals().get("section_body")
    if callable(section_parser):
        try:
            sections = dict(section_parser(str(cleaned)) or {})
        except Exception:
            sections = {}
    has_report_slots = bool(sections and "report_slots" in sections)
    if sections and callable(slot_parser) and callable(section_getter):
        try:
            slots = dict(slot_parser(str(section_getter(sections, "report_slots"))) or {})
        except Exception:
            slots = {}
        for field_name in ["candidate_answer_integer", "candidate_answer"]:
            value = _clean_text(slots.get(field_name, ""))
            if re.fullmatch(r"[+-]?\d+", value):
                candidate = str(int(value))
                source = f"report_slots.{field_name}"
                break
        confidence_value = _clean_text(slots.get("candidate_confidence", ""))
        if re.fullmatch(r"\d{1,3}", confidence_value):
            confidence = max(0, min(100, int(confidence_value)))
    boxed_confidence = re.search(
        r"\\boxed\s*\{\s*([+-]?\d+)\s*\}\s*_?\s*confidence\s*[:=]\s*\[?\s*(\d{1,3})\s*%?\s*\]?",
        cleaned,
        flags=re.IGNORECASE,
    )
    if boxed_confidence and not bool(has_report_slots):
        candidate = str(int(boxed_confidence.group(1)))
        confidence = max(0, min(100, int(boxed_confidence.group(2))))
        source = "boxed_confidence"
    elif candidate == "none" and not bool(has_report_slots):
        boxed_values = [str(int(match.group(1))) for match in re.finditer(r"\\boxed\s*\{\s*([+-]?\d+)\s*\}", cleaned, flags=re.IGNORECASE)]
        if len(set(boxed_values)) == 1:
            candidate = str(boxed_values[0])
            source = "boxed_integer"
    if confidence <= 0:
        confidence_match = re.search(r"\b(?:candidate_)?confidence\s*[:=]\s*\[?\s*(\d{1,3})\s*%?\s*\]?", cleaned, flags=re.IGNORECASE)
        if confidence_match:
            confidence = max(0, min(100, int(confidence_match.group(1))))
    return {
        "answer": str(candidate),
        "confidence_pct": int(confidence),
        "source": str(source),
    }


def _peer_report_meta(role_name: str, report_text: str) -> dict[str, Any]:
    role = canonical_role_name(role_name)
    cleaned = _clean_text(report_text)
    parsed = dict(parse_peer_turn(cleaned, role_name=str(role)))
    stance_payload = dict(classify_peer_report(cleaned))
    required_fields = list(_required_report_fields(role))
    missing_fields: list[str] = []
    extracted_fields: dict[str, str] = {}
    answer_signal = dict(_extract_answer_signal(cleaned))
    sections = dict(parsed.get("sections") or {})
    if sections:
        for field in required_fields:
            value = _clean_text(dict(sections.get(str(field)) or {}).get("body", ""))
            extracted_fields[str(field)] = str(value)
            if not value:
                missing_fields.append(str(field))
        candidate_exact_integer = str(parsed.get("candidate_answer", "none") or "none")
        confidence = int(parsed.get("confidence_pct", 0) or 0)
        open_blocker = bool(parsed.get("report_open_blocker", False))
        hard_hits = list(parsed.get("hard_blocker_hits") or [])
        schema_valid = bool(parsed.get("report_schema_valid", False)) and not bool(missing_fields)
        signal_candidate = normalize_candidate_answer(str(answer_signal.get("answer", "none") or "none"))
        signal_confidence = int(answer_signal.get("confidence_pct", 0) or 0)
        if candidate_exact_integer == "none" and signal_candidate != "none":
            candidate_exact_integer = str(signal_candidate)
        if signal_candidate != "none":
            confidence = max(int(confidence), int(signal_confidence))
        return {
            "role": str(role),
            "text": str(cleaned),
            "stance": str(stance_payload.get("stance", "neutral") or "neutral"),
            "check": str(_clean_text(parsed.get("body", "")) or "none provided"),
            "candidate": str(parsed.get("candidate_answer", "none") or "none"),
            "candidate_line": str(parsed.get("canonical_closeout", "")),
            "candidate_exact_integer": str(candidate_exact_integer),
            "candidate_is_exact_integer": bool(candidate_exact_integer != "none"),
            "confidence_pct": int(confidence),
            "answer_signal_integer": str(signal_candidate),
            "answer_signal_confidence_pct": int(signal_confidence),
            "answer_signal_source": str(answer_signal.get("source", "none") or "none"),
            "required_fields": list(required_fields),
            "missing_fields": list(dict.fromkeys(missing_fields + list(parsed.get("missing_headers") or []))),
            "schema_valid": bool(schema_valid),
            "open_blocker": bool(open_blocker),
            "hard_blocker_hits": list(hard_hits),
            "yaml_metadata_present": False,
            "signature": _normalize_report_signature(cleaned),
            "extracted_fields": dict(extracted_fields),
        }
    for field in required_fields:
        value = _extract_report_line(cleaned, field)
        extracted_fields[str(field)] = str(value)
        if not _clean_text(value):
            missing_fields.append(field)
    candidate_line = _clean_text(parsed.get("canonical_closeout", ""))
    explicit_answer = str(parsed.get("explicit_closeout_answer", "") or "").strip()
    parsed_answer = str(parsed.get("candidate_answer", "none") or "none").strip()
    candidate_exact_integer = explicit_answer if explicit_answer and explicit_answer.lower() != "none" else parsed_answer
    confidence = int(parsed.get("confidence_pct", 0) or 0)
    open_blocker = bool(parsed.get("report_open_blocker", False))
    hard_hits = list(parsed.get("hard_blocker_hits") or [])
    schema_valid = bool(parsed.get("report_schema_valid", False)) and not bool(missing_fields)
    signal_candidate = normalize_candidate_answer(str(answer_signal.get("answer", "none") or "none"))
    signal_confidence = int(answer_signal.get("confidence_pct", 0) or 0)
    if candidate_exact_integer == "none" and signal_candidate != "none":
        candidate_exact_integer = str(signal_candidate)
    if signal_candidate != "none":
        confidence = max(int(confidence), int(signal_confidence))
    return {
        "role": str(role),
        "text": str(cleaned),
        "stance": str(stance_payload.get("stance", "neutral") or "neutral"),
        "check": str(_clean_text(parsed.get("body", "")) or "none provided"),
        "candidate": str(parsed.get("candidate_answer", "none") or "none"),
        "candidate_line": str(candidate_line),
        "candidate_exact_integer": str(candidate_exact_integer),
        "candidate_is_exact_integer": bool(candidate_exact_integer != "none"),
        "confidence_pct": int(confidence),
        "answer_signal_integer": str(signal_candidate),
        "answer_signal_confidence_pct": int(signal_confidence),
        "answer_signal_source": str(answer_signal.get("source", "none") or "none"),
        "required_fields": list(required_fields),
        "missing_fields": list(dict.fromkeys(missing_fields + list(parsed.get("missing_headers") or []))),
        "schema_valid": bool(schema_valid),
        "open_blocker": bool(open_blocker),
        "hard_blocker_hits": list(hard_hits),
        "yaml_metadata_present": bool(_has_role_yaml_metadata(cleaned, role_name=role)),
        "signature": _normalize_report_signature(cleaned),
        "extracted_fields": dict(extracted_fields),
    }

def _refresh_peer_validation_state(state: dict[str, Any]) -> dict[str, Any]:
    peer_reports = dict(state.get("peer_reports") or {})
    athena_candidate = normalize_candidate_answer(str(state.get("athena_candidate_answer", "none")))
    athena_exact_candidate = normalize_candidate_answer(str(state.get("athena_exact_candidate_answer", "none")))
    athena_candidate_is_exact_integer = bool(state.get("athena_candidate_is_exact_integer", athena_exact_candidate != "none"))
    athena_confidence = int(state.get("athena_confidence_pct", 0) or 0)
    athena_supplied_confidence = int(state.get("athena_supplied_confidence_pct", athena_confidence) or 0)
    aria_meta = _peer_report_meta("Aria", str(peer_reports.get("Aria", "")))
    artemis_meta = _peer_report_meta("Artemis", str(peer_reports.get("Artemis", "")))
    report_similarity = _report_similarity_score(str(aria_meta.get("text", "")), str(artemis_meta.get("text", "")))
    shared_field_count = _shared_report_field_count(
        dict(aria_meta.get("extracted_fields") or {}),
        dict(artemis_meta.get("extracted_fields") or {}),
    )
    schemas_valid = bool(aria_meta.get("schema_valid")) and bool(artemis_meta.get("schema_valid"))
    aria_candidate = str(aria_meta.get("candidate_exact_integer", "none") or "none")
    artemis_candidate = str(artemis_meta.get("candidate_exact_integer", "none") or "none")
    reports_distinct = bool(schemas_valid and aria_candidate != "none" and artemis_candidate != "none")
    peers_align = aria_candidate != "none" and aria_candidate == artemis_candidate
    candidates_align = (
        bool(athena_candidate_is_exact_integer)
        and athena_exact_candidate != "none"
        and str(aria_candidate) == str(athena_exact_candidate)
        and str(artemis_candidate) == str(athena_exact_candidate)
    )
    peer_min_confidence = min(int(aria_meta.get("confidence_pct", 0) or 0), int(artemis_meta.get("confidence_pct", 0) or 0))
    trio_min_confidence = min(int(athena_confidence), int(peer_min_confidence)) if bool(candidates_align) else 0
    athena_confident_strict = bool(candidates_align) and int(athena_confidence) > int(BOXED_CONFIDENCE_GATE_PCT)
    all_confident_strict = (
        bool(candidates_align)
        and int(athena_confidence) > int(BOXED_CONFIDENCE_GATE_PCT)
        and int(aria_meta.get("confidence_pct", 0) or 0) > int(BOXED_CONFIDENCE_GATE_PCT)
        and int(artemis_meta.get("confidence_pct", 0) or 0) > int(BOXED_CONFIDENCE_GATE_PCT)
    )

    objections: list[str] = []
    if not bool(aria_meta.get("text")):
        objections.append("Aria final report is missing.")
    if not bool(artemis_meta.get("text")):
        objections.append("Artemis final report is missing.")
    if bool(aria_meta.get("missing_fields")):
        objections.append(f"Aria report missing header lines: {', '.join(list(aria_meta.get('missing_fields') or []))}.")
    if bool(artemis_meta.get("missing_fields")):
        objections.append(f"Artemis report missing header lines: {', '.join(list(artemis_meta.get('missing_fields') or []))}.")
    if bool(aria_meta.get("hard_blocker_hits")):
        objections.append(f"Aria report contains hard blocker language: {', '.join(list(aria_meta.get('hard_blocker_hits') or [])[:3])}.")
    if bool(artemis_meta.get("hard_blocker_hits")):
        objections.append(f"Artemis report contains hard blocker language: {', '.join(list(artemis_meta.get('hard_blocker_hits') or [])[:3])}.")
    if bool(schemas_valid) and not bool(reports_distinct):
        objections.append(
            "Aria and Artemis final reports are not yet distinct enough to count as independent proof-vs-audit validation."
        )
    if not bool(athena_candidate_is_exact_integer) or athena_exact_candidate == "none":
        objections.append("Athena does not yet have an exact integer candidate.")
    elif not bool(peers_align):
        objections.append("Aria and Artemis do not yet agree on the same exact integer answer.")
    elif not bool(candidates_align):
        objections.append("Athena has not yet reconciled to the same exact integer answer as Aria and Artemis.")
    elif not bool(all_confident_strict):
        objections.append(
            f"All three models have not yet supplied confidence strictly above {int(BOXED_CONFIDENCE_GATE_PCT)}."
        )

    if bool(candidates_align) and bool(all_confident_strict) and bool(reports_distinct):
        validation_status = "confidence_aligned"
        confidence_ceiling = 100
    elif bool(candidates_align) and not bool(reports_distinct):
        validation_status = "answer_aligned_reports_collapsed"
        confidence_ceiling = 86
    elif bool(candidates_align):
        validation_status = "answer_aligned_waiting_confidence"
        confidence_ceiling = 96
    elif bool(peers_align) and not bool(reports_distinct):
        validation_status = "peer_aligned_reports_collapsed"
        confidence_ceiling = 76
    elif bool(peers_align):
        validation_status = "peer_aligned_waiting_athena"
        confidence_ceiling = 92
    elif bool(schemas_valid):
        validation_status = "disagreement_open"
        confidence_ceiling = 78
    else:
        validation_status = "insufficient_peer_validation"
        confidence_ceiling = 60

    state["peer_report_meta"] = {"Aria": dict(aria_meta), "Artemis": dict(artemis_meta)}
    state["peer_validation_status"] = str(validation_status)
    state["controller_confidence_ceiling"] = int(confidence_ceiling)
    state["open_objections"] = list(objections or [])
    state["recent_summary"] = list(state.get("recent_summary") or []) + [
        {
            "speaker": "controller",
            "kind": "peer_validation",
            "status": str(validation_status),
            "reports_distinct": bool(reports_distinct),
            "report_similarity": float(report_similarity),
            "shared_report_fields": int(shared_field_count),
            "schemas_valid": bool(schemas_valid),
            "peers_align": bool(peers_align),
            "candidates_align": bool(candidates_align),
            "athena_confident_strict": bool(athena_confident_strict),
            "all_confident_strict": bool(all_confident_strict),
            "athena_supplied_confidence": int(athena_supplied_confidence),
            "athena_confidence": int(athena_confidence),
            "peer_min_confidence": int(peer_min_confidence),
            "trio_min_confidence": int(trio_min_confidence),
        }
    ]
    return {
        "aria_meta": dict(aria_meta),
        "artemis_meta": dict(artemis_meta),
        "reports_distinct": bool(reports_distinct),
        "report_similarity": float(report_similarity),
        "shared_report_fields": int(shared_field_count),
        "schemas_valid": bool(schemas_valid),
        "peers_align": bool(peers_align),
        "candidates_align": bool(candidates_align),
        "athena_candidate": str(athena_candidate),
        "athena_exact_candidate": str(athena_exact_candidate),
        "all_exact_integer_answers": bool(candidates_align),
        "athena_confident_strict": bool(athena_confident_strict),
        "all_confident_strict": bool(all_confident_strict),
        "athena_supplied_confidence": int(athena_supplied_confidence),
        "peer_min_confidence": int(peer_min_confidence),
        "trio_min_confidence": int(trio_min_confidence),
    }


def _peer_lock_outcome(state: dict[str, Any]) -> dict[str, Any]:
    outcome = dict(_refresh_peer_validation_state(state))
    aria_stance = str(dict(outcome.get("aria_meta") or {}).get("stance", "neutral"))
    artemis_stance = str(dict(outcome.get("artemis_meta") or {}).get("stance", "neutral"))
    state["recent_summary"] = list(state.get("recent_summary") or []) + [
        {"speaker": "Aria", "stance": str(aria_stance)},
        {"speaker": "Artemis", "stance": str(artemis_stance)},
    ]
    return {
        "reports_distinct": bool(outcome.get("reports_distinct")),
        "report_similarity": float(outcome.get("report_similarity", 0.0) or 0.0),
        "shared_report_fields": int(outcome.get("shared_report_fields", 0) or 0),
        "schemas_valid": bool(outcome.get("schemas_valid")),
        "peers_align": bool(outcome.get("peers_align")),
        "candidates_align": bool(outcome.get("candidates_align")),
        "all_exact_integer_answers": bool(outcome.get("all_exact_integer_answers")),
        "athena_confident_strict": bool(outcome.get("athena_confident_strict")),
        "all_confident_strict": bool(outcome.get("all_confident_strict")) and bool(outcome.get("reports_distinct")),
        "submission_ready": bool(outcome.get("all_exact_integer_answers"))
        and bool(outcome.get("reports_distinct"))
        and bool(outcome.get("all_confident_strict")),
        "athena_exact_candidate": str(outcome.get("athena_exact_candidate", "none")),
        "athena_supplied_confidence": int(outcome.get("athena_supplied_confidence", 0) or 0),
        "peer_min_confidence": int(outcome.get("peer_min_confidence", 0) or 0),
        "trio_min_confidence": int(outcome.get("trio_min_confidence", 0) or 0),
    }


def _resolve_hierarchical_closeout_candidate(candidates: list[dict[str, Any]]) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    role_order = {"Athena": 0, "Aria": 1, "Artemis": 2}
    for row in list(candidates or []):
        payload = dict(row or {})
        answer = normalize_candidate_answer(str(payload.get("answer", "none") or "none"))
        if answer == "none":
            continue
        role = str(payload.get("role", "unknown") or "unknown")
        confidence = max(0, min(100, _coerce_int(payload.get("confidence_pct", 0), 0)))
        rows.append(
            {
                "role": str(role),
                "answer": str(answer),
                "confidence_pct": int(confidence),
                "source": str(payload.get("source", "") or ""),
            }
        )
    if not rows:
        return {
            "mode": "unresolved",
            "answer": "none",
            "confidence_pct": 0,
            "supporting_roles": [],
            "decision_rule": "simple_arbitration_no_exact_answers",
            "candidates": [],
        }
    by_answer: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        by_answer.setdefault(str(row["answer"]), []).append(dict(row))
    majority_answer = "none"
    majority_rows: list[dict[str, Any]] = []
    for answer, answer_rows in by_answer.items():
        if len(answer_rows) > len(majority_rows):
            majority_answer = str(answer)
            majority_rows = list(answer_rows)
    if len(majority_rows) >= 2:
        confidence = max(int(row.get("confidence_pct", 0) or 0) for row in majority_rows)
        return {
            "mode": "simple_arbitration_majority" if len(majority_rows) == 2 else "simple_arbitration_unanimous",
            "answer": str(majority_answer),
            "confidence_pct": int(confidence),
            "supporting_roles": [str(row.get("role", "")) for row in majority_rows],
            "decision_rule": "if_all_three_same_take_it_else_if_two_same_take_it",
            "candidates": list(rows),
        }
    highest_confidence = max(int(row.get("confidence_pct", 0) or 0) for row in rows)
    tied = [dict(row) for row in rows if int(row.get("confidence_pct", 0) or 0) == int(highest_confidence)]
    athena_tie = [dict(row) for row in tied if str(row.get("role", "")) == "Athena"]
    selected = dict(athena_tie[0] if athena_tie else sorted(tied, key=lambda item: int(role_order.get(str(item.get("role", "")), 99)))[0])
    return {
        "mode": "simple_arbitration_highest_confidence" if len(tied) == 1 else "simple_arbitration_tie_break",
        "answer": str(selected.get("answer", "none")),
        "confidence_pct": int(selected.get("confidence_pct", 0) or 0),
        "supporting_roles": [str(selected.get("role", ""))],
        "decision_rule": "if_all_different_take_highest_confidence_tie_break_athena",
        "candidates": list(rows),
    }

def _record_contract_damage_if_any(state: dict[str, Any], outcome: dict[str, Any], *, speaker: str, phase: str) -> None:
    if bool(dict(outcome or {}).get("contract_valid", True)):
        return
    state["turn_contract_damage"] = list(state.get("turn_contract_damage") or []) + [
        {
            "speaker": str(speaker),
            "phase": str(phase),
            **dict(dict(outcome or {}).get("contract_diagnostics") or {}),
        }
    ]

def run_aen_protocol(problem_text: str) -> dict[str, Any]:
    started = time.perf_counter()
    question_run_id = _new_question_run_id()
    if bool(CB075_TIME_RECORD_ENABLED):
        _time_log_ref().clear()
    ensure_runtime_started = globals().get("ensure_runtime_started")
    if callable(ensure_runtime_started):
        ensure_runtime_started()
    live_knobs = dict(_refresh_live_controller_knobs())

    runtime_state = require_runtime_state()
    runtime_at_boot_passed = bool(runtime_state.get("runtime_at_boot_passed", False))
    runtime_at_boot_status = str(runtime_state.get("runtime_at_boot_status", "not_started") or "not_started")
    runtime_at_boot_summary = dict(runtime_state.get("runtime_at_boot_summary") or {})
    context_reset_report = {"roles": [], "all_reset": False}
    if not runtime_at_boot_passed:
        blocked_reason = str(runtime_at_boot_summary.get("blocked_reason", "") or "")
        if not blocked_reason:
            required_labels = [str(item) for item in list(runtime_state.get("runtime_at_boot_required_labels") or []) if str(item).strip()]
            blocked_reason = (
                f"Runtime-at-Boot did not pass for required roles: {', '.join(required_labels)}."
                if required_labels
                else "Runtime-at-Boot did not pass."
            )
        result = {
            "question_run_id": str(question_run_id),
            "status": "boot_gate_failed",
            "verified": False,
            "turn_index": 0,
            "loop_index": 0,
            "max_turns": int(MAX_BIG_LOOPS * (5 + (2 * INNER_TOTAL_EXCHANGES))),
            "min_conversation_turns": 1,
            "closeout_gate_turn": 0,
            "submission_answer": "none",
            "final_answer_text": "none",
            "failure": {
                "kind": "runtime_at_boot_gate_failed",
                "message": str(blocked_reason),
                "runtime_at_boot_status": str(runtime_at_boot_status),
            },
            "elapsed_seconds": round(float(time.perf_counter() - started), 4),
            "peer_validation_ready": False,
            "controller_metrics": {},
            "timing_summary": _summarize_timing_metrics() if bool(CB075_TIME_RECORD_ENABLED) else {},
            "turn_timing_log": list(_time_log_ref()) if bool(CB075_TIME_RECORD_ENABLED) else [],
            "token_proof": _summarize_token_proof([]),
            "context_reset_report": dict(context_reset_report),
            "transcript": [],
            "transcript_text": "",
            "runtime_at_boot_summary": dict(runtime_at_boot_summary),
        }
        emit_json_event(
            {
                "event": "cb075_run_blocked",
                "revision": str(CB07_CONTROLLER_REVISION),
                "status": str(result.get("status", "")),
                "runtime_at_boot_status": str(runtime_at_boot_status),
                "message": str(blocked_reason),
            },
            force=False,
        )
        return result

    runtime_state = _ensure_runtime_sessions_alive()
    solver_session = runtime_session_for_role(runtime_state, "solver")
    clerk_session = runtime_session_for_role(runtime_state, "clerk")
    agent_session = runtime_session_for_role(runtime_state, "agent")
    if solver_session is None or clerk_session is None or agent_session is None:
        raise RuntimeError("CB7 requires solver, clerk, and agent sessions from CB8.")
    context_reset_report = _reset_sessions_for_new_question(runtime_state)
    emit_json_event(
        {
            "event": "cb075_question_context_reset",
            "question_run_id": str(question_run_id),
            "all_reset": bool(context_reset_report.get("all_reset", False)),
            "roles": list(context_reset_report.get("roles") or []),
        },
        force=False,
    )

    transcript: list[dict[str, Any]] = []
    turn_index = 0
    loop_index = 0
    status = "loop_exhausted_without_final"
    verified = False
    failure: dict[str, Any] = {}
    final_answer_text = "none"
    observed_final_answer_text = "none"
    submission_answer_override = "none"
    submission_mode = "unresolved"
    state = dict(new_controller_state(str(problem_text), LOOP_MECHANICS))

    emit_json_event(
        {
            "event": "cb075_run_start",
            "revision": str(CB07_CONTROLLER_REVISION),
            "max_loops": int(MAX_BIG_LOOPS),
            "inner_total_exchanges": int(INNER_TOTAL_EXCHANGES),
            "inner_reasoning_exchanges": int(INNER_REASONING_EXCHANGES),
            "min_big_loop_for_closeout": int(MIN_BIG_LOOP_FOR_CLOSEOUT),
            "closeout_confidence_pct_strict_gt": int(BOXED_CONFIDENCE_GATE_PCT),
            "closeout_requires_exact_integer_consensus": True,
            "closeout_decision_rule": "strict_trio_confidence_until_max_loop_then_best_confidence",
            "routing_mode": str(LOOP_MECHANICS.get("controller_routing_mode", "")),
            "live_knobs": dict(live_knobs),
        },
        force=False,
    )

    for loop_no in range(1, int(MAX_BIG_LOOPS) + 1):
        loop_index = int(loop_no)
        state["loop_no"] = int(loop_no)

        stage = "decompose" if int(loop_no) == 1 and int(MIN_BIG_LOOP_FOR_CLOSEOUT) > 1 else "solve"
        state["athena_stage"] = str(stage)
        if str(stage) == "decompose":
            state["controller_confidence_ceiling"] = 0
            state["peer_validation_status"] = "independent_decomposition"
            state["open_objections"] = ["Peer validation has not started for this problem yet."]
        else:
            state["controller_confidence_ceiling"] = min(_coerce_int(state.get("controller_confidence_ceiling"), 55), 55)
            state["peer_validation_status"] = "pre_peer_validation"
            state["open_objections"] = ["Peer validation for this loop is not complete yet."]

        _refresh_athena_confidence_rubric_state(state, stage=str(stage))
        prompt_state = make_prompt_state(state, LOOP_MECHANICS)
        athena_open_route = make_athena_open_route(state, LOOP_MECHANICS)
        turn_index, athena_open_outcome = _run_role_text_turn(
            speaker="Athena",
            phase="athena_open",
            session=solver_session,
            problem_text=str(problem_text),
            prompt_state=prompt_state,
            route=dict(athena_open_route),
            generation_base=dict(SOLVER_SOLVE_GENERATION),
            token_limit=int(ATHENA_OPEN_MAX_TOKENS),
            repair_attempts=int(ATHENA_REPAIR_ATTEMPTS),
            turn_index=int(turn_index),
            transcript=transcript,
            trace_text=format_trace(list(state.get("peer_reasoning_log") or []), max_chars=int(TRACE_CHARS)),
            as_report=False,
        )
        if not bool(athena_open_outcome.get("ok")):
            failure = dict(athena_open_outcome.get("failure") or {})
            status = "failed"
            break
        _record_contract_damage_if_any(state, dict(athena_open_outcome), speaker="Athena", phase="athena_open")
        parsed_open = dict(parse_athena_turn(str(athena_open_outcome.get("role_text", "")), loop_no=int(loop_no)))
        _update_athena_state(state, parsed_open, loop_no=int(loop_no), stage=str(stage))
        routed_loads = dict(_capture_athena_routing_loads(state, str(athena_open_outcome.get("role_text", ""))))
        state["recent_summary"] = list(state.get("recent_summary") or []) + [
            {
                "speaker": "controller",
                "kind": "athena_question_routing",
                "aria_question_chars": len(str(routed_loads.get("athena_questions_for_aria", ""))),
                "artemis_question_chars": len(str(routed_loads.get("athena_questions_for_artemis", ""))),
                "source_facts_chars": len(str(routed_loads.get("athena_source_facts", ""))),
                "ready": bool(routed_loads.get("athena_question_routing_ready", False)),
            }
        ]

        last_peer_text: dict[str, str] = {"Aria": "", "Artemis": ""}
        state["peer_reports"] = {"Aria": "", "Artemis": ""}

        for exchange_no in range(1, int(INNER_TOTAL_EXCHANGES) + 1):
            for role_name, session, generation in [
                ("Aria", agent_session, AGENT_REVIEW_GENERATION),
                ("Artemis", clerk_session, CLERK_PATCH_GENERATION),
            ]:
                counterpart = "Artemis" if role_name == "Aria" else "Aria"
                route = make_peer_exchange_route(
                    state,
                    LOOP_MECHANICS,
                    role_name=str(role_name),
                    exchange_no=int(exchange_no),
                    counterpart_last=str(last_peer_text.get(counterpart, "")),
                )
                prompt_state = make_prompt_state(state, LOOP_MECHANICS)
                turn_index, peer_outcome = _run_role_text_turn(
                    speaker=str(role_name),
                    phase=f"{str(role_name).lower()}_exchange_{int(exchange_no)}",
                    session=session,
                    problem_text=str(problem_text),
                    prompt_state=prompt_state,
                    route=dict(route),
                    generation_base=dict(generation),
                    token_limit=int(ARIA_EXCHANGE_MAX_TOKENS if str(role_name) == "Aria" else ARTEMIS_EXCHANGE_MAX_TOKENS),
                    repair_attempts=int(PEER_REPAIR_ATTEMPTS),
                    turn_index=int(turn_index),
                    transcript=transcript,
                    trace_text=format_trace(
                        list(state.get("peer_reasoning_log") or [])[-6:],
                        max_chars=int(TRACE_CHARS),
                    ),
                    as_report=False,
                )
                if not bool(peer_outcome.get("ok")):
                    failure = dict(peer_outcome.get("failure") or {})
                    status = "failed"
                    break
                _record_contract_damage_if_any(state, dict(peer_outcome), speaker=str(role_name), phase=f"{str(role_name).lower()}_exchange_{int(exchange_no)}")
                role_text = _clean_text(peer_outcome.get("role_text"))
                last_peer_text[str(role_name)] = str(role_text)
                solve_parser = globals().get("parse_solve_turn")
                if callable(solve_parser) and int(exchange_no) > 1:
                    solve_meta = dict(solve_parser(str(role_text), role_name=str(role_name)))
                    state["latest_solve_meta"] = dict(state.get("latest_solve_meta") or {})
                    state["latest_solve_meta"][str(role_name)] = dict(solve_meta)
                state["peer_reasoning_log"] = list(state.get("peer_reasoning_log") or []) + [
                    {
                        "speaker": str(role_name),
                        "loop": int(loop_no),
                        "exchange": int(exchange_no),
                        "text": str(role_text),
                    }
                ]
                state["recent_summary"] = list(state.get("recent_summary") or []) + [
                    {"speaker": str(role_name), "loop": int(loop_no), "exchange": int(exchange_no), "kind": "reasoning"}
                ]
            if str(status) == "failed":
                break
        if str(status) == "failed":
            break

        artemis_solve_parser = globals().get("parse_solve_turn")
        artemis_solve_state = (
            dict(artemis_solve_parser(str(last_peer_text.get("Artemis", "")), role_name="Artemis"))
            if callable(artemis_solve_parser)
            else {"candidate_answer": "none", "open_blocker": True}
        )
        if bool(artemis_solve_state.get("open_blocker", True)) or str(artemis_solve_state.get("candidate_answer", "none")) == "none":
            forced_route = {
                "role": "Artemis",
                "stage": "peer_reasoning",
                "phase": "forced_solve",
                "loop_no": int(loop_no),
                "exchange_no": int(INNER_TOTAL_EXCHANGES) + 1,
                "inner_total_exchanges": int(INNER_TOTAL_EXCHANGES),
                "athena_message": str(state.get("athena_last_message", "")),
                "counterpart_last": str(last_peer_text.get("Aria", "")),
            }
            prompt_state = make_prompt_state(state, LOOP_MECHANICS)
            turn_index, forced_artemis_outcome = _run_role_text_turn(
                speaker="Artemis",
                phase="artemis_forced_solve",
                session=clerk_session,
                problem_text=str(problem_text),
                prompt_state=prompt_state,
                route=dict(forced_route),
                generation_base=dict(CLERK_PATCH_GENERATION),
                token_limit=int(ARTEMIS_EXCHANGE_MAX_TOKENS),
                repair_attempts=int(PEER_REPAIR_ATTEMPTS),
                turn_index=int(turn_index),
                transcript=transcript,
                trace_text=format_trace(
                    list(state.get("peer_reasoning_log") or [])[-8:],
                    max_chars=int(TRACE_CHARS),
                ),
                as_report=False,
            )
            if not bool(forced_artemis_outcome.get("ok")):
                failure = dict(forced_artemis_outcome.get("failure") or {})
                status = "failed"
                break
            _record_contract_damage_if_any(state, dict(forced_artemis_outcome), speaker="Artemis", phase="artemis_forced_solve")
            forced_text = _clean_text(forced_artemis_outcome.get("role_text"))
            last_peer_text["Artemis"] = str(forced_text)
            if callable(artemis_solve_parser):
                solve_meta = dict(artemis_solve_parser(str(forced_text), role_name="Artemis"))
                state["latest_solve_meta"] = dict(state.get("latest_solve_meta") or {})
                state["latest_solve_meta"]["Artemis"] = dict(solve_meta)
            state["peer_reasoning_log"] = list(state.get("peer_reasoning_log") or []) + [
                {
                    "speaker": "Artemis",
                    "loop": int(loop_no),
                    "exchange": int(INNER_TOTAL_EXCHANGES) + 1,
                    "kind": "forced_solve",
                    "text": str(forced_text),
                }
            ]

        for role_name, session, generation in [
            ("Aria", agent_session, AGENT_REVIEW_GENERATION),
            ("Artemis", clerk_session, CLERK_PATCH_GENERATION),
        ]:
            report_route = make_peer_report_route(
                state,
                LOOP_MECHANICS,
                role_name=str(role_name),
                completed_reasoning_exchanges=int(INNER_TOTAL_EXCHANGES),
            )
            prompt_state = make_prompt_state(state, LOOP_MECHANICS)
            turn_index, peer_outcome = _run_role_text_turn(
                speaker=str(role_name),
                phase=f"{str(role_name).lower()}_report",
                session=session,
                problem_text=str(problem_text),
                prompt_state=prompt_state,
                route=dict(report_route),
                generation_base=dict(generation),
                token_limit=int(ARIA_REPORT_MAX_TOKENS if str(role_name) == "Aria" else ARTEMIS_REPORT_MAX_TOKENS),
                repair_attempts=int(PEER_REPAIR_ATTEMPTS),
                turn_index=int(turn_index),
                transcript=transcript,
                trace_text=format_trace(
                    list(state.get("peer_reasoning_log") or [])[-6:],
                    max_chars=int(REPORT_TRACE_CHARS),
                ),
                as_report=True,
            )
            if not bool(peer_outcome.get("ok")):
                failure = dict(peer_outcome.get("failure") or {})
                status = "failed"
                break
            _record_contract_damage_if_any(state, dict(peer_outcome), speaker=str(role_name), phase=f"{str(role_name).lower()}_report")
            role_text = _clean_text(peer_outcome.get("role_text"))
            report_text = str(peer_outcome.get("report_text") or parse_peer_report(str(role_text), role_name=str(role_name)))
            state["peer_reports"][str(role_name)] = str(format_controller_report(str(report_text), role_name=str(role_name)))
            state["recent_summary"] = list(state.get("recent_summary") or []) + [
                {
                    "speaker": str(role_name),
                    "loop": int(loop_no),
                    "exchange": int(INNER_TOTAL_EXCHANGES),
                    "kind": "report",
                    "excerpt": _clean_text(report_text)[:240],
                }
            ]
        if str(status) == "failed":
            break

        _refresh_peer_validation_state(state)
        _refresh_athena_confidence_rubric_state(state, stage="synthesis")
        prompt_state = make_prompt_state(state, LOOP_MECHANICS)
        athena_synthesis_route = make_athena_synthesis_route(state, LOOP_MECHANICS)
        turn_index, athena_synth_outcome = _run_role_text_turn(
            speaker="Athena",
            phase="athena_synthesis",
            session=solver_session,
            problem_text=str(problem_text),
            prompt_state=prompt_state,
            route=dict(athena_synthesis_route),
            generation_base=dict(SOLVER_SOLVE_GENERATION),
            token_limit=int(ATHENA_SYNTHESIS_MAX_TOKENS),
            repair_attempts=int(ATHENA_REPAIR_ATTEMPTS),
            turn_index=int(turn_index),
            transcript=transcript,
            trace_text=format_trace(list(state.get("peer_reasoning_log") or [])[-6:], max_chars=int(TRACE_CHARS)),
            as_report=False,
        )
        if not bool(athena_synth_outcome.get("ok")):
            failure = dict(athena_synth_outcome.get("failure") or {})
            status = "failed"
            break
        _record_contract_damage_if_any(state, dict(athena_synth_outcome), speaker="Athena", phase="athena_synthesis")
        parsed_synth = dict(parse_athena_turn(str(athena_synth_outcome.get("role_text", "")), loop_no=int(loop_no), require_final_block=False))
        _update_athena_state(state, parsed_synth, loop_no=int(loop_no), stage="synthesis")

        lock_outcome = _peer_lock_outcome(state)
        peer_meta = dict(state.get("peer_report_meta") or {})
        aria_meta = dict(peer_meta.get("Aria") or {})
        artemis_meta = dict(peer_meta.get("Artemis") or {})
        peer_reports_distinct = bool(lock_outcome.get("reports_distinct"))
        peer_min_confidence = int(lock_outcome.get("peer_min_confidence", 0) or 0)
        final_candidate = normalize_candidate_answer(str(state.get("athena_exact_candidate_answer", state.get("athena_candidate_answer", "none"))))
        final_confidence_pct = int(state.get("athena_confidence_pct", 0) or 0)
        aria_exact_candidate = str(aria_meta.get("candidate_exact_integer", "none") or "none")
        artemis_exact_candidate = str(artemis_meta.get("candidate_exact_integer", "none") or "none")
        arbitration_candidates = [
            {
                "role": "Athena",
                "answer": str(final_candidate),
                "confidence_pct": int(final_confidence_pct),
                "supplied_confidence_pct": int(state.get("athena_supplied_confidence_pct", final_confidence_pct) or final_confidence_pct),
                "source": "athena_synthesis",
            },
            {
                "role": "Aria",
                "answer": str(aria_meta.get("answer_signal_integer", aria_exact_candidate) or aria_exact_candidate),
                "confidence_pct": int(aria_meta.get("answer_signal_confidence_pct", aria_meta.get("confidence_pct", 0)) or 0),
                "source": str(aria_meta.get("answer_signal_source", "peer_report") or "peer_report"),
            },
            {
                "role": "Artemis",
                "answer": str(artemis_meta.get("answer_signal_integer", artemis_exact_candidate) or artemis_exact_candidate),
                "confidence_pct": int(artemis_meta.get("answer_signal_confidence_pct", artemis_meta.get("confidence_pct", 0)) or 0),
                "source": str(artemis_meta.get("answer_signal_source", "peer_report") or "peer_report"),
            },
        ]
        arbitration_resolution = dict(_resolve_hierarchical_closeout_candidate(arbitration_candidates))
        peer_answer_values = [
            normalize_candidate_answer(str(value))
            for value in [aria_exact_candidate, artemis_exact_candidate]
            if normalize_candidate_answer(str(value)) != "none"
        ]
        peer_reports_disagree = bool(len(peer_answer_values) >= 2 and len(set(peer_answer_values)) > 1)
        preliminary_selected_candidate = normalize_candidate_answer(str(arbitration_resolution.get("answer", "none") or "none"))
        final_prompt_state = dict(make_prompt_state(state, LOOP_MECHANICS))
        final_prompt_state["athena_last_message"] = str(state.get("athena_last_message", ""))
        turn_index, athena_final_outcome = _run_final_turn(
            session=solver_session,
            problem_text=str(problem_text),
            prompt_state=dict(final_prompt_state),
            generation_base=dict(SOLVER_SOLVE_GENERATION),
            chosen_answer=str(preliminary_selected_candidate),
            turn_index=int(turn_index),
            transcript=transcript,
        )
        if bool(athena_final_outcome.get("ok")):
            finalized_answer = normalize_candidate_answer(str(athena_final_outcome.get("answer", "none") or "none"))
            finalized_confidence = int(athena_final_outcome.get("confidence_pct", 0) or 0)
            if str(finalized_answer) != "none":
                final_candidate = str(finalized_answer)
                final_confidence_pct = int(finalized_confidence)
                state["athena_candidate_answer"] = str(finalized_answer)
                state["athena_exact_candidate_answer"] = str(finalized_answer)
                state["athena_candidate_is_exact_integer"] = True
                state["athena_confidence_pct"] = int(finalized_confidence)
                state["athena_supplied_confidence_pct"] = int(finalized_confidence)
                final_text_from_finalizer = str(
                    athena_final_outcome.get("final_text", emit_final(str(finalized_answer), confidence_pct=int(finalized_confidence)))
                )
                observed_final_answer_text = str(final_text_from_finalizer)
                state["observed_final_answer_text"] = str(final_text_from_finalizer)
                state["recent_summary"] = list(state.get("recent_summary") or []) + [
                    {
                        "speaker": "Athena",
                        "loop": int(loop_no),
                        "stage": "finalization",
                        "candidate_answer": str(finalized_answer),
                        "confidence_pct": int(finalized_confidence),
                        "reason": "mandatory_final_answer_block_turn",
                    }
                ]
                arbitration_candidates[0]["answer"] = str(finalized_answer)
                arbitration_candidates[0]["confidence_pct"] = int(finalized_confidence)
                arbitration_candidates[0]["supplied_confidence_pct"] = int(finalized_confidence)
                arbitration_candidates[0]["source"] = "athena_finalization"
        else:
            state["recent_summary"] = list(state.get("recent_summary") or []) + [
                {
                    "speaker": "Athena",
                    "loop": int(loop_no),
                    "stage": "finalization",
                    "candidate_answer": "none",
                    "confidence_pct": 0,
                    "reason": "mandatory_final_answer_block_turn_failed",
                }
            ]
        if str(final_candidate) == "none":
            arbitration_resolution = {
                "mode": "unresolved_no_valid_mandatory_final_answer_turn",
                "answer": "none",
                "confidence_pct": 0,
                "supporting_roles": [],
                "decision_rule": "mandatory_athena_final_answer_block_turn_required",
                "candidates": list(arbitration_candidates),
            }
        else:
            supporting_roles = ["Athena"]
            if str(final_candidate) == str(aria_exact_candidate):
                supporting_roles.append("Aria")
            if str(final_candidate) == str(artemis_exact_candidate):
                supporting_roles.append("Artemis")
            arbitration_resolution = {
                "mode": "athena_mandatory_final_answer_turn",
                "answer": str(final_candidate),
                "confidence_pct": int(final_confidence_pct),
                "supporting_roles": list(supporting_roles),
                "decision_rule": "final_answer_block_is_separate_unskippable_athena_turn",
                "candidates": list(arbitration_candidates),
            }
        selected_candidate = normalize_candidate_answer(str(arbitration_resolution.get("answer", "none") or "none"))
        selected_confidence_pct = int(arbitration_resolution.get("confidence_pct", 0) or 0)
        final_trio_exact_alignment = bool(
            final_candidate != "none"
            and final_candidate == aria_exact_candidate
            and final_candidate == artemis_exact_candidate
        )
        final_confident_enough = bool(int(final_confidence_pct) > int(BOXED_CONFIDENCE_GATE_PCT))
        peers_confident_enough = bool(int(peer_min_confidence) > int(BOXED_CONFIDENCE_GATE_PCT))
        open_objections = [str(item).strip() for item in list(state.get("open_objections") or []) if str(item).strip()]
        loop_summary_bits = [
            f"loop={int(loop_no)}",
            f"athena={str(final_candidate)}/{int(final_confidence_pct)}",
            f"aria={str(aria_exact_candidate)}/{int(aria_meta.get('confidence_pct', 0) or 0)}",
            f"artemis={str(artemis_exact_candidate)}/{int(artemis_meta.get('confidence_pct', 0) or 0)}",
            f"peer_validation={str(state.get('peer_validation_status', 'unknown') or 'unknown')}",
            f"trio_confidence={min(int(final_confidence_pct), int(peer_min_confidence)) if int(peer_min_confidence) > 0 else int(final_confidence_pct)}",
            f"arbitration={str(selected_candidate)}/{int(selected_confidence_pct)}:{str(arbitration_resolution.get('mode', 'unresolved'))}",
        ]
        closeout_objections = list(open_objections)
        if str(final_candidate) == "none":
            closeout_objections.append("Athena did not produce a valid mandatory final_answer_block turn.")
        if not bool(peer_reports_distinct):
            closeout_objections.append("Peer reports are not sufficiently distinct.")
        if not bool(final_trio_exact_alignment):
            closeout_objections.append("Athena has not yet reconciled to the same exact integer answer as Aria and Artemis.")
        if not bool(final_confident_enough):
            closeout_objections.append(f"Athena final confidence is below {int(BOXED_CONFIDENCE_GATE_PCT)}.")
        if not bool(peers_confident_enough):
            closeout_objections.append(f"Peer confidence is below {int(BOXED_CONFIDENCE_GATE_PCT)}.")
        if bool(closeout_objections):
            loop_summary_bits.append(f"objection={closeout_objections[0]}")
        print(f"cb075_loop_end = {' | '.join(loop_summary_bits)}", flush=True)

        peer_validation_aligned = bool(str(state.get("peer_validation_status", "") or "") == "confidence_aligned")
        strict_closeout_ready = bool(
            int(loop_no) >= int(MIN_BIG_LOOP_FOR_CLOSEOUT)
            and str(selected_candidate) != "none"
            and bool(final_trio_exact_alignment)
            and bool(final_confident_enough)
            and bool(peers_confident_enough)
            and bool(peer_reports_distinct)
            and bool(peer_validation_aligned)
            and not bool(closeout_objections)
        )
        max_loop_best_confidence_ready = bool(
            int(loop_no) >= int(MAX_BIG_LOOPS)
            and str(selected_candidate) != "none"
        )
        if bool(strict_closeout_ready) or bool(max_loop_best_confidence_ready):
            status = (
                "closed_out_strict_trio_confidence"
                if bool(strict_closeout_ready)
                else "closed_out_max_loop_best_confidence_arbitration"
            )
            verified = True
            submission_answer_override = str(selected_candidate)
            submission_mode = str(arbitration_resolution.get("mode", "simple_arbitration") or "simple_arbitration")
            state["closeout_resolution"] = {
                "mode": str(submission_mode),
                "answer": str(submission_answer_override),
                "confidence_pct": int(selected_confidence_pct),
                "supporting_roles": list(arbitration_resolution.get("supporting_roles") or []),
                "decision_rule": str(arbitration_resolution.get("decision_rule", "")),
                "controller_closeout_rule": "strict_trio_confidence_until_max_loop_then_best_confidence",
                "strict_closeout_ready": bool(strict_closeout_ready),
                "max_loop_best_confidence_ready": bool(max_loop_best_confidence_ready),
                "loop_no": int(loop_no),
                "max_big_loops": int(MAX_BIG_LOOPS),
                "min_big_loop_for_closeout": int(MIN_BIG_LOOP_FOR_CLOSEOUT),
                "final_trio_exact_alignment": bool(final_trio_exact_alignment),
                "final_confident_enough": bool(final_confident_enough),
                "peers_confident_enough": bool(peers_confident_enough),
                "peer_reports_distinct": bool(peer_reports_distinct),
                "peer_validation_aligned": bool(peer_validation_aligned),
                "candidates": list(arbitration_resolution.get("candidates") or []),
                "diagnostic_objections": list(closeout_objections),
            }
            final_answer_text = str(emit_final(str(selected_candidate), confidence_pct=int(selected_confidence_pct)))
            observed_final_answer_text = str(final_answer_text)
            state["observed_final_answer_text"] = str(observed_final_answer_text)
            break

        state["recent_summary"] = list(state.get("recent_summary") or [])[-12:]
        state["peer_reasoning_log"] = list(state.get("peer_reasoning_log") or [])[-18:]

    timing_summary = _summarize_timing_metrics() if bool(CB075_TIME_RECORD_ENABLED) else {}
    display_final_answer_text = str(final_answer_text)
    if not bool(verified) and str(display_final_answer_text or "none") == "none" and str(observed_final_answer_text or "none") != "none":
        display_final_answer_text = str(observed_final_answer_text)
    normalized_submission_answer = _normalize_submission_answer_safe(str(final_answer_text)) if bool(verified) else "none"
    resolved_submission_answer = str(
        submission_answer_override
        if str(submission_answer_override or "none") != "none"
        else normalized_submission_answer
    )
    submission_mode = str(
        submission_mode
        if str(submission_answer_override or "none") != "none"
        else "unresolved_no_strict_consensus"
    )

    result = {
        "question_run_id": str(question_run_id),
        "status": str(status),
        "verified": bool(verified),
        "turn_index": int(turn_index),
        "loop_index": int(loop_index),
        "max_turns": int(MAX_BIG_LOOPS * (5 + (2 * INNER_TOTAL_EXCHANGES))),
        "min_conversation_turns": 1,
        "closeout_gate_turn": int(turn_index),
        "submission_answer": str(resolved_submission_answer),
        "submission_mode": str(submission_mode),
        "final_answer_text": str(display_final_answer_text),
        "verified_final_answer_text": str(final_answer_text),
        "observed_final_answer_text": str(observed_final_answer_text),
        "failure": dict(failure or {}),
        "elapsed_seconds": round(float(time.perf_counter() - started), 4),
        "peer_validation_ready": bool(str(state.get("peer_validation_status", "")) == "confidence_aligned" and bool(verified)),
        "controller_metrics": _summarize_controller_metrics(transcript, state),
        "controller_state": dict(state),
        "turn_contract_damage": list(state.get("turn_contract_damage") or []),
        "timing_summary": dict(timing_summary),
        "turn_timing_log": list(_time_log_ref()) if bool(CB075_TIME_RECORD_ENABLED) else [],
        "token_proof": _summarize_token_proof(transcript),
        "context_reset_report": dict(context_reset_report),
        "transcript": list(transcript),
        "transcript_text": _render_transcript_text(transcript),
        "runtime_at_boot_summary": dict(runtime_at_boot_summary),
    }

    if str(status) == "failed":
        failure_bits = dict(failure or {})
        print(
            "cb075_failure = "
            + " | ".join(
                [
                    f"speaker={str(failure_bits.get('speaker', 'unknown') or 'unknown')}",
                    f"phase={str(failure_bits.get('phase', 'unknown') or 'unknown')}",
                    f"turn={int(failure_bits.get('turn', 0) or 0)}",
                    f"error_type={str(failure_bits.get('error_type', 'unknown') or 'unknown')}",
                    f"error_message={str(failure_bits.get('error_message', '') or '')[:400]}",
                ]
            ),
            flush=True,
        )

    emit_json_event(
        {
            "event": "cb075_run_end",
            "status": str(result.get("status", "")),
            "verified": bool(result.get("verified", False)),
            "submission_answer": str(result.get("submission_answer", "none")),
            "turn_index": int(result.get("turn_index", 0) or 0),
            "loop_index": int(result.get("loop_index", 0) or 0),
            "question_run_id": str(question_run_id),
            "total_tokens": int(dict(result.get("token_proof") or {}).get("total_tokens", 0) or 0),
        },
        force=False,
    )
    if bool(CB075_TIME_RECORD_ENABLED):
        emit_json_event({"event": "cb075_timing_summary", **dict(timing_summary)}, force=False)
    return result


if bool(PRINT_CB7_CONFIG_JSON):
    emit_json_event(
        {
            "event": "cb7_generation_config",
            "revision": str(CB07_CONTROLLER_REVISION),
            "max_big_loops": int(MAX_BIG_LOOPS),
            "min_big_loop_for_closeout": int(MIN_BIG_LOOP_FOR_CLOSEOUT),
            "inner_total_exchanges": int(INNER_TOTAL_EXCHANGES),
            "inner_reasoning_exchanges": int(INNER_REASONING_EXCHANGES),
            "boxed_confidence_gate_pct_strict_gt": int(BOXED_CONFIDENCE_GATE_PCT),
            "time_record_enabled": bool(CB075_TIME_RECORD_ENABLED),
            "time_record_json": bool(CB075_TIME_RECORD_JSON),
            "athena_open_max_tokens": int(ATHENA_OPEN_MAX_TOKENS),
            "peer_exchange_max_tokens": int(PEER_EXCHANGE_MAX_TOKENS),
            "peer_report_max_tokens": int(PEER_REPORT_MAX_TOKENS),
            "athena_synthesis_max_tokens": int(ATHENA_SYNTHESIS_MAX_TOKENS),
            "athena_final_max_tokens": int(ATHENA_FINAL_MAX_TOKENS),
            "aria_exchange_max_tokens": int(ARIA_EXCHANGE_MAX_TOKENS),
            "aria_report_max_tokens": int(ARIA_REPORT_MAX_TOKENS),
            "artemis_exchange_max_tokens": int(ARTEMIS_EXCHANGE_MAX_TOKENS),
            "artemis_report_max_tokens": int(ARTEMIS_REPORT_MAX_TOKENS),
            "trace_chars": int(TRACE_CHARS),
            "report_trace_chars": int(REPORT_TRACE_CHARS),
            "routing_mode": str(LOOP_MECHANICS.get("controller_routing_mode", "")),
        }
    )

"""## 08 - Load Athena-Artemis-Aria Sessions



"""

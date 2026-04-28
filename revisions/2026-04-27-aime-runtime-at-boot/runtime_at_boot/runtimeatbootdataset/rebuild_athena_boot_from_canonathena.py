from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parents[1]
CANON_DIR = ROOT / "canonathena"
BOOT_DIR = ROOT / "boot" / "athena"

CANON_STUDY = CANON_DIR / "Athena_100_HQ_canon_v21_schema.ndjson"
ROLE_SOURCE = PROJECT_ROOT / "runtimeatbootdataset" / "source" / "Athena_epistemic_boot_100_final_hq.ndjson"
CURRENT_STUDY = BOOT_DIR / "Athena_epistemic_boot_100_final_hq.ndjson"
CURRENT_CERT = BOOT_DIR / "Athena_epistemic_boot_100_final_certification_hq.ndjson"
OUT_STUDY = CURRENT_STUDY
OUT_CERT = CURRENT_CERT
AUDIT_PATH = BOOT_DIR / "ATHENA_BOOT_DATASET_AUDIT.md"
MANIFEST_PATH = ROOT / "runtimeatboot_manifest.json"

GOLDEN_COUNT = 5
ROLE_COUNT = 5
FULL_CANON_PER_DOMAIN = 2
FULL_CANON_DOMAINS = ["number_theory", "combinatorics", "algebra", "geometry"]
FULL_CANON_COUNT = FULL_CANON_PER_DOMAIN * len(FULL_CANON_DOMAINS)
SCHEMA_ONLY_CANON_COUNT = 100 - GOLDEN_COUNT - ROLE_COUNT - FULL_CANON_COUNT
VERBATIM_SCHEMA_CERT_COUNT = 5
LETTERS = ["A", "B", "C", "D"]
REDACTION = "REDACTED_FOR_BOOT_MEMORY"
SCHEMA_ONLY = "REDACTED_SCHEMA_ONLY"


def load_ndjson(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for raw in handle:
            line = raw.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def write_ndjson(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for row in rows:
            handle.write(
                json.dumps(row, ensure_ascii=False, sort_keys=False, separators=(",", ":")) + "\n"
            )


def canon_role_id(canon_id: str) -> str:
    return canon_id.replace("ATHENA-100-HQ-", "ATHENA-ROLE-HQ100-")


def parse_canon_payload(row: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    text = str(row["text"])
    if "\n\n" in text:
        preamble, yaml_text = text.split("\n\n", 1)
    else:
        preamble, yaml_text = "Athena Canon v2.1 breakdown record.", text
    payload = yaml.safe_load(yaml_text)
    if not isinstance(payload, dict):
        raise RuntimeError(f"Could not parse Canon YAML for {row.get('id')}")
    return preamble, payload


def sorted_by_quality(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(rows, key=lambda row: (-float(row.get("quality_score", 0)), str(row.get("id", ""))))


def redact_instance_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    payload = dict(payload)
    payload["instance_snapshot"] = {
        "parameter_value(s)": REDACTION,
        "final_answer": REDACTION,
    }
    return payload


def slim_list(values: Any, limit: int = 8) -> list[Any]:
    if not isinstance(values, list):
        return []
    return values[:limit]


def names_only(items: Any, limit: int = 8) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    if not isinstance(items, list):
        return out
    for item in items[:limit]:
        if isinstance(item, dict):
            clean = {"name": item.get("name", SCHEMA_ONLY)}
            if "type" in item:
                clean["type"] = item.get("type")
            if "role" in item:
                clean["role"] = item.get("role")
            if "dependency" in item:
                clean["dependency"] = item.get("dependency")
            out.append(clean)
        else:
            out.append({"name": str(item)})
    return out


def schema_only_payload(source: dict[str, Any]) -> dict[str, Any]:
    _, payload = parse_canon_payload(source)
    identity = dict(payload.get("identity", {}) or {})
    taxonomy = dict(payload.get("taxonomy", {}) or {})
    answer_spec = payload.get("answer_spec", {}) or {}
    signature = payload.get("solution_signature", {}) or {}

    return {
        "identity": {
            "short_name": identity.get("short_name"),
        },
        "taxonomy": {
            "domain": taxonomy.get("domain"),
        },
        "problem_spec": {
            "summary": SCHEMA_ONLY,
            "object(s)": SCHEMA_ONLY,
            "givens": SCHEMA_ONLY,
            "ask": SCHEMA_ONLY,
        },
        "answer_spec": {
            key: answer_spec.get(key)
            for key in ("type", "normalization", "modulus")
            if key in answer_spec
        },
        "family_structure": {
            "parameter(s)": SCHEMA_ONLY,
            "invariant(s)": SCHEMA_ONLY,
            "operator(s)": SCHEMA_ONLY,
            "essential_assumption(s)": SCHEMA_ONLY,
            "uniqueness_certificate(s)": SCHEMA_ONLY,
        },
        "reasoning_components": {
            "technique(s)": SCHEMA_ONLY,
            "theorem(s)": SCHEMA_ONLY,
            "closest_first_principle_concept_applied": SCHEMA_ONLY,
        },
        "solution_signature": {
            "critical_trick(s)": SCHEMA_ONLY,
            "finish_type": signature.get("finish_type"),
        },
        "computational_context": SCHEMA_ONLY,
        "well_posed": payload.get("well_posed"),
        "instance_snapshot": {
            "parameter_value(s)": REDACTION,
            "final_answer": REDACTION,
        },
    }


def full_canon_text(row: dict[str, Any]) -> str:
    preamble, payload = parse_canon_payload(row)
    payload = redact_instance_snapshot(payload)
    yaml_text = yaml.safe_dump(
        payload,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=100,
    ).strip()
    return (
        f"{preamble}\n"
        "Boot redaction note: this is one of eight full Canon exemplars; instance_snapshot values and final answers are redacted.\n\n"
        f"{yaml_text}\n"
    )


def schema_only_text(row: dict[str, Any]) -> str:
    payload = schema_only_payload(row)
    yaml_text = yaml.safe_dump(
        payload,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
        width=100,
    ).strip()
    return f"{yaml_text}\n"


def canon_boot_row(row: dict[str, Any], full: bool) -> dict[str, Any]:
    return {
        "id": canon_role_id(str(row["id"])),
        "group": "athena_100_hq_canon_v21_schema_full" if full else "athena_100_hq_canon_v21_schema_only",
        "target": ["athena"],
        "priority": int(row.get("priority", 10)),
        "text": full_canon_text(row) if full else schema_only_text(row),
        "runtime_label": "solver",
        "role_name": "Athena",
        "schema_version": "athena_100_hq_canon_v21_schema_boot_slim_v3",
        "source_schema_id": row.get("source_schema_id", "distillator_dsl.math.v2.1"),
        "source_domain": row.get("source_domain"),
        "source_short_name": row.get("source_short_name"),
        "quality_score": row.get("quality_score"),
        "canon_boot_mode": "full_exemplar_redacted" if full else "schema_only_redacted",
    }


def select_full_canon(canon_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    for domain in FULL_CANON_DOMAINS:
        domain_rows = [row for row in canon_rows if row.get("source_domain") == domain]
        picks = sorted_by_quality(domain_rows)[:FULL_CANON_PER_DOMAIN]
        if len(picks) != FULL_CANON_PER_DOMAIN:
            raise RuntimeError(f"Need {FULL_CANON_PER_DOMAIN} Canon rows for {domain}, got {len(picks)}")
        selected.extend(picks)
    return selected


def select_schema_only_canon(
    canon_rows: list[dict[str, Any]],
    full_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    full_ids = {row["id"] for row in full_rows}
    remaining = [row for row in sorted_by_quality(canon_rows) if row["id"] not in full_ids]
    return remaining[:SCHEMA_ONLY_CANON_COUNT]


def option_text(options: list[str], answer: str, question: str) -> str:
    lines = ["Question:", question, "", "Options:"]
    for letter, option in zip(LETTERS, options):
        lines.append(f"{letter}. {option}")
    lines.extend(["", "Answer:", answer])
    return "\n".join(lines)


def canon_verbatim_schema_excerpt(row: dict[str, Any], max_lines: int = 14) -> str:
    text = str(row["text"])
    yaml_text = text.split("\n\n", 1)[1] if "\n\n" in text else text
    lines = yaml_text.splitlines()
    excerpt: list[str] = []
    for line in lines:
        if line.startswith("problem_spec:"):
            break
        excerpt.append(line)
        if len(excerpt) >= max_lines:
            break
    return "\n".join(excerpt).strip()


def next_answer(answer_counts: Counter[str]) -> str:
    return min(LETTERS, key=lambda letter: (answer_counts[letter], LETTERS.index(letter)))


def build_mcq(
    proof_id: str,
    suffix: str,
    kind: str,
    question: str,
    correct: str,
    distractors: list[str],
    answer_counts: Counter[str],
    priority: int = 10,
    schema_version: str = "athena_boot_slim_schema_cert_v3",
) -> dict[str, Any]:
    unique = [correct]
    for option in distractors:
        if option not in unique:
            unique.append(option)
        if len(unique) == 4:
            break
    if len(unique) != 4:
        raise RuntimeError(f"Need four unique options for {proof_id}-{suffix}")
    answer = next_answer(answer_counts)
    answer_counts[answer] += 1
    answer_index = LETTERS.index(answer)
    options = [option for option in unique if option != correct]
    options.insert(answer_index, correct)
    probe_id = f"{proof_id}-{suffix}"
    return {
        "id": probe_id,
        "proof_id": proof_id,
        "group": "athena_epistemic_mcq",
        "target": ["athena"],
        "priority": priority,
        "kind": kind,
        "probe_type": "mcq",
        "question": question,
        "options": options,
        "answer": answer,
        "text": option_text(options, answer, question),
        "runtime_label": "solver",
        "role_name": "Athena",
        "probe_prompt": question,
        "probe_answer": answer,
        "probe_ready": True,
        "study_source_id": proof_id,
        "schema_version": schema_version,
        "answer_position_policy": "balanced_lowest_count_assignment",
        "answer_slot_index": answer_index,
        "probe_source_id": probe_id,
    }


def normalize_existing_golden_probe(row: dict[str, Any]) -> dict[str, Any]:
    clean = dict(row)
    answer = clean.get("answer", "A")
    clean["target"] = ["athena"]
    clean["runtime_label"] = "solver"
    clean["role_name"] = "Athena"
    clean["probe_answer"] = answer
    clean["probe_ready"] = True
    clean["answer_slot_index"] = LETTERS.index(answer)
    clean["study_source_id"] = clean.get("proof_id", clean.get("study_source_id"))
    clean["probe_source_id"] = clean.get("id")
    return clean


def golden_cert_rows(golden_rows: list[dict[str, Any]], answer_counts: Counter[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in golden_rows:
        proof_id = row["id"]
        rows.append(
            build_mcq(
                proof_id,
                "Q1",
                "golden_route_lock_recall",
                "What should Athena do after a VoE golden route is genuinely locked?",
                "Safe: state the compact result and stop expanding dead alternatives.",
                [
                    "Unsafe: reopen rejected branches to sound more thorough.",
                    "Unsafe: delay the answer until every role writes a long report.",
                    "Unsafe: replace the solved route with a narrative majority vote.",
                ],
                answer_counts,
                priority=100,
                schema_version="goldenanswers_high_value_cert_v2",
            )
        )
        rows.append(
            build_mcq(
                proof_id,
                "Q2",
                "golden_output_contract_recall",
                "How should Athena handle a puzzle answer object versus the benchmark integer?",
                "Safe: solve the raw answer object first, then apply the controller output conversion explicitly.",
                [
                    "Unsafe: skip the raw object and guess the benchmark integer.",
                    "Unsafe: hide the conversion because the controller might infer it.",
                    "Unsafe: return multiple answer forms without selecting the required output.",
                ],
                answer_counts,
                priority=100,
                schema_version="goldenanswers_high_value_cert_v2",
            )
        )
    return rows


def role_cert_rows(role_rows: list[dict[str, Any]], answer_counts: Counter[str]) -> list[dict[str, Any]]:
    do_lines = [field_from_text(row["text"], "Do:") for row in role_rows]
    stop_lines = [field_from_text(row["text"], "Stop:") for row in role_rows]
    rows: list[dict[str, Any]] = []
    for index, row in enumerate(role_rows):
        proof_id = row["id"]
        rows.append(
            build_mcq(
                proof_id,
                "Q1",
                "do_recall",
                "What should Athena do here?",
                do_lines[index],
                [do_lines[(index + offset) % len(do_lines)] for offset in (1, 2, 3)],
                answer_counts,
            )
        )
        rows.append(
            build_mcq(
                proof_id,
                "Q2",
                "stop_recall",
                "When is this route ready to close?",
                stop_lines[index],
                [stop_lines[(index + offset) % len(stop_lines)] for offset in (1, 2, 3)],
                answer_counts,
            )
        )
    return rows


def field_from_text(text: str, prefix: str) -> str:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line.removeprefix(prefix).strip()
    raise RuntimeError(f"Missing {prefix!r} in role row")


def finish_distractors(correct: str, finish_types: list[str], index: int) -> list[str]:
    choices: list[str] = []
    for offset in (7, 19, 43, 61):
        candidate = finish_types[(index + offset) % len(finish_types)]
        if candidate != correct and candidate not in choices:
            choices.append(candidate)
        if len(choices) == 3:
            return choices
    for candidate in finish_types:
        if candidate != correct and candidate not in choices:
            choices.append(candidate)
        if len(choices) == 3:
            return choices
    return choices


def canon_cert_rows(
    canon_rows: list[dict[str, Any]],
    answer_counts: Counter[str],
    full_canon_ids: set[str],
) -> list[dict[str, Any]]:
    parsed = [parse_canon_payload(row)[1] for row in canon_rows]
    finish_types = [
        str(payload.get("solution_signature", {}).get("finish_type", "schema_guided_finish"))
        for payload in parsed
    ]
    rows: list[dict[str, Any]] = []
    for index, (source_row, payload) in enumerate(zip(canon_rows, parsed)):
        proof_id = canon_role_id(str(source_row["id"]))
        mode = "full_exemplar" if str(source_row["id"]) in full_canon_ids else "schema_only"
        if index < VERBATIM_SCHEMA_CERT_COUNT:
            excerpt = canon_verbatim_schema_excerpt(source_row)
            question = (
                "Canon HQ metadata excerpt:\n"
                f"{excerpt}\n\n"
                "What should Athena establish from this metadata before solving?"
            )
            kind = "schema_verbatim_excerpt_recall"
        else:
            question = "What should Athena use from a slim Canon v2.1 boot row?"
            kind = "schema_behavior_recall"
        rows.append(
            build_mcq(
                proof_id,
                "Q1",
                kind,
                question,
                "Safe: build the schema ledger from identity/domain, objects, givens/ask, answer_spec, invariants, route tools, finish type, and normalization.",
                [
                    "Unsafe: hunt for a hidden final answer in instance_snapshot.",
                    "Unsafe: use source paths or provenance folders as route evidence.",
                    "Unsafe: reduce the row to only a short prose title summary.",
                ],
                answer_counts,
            )
        )
        if mode == "full_exemplar":
            rows.append(
                build_mcq(
                    proof_id,
                    "Q2",
                    "finish_type_recall",
                    "Which solution_signature.finish_type should Athena preserve from this full Canon exemplar?",
                    finish_types[index],
                    finish_distractors(finish_types[index], finish_types, index),
                    answer_counts,
                )
            )
        else:
            rows.append(
                build_mcq(
                    proof_id,
                    "Q2",
                    "schema_only_behavior_recall",
                    "What should Athena do with a schema-only Canon row?",
                    "Safe: use the YAML slot structure and redaction markers as routing discipline, without inventing missing givens or answers.",
                    [
                        "Unsafe: reconstruct the redacted problem statement from the short_name.",
                        "Unsafe: treat REDACTED_SCHEMA_ONLY as a value to solve with.",
                        "Unsafe: infer a final answer from domain, modulus, or finish_type alone.",
                    ],
                    answer_counts,
                )
            )
    return rows


def validate(
    boot_rows: list[dict[str, Any]],
    cert_rows: list[dict[str, Any]],
    full_canon: list[dict[str, Any]],
    schema_only_canon: list[dict[str, Any]],
) -> dict[str, Any]:
    errors: list[str] = []
    boot_ids = [row["id"] for row in boot_rows]
    cert_ids = [row["id"] for row in cert_rows]
    if len(boot_rows) != 100:
        errors.append(f"boot_count={len(boot_rows)} expected 100")
    if len(cert_rows) != 200:
        errors.append(f"cert_count={len(cert_rows)} expected 200")
    if len(boot_ids) != len(set(boot_ids)):
        errors.append("duplicate boot ids")
    if len(cert_ids) != len(set(cert_ids)):
        errors.append("duplicate certification ids")

    probes_by_parent = Counter(row.get("proof_id") for row in cert_rows)
    boot_id_set = set(boot_ids)
    for row in cert_rows:
        if row.get("proof_id") not in boot_id_set:
            errors.append(f"{row.get('id')} has missing parent {row.get('proof_id')}")
        if row.get("answer") not in LETTERS:
            errors.append(f"{row.get('id')} invalid answer")
        if row.get("answer") != row.get("probe_answer"):
            errors.append(f"{row.get('id')} answer/probe_answer mismatch")
        if len(row.get("options", [])) != 4 or len(set(row.get("options", []))) != 4:
            errors.append(f"{row.get('id')} options are not four unique values")
    verbatim_schema_probe_count = sum(
        row.get("kind") == "schema_verbatim_excerpt_recall" and "Canon HQ metadata excerpt:" in row.get("text", "")
        for row in cert_rows
    )
    if verbatim_schema_probe_count < VERBATIM_SCHEMA_CERT_COUNT:
        errors.append(
            f"verbatim_schema_probe_count={verbatim_schema_probe_count} expected at least {VERBATIM_SCHEMA_CERT_COUNT}"
        )
    for boot_id in boot_ids:
        if probes_by_parent[boot_id] != 2:
            errors.append(f"{boot_id} has {probes_by_parent[boot_id]} probes, expected 2")
    for row in boot_rows[:15]:
        if probes_by_parent[row["id"]] != 2:
            errors.append(f"first15 row {row['id']} does not have exactly two probes")
    for row in boot_rows:
        if row.get("runtime_label") != "solver":
            errors.append(f"{row['id']} runtime_label is not solver")
        if row.get("role_name") != "Athena":
            errors.append(f"{row['id']} role_name is not Athena")
    first20_groups = [
        "golden" if row["id"].startswith("ATHENA-GOLDEN-")
        else "role" if row.get("group") == "athena_role_runtime_hq"
        else "full_canon" if row.get("canon_boot_mode") == "full_exemplar_redacted"
        else "metadata_only" if row.get("canon_boot_mode") == "schema_only_redacted"
        else "other"
        for row in boot_rows[:20]
    ]
    expected_first20 = ["golden"] * 5 + ["role"] * 5 + ["full_canon"] * 5 + ["metadata_only"] * 5
    if first20_groups != expected_first20:
        errors.append(f"first20 layout mismatch: {first20_groups}")

    full_ids = {canon_role_id(row["id"]) for row in full_canon}
    schema_only_ids = {canon_role_id(row["id"]) for row in schema_only_canon}
    for row in boot_rows:
        text = row.get("text", "")
        if row["id"] in full_ids:
            for marker in ["problem_spec:", "answer_spec:", "family_structure:", "reasoning_components:", "solution_signature:"]:
                if marker not in text:
                    errors.append(f"{row['id']} full Canon row missing {marker}")
        if row["id"] in schema_only_ids:
            for marker in ["problem_spec:", "givens: REDACTED_SCHEMA_ONLY", "ask: REDACTED_SCHEMA_ONLY"]:
                if marker not in text:
                    errors.append(f"{row['id']} schema-only row missing {marker}")
            for forbidden in ["Compute ", "Question:", "Canonical Golden Transcript", "final_answer:\n    value:", "final_answer:\n  value:"]:
                if forbidden in text:
                    errors.append(f"{row['id']} schema-only row contains forbidden content {forbidden!r}")

    serialized = "\n".join(json.dumps(row, ensure_ascii=False) for row in [*boot_rows, *cert_rows])
    for marker in ["source_path", "metadata_yaml_path", "/kaggle", "\\kaggle"]:
        if marker.lower() in serialized.lower():
            errors.append(f"path/provenance marker found: {marker}")
    for drive in ("D", "N"):
        if re.search(rf"(?<![A-Za-z]){drive}:\\\\[A-Za-z0-9_.-]", serialized):
            errors.append(f"path/provenance marker found: {drive}:\\")
    if "Canon v2.1 synthesis:" in serialized or "Theme: canon route" in serialized:
        errors.append("shallow Canon summary marker found")

    return {
        "ok": not errors,
        "errors": errors,
        "boot_count": len(boot_rows),
        "certification_count": len(cert_rows),
        "first15_layout": {
            "rows_1_5": "VoE golden-answer memory rows",
            "rows_6_10": "compact Athena role prompts",
            "rows_11_15": "first five of eight full redacted Canon exemplars",
        },
        "first20_layout": {
            "rows_1_5": "VoE golden-answer memory rows",
            "rows_6_10": "compact Athena role prompts",
            "rows_11_15": "full redacted Canon exemplars with metadata/method structure",
            "rows_16_20": "schema-only redacted Canon metadata skeletons",
        },
        "full_canon_exemplar_count": len(full_canon),
        "schema_only_canon_count": len(schema_only_canon),
        "answer_counts": dict(sorted(Counter(row["answer"] for row in cert_rows).items())),
        "verbatim_schema_probe_count": verbatim_schema_probe_count,
        "full_canon_source_ids": [row["id"] for row in full_canon],
        "dropped_canon_ids": [
            row["id"]
            for row in sorted_by_quality(load_ndjson(CANON_STUDY))
            if row["id"] not in {item["id"] for item in [*full_canon, *schema_only_canon]}
        ],
        "source_files_used": [
            str(CANON_STUDY),
            str(ROLE_SOURCE),
            str(CURRENT_STUDY) + " (first five golden rows only)",
        ],
        "outputs": {
            "study": str(OUT_STUDY),
            "certification": str(OUT_CERT),
            "audit": str(AUDIT_PATH),
            "manifest": str(MANIFEST_PATH),
        },
    }


def update_manifest() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    manifest["status"] = "athena_boot_slim_canon_schema_with_golden5_roles"
    manifest["notes"] = [
        "Updated on 2026-04-22: Athena boot rows now keep five VoE golden memory rows, five compact role rows, eight full redacted Canon exemplars, and schema-only redacted Canon rows.",
        "Most Canon rows are intentionally stripped to YAML metadata-schema shape only: no question text, no exact givens/ask, no final answer values.",
        "Eight full redacted Canon exemplars are retained: two number_theory, two combinatorics, two algebra, and two geometry rows.",
        "The first five golden rows remain answer-bearing by design for Runtime-at-Boot recall.",
    ]
    live = manifest.setdefault("boot", {}).setdefault("live_canonical", {})
    live["athena_study_count"] = 100
    live["athena_certification_count"] = 200
    live["athena_first15_layout"] = {
        "golden_answer_memory_rows": 5,
        "role_prompt_rows": 5,
        "full_redacted_canon_exemplar_rows_in_first15": 5,
        "schema_only_canon_rows": SCHEMA_ONLY_CANON_COUNT,
    }
    live["athena_first20_layout"] = {
        "golden_answer_memory_rows": 5,
        "role_prompt_rows": 5,
        "full_redacted_canon_exemplar_rows": 5,
        "schema_only_canon_rows": 5,
        "recommended_certification_line_limit": 20,
    }
    live["athena_canonathena_source_path"] = str(CANON_STUDY)
    MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_audit(validation: dict[str, Any]) -> None:
    lines = [
        "# Athena Boot Dataset Audit",
        "",
        "Audit date: 2026-04-22",
        "",
        "## Verdict",
        "",
        "The Athena boot-context dataset has been slimmed. It keeps VoE golden memory and compact role prompts, keeps only eight full redacted Canon exemplars, and strips the remaining Canon rows to YAML metadata-schema skeletons.",
        "",
        "## Source Files Used",
        "",
        f"- `{CANON_STUDY}`",
        f"- `{ROLE_SOURCE}`",
        f"- `{CURRENT_STUDY}` for the first five golden rows only",
        "- Golden certification probes are regenerated by this script with Safe/Unsafe wording.",
        "",
        "## First 15 Rows",
        "",
        "- Rows 1-5: preserved VoE golden-answer memory rows.",
        "- Rows 6-10: compact Athena role prompts.",
        "- Rows 11-15: first five full redacted Canon exemplars.",
        "- Rows 16-20: first five schema-only redacted Canon metadata skeletons.",
        "",
        "## Canon Policy",
        "",
        "- Full exemplars retained: 2 number_theory, 2 combinatorics, 2 algebra, 2 geometry.",
        "- All other Canon rows are schema-only redacted metadata skeletons.",
        "- Schema-only Canon rows redact problem summaries, exact givens, asks, critical tricks, assumptions, uniqueness text, computational details, and instance snapshots.",
        "- Full Canon exemplars redact instance_snapshot values and final answers.",
        "",
        "## Counts",
        "",
        f"- Athena boot rows written: {validation['boot_count']}.",
        f"- Athena certification probes written: {validation['certification_count']}.",
        f"- Full redacted Canon exemplars: {validation['full_canon_exemplar_count']}.",
        f"- Schema-only Canon rows: {validation['schema_only_canon_count']}.",
        f"- Certification answer distribution: {validation['answer_counts']}.",
        f"- Verbatim Canon metadata-schema certification probes: {validation['verbatim_schema_probe_count']}.",
        "- First 20 boot rows provide four flavors: golden, role, full Canon, metadata-only Canon.",
        "",
        "## Full Canon Exemplar Source IDs",
        "",
    ]
    lines.extend(f"- `{row_id}`" for row_id in validation["full_canon_source_ids"])
    lines.extend(["", "## Validation", ""])
    if validation["errors"]:
        lines.extend(f"- ERROR: {error}" for error in validation["errors"])
    else:
        lines.extend(
            [
                "- NDJSON parses cleanly.",
                "- Boot IDs are unique.",
                "- Certification parent IDs all match boot IDs.",
                "- Every boot row has exactly two probes.",
                "- The first 15 boot rows have exactly two probes each.",
                "- The first 20 boot rows have exactly two probes each and cover golden, role, full Canon, and metadata-only Canon flavors.",
                "- Runtime role fields are consistent.",
                "- Shallow Canon synthesis summaries are absent.",
                "- Path/provenance markers are absent from boot/certification rows.",
            ]
        )
    AUDIT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    current_boot = load_ndjson(CURRENT_STUDY)
    canon_rows = load_ndjson(CANON_STUDY)
    role_source = load_ndjson(ROLE_SOURCE)

    golden_rows = current_boot[:GOLDEN_COUNT]
    if not all(row["id"].startswith("ATHENA-GOLDEN-") for row in golden_rows):
        raise RuntimeError("Current Athena boot file does not start with five golden rows")
    golden_ids = [row["id"] for row in golden_rows]

    role_rows = [
        {
            "id": row["id"],
            "group": "athena_role_runtime_hq",
            "target": ["athena"],
            "priority": int(row.get("priority", 10)),
            "text": row["text"],
            "runtime_label": "solver",
            "role_name": "Athena",
        }
        for row in role_source[:ROLE_COUNT]
    ]

    full_canon = select_full_canon(canon_rows)
    schema_only_canon = select_schema_only_canon(canon_rows, full_canon)
    first_window_full = full_canon[:5]
    first_window_schema = schema_only_canon[:5]
    remaining_full = full_canon[5:]
    remaining_schema = schema_only_canon[5:]
    ordered_canon = first_window_full + first_window_schema + remaining_full + remaining_schema
    full_canon_ids = {str(row["id"]) for row in full_canon}

    boot_rows = [
        {
            **row,
            "target": ["athena"],
            "runtime_label": "solver",
            "role_name": "Athena",
        }
        for row in golden_rows
    ]
    boot_rows.extend(role_rows)
    boot_rows.extend(canon_boot_row(row, full=True) for row in first_window_full)
    boot_rows.extend(canon_boot_row(row, full=False) for row in first_window_schema)
    boot_rows.extend(canon_boot_row(row, full=True) for row in remaining_full)
    boot_rows.extend(canon_boot_row(row, full=False) for row in remaining_schema)

    answer_counts: Counter[str] = Counter()
    cert_rows = golden_cert_rows(golden_rows, answer_counts)
    cert_rows.extend(role_cert_rows(role_rows, answer_counts))
    cert_rows.extend(canon_cert_rows(ordered_canon, answer_counts, full_canon_ids))

    validation = validate(boot_rows, cert_rows, full_canon, schema_only_canon)
    if not validation["ok"]:
        raise RuntimeError(json.dumps(validation, ensure_ascii=False, indent=2))

    write_ndjson(OUT_STUDY, boot_rows)
    write_ndjson(OUT_CERT, cert_rows)
    update_manifest()
    write_audit(validation)
    print(json.dumps(validation, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

# Auto-extracted by Aster from AENAIMO260_0_2_3_FINAL_CB5_CB8_CLOSED_BOOK_WORKING_20260427.ipynb
# Source cell: 32 / CB07.25 Turn Discipline Schemas
# Intended use: replace/run this CB cell in notebook order.

"""## 07.25 Turn Discipline Schemas"""

# 07.25 - Static Role Schema Contracts
# ---------------------------------------------------------------------------
# Static role schema contracts (CB7.25)
# ---------------------------------------------------------------------------

"""## 07.25 - Static Role Schema Contracts

Immutable schema and role-contract facts. This block must stay static: it names
which metadata schemas exist and which role owns each invariant. Dynamic turn
instructions are intentionally kept out of CB7/CB7.25 and live in CB7.5.

"""

CB07_SECTION_WRAPPER_REVISION = "2026-04-27-cb07-controller-section-wrapper-v1.5.1-closed-book-confidence"
ATHENA_SCHEMA_ID = "distillator_dsl.math.v2.1"
ARIA_SCHEMA_ID = "prooflineage_dsl.v2.2"
ARTEMIS_CONTRACT_ID = "auditlineage_dsl.v2.3"

ATHENA_SCHEMA_FIELDS = (
    "identity",
    "taxonomy",
    "problem_spec",
    "answer_spec",
    "family_structure",
    "reasoning_components",
    "solution_signature",
    "computational_context",
    "well_posed",
    "instance_snapshot",
)

ARIA_SCHEMA_FIELDS = (
    "identity",
    "classification",
    "statement_metadata",
    "structure",
    "lineage",
    "references",
    "artifact_links",
    "snapshot",
)

ARTEMIS_AUDIT_FIELDS = (
    "identity",
    "audit_scope",
    "source_alignment",
    "answer_contract",
    "decomposition_audit",
    "arithmetic_audit",
    "boundary_case_audit",
    "computation_status",
    "peer_comparison",
    "final_recommendation",
    "snapshot",
)

ATHENA_SETUP_YAML = """schema_id: distillator_dsl.math.v2.1
schema_version: 1
identity:
  family_id: unknown
  instance_id: current_problem
  short_name: unknown
  generation: 1
taxonomy:
  domain: unknown
  subdomain(s):
    - unknown
  topic_path:
    - unknown
  tags:
    - unknown
problem_spec:
  summary: unknown
  object(s):
    - name: unknown
      type: other
      role: unknown
      dependency: unknown
  givens:
    - unknown
  ask:
    - unknown
answer_spec:
  type: unknown
  normalization: unknown
family_structure:
  parameter(s):
    - name: unknown
      type: other
      domain: unknown
      purpose: unknown
  invariant(s):
    - name: unknown
      depends_on: []
      statement: unknown
  operator(s):
    - unknown
  essential_assumption(s):
    - unknown
  uniqueness_certificate(s):
    - unknown
reasoning_components:
  technique(s):
    - name: unknown
      inputs:
        - unknown
      purpose: unknown
      outputs:
        - unknown
  theorem(s):
    - name: unknown
      role: unknown
  closest_first_principle_concept_applied:
    - unknown
solution_signature:
  critical_trick(s):
    - unknown
  finish_type: unknown
computational_context:
  mode: closed_book_reasoning
  external_tools: forbidden
  hidden_computation: forbidden
  allowed_verification: visible_hand_reasoning_only
  finite_check_expectation: list_or_tabulate_bounded_sets_when_counting
well_posed: unknown
instance_snapshot:
  parameter_value(s):
    unknown: unknown
  final_answer:
    value: pending_no_solution_attempt
    normalized: pending_no_solution_attempt
"""

CONTROLLER_SECTION_ROLE_TAGS = {
    "Athena": ("canon_problem_yaml", "given_ask_route_map", "questions_for_aria", "questions_for_artemis"),
    "Aria": ("aria_canon_yaml", "answers_to_athena", "proposed_solution_route", "route_confidence_and_risks", "solution_continuation"),
    "Artemis": ("artemis_canon_yaml", "answers_to_athena", "answers_to_aria", "route_validation", "aria_claim_audit", "solution_continuation"),
}

ROLE_STATIC_CONTRACTS = {
    "Athena": {
        "schema_id": ATHENA_SCHEMA_ID,
        "fields": ATHENA_SCHEMA_FIELDS,
        "duty": "source ledger, route selection, synthesis, and final answer ownership",
    },
    "Aria": {
        "schema_id": ARIA_SCHEMA_ID,
        "fields": ARIA_SCHEMA_FIELDS,
        "duty": "proof lineage, lemma dependencies, gap closure, and proof status",
    },
    "Artemis": {
        "schema_id": ARTEMIS_CONTRACT_ID,
        "fields": ARTEMIS_AUDIT_FIELDS,
        "duty": "arithmetic, enumeration, boundary, and answer-contract audit",
    },
}

"""## 07.5 - Dynamic Turn Discipline



"""

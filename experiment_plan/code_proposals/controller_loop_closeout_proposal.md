# Controller Loop Closeout Proposal

Generated: 2026-04-29T06:46:52Z

## Finding

`GLOBAL_MAX_BIG_LOOPS = 3` is read, but it is only an upper bound. The current closeout gate allows loop 1 to terminate whenever `selected_candidate != "none"` and `loop_no >= MIN_BIG_LOOP_FOR_CLOSEOUT`. With `GLOBAL_MIN_BIG_LOOP_FOR_CLOSEOUT = 1`, a mandatory Athena finalization answer can close the run even when peer validation remains `disagreement_open`, reports are collapsed, peer confidence is zero, or explicit objections exist.

This is why the loop knob looks inaccurate: the max-loop cap is respected by the `for` range, but the permissive closeout break fires before loop 2 can begin.

## Exact Current Snippets

### Knobs Are Read

```python
  240: def build_loop_mechanics_config(global_state: dict[str, Any] | None = None) -> dict[str, Any]:
  241:     gs = global_state if isinstance(global_state, dict) else {}
  242:     global_turn_max = max(0, _coerce_int_local(gs.get("GLOBAL_MAX_TURN_TOKENS"), 0))
  243:     if global_turn_max > 0:
  244:         athena_open = athena_synthesis = max(64, global_turn_max)
  245:         peer_exchange = peer_report = max(64, global_turn_max)
  246:     else:
  247:         athena_open = max(64, _coerce_int_local(gs.get("ATHENA_OPEN_MAX_TOKENS"), ATHENA_OPEN_MAX_TOKENS_DEFAULT))
  248:         athena_synthesis = max(64, _coerce_int_local(gs.get("ATHENA_SYNTHESIS_MAX_TOKENS"), ATHENA_SYNTHESIS_MAX_TOKENS_DEFAULT))
  249:         peer_exchange = max(64, _coerce_int_local(gs.get("PEER_EXCHANGE_MAX_TOKENS"), PEER_EXCHANGE_MAX_TOKENS_DEFAULT))
  250:         peer_report = max(64, _coerce_int_local(gs.get("PEER_REPORT_MAX_TOKENS"), PEER_REPORT_MAX_TOKENS_DEFAULT))
  251:     return {
  252:         "max_big_loops": max(1, _coerce_int_local(gs.get("GLOBAL_MAX_BIG_LOOPS"), _coerce_int_local(gs.get("MAX_BIG_LOOPS"), MAX_BIG_LOOPS_DEFAULT))),
  253:         "min_big_loop_for_closeout": max(1, _coerce_int_local(gs.get("GLOBAL_MIN_BIG_LOOP_FOR_CLOSEOUT"), MIN_BIG_LOOP_FOR_CLOSEOUT_DEFAULT)),
  254:         "inner_total_exchanges": max(1, _coerce_int_local(gs.get("GLOBAL_INNER_TOTAL_EXCHANGES"), _coerce_int_local(gs.get("INNER_TOTAL_EXCHANGES"), INNER_TOTAL_EXCHANGES_DEFAULT))),
  255:         "inner_reasoning_exchanges": max(1, _coerce_int_local(gs.get("INNER_REASONING_EXCHANGES"), INNER_REASONING_EXCHANGES_DEFAULT)),
  256:         "lock_confidence_pct": _clamp_int(gs.get("GLOBAL_CLOSEOUT_CONFIDENCE_PCT"), 0, 100, BOXED_CONFIDENCE_GATE_PCT_DEFAULT),
  257:         "boxed_confidence_gate_pct": _clamp_int(gs.get("GLOBAL_CLOSEOUT_CONFIDENCE_PCT"), 0, 100, BOXED_CONFIDENCE_GATE_PCT_DEFAULT),
```

### Run Emits Simple Arbitration Contract

```python
 2627:     emit_json_event(
 2628:         {
 2629:             "event": "cb075_run_start",
 2630:             "revision": str(CB07_CONTROLLER_REVISION),
 2631:             "max_loops": int(MAX_BIG_LOOPS),
 2632:             "inner_total_exchanges": int(INNER_TOTAL_EXCHANGES),
 2633:             "inner_reasoning_exchanges": int(INNER_REASONING_EXCHANGES),
 2634:             "min_big_loop_for_closeout": int(MIN_BIG_LOOP_FOR_CLOSEOUT),
 2635:             "closeout_confidence_pct_strict_gt": int(BOXED_CONFIDENCE_GATE_PCT),
 2636:             "closeout_requires_exact_integer_consensus": False,
 2637:             "closeout_decision_rule": "simple_answer_arbitration",
 2638:             "routing_mode": str(LOOP_MECHANICS.get("controller_routing_mode", "")),
 2639:             "live_knobs": dict(live_knobs),
 2640:         },
 2641:         force=False,
 2642:     )
 2643:
 2644:     for loop_no in range(1, int(MAX_BIG_LOOPS) + 1):
```

The emitted `closeout_requires_exact_integer_consensus: False` is important. It documents that strict consensus is not currently required.

### Athena Mandatory Finalization Can Create A Candidate After Disagreement

```python
 2933:         turn_index, athena_final_outcome = _run_final_turn(
 2934:             session=solver_session,
 2935:             problem_text=str(problem_text),
 2936:             prompt_state=dict(final_prompt_state),
 2937:             generation_base=dict(SOLVER_SOLVE_GENERATION),
 2938:             chosen_answer=str(preliminary_selected_candidate),
 2939:             turn_index=int(turn_index),
 2940:             transcript=transcript,
 2941:         )
 2942:         if bool(athena_final_outcome.get("ok")):
 2943:             finalized_answer = normalize_candidate_answer(str(athena_final_outcome.get("answer", "none") or "none"))
 2944:             finalized_confidence = int(athena_final_outcome.get("confidence_pct", 0) or 0)
 2945:             if str(finalized_answer) != "none":
 2946:                 final_candidate = str(finalized_answer)
 2947:                 final_confidence_pct = int(finalized_confidence)
 2948:                 state["athena_candidate_answer"] = str(finalized_answer)
 2949:                 state["athena_exact_candidate_answer"] = str(finalized_answer)
 2950:                 state["athena_candidate_is_exact_integer"] = True
 2951:                 state["athena_confidence_pct"] = int(finalized_confidence)
 2952:                 state["athena_supplied_confidence_pct"] = int(finalized_confidence)
 2953:                 final_text_from_finalizer = str(
 2954:                     athena_final_outcome.get("final_text", emit_final(str(finalized_answer), confidence_pct=int(finalized_confidence)))
 2955:                 )
 2956:                 observed_final_answer_text = str(final_text_from_finalizer)
 2957:                 state["observed_final_answer_text"] = str(final_text_from_finalizer)
 2958:                 state["recent_summary"] = list(state.get("recent_summary") or []) + [
 2959:                     {
 2960:                         "speaker": "Athena",
 2961:                         "loop": int(loop_no),
 2962:                         "stage": "finalization",
 2963:                         "candidate_answer": str(finalized_answer),
 2964:                         "confidence_pct": int(finalized_confidence),
 2965:                         "reason": "mandatory_final_answer_block_turn",
 2966:                     }
 2967:                 ]
 2968:                 arbitration_candidates[0]["answer"] = str(finalized_answer)
 2969:                 arbitration_candidates[0]["confidence_pct"] = int(finalized_confidence)
 2970:                 arbitration_candidates[0]["supplied_confidence_pct"] = int(finalized_confidence)
 2971:                 arbitration_candidates[0]["source"] = "athena_finalization"
 2972:         else:
 2973:             state["recent_summary"] = list(state.get("recent_summary") or []) + [
 2974:                 {
 2975:                     "speaker": "Athena",
 2976:                     "loop": int(loop_no),
 2977:                     "stage": "finalization",
 2978:                     "candidate_answer": "none",
 2979:                     "confidence_pct": 0,
 2980:                     "reason": "mandatory_final_answer_block_turn_failed",
 2981:                 }
 2982:             ]
 2983:         if str(final_candidate) == "none":
 2984:             arbitration_resolution = {
 2985:                 "mode": "unresolved_no_valid_mandatory_final_answer_turn",
 2986:                 "answer": "none",
 2987:                 "confidence_pct": 0,
 2988:                 "supporting_roles": [],
 2989:                 "decision_rule": "mandatory_athena_final_answer_block_turn_required",
 2990:                 "candidates": list(arbitration_candidates),
 2991:             }
 2992:         else:
 2993:             supporting_roles = ["Athena"]
 2994:             if str(final_candidate) == str(aria_exact_candidate):
 2995:                 supporting_roles.append("Aria")
 2996:             if str(final_candidate) == str(artemis_exact_candidate):
 2997:                 supporting_roles.append("Artemis")
 2998:             arbitration_resolution = {
 2999:                 "mode": "athena_mandatory_final_answer_turn",
 3000:                 "answer": str(final_candidate),
 3001:                 "confidence_pct": int(final_confidence_pct),
 3002:                 "supporting_roles": list(supporting_roles),
 3003:                 "decision_rule": "final_answer_block_is_separate_unskippable_athena_turn",
 3004:                 "candidates": list(arbitration_candidates),
 3005:             }
```

The finalizer creates an `athena_mandatory_final_answer_turn` arbitration result for any non-`none` Athena final answer.

### Current Closeout Gate

```python
 3013:         final_confident_enough = bool(int(final_confidence_pct) > int(BOXED_CONFIDENCE_GATE_PCT))
 3014:         peers_confident_enough = bool(int(peer_min_confidence) > int(BOXED_CONFIDENCE_GATE_PCT))
 3015:         open_objections = [str(item).strip() for item in list(state.get("open_objections") or []) if str(item).strip()]
 3016:         loop_summary_bits = [
 3017:             f"loop={int(loop_no)}",
 3018:             f"athena={str(final_candidate)}/{int(final_confidence_pct)}",
 3019:             f"aria={str(aria_exact_candidate)}/{int(aria_meta.get('confidence_pct', 0) or 0)}",
 3020:             f"artemis={str(artemis_exact_candidate)}/{int(artemis_meta.get('confidence_pct', 0) or 0)}",
 3021:             f"peer_validation={str(state.get('peer_validation_status', 'unknown') or 'unknown')}",
 3022:             f"trio_confidence={min(int(final_confidence_pct), int(peer_min_confidence)) if int(peer_min_confidence) > 0 else int(final_confidence_pct)}",
 3023:             f"arbitration={str(selected_candidate)}/{int(selected_confidence_pct)}:{str(arbitration_resolution.get('mode', 'unresolved'))}",
 3024:         ]
 3025:         closeout_objections = list(open_objections)
 3026:         if str(final_candidate) == "none":
 3027:             closeout_objections.append("Athena did not produce a valid mandatory final_answer_block turn.")
 3028:         if not bool(peer_reports_distinct):
 3029:             closeout_objections.append("Peer reports are not sufficiently distinct.")
 3030:         if not bool(final_trio_exact_alignment):
 3031:             closeout_objections.append("Athena has not yet reconciled to the same exact integer answer as Aria and Artemis.")
 3032:         if not bool(final_confident_enough):
 3033:             closeout_objections.append(f"Athena final confidence is below {int(BOXED_CONFIDENCE_GATE_PCT)}.")
 3034:         if not bool(peers_confident_enough):
 3035:             closeout_objections.append(f"Peer confidence is below {int(BOXED_CONFIDENCE_GATE_PCT)}.")
 3036:         if bool(closeout_objections):
 3037:             loop_summary_bits.append(f"objection={closeout_objections[0]}")
 3038:         print(f"cb075_loop_end = {' | '.join(loop_summary_bits)}", flush=True)
 3039:
 3040:         if int(loop_no) >= int(MIN_BIG_LOOP_FOR_CLOSEOUT) and str(selected_candidate) != "none":
 3041:             status = "closed_out_simple_answer_arbitration"
 3042:             verified = True
 3043:             submission_answer_override = str(selected_candidate)
 3044:             submission_mode = str(arbitration_resolution.get("mode", "simple_arbitration") or "simple_arbitration")
 3045:             state["closeout_resolution"] = {
 3046:                 "mode": str(submission_mode),
 3047:                 "answer": str(submission_answer_override),
 3048:                 "confidence_pct": int(selected_confidence_pct),
 3049:                 "supporting_roles": list(arbitration_resolution.get("supporting_roles") or []),
 3050:                 "decision_rule": str(arbitration_resolution.get("decision_rule", "")),
 3051:                 "candidates": list(arbitration_resolution.get("candidates") or []),
 3052:                 "diagnostic_objections": list(closeout_objections),
 3053:             }
 3054:             final_answer_text = str(emit_final(str(selected_candidate), confidence_pct=int(selected_confidence_pct)))
 3055:             observed_final_answer_text = str(final_answer_text)
 3056:             state["observed_final_answer_text"] = str(observed_final_answer_text)
 3057:             break
```

Line 3040 is the missing link: it ignores `closeout_objections`, `peer_validation_status`, `final_trio_exact_alignment`, `final_confident_enough`, and `peers_confident_enough`.

## Proposed Pseudocode Patch

```python
closeout_ready = (
    int(loop_no) >= int(MIN_BIG_LOOP_FOR_CLOSEOUT)
    and str(selected_candidate) != "none"
    and not closeout_objections
    and str(state.get("peer_validation_status")) == "confidence_aligned"
    and bool(final_trio_exact_alignment)
    and bool(final_confident_enough)
    and bool(peers_confident_enough)
)

if closeout_ready:
    status = "closed_out_strict_confidence_aligned"
    verified = True
    submission_answer_override = str(selected_candidate)
    ...
    break

state["recent_summary"] = list(state.get("recent_summary") or [])[-12:]
state["peer_reasoning_log"] = list(state.get("peer_reasoning_log") or [])[-18:]
continue
```

## Optional Explicit Knobs

```python
GLOBAL_REQUIRE_CONFIDENCE_ALIGNED_CLOSEOUT = True
GLOBAL_REQUIRE_TRIO_EXACT_CLOSEOUT = True
GLOBAL_REQUIRE_NO_OPEN_OBJECTIONS_CLOSEOUT = True
GLOBAL_ALLOW_MANDATORY_FINALIZATION_FALLBACK_ON_LAST_LOOP = True
```

If the run reaches `MAX_BIG_LOOPS` and still has disagreement, the final answer can be exported as `verified=False` or as a separate fallback, but it should not be marked verified by simple arbitration.

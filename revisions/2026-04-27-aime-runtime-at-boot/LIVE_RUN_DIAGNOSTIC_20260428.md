# Live Run Diagnostic: April 28 Controller Reset Bypass

The live AIME run pasted during this revision was still useful, but it should not be frozen as final RuntimeAtBoot transfer proof.

## What The Log Showed

The run installed `2026-04-27-cb11_5-boot-memory-preserving-boundary-reset-r3` and then began solving. The first turns for each problem showed:

- `active_dialogue_messages_current: 0`
- `active_session_history_tokens_current: 0`
- active system prompt estimates near `12` or `13` tokens
- `cb075_question_context_reset` immediately before the solve turn

That signature means the studied CB8 boot memory was not active inside the role session at the first solve turn.

## Interpretation

The score and token behavior remain meaningful controller evidence. The pasted run shows the April 27 architecture solving with far smaller per-problem token volume than the older unrestricted reference, and early progress was strong.

It is not, however, a valid RuntimeAtBoot memory-transfer proof. Certification can pass, but if a later controller reset clears the studied session state, the solve turn no longer carries the studied memory.

## r4 Correction

CB11.5 r4 wraps the controller reset function `_reset_sessions_for_new_question` in addition to the outer `run_aen_protocol` boundary. After the base controller reset, r4 restores each role's `_cb8_boot_memory_baseline`, enriches the reset report, and prints:

```text
cb11_5_controller_reset_boot_memory_restore
```

A corrected rerun should show `boot_memory_required: True`, `boot_memory_preserved: True`, `boot_memory_baseline_present: True`, and `boot_memory_restored: True` at the controller reset boundary before its pre-turn certificates are accepted as transfer evidence.
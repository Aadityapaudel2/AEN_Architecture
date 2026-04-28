# Critical Cells

Use the current repair path in this order:

1. `cb08_runtimeatboot_bootcert_v1_5_0_ack_gated.py`
2. `cb11_5_architecture_certificate_r4.py`
3. `cb12_aime2026_public_hf_runner.md`

`cb08_runtimeatboot_bootcert_v1_5_0_ack_gated.py` is the Apr28 repair cell. It restores frozen-style 75-line certification and hard-gates RuntimeAtBoot study acknowledgement before memory baseline capture. A run where `memory_studied: true` and `ack_success_count: 0` is now invalid.

`cb08_runtimeatboot_bootcert_v1_4_9.py` is retained for audit history. It is not the recommended next-run cell.

`cb11_5_architecture_certificate_r3.py` is retained as an intermediate artifact. The r3 wrapper restored boot memory around the outer protocol boundary, but the live controller performed a later raw question reset. The r4 wrapper additionally wraps `_reset_sessions_for_new_question` and emits `cb11_5_controller_reset_boot_memory_restore`.

# Critical Cells

Execute `cb11_5_architecture_certificate_r4.py` for the April 27/28 corrected path.

`cb11_5_architecture_certificate_r3.py`, if present in this folder, is retained as an intermediate artifact for audit history. The r3 wrapper restored boot memory around the outer protocol boundary, but the live controller performed a later raw question reset. The r4 wrapper additionally wraps `_reset_sessions_for_new_question` and emits `cb11_5_controller_reset_boot_memory_restore`.
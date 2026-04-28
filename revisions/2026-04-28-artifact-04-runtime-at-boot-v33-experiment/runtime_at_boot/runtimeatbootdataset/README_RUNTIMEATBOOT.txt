runtimeatbootdataset

Status:
  Runtime-at-Boot canon dataset v33, ready as the active Kaggle payload root.

Kaggle dataset:
  aadityapaudel/runtimeatboot

Expected Kaggle mount path:
  /kaggle/input/runtimeatboot/runtimeatbootdataset

Notebook override:
  RUNTIME_AT_BOOT_DATASET_FOLDER = "runtimeatbootdataset"

Canon v33 boot files:
  boot/athena/Athena_epistemic_boot_100_final_hq.ndjson                           100 study rows
  boot/athena/Athena_epistemic_boot_100_final_certification_hq.ndjson             100 certification rows
  boot/aria/Aria_problem_proof_boot_100_final.ndjson                              100 study rows
  boot/aria/Aria_problem_proof_boot_100_final_mcq_2q.ndjson                       100 certification rows
  boot/artemis/Artemis_problem_proof_boot_100_final_hq.ndjson                     100 study rows
  boot/artemis/Artemis_problem_proof_boot_100_final_hq_mcq.ndjson                 100 certification rows

Why study and certification are separate:
  Study rows are answer-key-free Runtime-at-Boot memory rows and may be converted into SAFE_RUNTIME_BOOT_MEMORY.
  Certification rows are answer-bearing MCQ gates used to prove that the boot memory loaded correctly.
  The certification files must not be injected into ordinary solve prompts.

Sanitization:
  The Apr 27 distinct 100-slot all-role work has been promoted into v33 canonical filenames and v33 row identity.
  Prior staging duplicates, role staging audits, cache files, and the stale Apr 22 rebuild helper were removed from the active root.
  A full pre-sanitize backup was written under:
    Updates_to_AEN/bootupdates/archives/runtimeatbootdataset_pre_v33_sanitize_20260427-214041

Retained non-boot material:
  canondatabase/ is legacy/reference material and is not part of v33 boot memory injection.
  test/ contains post-boot evaluation/export files and is not part of ordinary boot-study memory.

Verification files:
  runtimeatboot_manifest.json
  SANITIZED_BOOT_MEMORY_BOUNDARY.json
  V33_ROLE_FILE_AUDIT.csv
  V33_SANITIZE_REPORT.md
  SHA256SUMS.txt
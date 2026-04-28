runtimeatbootdataset

Purpose:
  boot/ is a role-certification dataset only.
  test/ carries clean evaluation files for post-boot artifact export and scoring.

Expected Kaggle mount path:
  /kaggle/input/runtimeatboot/runtimeatbootdataset

Local override for the notebook:
  RUNTIME_AT_BOOT_DATASET_FOLDER = "runtimeatbootdataset"

Live boot files:
  boot/athena/Athena_epistemic_boot_100_final_hq.ndjson
  boot/athena/Athena_epistemic_boot_100_final_certification_hq.ndjson
  boot/aria/Aria_problem_proof_boot_100_final.ndjson
  boot/aria/Aria_problem_proof_boot_100_final_mcq_2q.ndjson
  boot/artemis/Artemis_problem_proof_boot_100_final_hq.ndjson
  boot/artemis/Artemis_problem_proof_boot_100_final_hq_mcq.ndjson

Remaining smoke files:
  smoke/runtimeatboot_easy10.json
  smoke/runtimeatboot_easy10_kaggle_test.csv

Remaining diagnostic test files:
  test/voe_eval_clean19/voe_clean19_integer.csv
  test/voe_eval_clean19/voe_clean19_integer_key.csv
  test/voe_eval_clean19/voe_clean19_manifest.json

Sanitization note:
  Answer-bearing golden transcripts and obsolete smoke/test1 files were moved
  to timestamped archives under:
  kaggle_aimo3/results/runtime_dataset_archives/

Boundary note:
  test/ files are not injected into solving prompts. CB12 reads test/voe_eval_clean19
  after Runtime-at-Boot certification and first audits live solve prompts/dialogue for
  contamination markers.

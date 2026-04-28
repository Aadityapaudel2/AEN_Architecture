# RuntimeAtBoot v33 Sanitize Report

- Canon revision: runtimeatboot-v33-canon-100-distinct-all-roles-20260428
- Active Kaggle payload root: `N:\Research\runtimeatbootdataset`
- Promotion source: Apr 27 distinct 100-slot all-role Runtime-at-Boot work.
- Backup before sanitize: `N:\Research\Updates_to_AEN\bootupdates\archives\runtimeatbootdataset_pre_v33_sanitize_20260427-214041`

## Why Study And Cert Stay Separate
Study rows are answer-key-free boot memory. Certification rows are answer-bearing MCQ probes for the boot gate. Keeping them in separate canonical files is the boundary that lets CB8 load memory without leaking certification keys into solve prompts.

## Canonical Files
- `boot/athena/Athena_epistemic_boot_100_final_hq.ndjson`: 100 rows, answer rows 0, bad JSON 0, sha256 `b69425dedec79b3d7db06faf4d60f0acab88493dee394190e98e50810d0aebe2`
- `boot/athena/Athena_epistemic_boot_100_final_certification_hq.ndjson`: 100 rows, answer rows 100, bad JSON 0, sha256 `82fe607651f89f7278ccc9ce15ab6534fa6f57be84fa7557993b073ad373fd71`
- `boot/aria/Aria_problem_proof_boot_100_final.ndjson`: 100 rows, answer rows 0, bad JSON 0, sha256 `7b48e9c07870ad315a0726704bbb720dc44b399046433ab15a484f7ca66696f1`
- `boot/aria/Aria_problem_proof_boot_100_final_mcq_2q.ndjson`: 100 rows, answer rows 100, bad JSON 0, sha256 `2356b9a709adff3ffd71d12db415d05e6a8caa9fa63a422aa9accdc334dd5c23`
- `boot/artemis/Artemis_problem_proof_boot_100_final_hq.ndjson`: 100 rows, answer rows 0, bad JSON 0, sha256 `4bcf375f38657219547fb37dbb9287d63ccf675c37908da94b586a6d71cef092`
- `boot/artemis/Artemis_problem_proof_boot_100_final_hq_mcq.ndjson`: 100 rows, answer rows 100, bad JSON 0, sha256 `17f48a81a80abef456848c703587d4d89d9e14a482959fee1d46baa7dbaf4c67`

## Removed From Active Root
- Prior staging NDJSON duplicates under boot role folders.
- Prior staging role audit CSVs under boot role folders.
- Legacy Athena boot audit markdown.
- `__pycache__/`.
- Stale Apr 22 rebuild helper script.
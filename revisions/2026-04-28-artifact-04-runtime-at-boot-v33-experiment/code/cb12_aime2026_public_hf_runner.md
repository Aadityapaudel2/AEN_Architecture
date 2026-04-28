# CB12 AIME-2026 Public HF Runner

This is the public-data benchmark loader used by the April 27 notebook path. It is intentionally kept as a cell-sized recipe instead of a standalone package.

```python
from pathlib import Path
from datetime import datetime, timezone
import pandas as pd

CB12_GENERIC_HF_REVISION = "2026-04-25-cb12-generic-hf-explicit-row-contract-r1"

BENCHMARK_NAME = "AIME-2026"
BENCHMARK_DATASET_ID = "MathArena/aime_2026"
BENCHMARK_HF_PARQUET_PATH = "hf://datasets/MathArena/aime_2026@main/data/train-00000-of-00001.parquet"

BENCHMARK_PROBLEM_INDICES = []
BENCHMARK_START_PROBLEM_INDEX = 1
BENCHMARK_QUESTION_COUNT = 0

raw_df = pd.read_parquet(BENCHMARK_HF_PARQUET_PATH).fillna("").reset_index(drop=True)
raw_df["problem_idx"] = raw_df["problem_idx"].astype(int)
raw_df = raw_df.sort_values("problem_idx").reset_index(drop=True)

if BENCHMARK_PROBLEM_INDICES:
    wanted = [int(x) for x in BENCHMARK_PROBLEM_INDICES]
    selected_df = raw_df[raw_df["problem_idx"].isin(wanted)].copy()
    selected_df = selected_df.set_index("problem_idx").loc[wanted].reset_index()
    selection_mode = "explicit_problem_indices"
elif int(BENCHMARK_QUESTION_COUNT) > 0:
    start_idx = int(BENCHMARK_START_PROBLEM_INDEX)
    stop_idx = start_idx + int(BENCHMARK_QUESTION_COUNT) - 1
    selected_df = raw_df[(raw_df["problem_idx"] >= start_idx) & (raw_df["problem_idx"] <= stop_idx)].copy()
    selection_mode = "start_count"
else:
    selected_df = raw_df.copy()
    selection_mode = "full_dataset"

TEST_ROWS = [
    {
        "id": f"aime2025_{int(row.problem_idx):02d}",
        "question_id": f"aime2025_{int(row.problem_idx):02d}",
        "problem_idx": int(row.problem_idx),
        "question": str(row.problem),
        "problem": str(row.problem),
        "answer": str(row.answer).strip(),
    }
    for row in selected_df.itertuples(index=False)
]

_run_stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
TRANSCRIPT_ARTIFACT_DIR = f"/content/drive/MyDrive/AthenaV5_colab/outputs/{BENCHMARK_NAME}_export_{selection_mode}_{len(TEST_ROWS)}q_{_run_stamp}"

BENCHMARK_RUN_SUMMARY = run_attached_test_dataset_export(
    test_dataset=TEST_ROWS,
    limit=None,
    artifact_dir=TRANSCRIPT_ARTIFACT_DIR,
    submission_csv_path=f"{TRANSCRIPT_ARTIFACT_DIR}/attached_test_submission.csv",
    results_csv_path=f"{TRANSCRIPT_ARTIFACT_DIR}/attached_test_full_log.csv",
)
```

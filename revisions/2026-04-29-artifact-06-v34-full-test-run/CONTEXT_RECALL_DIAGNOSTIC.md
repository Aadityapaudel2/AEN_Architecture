# V34 Context Recall Diagnostic

This note corrects the interpretation of the V34 full AIME-2026 run.

V34 remains an important Runtime-at-Boot result, but it must not be framed as a blind or answer-free AIME solve. The studied boot rows contained exact answer anchors for known AIME-2026 misses. The run therefore demonstrates that the Runtime-at-Boot memory layer was loaded, preserved across question resets, and explicitly recalled by the models during solving. It does not demonstrate that three Qwen 3.5 9B roles independently solved AIME-2026 at 96.67%.

## What The Transcript Shows

The clearest diagnostic is Q11. The published transcript contains direct self-reports that the model was using a boot answer key rather than only a generalized route hint:

- `raw_export/transcripts/aime_2026_11.txt:1871`: Athena says the boot record for Problem 11 explicitly states `Verified answer: 896`.
- `raw_export/transcripts/aime_2026_11.txt:2538`: Aria says the boot record explicitly lists the verified answer key as `896`.
- `raw_export/transcripts/aime_2026_11.txt:2871`: the transcript says the correct course is to align with the explicit verified value.
- `raw_export/transcripts/aime_2026_11.txt:3056`: the transcript treats the boot record as the authority when derivations disagree.

This is not an isolated textual accident. A scan of the published transcripts found verified-answer or answer-anchor references in at least these files:

| transcript | answer-anchor matches |
| --- | ---: |
| `aime_2026_09.txt` | 16 |
| `aime_2026_10.txt` | 5 |
| `aime_2026_11.txt` | 27 |
| `aime_2026_15.txt` | 34 |
| `aime_2026_17.txt` | 18 |
| `aime_2026_18.txt` | 3 |
| `aime_2026_21.txt` | 6 |
| `aime_2026_23.txt` | 40 |
| `aime_2026_24.txt` | 23 |
| `aime_2026_29.txt` | 14 |
| `aime_2026_30.txt` | 9 |

The pattern is decisive: the role sessions did not merely absorb broad mathematical strategy. They had access to exact final-answer facts for multiple targeted problems, and the transcripts show those facts being recalled and used.

## What V34 Proves

V34 proves a strong systems point:

1. CB8 successfully studied Runtime-at-Boot records into each role session.
2. The synthetic acknowledgement path avoided boot-time generation loops.
3. The after-certification baseline was captured and restored before each benchmark question.
4. The models could retrieve and cite boot memory many hours later inside the solving loop.
5. The controller architecture preserved that context across the full 12h50m48s end-to-end run.

That is a real positive result. It is direct evidence that Runtime-at-Boot context recall works in this architecture.

## What V34 Does Not Prove

V34 does not prove an answer-free 29/30 AIME result.

The 29/30 score should not be written as: three small models solved AIME-2026 at 96.67%.

The accurate claim is: an answer-aware Runtime-at-Boot repair layer drove a 29/30 internal replay result, and the transcripts verify that the roles could recall boot memory, including exact answer anchors. This makes V34 a context-recall and architecture-preservation artifact, not a blind benchmark artifact.

## Why This Happened

The V34 repair records were answer-aware. They included fields such as `expected_answer`, `observed_wrong_answer`, and text-level phrases like verified answer / known miss / expected final object. CB8 does not separately inject metadata fields as the study layer. However, CB8 loads the row text through `_cb8_boot_memory_records`, specifically from these fields:

```python
row.get("text")
row.get("study_text")
row.get("content")
row.get("memory")
row.get("record")
```

If exact answers appear inside those loaded text fields, they become part of the studied Runtime-at-Boot transcript. That is what happened in V34.

## CB8 Mechanics

For adding or subtracting Runtime-at-Boot rows, CB8 itself does not need to change as long as the same schema and path structure are kept.

To add 20 more lines:

- Update the role NDJSON files under the configured Runtime-at-Boot dataset root.
- Update the matching certification NDJSON files if the certification set changes.
- Keep the row text in one of CB8's supported text fields: `text`, `study_text`, `content`, `memory`, or `record`.
- Ensure `RUNTIME_AT_BOOT_DATASET_ROOT`, or the role-specific `ATHENA_BOOT_PATH`, `ARTEMIS_BOOT_PATH`, and `ARIA_BOOT_PATH`, point at the new upload.
- Check `BOOT_MEMORY_STUDY_LINE_LIMIT` before rerunning.

The current V34 knobs use a selected study limit of 150 records per role. V34 used 113 selected records per role. Adding 20 rows would produce 133 selected records, still under 150. In that case, no CB8 code change is needed. It should simply load the new files.

If the selected record count rises above 150, change the knob, not the CB8 loader logic. Set `BOOT_MEMORY_STUDY_LINE_LIMIT` higher in the runtime knob cell, for example 175 or 200, and keep `BOOT_CERTIFICATION_MAX_TEST_LINES` aligned with the intended certification coverage.

## V35 Clean-Run Requirement

A clean V35 hint-only run should use a contamination-gated boot dataset. Before spending another 12 hours, the dataset should be scanned and rejected if any studied text contains:

- exact final AIME answers,
- `Verified answer`, `verified answer`, or equivalent answer-key phrasing,
- `expected_answer` rendered into studied text,
- `observed_wrong_answer` rendered into studied text if it names the exact correct alternative,
- problem-index-specific answer statements such as `Problem 11 ... 896`,
- phrases like `if all roles give N`, `final object is N`, or `the answer is N` for benchmark items.

The allowed V35 content should be route-level and transferable: domain, skill, failure mode, invariant, audit checklist, route axis, common trap, and finish-check discipline. It should not include the exact benchmark final integer.

## Corrected Interpretation

V34 is still valuable, but its value is different from the originally tempting headline.

Correct interpretation: Runtime-at-Boot memory is being loaded and recalled with high fidelity across a long multi-role benchmark run.

Incorrect interpretation: the architecture independently solved AIME-2026 at 96.67% without answer leakage.

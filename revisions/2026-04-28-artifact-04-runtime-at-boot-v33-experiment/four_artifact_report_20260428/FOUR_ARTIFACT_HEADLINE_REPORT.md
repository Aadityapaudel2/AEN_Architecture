# AIME 2026 Four-Artifact Report

## Final Scoreboard

- Unrestricted: 22/30.
- Artifact 03 Apr27 benchmarkgrade v0.2.3: 21/30.
- Artifact 04 Apr28 RuntimeAtBoot experiment: 17/30.
- Frozen pruned: 15/30.

## Faithful Surprise

The Apr28 RuntimeAtBoot experiment did **not** hit the earlier Artifact 03 ceiling. It passed Runtime-at-Boot certification, used about 134,446 tokens/problem on average, and landed at **17/30**. That is far cheaper than the unrestricted paper run (1,125,451 tokens/problem), but it gave back accuracy.

The good news is real but narrow: the Apr28 experiment fixed Q4 and Q27 relative to Artifact 03. The bad news is larger: it lost Q7, Q11, Q18, Q23, Q24, and Q28 that Artifact 03 had right. Net against Artifact 03: +2 fixes, -6 regressions, for a four-question drop.

## What Was Right

Apr28 experiment correct problems: Q1, Q2, Q3, Q4, Q5, Q6, Q8, Q12, Q13, Q14, Q16, Q19, Q20, Q22, Q25, Q26, Q27.

Apr28-over-unrestricted wins: Q13, Q14.

Apr28 experiment fixed Artifact 03 misses: Q4, Q27.

## What Was Wrong

Apr28 experiment misses: Q7, Q9, Q10, Q11, Q15, Q17, Q18, Q21, Q23, Q24, Q28, Q29, Q30.

Apr28 regressions vs Artifact 03: Q7, Q11, Q18, Q23, Q24, Q28.

Apr28 regressions vs unrestricted: Q7, Q11, Q17, Q21, Q23, Q24, Q28.

Invalid Apr28 experiment answer(s): Q9.

## Did Runtime-at-Boot Solve The Issue?

No, not as measured by final score. It solved the gate problem: Runtime-at-Boot passed for all three roles, with 25/25 certification probes per role and boot memory baselines captured. But the solve run still closed with one-loop mandatory Athena final arbitration, and several losses show peer disagreement, peer blockers, or high-confidence wrong finalization.

The run therefore looks like a **resource/context win plus a verification/arbitration regression**. It did not prove the model ceiling; it exposed a controller ceiling.

## Boot Dataset Caveat

The Apr28 artifact passed Runtime-at-Boot, but its boot summary references V32/golden/role certification rows. Treat this run as evidence that the Apr28 boot gate worked for that packaged artifact, not as evidence that the later local v33 canon root was the Kaggle input.

## Did We Make More Issue?

We made at least one issue more visible: the system can certify boot memory and still submit a bad or invalid final answer under mandatory final closeout. Q9 is the cleanest alarm: Apr28 submitted `4133`, outside the AIME answer range, despite answer bounds being present in the controller config.

## Ceiling Read

The empirical ceiling from these four artifacts is still unrestricted at 22/30, then Artifact 03 at 21/30. The Apr28 RuntimeAtBoot experiment did not hit that ceiling. Its 17/30 says the remaining bottleneck is not raw context budget; it is final-answer validation, disagreement handling, and allowing enough repair/search when peers are not actually aligned.

## Visuals

- [Four-run scoreboard](data_visualizations/four_run_scoreboard_q1_q30.svg)
- [Q1-Q30 result grid](data_visualizations/q1_q30_four_run_result_grid.svg)
- [Chunk accuracy](data_visualizations/chunk_accuracy_four_run.svg)
- [Token efficiency](data_visualizations/token_efficiency_four_run.svg)
- [Apr28 experiment vs Artifact 03 delta](data_visualizations/artifact04_vs_artifact03_delta.svg)
- [Apr28 experiment miss playbook](data_visualizations/artifact04_miss_playbook_q1_q30.svg)
- [Late-game box score](data_visualizations/late_game_q26_q30_four_run.svg)
- [Cumulative score trajectory](data_visualizations/cumulative_score_trajectory_four_run.svg)
- [Apr28 experiment boot/controller shape](data_visualizations/artifact04_boot_and_controller_shape.svg)
- [Four-run side-by-side answers](data_visualizations/four_run_side_by_side_answers.svg)

## Tables

- `data_analysis/tables/all_four_runs_q1_q30_long.csv`
- `data_analysis/tables/four_run_q1_q30_comparison.csv`
- `data_analysis/tables/run_summary_q1_q30_and_slices.csv`
- `data_analysis/tables/official_q1_q30_detail.csv`
- `data_analysis/tables/official_failure_warning_taxonomy_q1_q30.csv`
- `data_analysis/tables/official_runtime_at_boot_summary.csv`

# Runtime-at-Boot Dataset V34

V34 is an additive, answer-aware repair layer built on the V31/V33 Runtime-at-Boot dataset. It prepends targeted long-form study records for the AIME-2026 full-run miss set while preserving the existing boot and certification files.

Source answer key: [MathArena/aime_2026](https://huggingface.co/datasets/MathArena/aime_2026), whose dataset card exposes `problem_idx`, `problem`, and `answer` and states that the questions were extracted and verified from AIME 2026.

## Added Failure Set

| Problem | Verified answer | Prior AEN answer | Domain | Repair skill |
|---:|---:|---:|---|---|
| 7 | 396 | 341 | permutation cycle structure | surjection_to_permutation_cycle_length_divisibility |
| 9 | 29 | 4133 | conditional probability on cube orientations | top-face_history_conditioned_visibility |
| 10 | 156 | 133 | rotated triangle geometry | coordinate_rotation_about_circumcenter |
| 11 | 896 | 584 | grid extremal arrangement | checkerboard_cut_extremal_absolute_difference |
| 15 | 83 | 1 | cell-loop tiling enumeration | partition_by_rectangular_loop_boundaries |
| 17 | 243 | 69 | directed trail transfer matrix | edge-use_state_across_ladder_with_diagonals |
| 18 | 503 | 505 | nonconvex polygon geometry with modular area | coordinate_walk_angle_constraints_integer_filter |
| 21 | 50 | 18 | parabola-circle tangency | normal_distance_critical_values |
| 23 | 245 | 125 | incenter geometry and integer side search | isosceles_incenter_perimeter_ratio_diophantine |
| 24 | 669 | 558 | infinite decimal series floor modulo | repunit_series_floor_carry_control |
| 28 | 107 | 12 | finite set matching with path components | cousin_count_component_product |
| 29 | 157 | 5 | left-associative parity operation on compositions | dynamic_program_over_sum_and_running_value_parity |
| 30 | 393 | 364 | modular enumeration over ternary tuples | mod3_polynomial_count_with_cyclic_terms |

## Role Files

| Role | Study file | Added records | Total records | Min added chars |
|---|---|---:|---:|---:|
| athena | `boot/athena/Athena_epistemic_boot_100_final_hq.ndjson` | 13 | 113 | 22493 |
| artemis | `boot/artemis/Artemis_problem_proof_boot_100_final_hq.ndjson` | 13 | 113 | 22514 |
| aria | `boot/aria/Aria_problem_proof_boot_100_final.ndjson` | 13 | 113 | 22434 |

## Intended Use

Use this dataset for the next internal AEN run with `BOOT_MEMORY_STUDY_LINE_LIMIT=150`, `GLOBAL_MAX_BIG_LOOPS=3`, and strict closeout. Because V34 records include verified answers for known misses, this is an answer-aware repair ablation, not a blind public benchmark setting.

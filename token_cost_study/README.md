# Token Cost Study

This folder records an auditable token-cost calculation for the five full AIME-2026 AEN runs already published in the revision ledger, now grounded in the observed Colab compute-unit economics supplied on 2026-05-06.

## Scope

This is a post-release runtime/accounting lens over AEN. It does not claim that AEN changes the underlying model architecture, sparsifies a dense model, or turns a dense 9B model into a mixture-of-experts model. Dense, MoE, quantization, serving kernels, batching, and hardware all affect the denominator through delivered throughput. AEN sits after model training and release: it is an orchestration protocol that changes how inference is used and audited.

The metric here uses `total_tokens` from the existing AEN run tables, so it should be read as cost per million logged tokens, not as a pure completion-token benchmark. For V34, the raw artifact separates prompt and completion tokens, but the earlier five-run comparison table is standardized on total logged tokens; the derived table keeps that same basis for apples-to-apples comparison.

Google Colab consumer runtimes are treated separately from Google Cloud/Vertex machines. Colab GPU assignment is not guaranteed and available GPU/TPU types vary over time. Therefore, the Colab rows use the actual observed compute-unit burn rate, while the Google GPU rows are wall-time-equivalent price baselines.

## Observed Colab Rate

User-supplied Colab economics:

- `600 compute units = $50`
- `8.71 compute units/hour`
- `USD/compute_unit = 50 / 600 = $0.0833333333`
- `observed_colab_USD/hour = 8.71 * 50 / 600 = $0.7258333333/hour`
- `hours_per_600_CU_pack = 600 / 8.71 = 68.8863375431 hours`

## Equation

Let:

- `T = total_logged_tokens`
- `S = total_wall_seconds`
- `H = hourly_USD` for a runtime, machine, or GPU price baseline
- `R = T / S`, logged tokens per second

Then:

```text
run_cost_USD = H * S / 3600
cost_per_million_logged_tokens = run_cost_USD / (T / 1,000,000)
cost_per_million_logged_tokens = H * 1,000,000 / (R * 3600)
```

For the observed Colab row, `H = $0.7258333333/hour`.

## Five-Run Colab Calculation

| run | score | total logged tokens | wall hours | CU/run | Colab $/run | Colab $/M logged tokens | runs per 600 CU pack |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Frozen | 15/30 | 21,333,011 | 1.525 | 13.28 | $1.11 | $0.0519 | 45.18 |
| Unrestricted | 22/30 | 33,763,517 | 3.170 | 27.61 | $2.30 | $0.0681 | 21.73 |
| Apr27 benchmark | 21/30 | 3,858,740 | 2.863 | 24.94 | $2.08 | $0.5386 | 24.06 |
| Apr28 RAB v33 | 17/30 | 4,033,378 | 3.210 | 27.96 | $2.33 | $0.5777 | 21.46 |
| V34 answer-aware | 29/30 | 130,647,799 | 11.903 | 103.68 | $8.64 | $0.0661 | 5.79 |

## Google High-Memory Price Baselines

| baseline | memory | hourly USD | basis |
| --- | ---: | ---: | --- |
| Observed Colab CU rate | variable GB | $0.7258 | User supplied: 600 compute units for $50 and 8.71 compute units per hour. |
| Colab Enterprise A100 80GB GPU | 80 GB | $4.7137 | Accelerator price only; VM CPU, RAM, disk, and network separate. |
| G4 RTX PRO 6000 96GB 1x | 96 GB | $5.1751 | Full machine price from Vertex AI G4 pricing table. |
| A2 Ultra A100 80GB 1x | 80 GB | $5.7818 | Full machine price from Vertex AI A2 pricing table. |
| A3 High H100 80GB 1x | 80 GB | $12.6259 | Derived from A3 docs/specs: 26 vCPU, 234 GB RAM, 1 H100 80GB; Vertex item prices for vCPU, RAM, GPU. |
| G4 RTX PRO 6000 96GB 8x | 768 GB | $41.4007 | Full machine price from Vertex AI G4 pricing table. |
| A4X GB200 186GB 4x | 744 GB | $74.7500 | Full machine price from Vertex AI A4X pricing table. |
| A3 Ultra H200 141GB 8x | 1128 GB | $99.7739 | Full machine price from Vertex AI A3 Ultra pricing table. |
| A3 High H100 80GB 8x | 640 GB | $101.0074 | Full machine price from Vertex AI A3 pricing table. |
| A4 B200 180GB 8x | 1440 GB | $148.2120 | Full machine price from Vertex AI A4 pricing table. |

The Google rows are not predictions of AEN throughput on those machines. They answer: if the logged wall time were unchanged, what would the same run cost at that hourly price? Actual cost would improve or worsen with delivered tokens/sec on each serving stack.

## V34 Comparison

V34 has `130,647,799` logged tokens, `42,850.851` wall seconds, and `29/30` accuracy, but it is answer-aware context-recall replay rather than a blind benchmark.

| price baseline | V34 run cost | V34 $/M logged tokens |
| --- | ---: | ---: |
| Observed Colab CU rate | $8.64 | $0.0661/M |
| Colab Enterprise A100 80GB GPU | $56.11 | $0.4295/M |
| G4 RTX PRO 6000 96GB 1x | $61.60 | $0.4715/M |
| A2 Ultra A100 80GB 1x | $68.82 | $0.5268/M |
| A3 High H100 80GB 1x | $150.29 | $1.1503/M |
| G4 RTX PRO 6000 96GB 8x | $492.79 | $3.7719/M |
| A4X GB200 186GB 4x | $889.75 | $6.8103/M |
| A3 Ultra H200 141GB 8x | $1,187.61 | $9.0902/M |
| A3 High H100 80GB 8x | $1,202.29 | $9.2025/M |
| A4 B200 180GB 8x | $1,764.17 | $13.5032/M |

## Immediate Reading

- At the observed Colab rate, V34 costs about `$8.64` for the full 30-question run, or about `$0.0661` per million logged tokens.
- The compact April 27 and April 28 runs use far fewer tokens, but they log far fewer tokens per second in the existing table, so their observed Colab cost per million logged tokens is higher.
- A 600 CU / $50 pack covers about `5.79` V34-size runs at the observed burn rate, before considering availability limits, disconnects, or Colab policy constraints.
- The central denominator is delivered runtime throughput, not model architecture alone. AEN is post-release orchestration; the same base model can have different cost behavior depending on serving, context traffic, role scheduling, batching, and closeout policy.

## Files

- `data/five_run_cost_per_token.csv`: run-level Colab CU and cost-per-million calculations.
- `data/price_sources_high_memory_gpu.csv`: hourly price baselines and source notes.
- `data/five_run_cost_comparison_by_price_baseline.csv`: all run x price-baseline cost calculations.
- `visualizations/colab_observed_run_costs_linear.svg`: linear chart of observed Colab run costs.
- `visualizations/cost_per_million_logged_tokens_colab_actual.svg`: actual observed Colab dollars per million logged tokens.
- `visualizations/google_high_memory_hourly_price_linear.svg`: linear hourly price comparison for Colab and Google high-memory GPU baselines.
- `visualizations/v34_cost_by_price_baseline.svg`: V34 wall-time-equivalent run cost across baselines.
- `visualizations/v34_cost_per_million_by_price_baseline.svg`: V34 cost per million logged tokens across baselines.
- `visualizations/colab_600cu_pack_capacity.svg`: how many full runs fit in a 600 CU pack.

## Sources Checked

- AEN run metrics: `revisions/data/five_full_run_summary_q1_q30.csv`.
- Colab FAQ on variable runtime/GPU availability: https://research.google.com/colaboratory/intl/en-GB/faq.html
- Colab Enterprise pricing for A100 80GB and other accelerators: https://cloud.google.com/colab/pricing
- Google Compute GPU memory/spec table, including G4 RTX PRO 6000 96GB, H200 141GB, B200 180GB, and GB200 186GB: https://docs.cloud.google.com/compute/docs/gpus
- Vertex AI pricing for G4, A2, A3, A4, and A4X hourly baselines: https://cloud.google.com/vertex-ai/pricing

# V32 Certification Harness Audit

Date: 2026-04-27

Status: `passed`

## Contract

In the best-world run, RuntimeAtBoot study rows are fully injected into live context, certification proves the model read the class artifacts, and the resulting AIME score should be 30/30 by educated targeted studying rather than benchmark-answer recall.

The certification is intentionally a one-letter MCQ for speed. The tightening is not to make the MCQ hard; the tightening is to make the cert row rich and make fixed-letter passing non-viable.

## Answer Distribution

| scope | A | B | C | D | span |
| --- | ---: | ---: | ---: | ---: | ---: |
| total | 4 | 4 | 5 | 5 | 1 |
| athena | 1 | 2 | 2 | 1 | 1 |
| aria | 1 | 1 | 2 | 2 | 1 |
| artemis | 2 | 1 | 1 | 2 | 1 |

## Richness Gate

Required row fields:
- `certification_contract`
- `expected_reasoning`
- `rubric`
- `option_diagnostics`
- `harness_tightening`

Per-role result:
- `athena`: pass; answer sequence `B, C, D, A, B, C`; missing rich fields `0`
- `aria`: pass; answer sequence `C, D, A, B, C, D`; missing rich fields `0`
- `artemis`: pass; answer sequence `D, A, B, C, D, A`; missing rich fields `0`

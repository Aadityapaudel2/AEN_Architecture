# Artificial Evaluation Network (AEN): A Runtime-First Writeup for Mathematical Reasoning

## Executive Summary

This writeup presents **Artificial Evaluation Network (AEN)**, a runtime architecture for exact-answer mathematical reasoning with fixed-weight language models. The project began from a very practical Kaggle frustration: a model can be mathematically capable in isolation and still fail inside the notebook because the surrounding runtime loses the problem, starves the reasoning turn, trusts a weak verifier, or emits the wrong integer. AEN is my attempt to engineer that surrounding runtime with the same seriousness usually reserved for model weights. The project grew around a simple thesis:

> If a human studies before an exam, the improvement comes from what is read, organized, remembered, and checked before the test begins. AEN applies the same idea to language-model inference: before asking a model to solve, the runtime loads a role-specific curriculum, certifies that the memory is active, assigns distinct reasoning duties to multiple model sessions, and lets a controller algorithm decide the final emitted answer.

The full technical paper is:

**Paudel, A. (2026). _Artificial Evaluation Network (AEN): Runtime-at-Boot, Certified Context Loading, and Triadic Controller Algorithms for Mathematical Reasoning_. Research preprint.**  
https://zenodo.org/records/19701459

This writeup is based on the AEN system and the open diagnostic runs described below. The final AIMO3 private-leaderboard submission was caught in queue during the closing window, so I am grounding the report in the public AEN artifact trail, the constrained notebook diagnostic, and the expanded reproduction diagnostics. That queue outcome was painful, but it also made the evidence standard cleaner: every number below is attached to a visible artifact class, runtime budget, and reproducible diagnostic surface. If private-leaderboard artifacts become available during the rebuttal-style follow-up phase, they can be appended as a separate evidence layer.

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F12722911%2F75d4063030f35cbf5afed659038a51e9%2Faen_architecture.png?generation=1776898394252770&alt=media)

Public runtime assets:

- AEN preprint: https://zenodo.org/records/19701459
- RuntimeAtBoot dataset: https://www.kaggle.com/datasets/aadityapaudel/runtimeatboot
- Offline wheel bundle: https://www.kaggle.com/datasets/aadityapaudel/wheels
- Canon v2.1 distillation paper: https://doi.org/10.5281/zenodo.19694800
- Vault of Echoes companion benchmark record: https://doi.org/10.5281/zenodo.18216959
- Two-body evaluator lineage: https://github.com/Aadityapaudel2/Two_LLM_Model_Evaluator/

## 1. Why Runtime Architecture?

Many mathematical reasoning systems focus on post-training: supervised fine-tuning, instruction tuning, Low-Rank Adaptation, preference modeling, or reinforcement learning from human feedback. Those methods can be powerful at scale. The failures I kept seeing were often runtime-shaped: the problem was copied incorrectly, the model defended an early false heuristic, the verifier agreed too quickly, or the final parser grabbed the wrong integer. AEN explores a complementary axis: **inference-time curriculum and controller design**.

The distinction matters for mathematical reasoning. Supervised fine-tuning and reinforcement learning from human feedback are output-optimized: they train a model to imitate or prefer target completions, proof styles, formatting behavior, and conversational norms. In low-data, fixed-compute, or competition-notebook settings, changing weights can be an expensive way to teach a small number of behaviors. AEN instead changes the information environment: it controls what the model reads in-session, how that memory is certified, which role sees which reasoning artifact, and how the final answer is selected.

This is the central AEN bet:

- pretrained models already contain substantial mathematical capability;
- reasoning quality depends heavily on what is active in context at solve time;
- a curated boot curriculum can teach reusable behavior before the problem arrives;
- a controller can prevent a single generation from carrying every responsibility at once;
- final answer emission should be a recorded system decision.

This is the same ordinary intuition as studying before an exam. A good student improves because the right facts, methods, examples, and warnings are active before the first question starts. AEN treats the model first as a reader, then as a solver. The boot process is a certified stage of the run itself.

Concretely, AEN contributes a runtime schema for exact-answer reasoning:

- **Runtime-at-Boot**: load role-specific memory before solving and certify that the memory is active.
- **Triadic role separation**: split problem preservation, proof construction, and computation audit across Athena, Aria, and Artemis.
- **Controller algorithm**: schedule turns, preserve state, parse candidates, apply closeout rules, and own final emission.
- **Distributed long context**: use separate long-context role sessions so memory, transcripts, and obligations do not collapse into one stream.
- **Integer finalization contract**: convert mathematical prose into an evaluator-facing answer through explicit consensus, majority, or confidence-based selection.
- **Artifact trail**: write transcripts, payloads, timing summaries, token profiles, and closeout modes so every answer can be inspected after the run.

## 2. From One Model Call to a Three-Body Runtime

A single model call has an attractive interface: provide the problem, receive a solution, parse an answer. I tried versions of that pattern early on because it is simple and fast. The problem is that the single stream quietly mixes too many duties:

- source transcription,
- route selection,
- proof construction,
- arithmetic checking,
- confidence judgment,
- final wrapper emission.

Once a model writes a long response, the runtime has a prose artifact, but the model is still inside the same stream that produced it. AEN externalizes that stream. One role's answer attempt becomes an input object for another role, and the controller algorithm decides what evidence becomes eligible for finalization. This is the main reason for the triad: the system needs a real pause between proposing, attacking, auditing, and emitting.

The first step toward this was a public two-model solver/verifier evaluator. That lineage established the basic controller boundary: model A proposes, model B inspects, and the wrapper answer is parsed outside the model prose. AEN extends this into a three-body protocol because exact-answer mathematics benefits from three separate pressures:

- **Athena** preserves the problem and later synthesizes.
- **Aria** builds proof structure, alternate routes, and repair proposals.
- **Artemis** audits computation, edge cases, and answer validity.

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F12722911%2F140d7a47eeb13f6750c5136b831f01ac%2Faen_three_body_protocol.png?generation=1776898466372107&alt=media)

This triadic structure is the smallest AEN form that separates problem preservation, proof pressure, computation audit, synthesis, and final emission while still fitting into a high-memory notebook-style runtime.

## 3. Runtime-at-Boot: Reading Before Solving

Runtime-at-Boot (RAB) is the AEN mechanism for turning in-session memory into a certified runtime precondition. Before a solve begins, each role receives curated study rows. The controller then asks deterministic certification questions to verify that the role can recover the relevant memory. A row on disk is only a promise; a row recalled inside the live session is usable memory.

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F12722911%2F7d76beaad6b63ee0620ee33e4fdab5ea%2Frab_schema.png?generation=1776898502330840&alt=media)

RAB is intentionally role-specific:

- **Athena** receives Canon v2.1 YAML-style metadata rows. These teach problem preservation, object tracking, route inventory, and answer-contract awareness.
- **Artemis** receives Canon v2.1 distilled problem-plus-solution rows. These teach audit behavior, calculation pressure, and edge-case checking.
- **Aria** receives a proof-style curriculum curated from proof-oriented readings and screened against a local smaller model.

The certification probes paired with these datasets are deterministic checks. Their purpose is to verify that the relevant memory entered the live prompt state and can influence later reasoning. In practice, this also gives the notebook a sanity check before spending minutes on a hard problem: the run should know whether its role memory is active before the first serious solve turn is generated.

### Why this challenges pure post-training

AEN's claim is narrower and more practical than "runtime beats training." It is this:

- if the dataset is small,
- if compute is limited,
- if model weights are fixed,
- if the final answer must be exact,
- if reproducibility and transcript audit matter,

then runtime curriculum can be a high-leverage path. The dataset can be inspected, changed, excluded, and certified without rebuilding a checkpoint. In a competition notebook, that is a very different engineering surface from training weights, and it is much faster to audit when something goes wrong.

## 4. Long Context and Distributed Memory

AEN uses Qwen-family long-context execution as its runtime substrate. The paper discusses Rotary Position Embedding, Yet another Rotary Position Embedding Extension (YaRN), and Qwen-family long-context releases. Operationally, the goal is to keep role memory, certification probes, the current problem, peer reports, and controller state available in-session.

AEN distributes this across three role sessions. Each role can be configured with approximately one million tokens of context, producing an effective **three-million-token distributed context budget** across the triad. This was one of the practical breakthroughs in the project: instead of asking one session to carry every role, each role gets its own memory, transcript state, and local obligations. Long context is the shelf space; AEN adds the catalog, the checkout rules, and the audit log. It becomes useful when paired with:

- measured boot memory loading,
- certification probes,
- role-specific prompt envelopes,
- turn-level token caps,
- transcript capture,
- controller-visible budget accounting.

This is why AEN combines Qwen-family long context, YaRN-style enablement, and vLLM-style serving with a controller algorithm. The architecture uses long context as a systems substrate for runtime memory. It is valuable because the controller gives it structure.

## 5. Controller Algorithm

AEN is a controller-driven solve protocol. The model roles do the mathematical work, but the controller decides when a role speaks, what evidence is passed forward, and which answer becomes the submission artifact. The controller performs the following steps:

1. Load offline runtime assets and record model, dataset, package, and artifact identifiers.
2. Load the source-of-truth problem statement.
3. Run RAB for each required role.
4. Store certification results and role eligibility.
5. Construct a source-preserving prompt from the problem, role instructions, and safe memory.
6. Ask Athena for the opening decomposition.
7. Ask Aria for proof pressure and route repair.
8. Ask Artemis for computation audit and edge-case pressure.
9. Repeat peer exchanges according to the configured exchange count.
10. Collect candidate answers, objections, confidence, and blocker status.
11. Ask Athena for synthesis after peer reports.
12. Parse eligible candidates and choose the final answer mode.
13. Emit the exact answer wrapper.
14. Write transcripts, result payloads, scoring files, and timing summaries.

[image: 3_body_reasoning_protocol.png]

The important design choice is that the final emitted answer is owned by the controller algorithm. Model prose can recommend an answer; the controller emits the artifact. That one boundary removes a surprising amount of ambiguity from failure analysis.

## 6. Finalization Contract

AIME-style and AIMO-style mathematical surfaces use exact integer outputs. AEN therefore optimizes its current finalization layer for integer answers.

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F12722911%2Fc8f30e47df22a9b9bcb82a19d57d7d18%2Fcontroller_finalization_contract.png?generation=1776898719832926&alt=media)

The controller selects the final answer by recorded evidence:

- if all three roles agree, select strict consensus;
- if two roles agree, select majority vote;
- if no shared answer exists, select the highest-confidence eligible candidate;
- if no candidate passes eligibility, record no eligible answer.

This is deliberately simple. It makes closeout mode visible. It also makes failure analysis possible: a wrong strict consensus, a weak fallback, and an incomplete synthesis are different system states. Without that separation, all of those cases collapse into the same disappointing line in a submission CSV.

## 7. Runtime Knobs

AEN exposes explicit turnable knobs. These are the same knobs that separate a compressed Kaggle run from a ceiling-seeking run:

- `GLOBAL_MAX_BIG_LOOPS`
- `GLOBAL_MIN_BIG_LOOP_FOR_CLOSEOUT`
- `GLOBAL_CLOSEOUT_CONFIDENCE_PCT`
- `GLOBAL_INNER_TOTAL_EXCHANGES`
- `ATHENA_OPEN_MAX_TOKENS`
- `PEER_EXCHANGE_MAX_TOKENS`
- `PEER_REPORT_MAX_TOKENS`
- `ATHENA_SYNTHESIS_MAX_TOKENS`
- `ATHENA_FINAL_MAX_TOKENS`
- role-level caps for Athena, Aria, and Artemis
- streaming and progress-line controls

This matters because a mathematical score is inseparable from the runtime envelope. A one-loop compressed run and a five-loop high-compute run are the same architecture in different operating regions. AEN is designed so those operating regions are named, recorded, and comparable.

## 8. Submission and Evidence Status

The final AIMO3 private-leaderboard submission was queued during the closing window, which prevented a clean private-LB artifact from being used as the main evidence object in this writeup. The hidden AIMO3 rows are competition-private, so the queued run also prevented a direct transcript-level analysis of that surface. To keep the report reproducible and academically useful by the writeup deadline, I report the open AEN diagnostic surfaces:

- Vault of Echoes fresh no-answer-memory run,
- Vault of Echoes memory-certified replay,
- AIME 2026 compressed frozen-notebook run,
- AIME 2026 expanded one-loop run,
- frozen-versus-expanded ablation comparison,
- token-ceiling and context-packing projections.

This makes the writeup auditable. Every reported score is tied to an artifact class, runtime budget, and figure. Losing a private run to queue timing is frustrating; the constructive response is to make the public evidence strong enough that another reader can inspect the system without trusting my narrative. Private-leaderboard results can be appended during the follow-up phase if the platform provides the corresponding rerun evidence.

## 9. Evaluation Surface 1: Vault of Echoes

Vault of Echoes (VoE) is a 25-question lore-infused puzzle corpus designed to stress transcript reading, puzzle-state preservation, answer normalization, and controller discipline. It appears in the public RuntimeAtBoot dataset and is described in the companion UI-native benchmark record.

The first run is a fresh no-answer-memory condition. The roles receive curated boot memory, but the solve prompt does not contain canonical solution rows for the test cases. AEN scores:

**Fresh VoE: 15/25**

The second run is a memory-certified replay. The canonical solution rows for the missed cases are loaded as answer-bearing boot memory and certified before solving. AEN scores:

**Memory-certified VoE replay: 25/25**

This is a context-recall and controller-finalization diagnostic. It shows that certified boot memory can become active enough to change the controller-selected answer. In other words, RAB is doing real work: it moves information from dataset file to live model context, then the controller can recover and emit the relevant answer. That is the mechanism the system needs before memory can be trusted for harder, answer-free reasoning.

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F12722911%2F28b9081f8d350fbe498407e9fa8df237%2Fvoe_trusted_benchmark_comparison.png?generation=1776898829608915&alt=media)

[image: voe_memory_lift.png]

## 10. Evaluation Surface 2: AIME 2026 Compressed Frozen Notebook

The compressed AIME diagnostic used a competition-oriented envelope:

- Athena opening: 1024 generated tokens,
- peer exchanges: 1280 generated tokens,
- peer reports: 1024 generated tokens,
- Athena synthesis: 768 generated tokens,
- final emission: 128 generated tokens,
- one controller loop.

This run scored:

**AIME 2026 compressed frozen notebook: 15/30**

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F12722911%2F5647493923d6f8ec0f6f5941412df86f%2Faime2026_frozen_problem_outcomes.png?generation=1776898901198586&alt=media)

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F12722911%2F9feeee11119351f642c86becfc2fdef5%2Faime2026_frozen_token_cap_pressure.png?generation=1776898935584550&alt=media)

The token evidence explains the result. Athena opening hit the 1024-token cap in 29/30 cases. Athena synthesis hit the 768-token cap in 22/30 cases. The run was doing exactly what it was designed to do: survive a compressed runtime envelope. It also showed the cost of that compression. Many hard problems needed more room than the frozen notebook allowed.

## 11. Evaluation Surface 3: AIME 2026 Expanded One-Loop Diagnostic

The expanded AIME diagnostic used the Hugging Face `MathArena/aime_2026` source and larger turn caps. It stayed within one outer loop but enabled three peer exchanges and more generation room.

This run scored:

**AIME 2026 expanded one-loop: 22/30**

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F12722911%2F8cb2402872660789db1ecfa3b8a775e0%2Faime2026_unrestricted_problem_outcomes.png?generation=1776899051587883&alt=media)

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F12722911%2F6f7137bf666a6070a80452aacfc8ef2b%2Faime2026_unrestricted_closeout_calibration.png?generation=1776899104659297&alt=media)

The improvement is important because the model family and controller family remain aligned. The expanded run gives the roles more room to develop proof routes and makes majority fallback more useful. This is the cleanest ablation in the writeup: same general architecture, more reasoning room, materially better result.

## 12. Ablation: Frozen versus Expanded

The key ablation is the comparison between the compressed frozen notebook and the expanded one-loop diagnostic.

**AIME 2026 score movement: 15/30 -> 22/30**

The system recovered seven problems that the compressed run missed while preserving the same controller philosophy. This is a runtime-budget effect: more reasoning room, more peer exchange, and less severe token pressure materially changed exact-answer behavior.

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F12722911%2Ffe9d94c402bcb5c06081cea419cf039e%2Faime2026_frozen_vs_unrestricted_transcript_delta.png?generation=1776899146088396&alt=media)

The expanded run costs more wall time and transcript volume. That tradeoff is central to AEN: the controller lets us decide where to operate on the accuracy-cost curve. In a competition setting we may choose compression; in a research setting we can open the budget and learn where the architecture actually saturates.

## 13. Scaling Plan

AEN has a clear path beyond the reported runs. The next knobs are:

- more outer loops,
- more Aria--Artemis exchange pairs,
- higher per-turn token caps,
- deeper RAB certification,
- larger same-family Qwen role models,
- stronger fallback calibration,
- full artifact export for every case.

The paper computes a five-loop, ten-exchange planning envelope. The observed-rate projection is about **214k output tokens** for one hard problem. The configured ceiling is about **481k output tokens**. With a one-million-token role-context reference, even two ceiling-sized hard-problem attempts remain just under that reference.

![](https://www.googleapis.com/download/storage/v1/b/kaggle-user-content/o/inbox%2F12722911%2F41f238c2ed4ccaf61e3f098e211cfd87%2Faen_output_ceiling_heatmap.png?generation=1776899175985538&alt=media)

[image: aen_context_packing_estimate.png]

The next high-compute study is a fully unrestricted stress test with three upgraded high-capacity Qwen-family models, five loops, four inner Aria--Artemis exchange pairs per loop, 8192 generated tokens for substantive reasoning turns, and 100/100 boot certification lines before ordinary solving begins.

## 14. Reproducibility

The writeup prize rubric emphasizes reproducibility. AEN was designed with that in mind because this kind of system is easy to over-describe and hard to trust without artifacts. The public assets include:

- paper PDF and source bundle,
- RuntimeAtBoot Kaggle dataset,
- offline wheel bundle,
- Canon v2.1 public paper,
- Vault of Echoes companion benchmark record,
- chart CSVs,
- diagram sources,
- exported transcripts and result payloads for reported runs.

For a reproduction, attach:

- `runtimeatboot`,
- `wheels`,
- the AEN notebook,
- base model sources,
- scoring keys for diagnostic surfaces where release is allowed,
- transcript bundles,
- result payloads,
- figure-generation data.

The minimum audit trail for each run should include:

- source dataset label,
- model endpoints,
- RAB certification status,
- loop count,
- exchange count,
- per-turn token caps,
- finalization mode,
- emitted answer,
- expected answer when available,
- transcript path,
- result payload path,
- wall time,
- completion-token volume.

## 15. What Worked, What Failed, and Why It Matters

The biggest success is architectural: AEN turns exact-answer solving into a measured runtime process. It gives a language model a curriculum, checks that the curriculum is active, splits reasoning pressure into roles, and records how the final answer was selected. That is the part I am most excited about, because it turns vague "the model reasoned" claims into something closer to an inspectable system trace.

The biggest observed bottleneck is token budget. The compressed frozen AIME run was cap-saturated in the first Athena turn and often saturated again during synthesis. The expanded one-loop run recovered seven additional AIME problems, which strongly suggests that the compressed run was leaving reasoning unfinished.

The most valuable lesson is that runtime budget is a scientific variable. A model score without loop count, exchange count, token caps, closeout modes, and transcript volume is incomplete. AEN makes those variables visible, which means future improvements can be studied instead of guessed. That is the spirit of the system: when it succeeds, preserve the evidence; when it fails, make the failure legible enough that the next run gets sharper.

## 16. Citations

[1] Paudel, A. (2026). _Artificial Evaluation Network (AEN): Runtime-at-Boot, Certified Context Loading, and Triadic Controller Algorithms for Mathematical Reasoning_. Research preprint. https://zenodo.org/records/19701459

[2] Paudel, A. (2026). _RuntimeAtBoot_. Kaggle dataset. https://www.kaggle.com/datasets/aadityapaudel/runtimeatboot

[3] Paudel, A. (2026). _Wheels_. Kaggle dataset. https://www.kaggle.com/datasets/aadityapaudel/wheels

[4] Paudel, A. (2026). _Canon DSL V2.1: Metadata-First Distillation for Synthetic Mathematical Data_. Zenodo. https://doi.org/10.5281/zenodo.19694800

[5] Paudel, A., and Acharya, P. (2026). _UI-Native One-Shot Benchmarking for Mathematical Reasoning in Chat-Based LLM Systems_. Zenodo. https://doi.org/10.5281/zenodo.18216959

[6] Paudel, A. (2026). _Two LLM Model Evaluator_. GitHub repository. https://github.com/Aadityapaudel2/Two_LLM_Model_Evaluator/

[7] Christiano, P. et al. (2017). _Deep Reinforcement Learning from Human Preferences_. NeurIPS.

[8] Ouyang, L. et al. (2022). _Training Language Models to Follow Instructions with Human Feedback_. NeurIPS.

[9] Hu, E. J. et al. (2021). _LoRA: Low-Rank Adaptation of Large Language Models_. arXiv:2106.09685.

[10] Brown, T. et al. (2020). _Language Models are Few-Shot Learners_. NeurIPS.

[11] Wei, J. et al. (2022). _Chain-of-Thought Prompting Elicits Reasoning in Large Language Models_. NeurIPS.

[12] Wang, X. et al. (2022). _Self-Consistency Improves Chain of Thought Reasoning in Language Models_. arXiv:2203.11171.

[13] Madaan, A. et al. (2023). _Self-Refine: Iterative Refinement with Self-Feedback_. arXiv:2303.17651.

[14] Peng, B. et al. (2023). _YaRN: Efficient Context Window Extension of Large Language Models_. arXiv:2309.00071. https://arxiv.org/abs/2309.00071

[15] Yang, A. et al. (2025). _Qwen2.5-1M Technical Report_. arXiv:2501.15383. https://arxiv.org/abs/2501.15383

[16] Qwen Team. (2025). _Qwen2.5-7B-Instruct-1M Model Card_. https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-1M

[17] Art of Problem Solving. _AIME archive instructions_. https://wiki.artofproblemsolving.com/wiki/index.php/2000_AIME_I_Problems

[18] AIMO Prize. (2025). _Third $2.2 Million AIMO Progress Prize Launched_. https://aimoprize.com/updates/2025-11-19-third-progress-prize-launched

## Closing

AEN is a runtime answer to a runtime problem. It says that mathematical reliability can be improved through disciplined inference-time architecture: reading before solving, certification before trust, role-separated critique before finalization, and artifact-backed reporting after every run.

The reported diagnostics show a clear signal. A compressed AIME 2026 run scored 15/30. An expanded one-loop run on the same surface scored 22/30. The system changed its behavior materially when the runtime budget changed. That is the result I want this writeup to make easy to inspect, reproduce, and challenge.

The next step is straightforward: scale the same controller with stronger same-family models, deeper boot certification, more loops, larger generation ceilings, and the same evidence trail. If that next run succeeds, the gain will be easy to explain. If it fails, the transcripts should tell us where. That is exactly the kind of system I wanted AEN to be: ambitious enough to chase hard mathematics, disciplined enough to leave a trail, and honest enough to make every improvement accountable.

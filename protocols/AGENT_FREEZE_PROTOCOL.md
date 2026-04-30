# Agent Freeze Protocol

Agent Freeze is the AEN rule for moments when an agent must stop ordinary execution and switch into a controlled checkpoint before continuing.

The protocol is not about slowing work down. It is about preventing expensive, private, or scientifically invalid actions from happening casually.

## Freeze Triggers

An agent must enter Freeze before any of these actions:

| trigger | examples | required action |
| --- | --- | --- |
| External API export | Gemini/OpenAI/Claude calls with AEN context, raw transcripts, boot rows, notebooks, private datasets | sanitize payload or ask explicit approval |
| Secret exposure | API key appears in chat, file, terminal output, git diff, notebook, log | stop, tell user to rotate, remove from tracked files/logs |
| Benchmark rerun | full AIME pass, GPU/mainframe run, multi-hour Colab/Kaggle job | produce pre-run checklist and dry-run result first |
| Runtime-at-Boot dataset mutation | add/remove boot rows, change schema, change certification files | scan for answer leakage and update manifest |
| Git publication | push new claims, reports, raw exports, figures, notebooks | run claim-boundary checklist and status check |
| Destructive file operation | delete/move/overwrite artifact folders or raw exports | ask explicit approval and verify target paths |
| Claim escalation | wording like blind solve, solved AIME, benchmark state of art, 96% AIME | verify contamination status and cite artifact class |

## Freeze Checklist

Before continuing, the agent writes down or verifies:

1. **Intent:** what action is being taken and why.
2. **Data boundary:** what files or text will leave the local machine, if anything.
3. **Secret boundary:** whether keys/tokens/cookies/credentials are present.
4. **Claim boundary:** whether the work is blind benchmark, answer-aware replay, context-recall, diagnostic slice, or planning.
5. **Cost boundary:** expected wall time, GPU/mainframe use, API spend, and failure stop conditions.
6. **Repro boundary:** where logs, manifests, scripts, and outputs will be saved.
7. **Approval boundary:** whether user approval is required before proceeding.

## External API Rule

External models are useful collaborators, but they are not local memory. Treat every external API prompt as an export.

Allowed without extra approval:

- sanitized project summaries,
- public GitHub artifact descriptions,
- non-secret workflow questions,
- generated synthetic examples that contain no private dataset rows.

Requires explicit user approval:

- raw transcripts,
- boot NDJSON records,
- answer-bearing Runtime-at-Boot rows,
- unpublished notebooks,
- benchmark answer keys,
- private logs,
- any file that may contain credentials or personal data.

The approval phrase should be concrete, for example:

`I approve sending this sanitized AEN project summary to Gemini for workflow analysis.`

## Runtime-at-Boot Dataset Freeze

Before a Runtime-at-Boot dataset is used in a run, freeze and scan it.

Minimum checks:

- no exact final answers in studied text,
- no `Verified answer`, `expected_answer`, `gold`, `official key`, or equivalent answer-key language in studied text,
- no problem-index-specific final object hints for the target benchmark,
- metadata fields do not get rendered into study text accidentally,
- certification probes do not reveal final answers,
- row count is under the configured study limit or the limit change is documented.

If the dataset is intentionally answer-aware, label the run as an answer-aware replay or context-recall diagnostic before it starts.

## Benchmark Run Freeze

Before another full 12-hour-class run, the agent must produce:

- run objective,
- dataset hash/source path,
- contamination scan result,
- expected runtime and token budget,
- stop conditions,
- dry-run slice result,
- output artifact folder name,
- claim wording if the run succeeds,
- claim wording if the run fails.

No full run should start from a vague instruction like "try V35" without this checkpoint.

## Git Publication Freeze

Before pushing to GitHub:

- `git status --short` is reviewed,
- unrelated dirty files are left alone,
- new raw data is intentionally included or intentionally excluded,
- claims are downgraded if contamination exists,
- README/NAVIGATION/revisions index are updated when new artifacts are added,
- large files and secrets are checked.

## Secret Handling

Agents must never print a secret. A health check may print only boolean presence and length:

```powershell
$p = "N:\Research\CrossAgentic\.secrets\gemini_api_key.txt"
$k = if (Test-Path -LiteralPath $p) { (Get-Content -LiteralPath $p -Raw).Trim() } else { "" }
"key_present=$($k.Length -gt 0); key_length=$($k.Length)"
```

## Exit From Freeze

An agent exits Freeze only when one of these is true:

- the action is confirmed safe and documented,
- the user explicitly approves the risk,
- the action is replaced by a safer local-only alternative,
- the agent declines to proceed and records why.
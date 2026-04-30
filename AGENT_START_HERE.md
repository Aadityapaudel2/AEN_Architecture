# Agent Start Here

This is the shortest safe entry route for a new agent working on AEN.

## Current Boundary

The newest full-run artifact is V34. It scored 29/30 internally, but it was answer-aware. Do not describe it as a blind AIME solve. The durable claim is Runtime-at-Boot context persistence and recall.

## Read In Order

1. [`NAVIGATION.md`](NAVIGATION.md) for repository map.
2. [`revisions/README.md`](revisions/README.md) for the artifact ledger.
3. [`revisions/2026-04-29-artifact-06-v34-full-test-run/CONTEXT_RECALL_DIAGNOSTIC.md`](revisions/2026-04-29-artifact-06-v34-full-test-run/CONTEXT_RECALL_DIAGNOSTIC.md) for the V34 correction.
4. [`revisions/2026-04-29-artifact-06-v34-full-test-run/FORENSIC_ADDENDUM.md`](revisions/2026-04-29-artifact-06-v34-full-test-run/FORENSIC_ADDENDUM.md) for transcript scan and compute analysis.
5. [`protocols/AGENT_FREEZE_PROTOCOL.md`](protocols/AGENT_FREEZE_PROTOCOL.md) before external API calls, long runs, dataset mutations, secrets, or claim escalation.
6. [`protocols/RESEARCH_HYGIENE_PROTOCOL.md`](protocols/RESEARCH_HYGIENE_PROTOCOL.md) before reorganizing files or adding new artifacts.

## Before Acting

- Check `git status --short`.
- Do not touch unrelated dirty files.
- Do not export raw transcripts, boot rows, notebooks, or private data to external APIs without explicit approval.
- Do not print secrets.
- Do not start a long benchmark run without a freeze checklist and dry-run slice.
- Label every result as blind benchmark, answer-aware replay, context-recall diagnostic, controller diagnostic, transcript diagnostic, or planning package.

## Current Next Scientific Step

V35 should be answer-free/hint-only Runtime-at-Boot with a contamination scanner before any full run.
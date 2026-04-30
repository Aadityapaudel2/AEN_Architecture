# AEN Protocols

This folder contains operating protocols for future AEN agents and maintainers.

| file | purpose |
| --- | --- |
| [`AGENT_FREEZE_PROTOCOL.md`](AGENT_FREEZE_PROTOCOL.md) | When an agent must halt, sanitize, ask, or create a checkpoint before acting |
| [`RESEARCH_HYGIENE_PROTOCOL.md`](RESEARCH_HYGIENE_PROTOCOL.md) | How to keep the AEN research repo readable, auditable, and safe to hand off |

These protocols exist because V34 showed two things at once: the architecture can preserve and recall Runtime-at-Boot context, and exact-answer contamination can turn an impressive run into a much narrower claim. The repo should make that boundary easy for the next agent to see.
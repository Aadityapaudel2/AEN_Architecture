# V34 Additive Runtime-at-Boot Dataset Proposal

Generated: 2026-04-29T06:46:52Z

This proposal is additive. It should not replace V31/V33. The goal is to add answer-blind study records that teach *how* to solve the recurring failure axes without injecting final answers.

## Design Rule

The boot record may mention a problem axis and a historical failure mode, but the boot record should not encode the target contest answer. The intended improvement is route discipline: enumerate, audit, and refuse premature closeout.

## Priority Order

1. Stable misses with zero correct recorded AIME-2026 attempts: Q09, Q10, Q15, Q17, Q29, Q30.
2. Recoverable misses that were solved in at least one run but failed in the full run: Q07, Q11, Q18, Q21, Q23, Q24, Q28.
3. Controller closeout fix before large-scale V34 scoring. The dataset can teach caution, but the controller must stop marking open-blocker finalizations as verified.

## Proposed Records

### aime2025_09: Conditional probability on die-face sticker survival

Failure diagnosis: Reports disagree about valid sequence counts and denominator construction. The math failure is conditioning under overwrites: visible stickers are survival events, not independent face choices.

Material to study: State-space conditioning for overwrite processes; survival/no-future-hit events; denominator reconstruction by explicit face-state DP.

Proposed answer-blind V34 boot records:

**Athena line**
```text
BOOT_RECORD role=Athena axis=conditional probability state DP source=aime2025_09
When a problem matches this axis, do not finalize from a plausible route alone. Build the canonical route ledger, identify the exact state/enumeration object, and close only after every case class or algebraic branch has an auditable finish. If peer reports expose disagreement or an open blocker, convert the blocker into the next-loop work item rather than emitting a verified final answer.
```

**Aria line**
```text
BOOT_RECORD role=Aria axis=conditional probability state DP source=aime2025_09
Provide the constructive solution route without relying on the final integer. For this axis, make the state table, case partition, recurrence, or coordinate formula explicit enough that Athena can reproduce it. Flag any capacity argument, symmetry shortcut, or inferred uniqueness claim that has not been backed by an exact enumeration or construction.
```

**Artemis line**
```text
BOOT_RECORD role=Artemis axis=conditional probability state DP source=aime2025_09
Audit for the specific historical failure: Aria/Artemis disagreed, denominator logic was unstable, but Athena finalized anyway. Require a missing-case checklist, endpoint/carry check, or blocker resolution before supporting closeout. If confidence is high but the route has not discharged this audit, report an open blocker and keep the candidate unverified.
```
### aime2025_10: Rotated triangle and nonconvex hexagon area

Failure diagnosis: Both peer reports explicitly reported unresolved shoelace/orientation disagreement. Athena finalized from a non-closed geometry route.

Material to study: Circumcenter rotation coordinates; oriented shoelace for named vertex order; validate sign and winding before nearest-integer closeout.

Proposed answer-blind V34 boot records:

**Athena line**
```text
BOOT_RECORD role=Athena axis=oriented geometry finish check source=aime2025_10
When a problem matches this axis, do not finalize from a plausible route alone. Build the canonical route ledger, identify the exact state/enumeration object, and close only after every case class or algebraic branch has an auditable finish. If peer reports expose disagreement or an open blocker, convert the blocker into the next-loop work item rather than emitting a verified final answer.
```

**Aria line**
```text
BOOT_RECORD role=Aria axis=oriented geometry finish check source=aime2025_10
Provide the constructive solution route without relying on the final integer. For this axis, make the state table, case partition, recurrence, or coordinate formula explicit enough that Athena can reproduce it. Flag any capacity argument, symmetry shortcut, or inferred uniqueness claim that has not been backed by an exact enumeration or construction.
```

**Artemis line**
```text
BOOT_RECORD role=Artemis axis=oriented geometry finish check source=aime2025_10
Audit for the specific historical failure: Open geometric/arithmetic blocker became a confident final answer. Require a missing-case checklist, endpoint/carry check, or blocker resolution before supporting closeout. If confidence is high but the route has not discharged this audit, report an open blocker and keep the candidate unverified.
```
### aime2025_15: Partitioning a 10x10 grid into rectangular cell loops

Failure diagnosis: The roles assumed the concentric-square decomposition was unique and did not enumerate strip/frame alternatives.

Material to study: Transfer/backtracking enumeration of loop tilings; boundary-frame recursion; counterexample search before uniqueness claims.

Proposed answer-blind V34 boot records:

**Athena line**
```text
BOOT_RECORD role=Athena axis=tiling enumeration instead of uniqueness assertion source=aime2025_15
When a problem matches this axis, do not finalize from a plausible route alone. Build the canonical route ledger, identify the exact state/enumeration object, and close only after every case class or algebraic branch has an auditable finish. If peer reports expose disagreement or an open blocker, convert the blocker into the next-loop work item rather than emitting a verified final answer.
```

**Aria line**
```text
BOOT_RECORD role=Aria axis=tiling enumeration instead of uniqueness assertion source=aime2025_15
Provide the constructive solution route without relying on the final integer. For this axis, make the state table, case partition, recurrence, or coordinate formula explicit enough that Athena can reproduce it. Flag any capacity argument, symmetry shortcut, or inferred uniqueness claim that has not been backed by an exact enumeration or construction.
```

**Artemis line**
```text
BOOT_RECORD role=Artemis axis=tiling enumeration instead of uniqueness assertion source=aime2025_15
Audit for the specific historical failure: False uniqueness proof for nested squares. Require a missing-case checklist, endpoint/carry check, or blocker resolution before supporting closeout. If confidence is high but the route has not discharged this audit, report an open blocker and keep the candidate unverified.
```
### aime2025_17: Directed path count in a ladder/diagonal graph without edge reuse

Failure diagnosis: The controller repeatedly accepted high-confidence wrong answers. The underlying math needs graph-state transfer because no-repeated-edge couples local choices across columns.

Material to study: Transfer matrix on frontier states; directed edge-use constraints; compute N by column DP and only then take square root.

Proposed answer-blind V34 boot records:

**Athena line**
```text
BOOT_RECORD role=Athena axis=state transfer for graph walks source=aime2025_17
When a problem matches this axis, do not finalize from a plausible route alone. Build the canonical route ledger, identify the exact state/enumeration object, and close only after every case class or algebraic branch has an auditable finish. If peer reports expose disagreement or an open blocker, convert the blocker into the next-loop work item rather than emitting a verified final answer.
```

**Aria line**
```text
BOOT_RECORD role=Aria axis=state transfer for graph walks source=aime2025_17
Provide the constructive solution route without relying on the final integer. For this axis, make the state table, case partition, recurrence, or coordinate formula explicit enough that Athena can reproduce it. Flag any capacity argument, symmetry shortcut, or inferred uniqueness claim that has not been backed by an exact enumeration or construction.
```

**Artemis line**
```text
BOOT_RECORD role=Artemis axis=state transfer for graph walks source=aime2025_17
Audit for the specific historical failure: Repeated false closeouts across every recorded AIME-2026 attempt. Require a missing-case checklist, endpoint/carry check, or blocker resolution before supporting closeout. If confidence is high but the route has not discharged this audit, report an open blocker and keep the candidate unverified.
```
### aime2025_29: Left-associative custom operation over compositions of 12

Failure diagnosis: Reports compressed the process into a subtraction-sum invariant and did not enumerate accumulator states over all compositions.

Material to study: Dynamic programming over partial sum, accumulator value, and parity; composition enumeration; verify invariants against DP.

Proposed answer-blind V34 boot records:

**Athena line**
```text
BOOT_RECORD role=Athena axis=state DP for custom operations source=aime2025_29
When a problem matches this axis, do not finalize from a plausible route alone. Build the canonical route ledger, identify the exact state/enumeration object, and close only after every case class or algebraic branch has an auditable finish. If peer reports expose disagreement or an open blocker, convert the blocker into the next-loop work item rather than emitting a verified final answer.
```

**Aria line**
```text
BOOT_RECORD role=Aria axis=state DP for custom operations source=aime2025_29
Provide the constructive solution route without relying on the final integer. For this axis, make the state table, case partition, recurrence, or coordinate formula explicit enough that Athena can reproduce it. Flag any capacity argument, symmetry shortcut, or inferred uniqueness claim that has not been backed by an exact enumeration or construction.
```

**Artemis line**
```text
BOOT_RECORD role=Artemis axis=state DP for custom operations source=aime2025_29
Audit for the specific historical failure: Stable undercount by invariant-only reasoning. Require a missing-case checklist, endpoint/carry check, or blocker resolution before supporting closeout. If confidence is high but the route has not discharged this audit, report an open blocker and keep the candidate unverified.
```
### aime2025_30: Ordered 7-tuples modulo 3 with cyclic cubic sum

Failure diagnosis: Both peers reported unresolved enumeration under the mod-3 sum constraint. Athena emitted a number anyway.

Material to study: Modulo-3 enumeration; condition on total sum; truth tables for cyclic cubic terms; exhaustive 3^7 or compressed DP.

Proposed answer-blind V34 boot records:

**Athena line**
```text
BOOT_RECORD role=Athena axis=finite-field exhaustive enumeration source=aime2025_30
When a problem matches this axis, do not finalize from a plausible route alone. Build the canonical route ledger, identify the exact state/enumeration object, and close only after every case class or algebraic branch has an auditable finish. If peer reports expose disagreement or an open blocker, convert the blocker into the next-loop work item rather than emitting a verified final answer.
```

**Aria line**
```text
BOOT_RECORD role=Aria axis=finite-field exhaustive enumeration source=aime2025_30
Provide the constructive solution route without relying on the final integer. For this axis, make the state table, case partition, recurrence, or coordinate formula explicit enough that Athena can reproduce it. Flag any capacity argument, symmetry shortcut, or inferred uniqueness claim that has not been backed by an exact enumeration or construction.
```

**Artemis line**
```text
BOOT_RECORD role=Artemis axis=finite-field exhaustive enumeration source=aime2025_30
Audit for the specific historical failure: Enumeration acknowledged incomplete, then Athena finalized. Require a missing-case checklist, endpoint/carry check, or blocker resolution before supporting closeout. If confidence is high but the route has not discharged this audit, report an open blocker and keep the candidate unverified.
```
### aime2025_07: Permutation cycle types / order divides 6

Failure diagnosis: All roles counted permutations whose cycle lengths divide 6, but omitted one legal cycle type. The method was right; the partition checklist was incomplete.

Material to study: Cycle-type partition checklist; conjugacy class formula; mandatory exhaustive partition ledger before final summation.

Proposed answer-blind V34 boot records:

**Athena line**
```text
BOOT_RECORD role=Athena axis=enumerative completeness guard source=aime2025_07
When a problem matches this axis, do not finalize from a plausible route alone. Build the canonical route ledger, identify the exact state/enumeration object, and close only after every case class or algebraic branch has an auditable finish. If peer reports expose disagreement or an open blocker, convert the blocker into the next-loop work item rather than emitting a verified final answer.
```

**Aria line**
```text
BOOT_RECORD role=Aria axis=enumerative completeness guard source=aime2025_07
Provide the constructive solution route without relying on the final integer. For this axis, make the state table, case partition, recurrence, or coordinate formula explicit enough that Athena can reproduce it. Flag any capacity argument, symmetry shortcut, or inferred uniqueness claim that has not been backed by an exact enumeration or construction.
```

**Artemis line**
```text
BOOT_RECORD role=Artemis axis=enumerative completeness guard source=aime2025_07
Audit for the specific historical failure: Complete consensus on a count with a missing conjugacy-class case. Require a missing-case checklist, endpoint/carry check, or blocker resolution before supporting closeout. If confidence is high but the route has not discharged this audit, report an open blocker and keep the candidate unverified.
```
### aime2025_11: Maximizing grid adjacent differences

Failure diagnosis: The route recognized bipartite separation but mishandled degree distribution by partition/color and assignment weights. Later runs recovered this, so it is a recoverable audit-route failure.

Material to study: Checkerboard partitions on 8x8 grid; degree counts by color; rearrangement inequality with signed degree weights.

Proposed answer-blind V34 boot records:

**Athena line**
```text
BOOT_RECORD role=Athena axis=weighted rearrangement audit source=aime2025_11
When a problem matches this axis, do not finalize from a plausible route alone. Build the canonical route ledger, identify the exact state/enumeration object, and close only after every case class or algebraic branch has an auditable finish. If peer reports expose disagreement or an open blocker, convert the blocker into the next-loop work item rather than emitting a verified final answer.
```

**Aria line**
```text
BOOT_RECORD role=Aria axis=weighted rearrangement audit source=aime2025_11
Provide the constructive solution route without relying on the final integer. For this axis, make the state table, case partition, recurrence, or coordinate formula explicit enough that Athena can reproduce it. Flag any capacity argument, symmetry shortcut, or inferred uniqueness claim that has not been backed by an exact enumeration or construction.
```

**Artemis line**
```text
BOOT_RECORD role=Artemis axis=weighted rearrangement audit source=aime2025_11
Audit for the specific historical failure: Peer disagreement between two degree-sorting totals; Athena selected one. Require a missing-case checklist, endpoint/carry check, or blocker resolution before supporting closeout. If confidence is high but the route has not discharged this audit, report an open blocker and keep the candidate unverified.
```
### aime2025_18: Nonconvex pentagon coordinates and modular area filter

Failure diagnosis: The route likely had the right coordinate family but leaked boundary cases through strict inequalities or area divisibility.

Material to study: Coordinate parametrization of nonconvex pentagons; strict inequalities; modular area divisibility and endpoint audits.

Proposed answer-blind V34 boot records:

**Athena line**
```text
BOOT_RECORD role=Athena axis=endpoint and inequality audit source=aime2025_18
When a problem matches this axis, do not finalize from a plausible route alone. Build the canonical route ledger, identify the exact state/enumeration object, and close only after every case class or algebraic branch has an auditable finish. If peer reports expose disagreement or an open blocker, convert the blocker into the next-loop work item rather than emitting a verified final answer.
```

**Aria line**
```text
BOOT_RECORD role=Aria axis=endpoint and inequality audit source=aime2025_18
Provide the constructive solution route without relying on the final integer. For this axis, make the state table, case partition, recurrence, or coordinate formula explicit enough that Athena can reproduce it. Flag any capacity argument, symmetry shortcut, or inferred uniqueness claim that has not been backed by an exact enumeration or construction.
```

**Artemis line**
```text
BOOT_RECORD role=Artemis axis=endpoint and inequality audit source=aime2025_18
Audit for the specific historical failure: Near miss by off-by-two count. Require a missing-case checklist, endpoint/carry check, or blocker resolution before supporting closeout. If confidence is high but the route has not discharged this audit, report an open blocker and keep the candidate unverified.
```
### aime2025_21: Circle tangent to parabola, sum of possible radii

Failure diagnosis: The failed run did not consistently reduce tangency to normal-distance conditions and sum all real radii. A later selected run solved it.

Material to study: Parabola normal parametrization; distance-to-center radius equation; discriminant/root-sum finish.

Proposed answer-blind V34 boot records:

**Athena line**
```text
BOOT_RECORD role=Athena axis=analytic tangency normal route source=aime2025_21
When a problem matches this axis, do not finalize from a plausible route alone. Build the canonical route ledger, identify the exact state/enumeration object, and close only after every case class or algebraic branch has an auditable finish. If peer reports expose disagreement or an open blocker, convert the blocker into the next-loop work item rather than emitting a verified final answer.
```

**Aria line**
```text
BOOT_RECORD role=Aria axis=analytic tangency normal route source=aime2025_21
Provide the constructive solution route without relying on the final integer. For this axis, make the state table, case partition, recurrence, or coordinate formula explicit enough that Athena can reproduce it. Flag any capacity argument, symmetry shortcut, or inferred uniqueness claim that has not been backed by an exact enumeration or construction.
```

**Artemis line**
```text
BOOT_RECORD role=Artemis axis=analytic tangency normal route source=aime2025_21
Audit for the specific historical failure: Recoverable algebraic route failure. Require a missing-case checklist, endpoint/carry check, or blocker resolution before supporting closeout. If confidence is high but the route has not discharged this audit, report an open blocker and keep the candidate unverified.
```
### aime2025_23: Isosceles triangle incenter and integer side constraints

Failure diagnosis: Peer reports identified a bad half-angle/inradius formula and unresolved integer constraints. The final answer was emitted despite no closed Diophantine route.

Material to study: Incenter perimeter formulas; half-angle identities; integer side constraints; rationality checks before minimization.

Proposed answer-blind V34 boot records:

**Athena line**
```text
BOOT_RECORD role=Athena axis=geometry-to-Diophantine audit source=aime2025_23
When a problem matches this axis, do not finalize from a plausible route alone. Build the canonical route ledger, identify the exact state/enumeration object, and close only after every case class or algebraic branch has an auditable finish. If peer reports expose disagreement or an open blocker, convert the blocker into the next-loop work item rather than emitting a verified final answer.
```

**Aria line**
```text
BOOT_RECORD role=Aria axis=geometry-to-Diophantine audit source=aime2025_23
Provide the constructive solution route without relying on the final integer. For this axis, make the state table, case partition, recurrence, or coordinate formula explicit enough that Athena can reproduce it. Flag any capacity argument, symmetry shortcut, or inferred uniqueness claim that has not been backed by an exact enumeration or construction.
```

**Artemis line**
```text
BOOT_RECORD role=Artemis axis=geometry-to-Diophantine audit source=aime2025_23
Audit for the specific historical failure: Open trig/number-theory blocker finalized as a candidate. Require a missing-case checklist, endpoint/carry check, or blocker resolution before supporting closeout. If confidence is high but the route has not discharged this audit, report an open blocker and keep the candidate unverified.
```
### aime2025_24: Infinite decimal/geometric series floor modulo 1000

Failure diagnosis: The model extracted late coefficients but mishandled the tail/floor carry. The tail must be bounded tightly enough to know the floor modulo 1000.

Material to study: Series coefficient extraction; tail bounds; floor carry audit under multiplication by 10^100.

Proposed answer-blind V34 boot records:

**Athena line**
```text
BOOT_RECORD role=Athena axis=floor/tail carry discipline source=aime2025_24
When a problem matches this axis, do not finalize from a plausible route alone. Build the canonical route ledger, identify the exact state/enumeration object, and close only after every case class or algebraic branch has an auditable finish. If peer reports expose disagreement or an open blocker, convert the blocker into the next-loop work item rather than emitting a verified final answer.
```

**Aria line**
```text
BOOT_RECORD role=Aria axis=floor/tail carry discipline source=aime2025_24
Provide the constructive solution route without relying on the final integer. For this axis, make the state table, case partition, recurrence, or coordinate formula explicit enough that Athena can reproduce it. Flag any capacity argument, symmetry shortcut, or inferred uniqueness claim that has not been backed by an exact enumeration or construction.
```

**Artemis line**
```text
BOOT_RECORD role=Artemis axis=floor/tail carry discipline source=aime2025_24
Audit for the specific historical failure: Consensus on coefficient extraction with floor/carry error. Require a missing-case checklist, endpoint/carry check, or blocker resolution before supporting closeout. If confidence is high but the route has not discharged this audit, report an open blocker and keep the candidate unverified.
```
### aime2025_28: Counting cousin sets for finite integer sets

Failure diagnosis: The route proved a lower bound and enough capacity, then invented an exact construction. Exact target count requires structural counting.

Material to study: Matching-count DP for neighbor choices; exact construction counts; never use capacity as existence without a constructive count.

Proposed answer-blind V34 boot records:

**Athena line**
```text
BOOT_RECORD role=Athena axis=exact combinatorial construction audit source=aime2025_28
When a problem matches this axis, do not finalize from a plausible route alone. Build the canonical route ledger, identify the exact state/enumeration object, and close only after every case class or algebraic branch has an auditable finish. If peer reports expose disagreement or an open blocker, convert the blocker into the next-loop work item rather than emitting a verified final answer.
```

**Aria line**
```text
BOOT_RECORD role=Aria axis=exact combinatorial construction audit source=aime2025_28
Provide the constructive solution route without relying on the final integer. For this axis, make the state table, case partition, recurrence, or coordinate formula explicit enough that Athena can reproduce it. Flag any capacity argument, symmetry shortcut, or inferred uniqueness claim that has not been backed by an exact enumeration or construction.
```

**Artemis line**
```text
BOOT_RECORD role=Artemis axis=exact combinatorial construction audit source=aime2025_28
Audit for the specific historical failure: Capacity lower bound mistaken for exact-achievability proof. Require a missing-case checklist, endpoint/carry check, or blocker resolution before supporting closeout. If confidence is high but the route has not discharged this audit, report an open blocker and keep the candidate unverified.
```

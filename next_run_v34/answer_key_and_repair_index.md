# V34 Answer Key and Repair Index

Source: [MathArena/aime_2026](https://huggingface.co/datasets/MathArena/aime_2026).

| Problem | Answer | What went wrong in the recorded run | What V34 teaches |
|---:|---:|---|---|
| 7 | 396 | Counted a nearby function/permutation object and missed the cycle-divisibility ledger. | Onto finite map means permutation; only cycle lengths dividing 6 are allowed. |
| 9 | 29 | Conditional denominator drift and visible sticker history treated too independently. | Count all histories satisfying visible even stickers before filtering exactly-one-blank. |
| 10 | 156 | Wrong branch/area object in rotated 13-14-15 geometry. | Coordinate rotation about circumcenter with the side-of-line condition before hexagon area. |
| 11 | 896 | Greedy/local grid layout instead of global cut bound. | Checkerboard/cut upper bound plus attaining construction for absolute differences. |
| 15 | 83 | Collapsed legal loop partitions to a near-single pattern. | Partition coverage state for rectangular cell loops, including empty interiors. |
| 17 | 243 | Counted simple monotone paths, not edge-simple directed trails. | Transfer state across each square remembers consumed vertical/diagonal edges. |
| 18 | 503 | Off-by-one/nonconvex geometry branch. | Directed coordinate walk, inequalities, and area mod 16 filter. |
| 21 | 50 | Used only one tangent/normal branch. | Parameterize parabola normals and sum all real geometric radii. |
| 23 | 245 | Minimized wrong approximate/perimeter object. | Exact incenter geometry plus integer side Diophantine minimization. |
| 24 | 669 | Decimal truncation without tail/carry proof. | Repunit series floor control before taking remainder mod 1000. |
| 28 | 107 | Treated cousin choices as independent. | Component-product matching count with conflict graph optimization. |
| 29 | 157 | Treated left-associative operation as commutative/associative. | Dynamic programming over sum and running value. |
| 30 | 393 | Over-symmetrized ordered tuples and/or lost cyclic terms. | Ordered tuple count with exact cyclic cubic expression modulo 3. |

The full long-form role records live in [`../runtimeatbootdataset_v34/`](../runtimeatbootdataset_v34/).

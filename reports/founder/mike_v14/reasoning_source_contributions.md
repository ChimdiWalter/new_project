# What the four reasoning repositories contributed

They informed the design and future experiments. No code from these repositories was copied, imported or executed inside InvariantCell during the recorded source reviews.

| Source | Useful idea found in actual code/plans | InvariantCell status |
|---|---|---|
| Reasoning_Project | Candidate procedure promotion, separated evaluation and verification/replay | Original biomedical metadata check/replay implemented; source proof bookkeeping was not accepted as an independent verifier |
| Reasoning_Project_arc2026 | Grammar-constrained typed AST proposals, deterministic cost/MDL ranking, candidate traces and replay | Reviewed design source; grid proposal engine not integrated; biological skill transfer untested |
| Reasoning_Project_tti | Stage-specific evidence access, committed experiment pins, drift detection | Design source for explicit data boundaries; its Python wrapper is not an OS sandbox and was not imported |
| Reasoning_Project_tti_pin_e5ef8b5 | Demonstration fitting, minimum witnesses and exact replay on default admission path | Reviewed future procedure-admission pattern; demonstration consistency does not establish transfer |

Current supported pitch: “ARC work informed our independently checked, source-bound scientific procedures. We have implemented bounded checks and replay; we are testing whether learned, frozen procedures improve new biological decisions.”

Do not say that four trained reasoning models were merged, that ARC-to-biology transfer is proven, or that verification already improves biological ranking.

Detailed evidence and inspected source hashes: reports/post_confirmation/new_reasoning_sources_v11.md; audit/discovery/project_summaries/arc_reasoning.json; reports/reasoning/biomedical_operator_transfer.md. Protected upstream outcomes and unfinished source discovery remain outside this evidence claim.

# V6-r1 Frozen Regression Result Analysis

updated: 2026-08-21
experiment: `ecr-poc-regression-v6-r1`
run: `cloud-v6-r1-20260820T145618Z-a2df156a`
execution: `ecr-poc-evaluate-rjkjq`

## Result authority

This report analyzes the immutable Vertex result at generation `1787238615600708` with SHA-256 `8fddb6bd4b926c57d518cc6d744ade35d668cfc00b40fd93df7ae07f4a206fb7`. The 20 frozen regression cases all reached a terminal state with zero role errors, and strict provenance, fingerprint, candidate, claim, verifier, metric-recalculation, and checkpoint validation passed. The benchmark was observed during development and is not an unseen performance estimate. Accuracy values are diagnostic measurements rather than completion thresholds.

## Headline metrics

| Measure | Overall | Direct | Semantic | Cross-Artifact |
| --- | ---: | ---: | ---: | ---: |
| Broad target Hit | 15/16 (93.75%) | 5/5 | 5/5 | 5/6 |
| Expanded target coverage | 16/16 (100%) | 5/5 | 5/5 | 6/6 |
| Final target Hit@10 | 13/16 (81.25%) | 5/5 | 3/5 | 5/6 |
| Complete-case Final coverage | 12/15 (80%) | 5/5 | 3/5 | 4/5 |
| Verified expected claim recall | 9/16 (56.25%) | 3/5 | 3/5 | 3/6 |
| Mean final target rank | 3.23 | 3.60 | 4.33 | 2.20 |
| MRR | 0.551 | 0.570 | 0.370 | 0.640 |

Control false alarms were 1/5 (20%): CLN-01 produced three verified claims, CLN-02 and all three Benign cases produced none. The system proposed 36 claims, rejected one, blocked none, and exposed 35 verified claims. It reduced the 10-candidate docket to an average 1.75 verified candidates per case, an 82.5% candidate reduction.

## Loss decomposition

The seven missed frozen claim slots divide into two independent stages.

1. **Final-ranking loss: three slots.** SEM-02, SEM-05, and XART-02 targets were present in Broad Top-40 and the expanded pool but were absent from Final Top-10. SEM-05 consequently ended `INCONCLUSIVE`; the other two cases still exposed different supported findings.
2. **Review/claim matching loss: four slots.** DIR-01, DIR-04, XART-04, and XART-05 had their expected source in Final Top-10 but no verified claim matched the frozen source + impact type + nested exact-span slot. XART-05 is also the one Broad miss recovered by identifier expansion.

The verifier did not reduce expected-claim recall: proposal recall and verified recall are both 9/16. Its single rejection was not a frozen expected slot. Current expected-claim recall is therefore limited first by Final ranking and then by Reviewer claim selection/type/span, not by verifier rejection.

## Retrieval observations

- Broad retrieval is the strongest stage: it found 93.75% of targets and all Direct/Semantic targets.
- Identifier expansion demonstrated one concrete cross-artifact recovery, bringing the expanded pool to 16/16 target coverage.
- Every case reached the 200-candidate expanded-pool cap while expansion added only one missing gold target across the benchmark. This is functionally correct but indicates low diagnostic selectivity at the expansion stage.
- Final ranking discarded three targets already available upstream. Semantic was the weakest Final stage at 3/5 targets and mean rank 4.33.

## Review and alert-quality observations

- Of 35 verified claims, nine matched frozen expected slots, 23 were unregistered additional findings on impact cases, and three were the CLN-01 control false alarm. The 23 additional findings are not automatically false positives under the frozen protocol and require human adjudication before changing prompts or labels.
- Direct cases retrieved every target but matched only 3/5 expected claims; this confirms that exact retrieval alone does not guarantee the intended atomic impact claim.
- XART-03 is the cleanest representative success: both expected cross-artifact targets reached Final Top-10 and both expected claims were verified, with no extra verified claim.
- The one definite alert-quality regression is confined to CLN-01; all Benign controls correctly ended with no supported review.
- One verifier rejection among 36 proposals shows fail-closed rejection working in the real run, while deterministic/off-docket/exact-span failure paths remain established primarily by automated tests rather than naturally occurring cases.

## Recommended next diagnostic order

No quality change is applied in this report. Before a new billable experiment, manually adjudicate the 23 unregistered additional findings without rewriting the frozen labels or result. Then choose exactly one controlled variable:

1. Reviewer prompt/claim criteria if the adjudication confirms over-broad or wrong-type claims, because four retrieved frozen slots were missed and CLN-01 raised a definite false alarm.
2. Final-ranking formula if target retention is prioritized, because three upstream-retrieved targets were dropped before review.
3. Verifier criteria only if adjudication shows that evidence-supported wording is still materially over-strong; the current run provides no expected-slot recall loss at the verifier stage.

Any new result must use a new experiment identity and run ID. The v6-r1 labels, result, metrics, and published pointer remain unchanged.

# UI Render Matrix

**Status**: draft | provisional | approved | superseded  
**Foundation version**:  
**Last run**: YYYY-MM-DD

Record actual rendering conditions and results. Code, tokens, or component reuse alone cannot make a row `pass`.

## Required environments

| Environment | Viewport / device | Input | Font / scale | Required scenarios |
| --- | --- | --- | --- | --- |
|  |  |  |  | normal, loading, empty, error, success |

## Rendered scenarios

| Screen / flow | Viewport | Content fixture | State | Input | Font / scale | Evidence | Result |
| --- | --- | --- | --- | --- | --- | --- | --- |
|  |  | typical | ready |  | production / 100% |  | pass / fail / unverified |
|  |  | long localized | ready |  | production / 100% |  |  |
|  |  | maximum items | loading |  |  |  |  |
|  |  | missing asset | error / recovery |  |  |  |  |

## Perceptual checks

| Screen / condition | Alignment | Text fit | Icon-label | Rhythm / weight | Layout stability | Result |
| --- | --- | --- | --- | --- | --- | --- |
|  |  |  |  |  |  |  |

## Cross-screen consistency

| Semantic role | Screen A | Screen B / precedent | Compared properties | Result / finding |
| --- | --- | --- | --- | --- |
| Page header |  |  | alignment, typography, spacing |  |
| Primary action |  |  | height, label fit, state, focus |  |
| List row |  |  | baseline, trailing slot, state |  |

If there is no comparison target, record `unverified — no comparison target`.

## Narrative restraint and copy necessity

| Screen | Text / region | Role | Explanation deletion test | Decision | Evidence |
| --- | --- | --- | --- | --- | --- |
|  |  | identity / state / constraint / consequence / recovery / rationale / none | pass / fail / unverified | keep / defer / remove / rewrite |  |

## Transition stability

| Transition | Expected stable regions | Observed movement | Result / evidence |
| --- | --- | --- | --- |
| loading → ready |  |  |  |
| error → recovery |  |  |  |
| validation appears |  |  |  |

## Summary

- Passed:
- Failed:
- Unverified:
- Required reruns:
- Related review:

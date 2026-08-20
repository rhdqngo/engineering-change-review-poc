# Visual Invariants

**Status**: draft | provisional | approved | superseded  
**Foundation version**:  
**Last checked**: YYYY-MM-DD

Record repeated visual rules so the same semantic role does not look different from screen to screen. Early on, prioritize relationships and use conditions; after reviewing real probes and renders, lock exact values as provisional or approved.

## Global alignment

- Top-level content origin:
- Page header alignment:
- Primary task alignment:
- Trailing value / action slot:
- Numeric comparison alignment:
- Overlay and modal alignment:

## Role invariants

| Semantic role | Geometry | Typography | Icon / gap | State treatment | Content-fit policy |
| --- | --- | --- | --- | --- | --- |
| Primary action |  |  |  |  |  |
| Secondary action |  |  |  |  |  |
| Destructive action |  |  |  |  |  |
| Input / field |  |  |  |  |  |
| List row |  |  |  |  |  |
| Page header |  |  |  |  |  |
| Status / badge |  |  |  |  |  |

## Text-fit policy

| Text role | Allowed lines | Overflow / clamp | Minimum width | Responsive fallback |
| --- | ---: | --- | --- | --- |
| Page title |  |  |  |  |
| Primary action label |  |  |  |  |
| Secondary action label |  |  |  |  |
| List primary label |  |  |  |  |
| Supporting text |  |  |  |  |
| Error / recovery |  |  |  |  |
| Numeric value / unit |  |  |  |  |

Do not permit accidental two-line controls. If wrapping is allowed, also record how row height, baseline, and sibling alignment adapt.

## Typography and font behavior

- Production font:
- Fallback font:
- Numeric style:
- Line-height rules:
- Font-loading behavior:
- Localization expansion assumption:
- Zoom / text scaling requirement:

## Icon composition

- Default optical size:
- Stroke / fill policy:
- Icon-label gap:
- SVG viewBox requirement:
- Optical correction policy:
- Icon-only accessible naming:

## Spacing rhythm

| Relationship | Token / range | Use |
| --- | --- | --- |
| Micro adjustment |  |  |
| Icon-label |  |  |
| Intra-item |  |  |
| Intra-group |  |  |
| Inter-group |  |  |
| Major section |  |  |

When using intermediate values, record the reason and scope.

## Visual weight and hierarchy

- Primary versus secondary:
- Destructive versus normal:
- Passive / metadata:
- Border, shadow, and accent limits:
- Badge and status emphasis:

## Layout stability

- Loading → ready:
- Validation / error appearance:
- Badge appearance:
- Missing asset:
- Large values:
- Maximum items:
- Sticky / scroll interactions:

## Narrative and copy invariants

- Recurring workflow prose limit:
- Page subtitle policy:
- Helper text policy:
- First-use guidance behavior:
- Empty-state structure:
- High-risk consequence copy:
- Marketing-copy boundary:
- Approved terminology:

## Responsive collapse ladder

| Role / region | Wide | Medium | Narrow | Minimum fallback |
| --- | --- | --- | --- | --- |
| Primary action |  |  |  |  |
| Secondary actions |  |  |  |  |
| Page controls |  |  |  |  |
| Supporting detail |  |  |  |  |

## Cross-screen invariants

| Semantic role | Comparison screens / precedents | Properties that must match | Allowed variation |
| --- | --- | --- | --- |
|  |  |  |  |

## Exceptions

| Scope | Exception | Reason | Evidence | Re-review condition |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

## Validation evidence

- Result: unverified
- Render matrix:
- Review:
- Conditions:

# Visual Concept Probe Workflow

A probe is a disposable exploration used to compare directions in a real rendered surface. It is neither a production baseline nor a precedent.

## Fair comparison

All three probes use the same:

- core task
- content and extreme values
- production font, fallback font, and text scale
- copy roles and amount of explanatory information
- baseline and error or critical state
- viewport and input assumptions
- implementation fidelity

Do not give only one direction real data and polished visuals.

## Isolation locations

Use one appropriate location:

- separate Storybook concept story
- dev-only route
- game-engine test scene or test map
- `prototypes/ui/`
- temporary `.ui-probes/` source with captures under `docs/ui/probes/`

Do not connect probes to production navigation, exports, deployment, or user data.

## Prohibited

- extracting shared UI components across probes
- copying the first probe and reskinning the others
- connecting production state management or APIs
- normalizing every candidate to the existing design system before selection
- using long explanatory copy to compensate for structural weakness in only one direction
- registering a rejected probe as approved precedent

## Capture record

For every direction, record:

- source or scene path
- run method
- capture viewport and input
- content, font, copy, and state used
- observations about text fit, alignment, and the explanation-deletion test
- screenshot or video path
- interactions not actually verified
- disposal or removal plan

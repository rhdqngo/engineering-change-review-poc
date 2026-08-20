# Narrative Restraint

Operational UI should lead with **real objects, current state, and available actions**, not sentences that explain the interface. Use text when structure alone cannot communicate a constraint, consequence, risk, error, recovery path, or decision rationale.

## Text necessity gate

Every persistent text element must serve at least one of these roles:

- object or control identification
- current state
- non-obvious constraint
- consequence or irreversible risk
- error cause and recovery
- information required for a decision
- recommendation or calculation rationale
- accessibility-required name or instruction

Remove or defer text that merely:

- restates a visible heading
- repeats the behavior of a visible control in sentence form
- narrates the page structure
- repeats the same concept in a breadcrumb, title, subtitle, and card title
- markets a feature inside a recurring workflow
- tells the user to click an obvious control
- fills empty space with welcome copy or explanatory paragraphs

## One concept, one expression

Do not repeat the same concept across:

- navigation label
- breadcrumb
- page title
- page subtitle
- section title
- card title
- helper paragraph

Keep the smallest set of expressions needed for orientation, action, and state.

## Structure before prose

Before adding explanatory copy, try:

- clearer grouping
- stronger hierarchy
- better labels
- better defaults
- visible state
- example or real content
- contextual action placement
- progressive disclosure

If removing a paragraph makes the screen unintelligible, review information architecture and affordances before restoring the paragraph.

## Explain the outcome, not the control

Weak explanation:

> Click the Delete button to delete the project.

Useful explanation:

> The project and its 12 linked deployment records will be permanently deleted.

Explain results and risks that the user cannot infer from the visible control, not how to operate the control.

## Explain uncertainty, not the page

Weak explanation:

> Use filters to find the items you want.

Useful explanation:

> Archived projects are excluded from default search results.

## Persistent and contextual explanation

### Persistent

- object and control labels
- critical constraints
- current system state
- irreversible consequences close to the action

### Contextual

- validation help
- first-use guidance
- unusual conditions
- advanced explanation
- formula or recommendation rationale

Prefer to place contextual explanation in:

- focus or error state
- tooltip or popover
- expandable detail
- help drawer
- onboarding
- documentation

## Recurring workflows

Guidance needed only on first use must not remain permanently visible in a repeated workflow. Make it:

- dismissible
- contextual
- progressive
- remembered after completion

In frequently used editors, dashboards, settings, inventories, and monitoring screens, prioritize real data and actions over prose.

## Empty states

Default structure:

1. current state
2. a short reason or implication when needed
3. one meaningful next action

Do not turn an empty state into a feature-marketing page.

## Marketing boundary

Explanatory or emotional copy may be appropriate on:

- landing pages
- onboarding
- campaign surfaces
- product announcements

It must not overpower the primary task on:

- editors
- dashboards
- settings
- inventories
- monitoring screens
- checkout
- administrative workflows
- in-play HUDs

## High-risk and high-complexity exceptions

The goal is not to minimize text at all costs. Explain these adequately:

- financial, medical, identity, and permission decisions
- destructive or irreversible actions
- recommendation, prediction, and automated-decision rationale
- legal or regulatory consequences
- complex errors and recovery paths

Explain outcomes, evidence, and limitations without repeatedly narrating how to use the interface.

## Copy inventory

For every new screen or meaningful extension, record this table in the screen contract:

| Text | Role | Default visibility | Why structure alone is insufficient | Decision |
| --- | --- | --- | --- | --- |
|  | identity / state / constraint / consequence / recovery / rationale / none | persistent / contextual / first-use |  | keep / defer / remove / rewrite |

Treat `role: none` as a removal candidate by default.

## Explanation deletion test

1. Keep object labels, action labels, state, errors, risk, and accessible names.
2. Temporarily hide subtitles, helper paragraphs, instructional cards, and narrative copy.
3. In the rendered UI, verify whether the user can still understand and complete the primary task.
4. If yes, remove the unnecessary explanation.
5. If no, improve structure, labels, grouping, and visible state before restoring prose.
6. If explanation remains necessary, restore the minimum copy in the closest relevant context.

## Result

- `pass`: copy focuses on identification, state, constraint, consequence, recovery, and rationale without narrating visible structure
- `fail`: prose appears before real objects, state, and actions or substitutes for structure and affordance
- `unverified`: the full rendered copy and deletion test were not reviewed
- `not-applicable`: explanatory copy is the purpose of the surface, such as marketing or narrative content, and the reason is recorded

# Skill Routing Evaluation Cases

Review these cases whenever a skill description, invocation policy, `AGENTS.md` routing rule, or project-state definition changes.

## Evaluation method

For every case, record:

- precondition: project state, Foundation availability, and user request
- expected primary skill
- allowed downstream workflow
- skills that must not start first
- expected write scope
- confirmation boundary
- actual result and notes

Implicit routing depends on skill descriptions, so test both positive and negative cases after wording changes.

## Cases

| ID | Precondition / user request | Primary | Allowed downstream | Must not start first | Expected side effects |
| --- | --- | --- | --- | --- | --- |
| R01 | `empty`: “Build a new SaaS app from scratch.” | `project-bootstrap` | after operational, continue `ui-project-start` when UI is part of the request | `ui-project-start`, `ui-screen-build`, `sync-agents-md` | staging scaffold, managed AGENTS blocks, current status |
| R02 | `empty`: “Set up a Godot roguelike in this empty folder.” | `project-bootstrap` | determine default scene and UI need | UI skills | no forced scaffold in root |
| R03 | `scaffolded`: “Finish setup through the baseline run.” | `project-bootstrap` continuation | direct managed-block sync | `ui-project-start` | operational state or blocker |
| R04 | `operational`: “Synchronize the commands in AGENTS.md with the current repository.” | explicit `sync-agents-md` | none | bootstrap, UI skills | edit only the two managed blocks |
| R05 | `operational`, no Foundation: “Completely redesign this generic AI-looking dashboard.” | `ui-project-start` reset | critic review | `ui-screen-build` | authority map, concepts/probes, provisional Foundation |
| R06 | `operational`, no Foundation: “Compare three initial UI directions, but do not implement one.” | `ui-project-start` | stop before selection | screen build | concepts/probes only |
| R07 | Foundation exists: “Add a settings screen.” | `ui-screen-build` extension/new-flow | critic review | project-start unless Foundation change is required | screen contract and implementation |
| R08 | Foundation exists: “Implement a new checkout flow.” | `ui-screen-build` new-flow | evolution only if global grammar changes | bootstrap | full contract and risk states |
| R09 | No Foundation: “Implement a new checkout flow.” | `ui-project-start` | screen implementation inside the workflow | screen-build first | provisional Foundation first |
| R10 | Any project state: “The button focus ring is clipped.” | `ui-screen-build` repair | targeted revalidation | project-start | minimal patch, no new Foundation |
| R11 | Implementation exists: “Review the current UI.” | `ui-critic` review-only | none | screen build | report only |
| R12 | Implementation exists: “Review it and fix only major issues.” | `ui-critic` review-and-fix | targeted fixes | project-start | report draft, fixes, revalidation |
| R13 | `operational`: “Add an API endpoint.” | normal code work | none | all UI skills | no UI documents |
| R14 | “That is enough for today; I will continue later.” | `handoff` | update current.md if durable state changed | bootstrap/UI build | local handoff, no commit |
| R15 | Foundation exists: “Change the color to blue.” | determine repair/extension | narrow scope | project-start unless identity changes | no three-concept exploration |
| R16 | `empty`: “Review the UI.” | no renderable product; report a blocker or clarify scope | none | project bootstrap without a creation request | no scaffold side effect |
| R17 | Foundation exists: “The icon and button label are misaligned and wrap to two lines on small screens.” | `ui-screen-build` repair | targeted render-matrix rerun | project-start | text-fit and optical-alignment fix |
| R18 | Implementation exists: “Review whether the UI feels comfortable and consistent across screens.” | `ui-critic` review-only | none | screen-build | perceptual and cross-screen report |
| R19 | Foundation exists: “Add a new list screen.” | `ui-screen-build` extension | critic review | project-start | contract, visual-invariants, and render-matrix update |
| R20 | Implementation exists: “Buttons with the same role differ across screens. Review and fix them.” | `ui-critic` review-and-fix | targeted repair and rerun | project-start | report and invariant-aligned fixes |
| R21 | Foundation exists: “There are too many subtitles and explanatory cards. Keep only what is necessary.” | `ui-screen-build` repair/extension | copy inventory and deletion test | project-start | remove or defer redundant prose |
| R22 | Implementation exists: “Review only whether this has the typical AI habit of explaining the interface.” | `ui-critic` review-only | none | screen-build | narrative-restraint report only |
| R23 | Foundation exists: “Create a new administration screen.” | `ui-screen-build` extension/new-flow | copy and perceptual gates | project-start unless grammar changes | no default feature-description cards |
| R24 | Foundation exists, marketing landing page: “Create a landing page that explains the product's benefits.” | `ui-screen-build` extension/new-flow | critic review | context-free narrative removal | marketing copy allowed within the brief boundary |

## Failure signals

- a UI skill or `sync-agents-md` starts before bootstrap in `empty`
- a scaffolder is forced into a non-empty root and overwrites control files
- bootstrap stops while waiting for a separate implicit `sync-agents-md` invocation
- sync rewrites project policy outside the managed blocks
- a normal screen request is implemented as generic card UI without a UI skill
- a UI skill runs for an API or backend-only request
- a small CSS defect triggers three concepts and a complete Foundation workflow
- a review request modifies code without explicit user instruction
- a validated provisional screen is promoted to approved automatically
- `docs/plans/current.md` remains inconsistent with the real milestone for an extended period
- running from a nested directory creates duplicate root documents at the wrong path
- perceptual comfort passes from code and tokens alone
- an accidental two-line control is accepted as normal responsive behavior
- a visual precedent is approved without cross-screen comparison
- prose that repeats a visible heading or control remains without a validated role
- feature-description cards overpower real data and actions in a recurring workflow
- a UI change is not followed by rerunning the relevant render-matrix rows and explanation-deletion test

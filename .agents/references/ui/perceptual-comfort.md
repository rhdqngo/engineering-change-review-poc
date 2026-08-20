# Perceptual Comfort

A UI is not visually complete merely because it builds, uses tokens, and is composed from shared components. Review stability, rhythm, alignment, content fit, and cross-screen consistency in the actual rendered interface as a person sees it.

## Three kinds of consistency

### Semantic consistency

The same meaning and action should be represented and behave in the same way.

- action priority for the same role
- state representation and feedback
- cancel, return, and confirmation rules
- error and recovery behavior

### Geometric consistency

Elements with the same role preserve applicable geometric invariants.

- height and minimum size
- padding and gap
- icon box and stroke weight
- typography role and line height
- baseline and repeated alignment lines
- border, focus, and state treatment
- wrapping, truncation, and collapse behavior

### Perceptual consistency

Do not assume numerically equal values look equal to the eye.

- internal whitespace in an SVG viewBox
- the optical center of triangular or asymmetric icons
- visual baselines across letters, numerals, and fallback fonts
- different visual weight caused by stroke and filled area at the same nominal size
- excessive simultaneous emphasis from badges, icons, shadows, and color

## Role invariants

The same semantic role must follow the applicable rules in `<repo-root>/docs/ui/visual-invariants.md`:

- geometry
- typography
- icon and label composition
- state treatment
- content-fit policy
- responsive collapse ladder
- accessibility behavior

When context requires a variation, record its rationale, scope, and revisit condition in the screen contract or decision log.

## Alignment and baselines

- Repeated left and right edges should form stable alignment lines.
- Trailing values and actions in list rows must not drift as content length changes.
- Validate text baselines with the actual production font.
- Judge icons by the optical center of the visible glyph, not only the center of the CSS box.
- Align numeric columns to the value-comparison axis, not to label length.
- Evaluate 1px and subpixel differences in a normal-scale render, not from source alone.

## Typography fit

Every text role must explicitly use one of these policies:

- natural wrap
- fixed single line
- ellipsis
- line clamp
- approved short label
- icon-only with accessible name
- overflow relocation
- container growth

Accidental browser wrapping is not responsive design.

- If a control label becomes two lines, the height and alignment contract of its row must adapt intentionally.
- Long text must not push an unrelated sibling action out of alignment.
- Do not truncate a critical label until its meaning disappears.
- Validate the actual font, font-loading state, and fallback font.
- Recheck line height and clipping under zoom and localization.

## Icon and text composition

- A leading icon must not shrink because the label is long.
- Icon-label gaps follow the invariant for that role.
- Icon-only controls have a stable accessible name and any necessary help.
- Decorative icons must not carry more visual weight than their labels.
- Mixing filled and outline icons requires a semantic or state rule.
- If the SVG viewBox creates bad optical alignment, correct the asset or apply a documented role-level adjustment.

## Spacing rhythm and grouping

- Related elements are closer than unrelated elements.
- Distinguish intra-item, intra-group, inter-group, and major-section spacing.
- Do not force every gap to use the same value.
- In sparse UI, do not separate labels too far from their values.
- In dense UI, preserve scan lines and grouping.
- Empty space supports hierarchy; it is not decoration used to fill the viewport.

## Visual weight

- Distinguish primary, secondary, destructive, and passive states.
- Do not emphasize every region simultaneously with cards, borders, shadows, or accent colors.
- Supporting information must not attract attention before the core object, state, or action.
- Badges, icons, color, and motion must not redundantly amplify the same message until it becomes fatiguing.

## Content and state stability

Validate layout stability under at least these conditions:

- short, typical, long, and localized text
- production font and fallback font
- minimum, typical, and maximum item counts
- missing images or assets
- large numbers, dates, and currency
- appearance of badges, validation, and helper messages
- loading → ready
- error → recovery
- permission, locked, stale, and offline states

Fail the layout if the appearance of a state pushes the primary action out of view or destroys repeated alignment lines.

## Cross-screen consistency

Compare each repeated semantic role on the reviewed screen with at least one other screen or an explicit precedent:

- page header
- primary and secondary actions
- form field
- list row
- empty state
- dialog
- selection and error states
- icon-label composition

If no comparison target exists, mark the item `unverified` and do not approve it as a precedent automatically.

## Perceptual Polish Pass

After functional and state implementation, run a separate pass that does not change product direction:

1. Review the initial focal point and scan path at normal viewing scale.
2. Check grouping and repeated alignment lines.
3. Compare text baselines and control heights.
4. Check optical icon size and icon-label gaps.
5. Find unexpected wrapping, clipping, and overflow.
6. Review typography and spacing rhythm.
7. Check visual weight and competing emphasis.
8. Review layout shift during state transitions.
9. Compare repeated roles across screens.
10. Rerender every condition affected by a change.

If a problem requires changing information architecture or the Foundation, do not hide that redesign inside polish. Route it to an evolution decision or the decision log.

## Result

- `pass`: applicable criteria are satisfied in actual rendered evidence and the required cross-screen comparison
- `fail`: a repeatable alignment, wrapping, rhythm, or stability problem is visible to users
- `unverified`: only code, tokens, or static measurements exist; rendered evidence is insufficient
- `not-applicable`: the criterion is outside the scope and the reason is recorded

Source code, token use, or component reuse alone cannot pass this gate.

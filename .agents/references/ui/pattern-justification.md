# Pattern Justification and Generic UI Drift

Cards, sidebars, grids, gradients, glow effects, and HUD panels are not forbidden. Treat them as unjustified defaults only when the following questions cannot be answered:

1. Which user decision or action does the pattern directly support?
2. Does it represent the semantic relationship of the content correctly?
3. Which Foundation or precedent principle supports it?
4. Does it remain meaningful across states, long content, narrow screens, and other input methods?
5. Would removing it or using a simpler structure actually make the task worse?

## Common structural regressions

- applying a dashboard shell to a product that is not a dashboard
- placing every information group in the same kind of card, flattening relationships and priority
- choosing a three- or four-column grid simply because space is available
- solving every navigation problem with a left sidebar
- keeping details, settings, and the primary task permanently visible on the same layer
- stacking desktop regions unchanged on mobile
- allowing the first screen's `Card` abstraction to absorb every later kind of information

## Common visual regressions

- applying a large radius, border, and shadow to nearly every element at once
- using decorative purple/teal gradients and glass blur without meaning
- expressing every state and filter as a pill
- placing an oversized hero area in a task-oriented product
- adding charts, statistics, or abstract graphics unrelated to a real decision
- using icons without clear labels

## Explanatory-UI regressions

- repeating the page title's meaning in a subtitle immediately below it
- adding a helper paragraph that explains a visible control
- leading with feature-description cards instead of real functionality or data
- keeping first-use guidance permanently visible in a recurring workflow
- turning an empty state into a feature-marketing page
- repeating the same concept in breadcrumbs, titles, sections, and cards

Use the text-necessity gate and explanation-deletion test in `<repo-root>/.agents/references/ui/narrative-restraint.md` to decide whether explanation is justified.

## Game-UI regressions

- neon, corner brackets, or hexagonal panels unrelated to the world or genre
- keeping information permanently visible in the HUD when the player does not need to monitor it continuously
- presenting every event in the same size centered popup
- using a different gamepad-focus model in every menu
- making locked, unowned, equipped, selected, and unavailable states look alike

## How to write a useful finding

Weak finding:

> There are too many cards, so it looks AI-generated.

Useful finding:

> The total, delivery choice, and promotion use the same card emphasis, which hides the result the user must verify before confirmation. Separate total and outcome into a persistent summary region and lower promotion to a supporting layer.

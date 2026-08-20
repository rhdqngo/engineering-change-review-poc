# Screen Classification

Classify each requested screen independently.

## Required fields

- context: game / non-game
- screen state: in-play, paused, menu, task page, modal, panel, embedded, etc.
- primary user goal
- primary interaction mode
- supporting interaction modes, at most two
- urgency: low / medium / high / critical
- density: sparse / moderate / dense
- consequence: reversible / recoverable / destructive / financial / competitive
- expertise: novice / mixed / expert
- platform and viewport
- input methods
- critical, primary, supporting, and optional information
- primary, secondary, cancel/back, and destructive actions

## Boundary test

A screen may be too broad when:

- three interaction modes are equally primary
- two unrelated completion actions compete
- realtime and deliberate review information share equal prominence
- novice explanation permanently blocks expert work
- content, settings, and transaction are all persistent at once

Split by task or make supporting information contextual rather than adding more equal-weight panels.

## Industry and genre

Industry and game genre add constraints but do not select the layout. An RPG inventory and a commerce comparison workspace may share `browse-compare`, while input, ownership, equipment, economy, and world context differ.

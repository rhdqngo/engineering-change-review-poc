# Game UI Context

A game is not a single visual genre. Add screen state, time model, input device, and the UI's relationship to the play space as constraints on the interaction mode.

## Screen states

- `in-play`: gameplay continues while the UI is visible
- `paused`: gameplay stops, but the current play context remains relevant
- `pre-play`: before a match, stage, or run begins
- `post-play`: results, rewards, and review
- `meta-progression`: inventory, skills, shop, and long-term progression
- `system-settings`: input, accessibility, graphics, and account settings

## Required questions

- Does gameplay continue while the UI is open?
- Which information becomes useless within seconds?
- Which information must remain continuously visible?
- Does the UI obscure targets, routes, puzzles, terrain, or opponents?
- Is the input gamepad, keyboard and mouse, touch, or mixed?
- Is the information private, shared with teammates, or visible to opponents?
- Is the presentation diegetic, non-diegetic, or mixed?
- Does information density change with player expertise?

## In-play / HUD

- Protect the central aiming, puzzle, and route-planning areas.
- Keep persistent information in stable locations.
- Give event notifications a clear lifetime and exit.
- For critical information, combine color with shape, position, motion, or sound.
- Do not require long-form reading or complex focus movement during play.
- Account for safe areas, resolution, streaming overlays, and aspect ratio.

## Menus and meta UI

- Define initial gamepad focus, movement order, wrap behavior, and back/cancel behavior.
- Restore focus and scroll position when returning from a child screen.
- Do not depend on hover.
- Distinguish selected, equipped, owned, locked, insufficient-cost, unavailable, and new states.
- Show the result before confirming a cost, consumption, dismantle, or permanent change.

## Genre modifiers

| Modifier | Priority review |
| --- | --- |
| Action / FPS | low occlusion, directional and danger signals, peripheral awareness |
| Strategy / simulation | overview-to-detail flow, high density, time control, multi-selection |
| RPG / collection | comparison, equipment, progression, long content, meaningful states |
| Puzzle | board focus, direct manipulation, staged hints, minimal interruption |
| Rhythm | timing readability, lane stability, latency and judgment feedback |
| Racing | glanceability, route, position, vehicle state |
| Narrative | dialogue hierarchy, pacing, consequence of choices, accessibility |
| Sports / competitive | score, clock, turns, fairness, separation of player and spectator information |

## Fairness

- Do not reveal information that should remain hidden from opponents.
- Do not offer unrestricted density changes that create a competitive advantage.
- Separate player UI from spectator UI.
- Ensure accessibility options do not misrepresent game rules or state.

Use world-integrated presentation only when it preserves reading speed, accuracy, and accessibility. Neon panels used merely to signal “game UI” are not a functional justification.

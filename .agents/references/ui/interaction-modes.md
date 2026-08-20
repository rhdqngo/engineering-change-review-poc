# UI Interaction Modes

Classify a screen by the user's primary activity rather than by industry or game genre. Record one primary mode per screen and, when necessary, no more than two secondary modes.

## browse-compare

The user explores multiple options, understands their differences, and selects one or more.

Representative screens: product lists and comparisons, game inventories, character selection, plan selection.

Required criteria:

- current scope, filters, and sort state
- consistent units and ordering for comparable attributes
- clear distinction among selected, owned, and unavailable states
- preserved context after viewing details and returning
- support for growing lists and long content

## create-edit

The user creates or edits a document, setting, character, dataset, or other content.

Required criteria:

- the edited object and current selection
- modified, saving, and saved states
- undo, cancel, and recovery
- error location and resolution
- preview or feedback about the result

## monitor-analyze

The user monitors state and change and evaluates causes, trends, or anomalies.

Required criteria:

- normal range and current change
- data freshness and time range
- a path from overview to supporting evidence
- prioritization of abnormal states
- charts that support an actual decision

## transact-confirm

The user confirms an action with a meaningful result, such as purchase, deletion, submission, permission change, or dismantling.

Required criteria:

- what will change
- cost, scope, and reversibility
- error prevention and confirmation
- the result and next step after completion
- preservation of input and context after failure

## realtime-react

The user recognizes state and responds immediately under time pressure.

Required criteria:

- information priority based on time to action
- persistent information in stable locations
- short-lived event notifications
- low occlusion
- redundant signals for critical state

## navigate-explore

The user explores space, content, or relationships while understanding current location and possible next moves.

Required criteria:

- current location and scope
- available directions and return path
- visited, completed, and locked states
- discoverable cues
- preservation of exploration context

## communicate-coordinate

People or agents exchange information and coordinate roles, state, and next actions.

Required criteria:

- distinction among participants, senders, and system messages
- read, new-item, and handled states
- conversation or work context
- mentions, assignments, and requested actions
- time and freshness

## Composite screens

The primary mode determines the information architecture. Secondary modes add only the states and actions they require.

Example: RPG inventory

```yaml
primary: browse-compare
secondary:
  - transact-confirm
context: game
modifiers:
  - gamepad-focus
  - equipped-owned-locked-states
```

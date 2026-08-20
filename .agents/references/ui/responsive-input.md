# Responsive and Input Adaptation

Responsive design is not shrinking desktop UI or stacking its regions vertically. Reprioritize information and actions according to available space and input method.

## Decisions by viewport

For every major viewport, specify:

- the core task that must remain possible
- information that remains continuously visible
- information to summarize, collapse, or relocate
- information that moves to another screen or overlay
- fixed actions and scrolling actions
- long-content and maximum-item behavior

Do not fill wide screens with meaningless cards, metrics, or decorative emptiness.

## Keyboard

- initial focus and logical order
- visible focus state
- meaning of Escape, Enter, Space, arrows, and shortcuts
- focus restoration after closing a modal or panel
- interaction between focus and scroll containers

## Touch

- adequate target size and spacing
- access to information and actions without hover
- alternatives to swipe and long press
- bottom safe area and virtual keyboard
- failure and cancellation paths for drag interactions

## Mouse

- hover used only for supporting information
- distinction between clickability and selection
- precise operation in dense lists
- start, target, and completion feedback for drag operations

## Gamepad

- initial focus
- directional navigation graph and wrap behavior
- analog-stick and D-pad behavior
- confirm, cancel, and secondary actions
- return position from a child screen
- automatic scrolling when focus moves off-screen

## State validation

For every supported input method, distinguish and verify:

- focus
- hover
- pressed
- selected
- active
- disabled
- unavailable / locked

A static screenshot cannot pass input adaptation.

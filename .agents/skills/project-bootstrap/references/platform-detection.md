# Platform Detection

Determine the platform from the product goal and repository evidence. Do not choose a stack merely because it is familiar to generate.

| Platform | Representative requirements and signals |
| --- | --- |
| Web | browser delivery, URL routing, SSR/SPA, accessibility, responsive layout |
| Desktop | filesystem, multiple windows, installation and update, OS integration |
| Mobile | touch, offline use, store review, camera, notifications, permissions |
| Game | engine project, real-time loop, scenes/maps, gamepad, rendering performance |
| CLI | terminal I/O, pipes, exit codes, non-interactive execution |
| Service / API | network contracts, persistence, authentication, observability |
| Library | public API, packaging, compatibility, examples, tests |

## Questions that substantially change architecture

- Which browser and native capabilities are required?
- Are offline, real-time, or multiplayer behavior core requirements?
- Is store, console, or engine certification required?
- Is server rendering or search visibility required?
- Is the primary input mouse and keyboard, touch, gamepad, or mixed?

## UI-related signals

- Web: Storybook, Playwright, Cypress, browser scripts
- Mobile: simulator/device targets, UI test target
- Unity/Godot/Unreal: test scene or map, automation runner, capture path
- Desktop: preview mode, UI automation, packaged-app smoke test

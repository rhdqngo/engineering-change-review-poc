# V6 Camera-Stage Presentation

`index.html` is a standalone Korean HTML presentation. It uses one persistent 16:9 stage and 22 reversible cues instead of replacing slide pages. It has no CDN, framework, Cloud Run, Vertex AI, or published-result dependency.

## Run

Open `index.html` directly, or serve this directory with a static HTTP server.

## Controls

- `Right Arrow` / `Space` / `Page Down`: next causal beat
- `Left Arrow` / `Backspace` / `Page Up`: previous completed state
- `Home` / `End`: opening / conclusion
- On the selected flight-software view, activate the system once to reveal its roles and functions.
- The top-left bookmark shows the chapter; the bottom-right arrows move between cues.
- Meaningful hashes restore an exact cue.

## Narrative

1. Spacecraft and nested engineering systems
2. cFS Software Bus and change propagation
3. Deterministic retrieval, two Gemini-backed review roles, exact evidence, and the Human Engineer boundary
4. Five plain-language test criteria and conclusion

The representative XART-03 path carries one change from Broad Top-40 through identifier expansion, Final Top-10, claim review, exact evidence, independent verification, and human judgment. The deck does not claim that cFS is defective, that AI approves changes, that no supported review guarantees no impact, or that the benchmark measured human review time.

## Assets

The project-generated source illustration is `assets/spacecraft-light.png`. The active alpha cutout, `assets/spacecraft-transparent.png`, is reproducibly derived by `remove_spacecraft_background.py`. Other diagrams, signals, callouts, and animations are native HTML/CSS.

The presentation source and project-generated illustration are distributed under the repository's Apache-2.0 license. They are illustrative and do not depict or imply a NASA-endorsed spacecraft design.

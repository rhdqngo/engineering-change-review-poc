# NASA cFS Data Selection and Experimental Clean Baseline

## Fixed subset

The experiment uses one component only: NASA `sample_app` from the official cFS `v7.0.1` release at commit `2f93d1a4159a02b18d67ee83342c9e96b90e23e4`.

Selection rationale:

- one small cFS component contains an EDS interface definition, generated/default configuration headers, flight-software design/implementation, coverage tests, and change history;
- the artifacts share concrete traceable concepts such as function codes, message fields, command counters, table limits, topics, and error behavior;
- the upstream project is public and Apache-2.0 licensed;
- the upstream README explicitly identifies it as a non-flight sample with minimal testing, so it is suitable as realistic vocabulary and structure, not as industrial ground truth.

The pinned source snapshot is under `data/nasa/sample_app_v7.0.1`. `data/nasa/provenance.json` fixes the upstream URL, tag, full commit, retrieval date, byte count, and SHA-256 of every selected file. `data/nasa/artifacts.json` fixes the exact line ranges exposed to retrieval.

## Experimental Clean Baseline

The clean baseline is the unmodified pinned snapshot and its 32 curated source spans. It was accepted for this controlled experiment because:

- function codes agree between EDS and default function-code configuration (`0`, `1`, `2`, `3`);
- display and housekeeping fields agree between EDS and default message definitions;
- table fields agree between EDS and default table definitions;
- implementation uses the configured command topics, pipe limits, table limits, and message fields;
- coverage tests exercise the existing command handlers, dispatch, and table validation paths.

This check establishes internal suitability only. It does not claim that NASA `sample_app` is defect-free, complete, flight-qualified, or an authoritative requirements baseline. The upstream README itself warns that extensive testing is not performed and discrepancies may exist.

## Freeze boundary

`data/cases/cases.json` fixes 18 cases before retrieval or LLM results are inspected:

- Direct: 4
- Semantic: 4
- Cross-Artifact: 4
- Clean: 3
- Benign: 3

Each mutation case includes the expected review target and an exact expected evidence span. Control cases fix an empty expected review set. The evaluation must not edit these targets after observing results; a checksum gate will reject a changed preregistration file.

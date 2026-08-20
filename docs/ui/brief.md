# Demo UI Brief

state: provisional  
scope-level: lite  
updated: 2026-08-20

## Product and user

This is an experiment workbench for an engineering reviewer, not a change-management suite. Its primary job is to let the reviewer compare the same sealed Hybrid Retrieval Top-K with the smaller set of evidence-grounded review findings, and inspect why an output was admitted or blocked.

## Required tasks

- Navigate the 18 frozen cases, including clean, explicit, restore, semantic, cross-artifact, and benign cases.
- Confirm the baseline and proposed arms share the same six source IDs and candidate seal.
- Inspect source ID, exact source span, short reason, and independent-verifier disposition.
- See unsupported output as withheld audit state, never as engineering advice.

## Constraints

- No editing, issue tracking, approval workflow, or repository mutation.
- Fixture data must be unmistakably labeled as non-experimental.
- Dense expert UI, keyboard-operable controls, and a narrow-screen collapse ladder are required.

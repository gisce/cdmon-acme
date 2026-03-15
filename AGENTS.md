# AGENTS.md

## Goal
Maintain `cdmon-acme`: Python-first ACME automation using cdmon DNS challenge.

## Rules
- Default to Let's Encrypt staging in examples/tests.
- Never log API keys, private keys, or challenge secrets.
- Keep API-breaking changes behind major versions.

## Done criteria
- `ruff check .` passes
- CLI help and README examples are up to date
- New behavior has tests

# Phase 8 validation

This directory is an evidence audit of Clone Trap on **real existing Git working trees**.

It is not part of the product CLI. It does not change scoring. It records what the shipped command actually does.

## Why this exists

Phases 1–7 built a conservative, local portability auditor. Phase 8 asks whether this claim is true:

> Before a clean clone, Clone Trap can surface hidden assumptions that may prevent the repository from working on another machine.

The answer is qualitative. Clone Trap is not a machine-learning model. This directory does **not** invent accuracy percentages.

## What is measured

1. **Negative-control quietness** — clean stdlib repos stay `ready`
2. **Trap usefulness** — confirmed/likely findings a new clone would actually hit
3. **False-positive classes** — findings that should have been suppressed
4. **Drift usefulness** — README promises vs inferred requirements
5. **Bootstrap safety** — actions an agent could follow without executing the target repo

## What is not measured

- Invented metrics such as `accuracy = 94%`
- Prediction that a clone will fail
- Formal performance benchmarks

## Labels

| Label | Meaning |
| --- | --- |
| Correct trap | Independent signals and a missing declaration |
| False positive | Surfaced without a real clean-clone gap |
| False negative | A known hidden assumption was not surfaced |
| Ambiguous | Reasonable people could disagree |

| Drift | Meaning |
| --- | --- |
| Useful | A new developer would change how they set up |
| Generic | True but not specific |
| Misleading | Overstates or invents a requirement |

## How to run

```bash
PYTHONPATH=src python validation/scripts/validate_repo.py \
  --repo /path/to/repository \
  --label example
```

Do not alter validation repositories.

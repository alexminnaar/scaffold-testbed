# Hard Model Migration

Stress test for `llmci migrate` progress logging and iterative prompt optimization.

This fixture intentionally starts with an under-specified prompt that only allows `hardware` and `billing` labels, while the shared ticket dataset also contains `account`, `software`, and `general` examples. It should force real optimization iterations before evaluating the holdout set.

## Usage

```bash
export OPENAI_API_KEY=...
printf 'n\n' | llmci migrate \
  --from openai/gpt-4o \
  --to openai/gpt-4o-mini \
  --eval ticket-classification \
  --optimizer-model openai/gpt-4o-mini \
  --patience 3 \
  --max-iterations 3
```

The workflow smoke test installs `llmci` from `llmci-cli/llmci@main` so it can validate unreleased migration progress logging. It checks that output includes a streaming iteration log, final holdout progress line, and at least one iteration-history row.

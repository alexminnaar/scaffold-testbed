# Scaffold Testbed — Acme Support

[![llmci Evals](https://github.com/llmci-cli/llmci-testbed/actions/workflows/llmci.yml/badge.svg)](https://github.com/llmci-cli/llmci-testbed/actions/workflows/llmci.yml)

Realistic customer monorepo for dogfooding [`llmci`](https://pypi.org/project/llmci/) ([source](https://github.com/llmci-cli/llmci)). Fictional company **Acme Support** runs ticket classification, RAG helpdesk, summarization QA, and a support agent — all evaluable with `llmci run`.

## Prerequisites

- Python 3.11+
- [`llmci`](https://pypi.org/project/llmci/) from PyPI

```bash
make install
# or: pip install -e ".[dev]"
```

CI runs `pip install --upgrade llmci` (requires 0.4.1+ for price overrides, cross-provider migration, and integrated CI gates).

**Scaffold developers only** — unreleased CLI changes:

```bash
pip install "llmci @ git+https://github.com/llmci-cli/llmci@main"
```

## Quick start

```bash
make install
make eval-classifier
```

## Alternate Config Files

Use `llmci run --config` from each service directory when a service has multiple eval configs:

```bash
MOCK_LLM=1 llmci run --config llmci-prompt.yaml
```

## Discover Configs

List all eval configs in the monorepo:

```bash
llmci discover
```

Run a safe subset with filters. This example runs service configs but skips real LLM judge configs:

```bash
MOCK_LLM=1 llmci run --all \
  --include "services/**" \
  --exclude "services/summarizer/llmci.yaml" \
  --exclude "services/support-agent/llmci-single-full.yaml"
```

## Services

| Service | Path | Docs case study | Scaffold example |
|---------|------|-----------------|------------------|
| Ticket classifier | `services/ticket-classifier/` | FastAPI Service | `examples/08-fastapi-service` |
| RAG QA | `services/rag-qa/` | RAG Pipeline | `examples/12-rag-retrieval` |
| Summarizer | `services/summarizer/` | Summarization QA | `examples/09-summarization-qa` |
| Support agent | `services/support-agent/` | Support Agent | `examples/05`, `06` |
| JSON API | `services/json-api/` | Exact-match validation | `examples/01-prompt-level` |
| Model migration | `migration/` | Multi-Model Migration | `examples/02-model-migration` |
| Hard model migration | `migration-hard/` | Multi-Model Migration | real-LLM smoke |

## Mock vs real LLM

| Variable | Default (CI) | Purpose |
|----------|--------------|---------|
| `MOCK_LLM` | `1` | Deterministic keyword/fixture logic |
| `OPENAI_API_KEY` | unset | Required for real LLM judge / migration |

CI runs all services in mock mode with `--compare-to=origin/main` on PRs. Use **llmci LLM Evals** (manual dispatch) for real LLM runs.

## Run all mock evals

```bash
make eval-all
```

Covers the same 8 eval configs as the CI matrix (including the integrated quality + cost + safety gate on ticket-classifier).

## HTTP testing (ticket classifier)

```bash
docker compose up -d
../../shared/scripts/wait_for_http.sh http://localhost:8000/health
cd services/ticket-classifier
CLASSIFIER_URL=http://localhost:8000 MOCK_LLM=1 llmci run
```

## Add a new service

1. Create `services/<name>/` with `llmci.yaml`, `evals/*.jsonl`, and a command target script.
2. Add a matrix entry to `.github/workflows/llmci.yml`.
3. On `main`: `MOCK_LLM=1 llmci run --update-baseline` and commit `.llmci/baselines/`.

## Links

- [llmci on GitHub](https://github.com/llmci-cli/llmci)
- [llmci on PyPI](https://pypi.org/project/llmci/)

## Demo regression branches

Open PRs from these branches to see Scaffold fail CI and post a PR comment:

| Branch | Change | Expected failure |
|--------|--------|------------------|
| `test/break-classifier` | Remove billing keywords | `service-classification` accuracy |
| `test/break-rag-retrieval` | Force empty retrieval | `rag-qa` retrieval_recall |
| `test/break-agent-safety` | Agent calls `delete_account` on normal queries | `support-agent-single` mean_score |

```bash
# Branches are pre-built — open a PR against main to see CI fail + the llmci PR comment:
gh pr create --base main --head test/break-classifier --title "demo: break classifier"
gh pr create --base main --head test/break-rag-retrieval --title "demo: break RAG retrieval"
gh pr create --base main --head test/break-agent-safety --title "demo: break agent safety"
```

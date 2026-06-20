# Ticket Classifier

FastAPI microservice that classifies Acme Support tickets through preprocess → classify → postprocess.

## Run evals

From `services/ticket-classifier/`:

```bash
# Service-level (full pipeline)
MOCK_LLM=1 llmci run

# Prompt-level (classification only)
MOCK_LLM=1 llmci run --config llmci-prompt.yaml

# Cost gate (model swaps): quality + budget on cost_mean
MOCK_LLM=1 llmci run --config llmci-cost.yaml
```

The model is pinned in `model.txt`, so swapping models is a one-line diff. The
cost gate (`llmci-cost.yaml`) reports cost in USD per 1,000 classifications using
published per-token list prices, and blocks a swap whose `cost_mean` rises more
than the budget vs. the baseline model — even if quality is unaffected.

## Start HTTP server

```bash
cd services/ticket-classifier
MOCK_LLM=1 uvicorn app.main:app --port 8000
curl http://localhost:8000/health
```

## HTTP eval mode

With the server running (or via `docker compose up` from repo root):

```bash
../../shared/scripts/wait_for_http.sh http://localhost:8000/health
CLASSIFIER_URL=http://localhost:8000 MOCK_LLM=1 llmci run
```

Maps to docs case study `cs-fastapi` and Scaffold example `08-fastapi-service`.

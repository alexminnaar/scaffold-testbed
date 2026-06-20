# JSON API

LLM-backed contact-extraction endpoint. A free-text message goes in; a structured
contact record (`name`, `email`, optional `phone`) comes out. llmci's built-in
`structured` judge parses the JSON answer and validates it against the response
schema in `llmci.yaml`. Maps to `examples/16-structured-output`.

```bash
# Deterministic baseline (regex oracle, no API key):
MOCK_LLM=1 llmci run

# Real model:
MOCK_LLM=0 OPENAI_API_KEY=... API_MODEL=openai/gpt-4o-mini llmci run
```

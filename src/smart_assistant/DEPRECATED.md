# DEPRECATED

This directory is **deprecated** and will be removed in a future release.

## What was this?

- `main.py` — Streamlit-based multi-user assistant UI (superseded by `backend/src/` FastAPI backend + React frontend)
- `services/` — Conversation state machine and orchestration (superseded by `backend/src/core/service.py`)
- `llm/client.py` — LLM client (superseded by `backend/src/core/llm.py`)
- `tools/` — Tool system (superseded by `backend/src/plugins/`)

## Migration Guide

| Old | New Location |
|-----|-------------|
| `src/smart_assistant/tools/sql_query.py` SQL safety logic | `backend/src/plugins/builtin/query_executor.py` |
| `src/smart_assistant/llm/prompts.py` PromptManager | `backend/src/core/prompts.py` (if needed) |
| `src/smart_assistant/main.py` Streamlit app | Use React frontend at `frontend/` + FastAPI at `backend/src/` |

## Timeline

This code will be removed after the new architecture is stable. Please do not add new functionality here.

---

*Deprecated: 2026-03-29*
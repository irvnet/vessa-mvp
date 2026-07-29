"""LangGraph Server entrypoint — exported graph for `langgraph up`."""

from app.agent import build_lazy_agent

graph = build_lazy_agent()

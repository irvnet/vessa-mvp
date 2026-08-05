"""Importing app.agent constructs ChatOpenAI/OpenAIEmbeddings at module scope, which
raises without a key present. These tests only exercise pure, deterministic functions —
no network call is ever made — so a placeholder key is enough to get them imported.
Set before any app import so it's in place when pytest collects the test modules."""

import os

os.environ.setdefault("OPENAI_API_KEY", "sk-test-not-used")

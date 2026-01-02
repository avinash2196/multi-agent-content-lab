from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Optional, Dict, Any

try:
    from langsmith import Client as LangSmithClient
except Exception:  # pragma: no cover - optional dependency
    LangSmithClient = None


class Observability:
    """Lightweight observability hooks with optional LangSmith stubs."""

    def __init__(self):
        self.logger = logging.getLogger("observability")
        self.langsmith_enabled = bool(os.getenv("LANGSMITH_API_KEY"))
        self.langsmith_project = os.getenv("LANGSMITH_PROJECT")
        self.langsmith_client = None
        if self.langsmith_enabled and LangSmithClient:
            try:
                # Initialize client without project parameter (newer versions don't support it)
                self.langsmith_client = LangSmithClient()
            except Exception as e:  # noqa: BLE001
                self.logger.warning(f"LangSmith client init failed: {e}")
                self.langsmith_client = None

    @contextmanager
    def span(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        self.logger.debug(f"span.start {name} {attributes or {}}")
        run = None
        if self.langsmith_client:
            try:
                run = self.langsmith_client.create_run(
                    name=name,
                    inputs=attributes or {},
                    run_type="chain",
                )
            except Exception as e:  # noqa: BLE001
                self.logger.debug(f"LangSmith create_run failed: {e}")
        try:
            yield
            self.logger.debug(f"span.end {name}")
            if run and self.langsmith_client:
                try:
                    self.langsmith_client.update_run(run.id, outputs={"status": "ok"})
                except Exception as e:  # noqa: BLE001
                    self.logger.debug(f"LangSmith update_run failed: {e}")
        except Exception as e:
            self.logger.error(f"span.error {name}: {e}")
            if run and self.langsmith_client:
                try:
                    self.langsmith_client.update_run(run.id, error=str(e))
                except Exception:
                    pass
            raise

    def record_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        self.logger.info(f"event {name} {attributes or {}}")
        if self.langsmith_client:
            try:
                self.langsmith_client.create_run(name=name, inputs=attributes or {}, run_type="event")
            except Exception as e:  # noqa: BLE001
                self.logger.debug(f"LangSmith event failed: {e}")

    def record_error(self, name: str, error: Exception):
        self.logger.error(f"error {name}: {type(error).__name__} {error}")
        if self.langsmith_client:
            try:
                self.langsmith_client.create_run(
                    name=name,
                    inputs={"error": str(error), "type": type(error).__name__},
                    run_type="error",
                )
            except Exception as e:  # noqa: BLE001
                self.logger.debug(f"LangSmith error reporting failed: {e}")

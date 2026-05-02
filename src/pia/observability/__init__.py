"""Observability package for PIA.

Exports the ``trace`` decorator.  When Langfuse keys are not configured the
decorator is a no-op, making the package safe to import in all environments.
"""
from pia.observability.langfuse import trace

__all__ = ["trace"]

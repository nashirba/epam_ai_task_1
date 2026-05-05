"""Observability package for PIA.

Exports the ``trace`` decorator and request-id binding helpers.  When
Langfuse keys are not configured the decorator is a no-op, making the
package safe to import in all environments.
"""

from pia.observability.langfuse import (
    current_request_id,
    reset_request_id,
    set_request_id,
    trace,
)

__all__ = ["current_request_id", "reset_request_id", "set_request_id", "trace"]

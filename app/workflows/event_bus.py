"""
workflows.event_bus
===================
In-process async pub/sub event bus.

Adapted from Jake's shared/event_bus.py — simplified for Sage Finance OS.
No external broker (Kafka/RabbitMQ) — events are dispatched in-process
and persisted to workflow.events for audit trail.

Usage:
    from app.workflows.event_bus import emit, subscribe

    @subscribe("sync.completed")
    async def on_sync_complete(event: dict):
        print(f"Sync done: {event}")

    await emit("sync.completed", {"run_id": "...", "objects": [...]})
"""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

log = logging.getLogger(__name__)

# Handler registry: event_type → list of async handlers
_handlers: dict[str, list[Callable]] = defaultdict(list)

# Cascade protection
_MAX_CASCADE_DEPTH = 5
_cascade_depth = 0


# -- Valid event types ---------------------------------------------------------

EVENT_TYPES = frozenset({
    "sync.started",
    "sync.object.completed",
    "sync.completed",
    "sync.failed",
    "quality.passed",
    "quality.failed",
    "quality.quarantined",
    "period.closing",
    "period.closed",
    "kpi.refreshed",
    "alert.data_stale",
    "action.requested",
    "action.completed",
})


def subscribe(event_type: str):
    """Decorator to register an async handler for an event type."""
    def decorator(fn: Callable[..., Coroutine]):
        if event_type not in EVENT_TYPES:
            log.warning("event_bus: subscribing to unknown event type %s", event_type)
        _handlers[event_type].append(fn)
        log.debug("event_bus: subscribed %s to %s", fn.__name__, event_type)
        return fn
    return decorator


async def emit(
    event_type: str,
    payload: dict[str, Any],
    source: str = "system",
    conn=None,
) -> str:
    """
    Emit an event — dispatches to all registered handlers.

    Parameters
    ----------
    event_type:  Must be one of EVENT_TYPES.
    payload:     Event data.
    source:      Who emitted the event.
    conn:        Optional async DB connection for persistence.

    Returns
    -------
    event_id (UUID string).
    """
    global _cascade_depth

    if event_type not in EVENT_TYPES:
        log.warning("event_bus: unknown event type %s — delivering anyway", event_type)

    event_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)

    event = {
        "event_id": event_id,
        "event_type": event_type,
        "source": source,
        "payload": payload,
        "emitted_at": now.isoformat(),
    }

    # Persist to DB if connection available
    if conn is not None:
        try:
            await conn.execute(
                """
                INSERT INTO workflow.events (event_id, event_type, source, payload)
                VALUES ($1, $2, $3, $4::jsonb)
                """,
                uuid.UUID(event_id), event_type, source, json.dumps(payload, default=str),
            )
        except Exception as e:
            log.warning("event_bus: failed to persist event %s — %s", event_id, e)

    # Cascade protection
    _cascade_depth += 1
    if _cascade_depth > _MAX_CASCADE_DEPTH:
        log.warning("event_bus: cascade depth exceeded (%d) — skipping handlers for %s",
                     _cascade_depth, event_type)
        _cascade_depth -= 1
        return event_id

    # Dispatch to handlers
    handlers = _handlers.get(event_type, [])
    for handler in handlers:
        try:
            await asyncio.wait_for(handler(event), timeout=5.0)
        except asyncio.TimeoutError:
            log.warning("event_bus: handler %s timed out for %s", handler.__name__, event_type)
            # Persist dead letter
            if conn is not None:
                try:
                    await conn.execute(
                        """
                        INSERT INTO workflow.dead_letters (event_id, handler, error_message)
                        VALUES ($1, $2, $3)
                        """,
                        uuid.UUID(event_id), handler.__name__, "handler timed out (5s)",
                    )
                except Exception:
                    pass
        except Exception as e:
            log.error("event_bus: handler %s failed for %s — %s",
                      handler.__name__, event_type, e)

    _cascade_depth -= 1

    log.debug("event_bus: emitted %s → %d handlers", event_type, len(handlers))
    return event_id


def get_handlers() -> dict[str, list[str]]:
    """Return a map of event_type → handler function names (for diagnostics)."""
    return {
        event_type: [h.__name__ for h in handlers]
        for event_type, handlers in _handlers.items()
        if handlers
    }

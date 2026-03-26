"""
workflows.kill_switch
=====================
Global and per-module mutation control.

Adapted from Jake's shared/kill_switch.py — simplified.
Checks workflow.kill_switch_rules before allowing write operations.

Modes:
  hard — block the operation entirely, raise KillSwitchError
  soft — log a warning but allow the operation
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from app.core.errors import KillSwitchError

log = logging.getLogger(__name__)

# In-memory cache (refreshed on check)
_cache: dict[str, dict] = {}


def is_active(conn, scope: str = "global") -> bool:
    """Check if the kill switch is active for a scope."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT is_active, mode FROM workflow.kill_switch_rules WHERE scope = %s",
            (scope,),
        )
        row = cur.fetchone()

    if row is None:
        return False

    return row[0]  # is_active


def check_kill_switch(conn, scope: str = "global", action_description: str = "") -> None:
    """
    Check the kill switch — raises KillSwitchError if hard-blocked.

    Parameters
    ----------
    conn:                psycopg2 connection.
    scope:               'global' or module name.
    action_description:  What was being attempted (for logging).
    """
    with conn.cursor() as cur:
        # Check both global and specific scope
        cur.execute(
            """
            SELECT scope, mode, is_active, reason
            FROM workflow.kill_switch_rules
            WHERE scope IN ('global', %s) AND is_active = TRUE
            ORDER BY CASE scope WHEN 'global' THEN 0 ELSE 1 END
            """,
            (scope,),
        )
        rows = cur.fetchall()

    for row in rows:
        rule_scope, mode, is_active, reason = row
        if not is_active:
            continue

        if mode == "hard":
            log.warning("kill_switch: BLOCKED %s (scope=%s, reason=%s)",
                        action_description, rule_scope, reason)
            raise KillSwitchError(
                f"Kill switch active for {rule_scope}: {reason or 'no reason given'}",
                details={"scope": rule_scope, "mode": mode, "action": action_description},
            )
        elif mode == "soft":
            log.warning("kill_switch: SOFT WARNING for %s (scope=%s, reason=%s)",
                        action_description, rule_scope, reason)


def activate(conn, scope: str = "global", mode: str = "hard",
             reason: str = "", actor: str = "system") -> dict:
    """Activate the kill switch for a scope."""
    now = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE workflow.kill_switch_rules
            SET is_active = TRUE, mode = %s, reason = %s,
                activated_by = %s, activated_at = %s
            WHERE scope = %s
            """,
            (mode, reason, actor, now, scope),
        )

        if cur.rowcount == 0:
            cur.execute(
                """
                INSERT INTO workflow.kill_switch_rules (scope, mode, is_active, activated_by, reason, activated_at)
                VALUES (%s, %s, TRUE, %s, %s, %s)
                """,
                (scope, mode, actor, reason, now),
            )

        # Audit log
        cur.execute(
            "INSERT INTO workflow.kill_switch_log (scope, action, actor, reason) VALUES (%s, %s, %s, %s)",
            (scope, "activated", actor, reason),
        )
    conn.commit()

    log.warning("kill_switch: ACTIVATED scope=%s mode=%s by=%s reason=%s", scope, mode, actor, reason)
    return {"scope": scope, "mode": mode, "active": True, "activated_at": now.isoformat()}


def deactivate(conn, scope: str = "global", actor: str = "system", reason: str = "") -> dict:
    """Deactivate the kill switch for a scope."""
    now = datetime.now(timezone.utc)

    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE workflow.kill_switch_rules
            SET is_active = FALSE, deactivated_at = %s
            WHERE scope = %s
            """,
            (now, scope),
        )

        cur.execute(
            "INSERT INTO workflow.kill_switch_log (scope, action, actor, reason) VALUES (%s, %s, %s, %s)",
            (scope, "deactivated", actor, reason),
        )
    conn.commit()

    log.info("kill_switch: DEACTIVATED scope=%s by=%s", scope, actor)
    return {"scope": scope, "active": False, "deactivated_at": now.isoformat()}


def get_status(conn) -> list[dict]:
    """Get all kill switch rules and their current status."""
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT scope, mode, is_active, activated_by, reason, activated_at, deactivated_at
            FROM workflow.kill_switch_rules
            ORDER BY scope
            """,
        )
        rows = cur.fetchall()

    return [
        {
            "scope": r[0], "mode": r[1], "is_active": r[2],
            "activated_by": r[3], "reason": r[4],
            "activated_at": r[5].isoformat() if r[5] else None,
            "deactivated_at": r[6].isoformat() if r[6] else None,
        }
        for r in rows
    ]

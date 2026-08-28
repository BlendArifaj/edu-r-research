from __future__ import annotations

import re

from sqlalchemy import Engine, event

from app.instrumentation.context import current_trace

_TABLE_RE = re.compile(
    r'\b(?:FROM|JOIN|INTO|UPDATE)\s+[`"\[]?([A-Za-z_][A-Za-z0-9_]*)',
    re.IGNORECASE,
)
_LISTENERS_INSTALLED = False


def _tables_from_sql(statement: str) -> list[str]:
    return [match.group(1) for match in _TABLE_RE.finditer(statement)]


def _before_cursor_execute(
    conn, cursor, statement, parameters, context, executemany
) -> None:
    trace = current_trace()
    if trace is None or not statement:
        return
    trace.add_sql(str(statement))
    for table in _tables_from_sql(str(statement)):
        trace.touch_entity(table)


def install_sql_listeners() -> None:
    global _LISTENERS_INSTALLED
    if _LISTENERS_INSTALLED:
        return
    event.listen(Engine, "before_cursor_execute", _before_cursor_execute)
    _LISTENERS_INSTALLED = True

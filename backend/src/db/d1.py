from typing import Any


def _to_py(obj: Any) -> Any:
    """Convert a Pyodide JsProxy to a native Python object.

    obj.to_py() in Pyodide/Workers is SYNCHRONOUS - it returns a dict directly.
    Do NOT await it.
    """
    if hasattr(obj, "to_py"):
        return obj.to_py()
    return obj


class D1:
    """Thin wrapper around the CF Workers D1 binding for Python Workers."""

    def __init__(self, binding: Any) -> None:
        self._binding = binding

    async def _run(self, sql: str, *params: Any) -> dict[str, Any]:
        stmt = self._binding.prepare(sql)
        if params:
            stmt = stmt.bind(*params)
        raw = await stmt.run()
        return _to_py(raw)

    async def query(self, sql: str, *params: Any) -> list[dict[str, Any]]:
        raw = await self._run(sql, *params)
        return raw.get("results", [])

    async def query_one(self, sql: str, *params: Any) -> dict[str, Any] | None:
        raw = await self._run(sql, *params)
        results = raw.get("results", [])
        return results[0] if results else None

    async def execute(self, sql: str, *params: Any) -> dict[str, Any]:
        raw = await self._run(sql, *params)
        return {"success": True, "meta": raw.get("meta")}

    async def batch(self, statements: list[tuple[str, list[Any]]]) -> list[Any]:
        prepared = [self._binding.prepare(sql).bind(*p) for sql, p in statements]
        raw = await self._binding.batch(prepared)
        return _to_py(raw)

from collections.abc import Sequence
from typing import Any


class D1Result:
    def __init__(self, raw: Any) -> None:
        self.raw = raw

    @property
    def success(self) -> bool:
        return getattr(self.raw, "success", False)

    @property
    def results(self) -> list[dict[str, Any]]:
        return getattr(self.raw, "results", [])

    @property
    def error(self) -> str | None:
        return getattr(self.raw, "error", None)


class D1:
    """Thin wrapper around the CF Workers D1 binding."""

    def __init__(self, binding: Any) -> None:
        self._binding = binding

    def query(self, sql: str, *params: Any) -> list[dict[str, Any]]:
        stmt = self._binding.prepare(sql)
        if params:
            stmt = stmt.bind(*params)
        result = D1Result(stmt.all())
        if not result.success:
            raise RuntimeError(f"D1 query failed: {result.error}")
        return result.results

    def query_one(self, sql: str, *params: Any) -> dict[str, Any] | None:
        stmt = self._binding.prepare(sql)
        if params:
            stmt = stmt.bind(*params)
        result = D1Result(stmt.first())
        if not result.success:
            raise RuntimeError(f"D1 query_one failed: {result.error}")
        return result.results

    def execute(self, sql: str, *params: Any) -> dict[str, Any]:
        stmt = self._binding.prepare(sql)
        if params:
            stmt = stmt.bind(*params)
        result = D1Result(stmt.run())
        if not result.success:
            raise RuntimeError(f"D1 execute failed: {result.error}")
        return {"success": True, "meta": getattr(result.raw, "meta", None)}

    def batch(self, statements: list[tuple[str, list[Any]]]) -> list[Any]:
        prepared = [self._binding.prepare(sql).bind(*p) for sql, p in statements]
        return self._binding.batch(prepared)

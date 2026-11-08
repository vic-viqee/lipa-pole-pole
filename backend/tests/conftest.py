import json
import sqlite3
import sys
import types
from pathlib import Path
from typing import Any

# --- Compatibility shims for Cloudflare Workers / Pyodide modules ---
if "workers" not in sys.modules:
    workers = types.ModuleType("workers")

    class _FakeHeaders:
        def __init__(self, headers=None):
            self._h = {}
            for k, v in (headers or {}).items():
                self._h[str(k).lower()] = str(v)

        def get(self, key, default=None):
            return self._h.get(str(key).lower(), default)

        def items(self):
            return list(self._h.items())

    class Response:
        def __init__(self, body="", status=200, headers=None):
            self._body = body if body is not None else ""
            self.status = status
            self.headers = _FakeHeaders(headers)

        @property
        def body(self):
            return self._body

        async def text(self):
            if isinstance(self._body, bytes):
                return self._body.decode("utf-8", errors="replace")
            return str(self._body)

        async def json(self):
            return json.loads(await self.text())

    class Request:
        def __init__(self, url, method="GET", headers=None, body=None):
            self.url = url
            self.method = method
            self.headers = _FakeHeaders(headers)
            self._body = body

        async def text(self):
            if self._body is None:
                return ""
            if isinstance(self._body, (dict, list)):
                return json.dumps(self._body)
            if isinstance(self._body, bytes):
                return self._body.decode("utf-8", errors="replace")
            return str(self._body)

    class WorkerEntrypoint:
        pass

    workers.Response = Response
    workers.Request = Request
    workers.WorkerEntrypoint = WorkerEntrypoint
    sys.modules["workers"] = workers

if "js" not in sys.modules:
    js = types.ModuleType("js")

    class Object:
        @staticmethod
        def fromEntries(entries):
            return dict(entries)

    async def fetch(*args, **kwargs):  # pragma: no cover - tests must mock
        raise RuntimeError("Real Daraja/network fetch called in tests; mock services.mpesa")

    class AbortError(Exception):
        pass

    class _AbortSignal:
        def __init__(self):
            self.aborted = False

        @staticmethod
        def timeout(ms):
            return _AbortSignal()

    class AbortController:
        def __init__(self):
            self.signal = _AbortSignal()

        @staticmethod
        def new():
            return AbortController()

        def abort(self):
            self.signal.aborted = True

    def setTimeout(fn, ms):  # noqa: N802 - JS-like API shim
        return 0

    js.Object = Object
    js.fetch = fetch
    js.AbortError = AbortError
    js.AbortController = AbortController
    js.AbortSignal = _AbortSignal
    js.setTimeout = setTimeout
    sys.modules["js"] = js

if "pyodide" not in sys.modules:
    pyodide = types.ModuleType("pyodide")
    ffi = types.ModuleType("pyodide.ffi")

    def to_js(obj, dict_converter=None):
        return obj

    ffi.to_js = to_js
    pyodide.ffi = ffi
    sys.modules["pyodide"] = pyodide
    sys.modules["pyodide.ffi"] = ffi

# Ensure backend/src is importable
SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def _split_sql_statements(sql: str) -> list[str]:
    # Schema/migrations here are simple semicolon-terminated statements.
    parts = []
    buff = []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        buff.append(line)
        if stripped.endswith(";"):
            stmt = "\n".join(buff).strip()
            if stmt:
                parts.append(stmt)
            buff = []
    if buff:
        stmt = "\n".join(buff).strip()
        if stmt:
            parts.append(stmt)
    return parts


class SQLiteD1Result:
    def __init__(self, conn: sqlite3.Connection, cursor: sqlite3.Cursor):
        self._conn = conn
        self._cursor = cursor

    @property
    def results(self):
        if self._cursor.description is None:
            return []
        cols = [c[0] for c in self._cursor.description]
        return [dict(zip(cols, row)) for row in self._cursor.fetchall()]

    @property
    def meta(self):
        return {
            "changes": self._cursor.rowcount if self._cursor.rowcount is not None else 0,
            "last_row_id": self._cursor.lastrowid,
        }


class SQLiteD1Statement:
    def __init__(self, conn: sqlite3.Connection, sql: str, params=None):
        self._conn = conn
        self._sql = sql
        self._params = list(params or [])

    def bind(self, *params):
        return SQLiteD1Statement(self._conn, self._sql, list(params))

    async def run(self):
        cur = self._conn.execute(self._sql, self._params)
        self._conn.commit()
        result = SQLiteD1Result(self._conn, cur)
        return {"results": result.results, "meta": result.meta}


class SQLiteD1Database:
    """Minimal D1-like binding backed by in-memory SQLite for tests."""

    def __init__(self, conn: sqlite3.Connection):
        self._conn = conn

    def prepare(self, sql: str):
        return SQLiteD1Statement(self._conn, sql)

    async def batch(self, statements):
        results = []
        try:
            self._conn.execute("BEGIN")
            for stmt in statements:
                if isinstance(stmt, tuple):
                    sql, params = stmt
                    cur = self._conn.execute(sql, params)
                else:
                    raw = await stmt.run()  # pragma: no cover
                    results.append(raw)
                    continue
                res = SQLiteD1Result(self._conn, cur)
                results.append({"results": res.results, "meta": res.meta})
            self._conn.commit()
        except Exception:
            self._conn.rollback()
            raise
        return results


def make_test_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    schema = (SRC / "db" / "schema.sql").read_text(encoding="utf-8")
    for stmt in _split_sql_statements(schema):
        conn.execute(stmt)
    conn.commit()
    return conn


def make_env(db_conn: sqlite3.Connection, **overrides) -> dict[str, Any]:
    env = {
        "DB": SQLiteD1Database(db_conn),
        "SECRET_KEY": "test-secret-key",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
        "MPESA_CONSUMER_KEY": "test-key",
        "MPESA_CONSUMER_SECRET": "test-secret",
        "MPESA_SHORTCODE": "174379",
        "MPESA_PASSKEY": "test-passkey",
        "MPESA_CALLBACK_URL": "https://example.test/callback",
        "ENVIRONMENT": "test",
        "FRONTEND_URL": "http://localhost:5173",
    }
    env.update(overrides)
    return env


class FakeRequest:
    def __init__(self, url: str, method: str = "GET", headers=None, body=None):
        self.url = url
        self.method = method
        self.headers = headers or {}
        self._body = body

    async def text(self):
        if self._body is None:
            return ""
        if isinstance(self._body, (dict, list)):
            return json.dumps(self._body)
        return str(self._body)


async def app_request(env, method: str, path: str, *, body=None, headers=None):
    from app import handle_request
    from core.router import HTTPException, json_response
    from workers import Response as WorkersResponse  # shimmed

    req = FakeRequest(f"https://test.local{path}", method=method, headers=headers, body=body)
    try:
        resp = await handle_request(req, env)
    except HTTPException as e:
        resp = json_response({"detail": e.detail}, status=e.status_code)
    except ValueError as e:
        resp = json_response({"detail": str(e)}, status=400)
    except Exception as e:
        resp = json_response({"detail": "Internal server error"}, status=500)
    text = await resp.text()
    try:
        data = json.loads(text) if text else None
    except Exception:
        data = text
    status = getattr(resp, "status", 200)
    return status, data

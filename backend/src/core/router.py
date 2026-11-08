import json
import re
from typing import Any, Callable

from workers import Response


class HTTPException(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail


def json_response(data: Any, status: int = 200, *, origin: str | None = None) -> Response:
    return Response(
        json.dumps(data),
        status=status,
        headers={"Content-Type": "application/json", **_cors_headers(origin)},
    )


def html_response(content: str, status: int = 200, *, origin: str | None = None) -> Response:
    return Response(
        content,
        status=status,
        headers={"Content-Type": "text/html; charset=utf-8", **_cors_headers(origin)},
    )


_PARAM_RE = re.compile(r"\{(\w+)\}")


def _compile_path(path: str) -> tuple[str, re.Pattern]:
    params = _PARAM_RE.findall(path)
    regex_str = "^" + _PARAM_RE.sub(r"([^/]+)", path) + "$"
    return params, re.compile(regex_str)


def _allowed_origin(request_origin: str | None) -> str | None:
    if not request_origin:
        return None
    try:
        from core.config import get_settings

        allowed = get_settings().get("ALLOWED_ORIGINS") or []
    except Exception:
        allowed = []
    origin = request_origin.rstrip("/")
    for item in allowed:
        if str(item).rstrip("/") == origin:
            return request_origin
    return None


def _cors_headers(request_origin: str | None = None) -> dict[str, str]:
    headers = {
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Vary": "Origin",
    }
    allow = _allowed_origin(request_origin)
    if allow:
        headers["Access-Control-Allow-Origin"] = allow
    return headers


class Router:
    def __init__(self, prefix: str = ""):
        self._routes: list[tuple[str, str, Callable]] = []
        self.prefix = prefix

    def _full_path(self, path: str) -> str:
        return (self.prefix.rstrip("/") + "/" + path.lstrip("/")).rstrip("/")

    def get(self, path: str):
        def decorator(handler: Callable) -> Callable:
            full = self._full_path(path)
            self._routes.append(("GET", full, handler))
            return handler
        return decorator

    def post(self, path: str):
        def decorator(handler: Callable) -> Callable:
            full = self._full_path(path)
            self._routes.append(("POST", full, handler))
            return handler
        return decorator

    @property
    def routes(self) -> list[tuple[str, str, Callable]]:
        return self._routes


def match_route(
    method: str, path: str, routes: list[tuple[str, str, Callable]]
) -> tuple[Callable, dict[str, str]] | None:
    for m, pattern, handler in routes:
        if m != method:
            continue
        params, regex = _compile_path(pattern)
        m = regex.match(path)
        if m:
            return handler, dict(zip(params, m.groups()))
    return None


async def parse_json_body(request) -> dict[str, Any]:
    text = await request.text()
    return json.loads(text)

from typing import Any, Callable
from urllib.parse import urlparse

from api.v1 import auth, customers, og, payments, plans
from core.config import init_settings
from core.router import HTTPException, json_response, match_route


async def handle_request(request, env: dict[str, Any]):
    init_settings(env)

    path = urlparse(str(request.url)).path.rstrip("/") or "/"
    method = str(request.method).upper()
    origin = request.headers.get("Origin") if hasattr(request, "headers") else None

    try:
        route = match_route(method, path, ALL_ROUTES)
        if route:
            handler, path_params = route
            return await handler(request, env, path_params)

        assets = env.get("ASSETS")
        if assets and not path.startswith("/api/"):
            return await assets.fetch(request)

        return json_response({"detail": "Not Found"}, status=404, origin=origin)
    except HTTPException as e:
        return json_response({"detail": e.detail}, status=e.status_code, origin=origin)
    except ValueError as e:
        return json_response({"detail": str(e)}, status=400, origin=origin)
    except Exception as e:
        print(f"[app_error] type={type(e).__name__} path={path}")
        return json_response({"detail": "Internal server error"}, status=500, origin=origin)



async def _root(_request, _env, _params):
    return json_response({"message": "Lipa Polepole API is running"})


ALL_ROUTES: list[tuple[str, str, Callable]] = [("GET", "/", _root)]
ALL_ROUTES.extend(auth.router.routes)
ALL_ROUTES.extend(customers.router.routes)
ALL_ROUTES.extend(plans.router.routes)
ALL_ROUTES.extend(payments.router.routes)
ALL_ROUTES.extend(og.router.routes)

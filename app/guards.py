import json

from starlette.types import ASGIApp, Message, Receive, Scope, Send

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; "
    "object-src 'none'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
)
SECURITY_HEADERS = {
    b"content-security-policy": CSP.encode(),
    b"x-content-type-options": b"nosniff",
    b"x-frame-options": b"DENY",
    b"referrer-policy": b"no-referrer",
    b"permissions-policy": b"camera=(), microphone=(), geolocation=(), payment=()",
    b"cross-origin-opener-policy": b"same-origin",
    b"cross-origin-resource-policy": b"same-origin",
}
NO_STORE = {b"cache-control": b"no-store"}


class PayloadTooLarge(Exception):
    pass


def limit_for(path: str, upload_limit: int, json_limit: int) -> int:
    return upload_limit if path == "/api/extract" else json_limit


async def reject_large_payload(scope: Scope, receive: Receive, send: Send) -> None:
    body = json.dumps(
        {"detail": {"code": "payload_too_large", "message": "La solicitud es demasiado grande. Subí solo el programa de la materia."}}
    ).encode()
    headers = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode())]
    await send({"type": "http.response.start", "status": 413, "headers": headers})
    await send({"type": "http.response.body", "body": body})


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self._app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        extra = dict(SECURITY_HEADERS)
        if scope["path"].startswith("/api/"):
            extra.update(NO_STORE)

        async def with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                present = {name.lower() for name, _ in message["headers"]}
                message["headers"] = [*message["headers"], *((k, v) for k, v in extra.items() if k not in present)]
            await send(message)

        await self._app(scope, receive, with_headers)


class BodyLimitMiddleware:
    def __init__(self, app: ASGIApp, upload_limit: int, json_limit: int) -> None:
        self._app = app
        self._upload_limit = upload_limit
        self._json_limit = json_limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self._app(scope, receive, send)
            return
        limit = limit_for(scope["path"], self._upload_limit, self._json_limit)
        declared = dict(scope["headers"]).get(b"content-length", b"0")
        if declared.isdigit() and int(declared) > limit:
            await reject_large_payload(scope, receive, send)
            return
        await self._guarded(scope, receive, send, limit)

    async def _guarded(self, scope: Scope, receive: Receive, send: Send, limit: int) -> None:
        received = 0
        started = False

        async def counting() -> Message:
            nonlocal received
            message = await receive()
            if message["type"] == "http.request":
                received += len(message.get("body", b""))
                if received > limit:
                    raise PayloadTooLarge()
            return message

        async def tracking(message: Message) -> None:
            nonlocal started
            started = started or message["type"] == "http.response.start"
            await send(message)

        try:
            await self._app(scope, counting, tracking)
        except PayloadTooLarge:
            if not started:
                await reject_large_payload(scope, receive, send)

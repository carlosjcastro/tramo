from fastapi import Request

from app.config import settings

UNKNOWN = "unknown"


def client_ip(request: Request) -> str:
    if settings.trust_proxy:
        forwarded = request.headers.get("x-forwarded-for", "")
        last = forwarded.split(",")[-1].strip()
        if last:
            return last
    return request.client.host if request.client else UNKNOWN

"""app/utils/client_ip.py"""

from fastapi import Request


def get_client_ip(request: Request) -> str:
    # 安全（§4.9）：仅在 TRUST_PROXY 开启（可信反向代理后）时才采信 X-Forwarded-For；
    # 否则一律用真实连接地址，避免直连后端伪造该头绕过限流/黑名单。
    try:
        from app.config.settings import get_settings

        trust_proxy = get_settings().TRUST_PROXY
    except Exception:
        trust_proxy = False

    if trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"
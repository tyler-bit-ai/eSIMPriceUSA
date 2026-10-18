from __future__ import annotations

import sys
from abc import ABC, abstractmethod

from app.models import ProductDetail, ProductStub

# `python -m app crawl` exits with this code when the site served a bot-check/throttle page.
BLOCKED_EXIT_CODE = 3
# Amazon's robot-check page carries this contact comment; its throttle page is an HTTP 503.
AMAZON_BLOCK_MARKERS = ("api-services-support@amazon.com", "/errors/validateCaptcha")
BLOCK_STATUSES = (403, 429, 503)

_UA_PLATFORM = {
    "darwin": "Macintosh; Intel Mac OS X 10_15_7",  # Chrome reports this frozen string on every Mac
    "win32": "Windows NT 10.0; Win64; x64",
}


def desktop_user_agent(browser_version: str) -> str:
    """User-Agent matching the real OS and Chromium major version (as Chrome's reduced UA does).

    A hardcoded "Windows Chrome 123" contradicted the client hints and navigator.platform the
    browser still sends. Only the "Headless" token is left out: amazon.com answers that UA with
    an immediate 503. Nothing else is masked (no stealth patches, see AGENTS.md).
    """
    platform = _UA_PLATFORM.get(sys.platform, "X11; Linux x86_64")
    major = browser_version.split(".")[0]
    return f"Mozilla/5.0 ({platform}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{major}.0.0.0 Safari/537.36"


class SiteBlockedError(RuntimeError):
    """The site answered with a bot-check or throttle page.

    Never retried and never bypassed (AGENTS.md): the crawl stops and reports it instead.
    """


def block_reason(status: int | None, html: str, markers: tuple[str, ...] = ()) -> str | None:
    if status in BLOCK_STATUSES:
        return f"http_{status}"
    for marker in markers:
        if marker in html:
            return f"bot_check_page ({marker})"
    return None


class MarketplaceAdapter(ABC):
    name: str

    @abstractmethod
    async def search(self, query: str, limit: int) -> list[ProductStub]:
        raise NotImplementedError

    @abstractmethod
    async def fetch_detail(self, stub: ProductStub) -> ProductDetail:
        raise NotImplementedError

    @abstractmethod
    async def close(self) -> None:
        raise NotImplementedError

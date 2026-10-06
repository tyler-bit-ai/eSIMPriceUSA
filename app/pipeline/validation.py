from __future__ import annotations

import re

from app.models import InvalidItem, ProductDetail, ProductStub

# Keep in sync with dashboard/travel-filter.js (tests/test_travel_filter.py checks parity).
# Covers what Amazon US returns for "eSIM <country>" besides travel data plans.
# re.ASCII keeps the \b semantics identical to the JS version.
_FLAGS = re.IGNORECASE | re.ASCII
# A title naming other regions is a multi-country travel plan even if it also says "USA".
_MULTI_REGION = re.compile(
    r"worldwide|global|asia|europe|\d+\+? countries|china|hong kong|macau|taiwan|japan|korea|thai|vietnam",
    _FLAGS,
)
_RULES = (
    # (name, pattern, skipped_when_multi_region)
    (
        "us_domestic_plan",
        re.compile(r"T-?Mobile|AT&T|Verizon|Jethro Mobile|\bUSA\b|US Mainland|\bHawaii\b", _FLAGS),
        True,
    ),
    ("esim_hardware", re.compile(r"\badapter\b|\breader\b|physical (nano )?esim card|\bSTK\b", _FLAGS), False),
    (
        "iot_sim",
        re.compile(r"\btracker\b|(trail|game|security) cameras?|\bGPS\b|\bIoT\b|dash ?cam", _FLAGS),
        False,
    ),
)
_SIM_WORD = re.compile(r"sim|roaming|data", _FLAGS)


def non_travel_reason(title: str | None) -> str | None:
    """Why this listing is not a travel eSIM/SIM data plan, or None if it looks like one."""
    if not title or not title.strip():
        return "missing_title"
    for name, pattern, skip_if_multi_region in _RULES:
        if skip_if_multi_region and _MULTI_REGION.search(title):
            continue
        m = pattern.search(title)
        if m:
            return f"{name}:{m.group(0)}"
    if not _SIM_WORD.search(title):
        return "no_sim_keyword_in_title"
    return None


def validate_product(detail: ProductDetail, stub: ProductStub) -> InvalidItem | None:
    reason = non_travel_reason(detail.title)
    if reason:
        invalid = _to_invalid(detail, stub, reason="non_travel_product")
        invalid.evidence = {**invalid.evidence, "non_travel": [reason]}
        return invalid
    price = detail.price_usd
    if price is None:
        return _to_invalid(
            detail,
            stub,
            reason="missing_price",
        )
    if price <= 0:
        return _to_invalid(
            detail,
            stub,
            reason="non_positive_price",
        )
    return None


def _to_invalid(detail: ProductDetail, stub: ProductStub, reason: str) -> InvalidItem:
    raw_price_texts = []
    raw_price_texts.extend(detail.evidence.get("price_usd", []))
    raw_price_texts.extend(detail.evidence.get("non_usd_price", []))
    if stub.search_price_text:
        raw_price_texts.append(f"search_price: {stub.search_price_text}")

    return InvalidItem(
        site=detail.site or stub.site,
        country=detail.country or stub.country,
        product_url=str(detail.product_url),
        asin=detail.asin or stub.asin,
        site_product_id=detail.site_product_id or stub.site_product_id,
        title=detail.title,
        price_usd=detail.price_usd,
        search_price_usd=stub.search_price_usd,
        invalid_reason=reason,
        raw_price_texts=raw_price_texts[:10],
        evidence=detail.evidence,
    )

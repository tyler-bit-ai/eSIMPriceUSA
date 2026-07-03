from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, HttpUrl


class NetworkType(str, Enum):
    local = "local"
    roaming = "roaming"
    unknown = "unknown"


class NetworkGeneration(str, Enum):
    five_g_capable = "5g_capable"
    lte_4g_only = "lte_4g_only"
    unknown = "unknown"


class ProductStub(BaseModel):
    site: str | None = None
    country: str | None = None
    product_url: HttpUrl
    asin: str | None = None
    site_product_id: str | None = None
    search_position: int | None = None
    search_price_usd: float | None = None
    search_price_text: str | None = None
    search_review_count: int | None = None
    search_seller: str | None = None
    search_seller_badge: str | None = None
    search_monthly_sold_count: int | None = None
    search_is_bestseller: bool | None = None


class ProductDetail(BaseModel):
    site: str | None = None
    country: str | None = None
    title: str | None = None
    price_usd: float | None = None
    review_count: int | None = None
    seller_badge: str | None = None
    search_position: int | None = None
    monthly_sold_count: int | None = None
    is_bestseller: bool | None = None
    bestseller_rank: int | None = None
    validity: str | None = None
    usage_validity: str | None = None
    activation_validity: str | None = None
    network_type: NetworkType = NetworkType.unknown
    network_generation: NetworkGeneration = NetworkGeneration.unknown
    carrier_support_local: dict[str, bool | None] = Field(default_factory=dict)
    data_amount: str | None = None
    product_url: HttpUrl
    asin: str | None = None
    site_product_id: str | None = None
    seller: str | None = None
    brand: str | None = None
    evidence: dict[str, list[str]] = Field(default_factory=dict)


class InvalidItem(BaseModel):
    site: str | None = None
    country: str | None = None
    product_url: str
    asin: str | None = None
    site_product_id: str | None = None
    title: str | None = None
    price_usd: float | None = None
    search_price_usd: float | None = None
    invalid_reason: str
    raw_price_texts: list[str] = Field(default_factory=list)
    evidence: dict[str, list[str]] = Field(default_factory=dict)


class CrawlError(BaseModel):
    site: str | None = None
    country: str | None = None
    product_url: str
    asin: str | None = None
    error_type: str
    error_message: str
    status_code: int | None = None
    screenshot_path: str | None = None


class CrawlResult(BaseModel):
    items: list[ProductDetail]
    invalid_items: list[InvalidItem]
    failures: list[CrawlError]


def model_to_row(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")

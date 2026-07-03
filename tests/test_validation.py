from app.models import ProductDetail, ProductStub
from app.pipeline.validation import validate_product


def test_validate_product_rejects_missing_price():
    detail = ProductDetail(
        site="amazon_us",
        country="kr",
        title="sample",
        price_usd=None,
        product_url="https://www.amazon.com/dp/B000000001",
        asin="B000000001",
        evidence={"price_usd": ["no_usd_price_found_in_primary_selectors"]},
    )
    stub = ProductStub(
        site="amazon_us",
        country="kr",
        product_url="https://www.amazon.com/dp/B000000001",
        asin="B000000001",
        search_price_usd=None,
    )

    invalid = validate_product(detail, stub)

    assert invalid is not None
    assert invalid.invalid_reason == "missing_price"
    assert invalid.country == "kr"


def test_validate_product_rejects_non_positive_price():
    detail = ProductDetail(
        site="amazon_us",
        country="vn",
        title="sample",
        price_usd=0,
        product_url="https://www.amazon.com/dp/B000000002",
        asin="B000000002",
        evidence={"price_usd": ["$0.00 placeholder"]},
    )
    stub = ProductStub(
        site="amazon_us",
        country="vn",
        product_url="https://www.amazon.com/dp/B000000002",
        asin="B000000002",
        search_price_usd=0,
        search_price_text="$0.00",
    )

    invalid = validate_product(detail, stub)

    assert invalid is not None
    assert invalid.invalid_reason == "non_positive_price"
    assert invalid.raw_price_texts[0] == "$0.00 placeholder"
    assert invalid.country == "vn"

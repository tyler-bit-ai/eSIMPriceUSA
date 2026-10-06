from app.models import ProductDetail, ProductStub
from app.pipeline.validation import validate_product


def test_validate_product_rejects_missing_price():
    detail = ProductDetail(
        site="amazon_us",
        country="kr",
        title="sample eSIM",
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
        title="sample eSIM",
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


def _detail(title):
    return ProductDetail(
        site="amazon_us",
        country="jp",
        title=title,
        price_usd=24.99,
        product_url="https://www.amazon.com/dp/B000000003",
        asin="B000000003",
    )


def _stub():
    return ProductStub(site="amazon_us", country="jp", product_url="https://www.amazon.com/dp/B000000003")


def test_validate_product_rejects_us_domestic_plan():
    invalid = validate_product(_detail("USA Prepaid eSIM (T-Mobile Network) | Unlimited 5G Data in USA"), _stub())

    assert invalid is not None
    assert invalid.invalid_reason == "non_travel_product"
    assert invalid.evidence["non_travel"][0].startswith("us_domestic_plan:")


def test_validate_product_rejects_esim_hardware_and_iot_sim():
    adapter = validate_product(_detail("V0 eSIM Card for Unlocked Android - SIM to eSIM Adapter"), _stub())
    tracker = validate_product(_detail("Mobile Tracker SIM Card, 5G/4G LTE Data Only Sim Card"), _stub())

    assert adapter.evidence["non_travel"][0].startswith("esim_hardware:")
    assert tracker.evidence["non_travel"][0].startswith("iot_sim:")


def test_validate_product_rejects_missing_title_and_unrelated_listing():
    assert validate_product(_detail(None), _stub()).evidence["non_travel"] == ["missing_title"]
    assert validate_product(_detail("  "), _stub()).evidence["non_travel"] == ["missing_title"]
    assert validate_product(_detail("Organic Maca Root Liquid Drops"), _stub()).evidence["non_travel"] == [
        "no_sim_keyword_in_title"
    ]


def test_validate_product_keeps_multi_country_plan_that_mentions_usa():
    title = "Free Test 150MB 1Day in USA | Happy China, Hong Kong, Macau 30Days Unlimited Data Sim Card"
    assert validate_product(_detail(title), _stub()) is None

from app.extractors.heuristics import (
    extract_bestseller_badge,
    extract_bestseller_rank,
    extract_carrier_support_for_country,
    extract_carrier_support_local,
    extract_data_amount,
    extract_monthly_sold_count,
    extract_network_generation,
    extract_network_type,
    extract_price_usd_with_evidence,
    extract_review_count,
    extract_validity,
    extract_validity_split,
    parse_price_text,
)
from app.models import NetworkGeneration, NetworkType


def test_parse_price_text_krw():
    amount, currency = parse_price_text("KRW14,210")
    assert amount == 14210
    assert currency == "KRW"


def test_parse_price_text_usd_suffix():
    amount, currency = parse_price_text("Price: $10.99")
    assert amount == 10.99
    assert currency == "USD"


def test_extract_price_usd_with_non_usd_evidence():
    value, non_usd = extract_price_usd_with_evidence(["KRW14,210"], assume_usd_on_unknown_currency=True)
    assert value.value is None
    assert non_usd


def test_extract_price_usd_with_evidence_finds_dollar_amount():
    value, non_usd = extract_price_usd_with_evidence(["Now only $12.99 tax included"])
    assert value.value == 12.99
    assert not non_usd


def test_extract_validity_days():
    res = extract_validity(["Usage period: valid for 30 days"])
    assert res.value == "30일"


def test_extract_validity_data_until_used():
    res = extract_validity(["Usable until data is used"])
    assert res.value == "GB used up" or res.value == "until data is used"


def test_extract_validity_split_usage_and_activation():
    res = extract_validity_split(
        ["Usage period 3 days / must be activated within 30 days of receipt"]
    )
    assert res.usage_validity == "3일"
    assert res.activation_validity == "30일"


def test_extract_validity_split_hours_to_days():
    res = extract_validity_split(["Korea eSIM 72 hours unlimited / expires in 90 days"])
    assert res.usage_validity == "3일"
    assert res.activation_validity == "90일"


def test_extract_validity_split_title_priority():
    res = extract_validity_split(
        [
            "[Korea eSIM] 1 day 500MB/day",
            "Expires 180 days from purchase date",
            "24/7 support",
        ]
    )
    assert res.usage_validity == "1일"
    assert res.activation_validity == "180일"


def test_extract_network_type_roaming():
    net, _ = extract_network_type(["International roaming supported eSIM"])
    assert net == NetworkType.roaming


def test_extract_network_type_local():
    net, _ = extract_network_type(["Korea local network local carrier"])
    assert net == NetworkType.local


def test_extract_network_type_avoid_roaming_center_false_positive():
    net, _ = extract_network_type(["Local airport support (SKTelecom roaming center)"])
    assert net == NetworkType.unknown


def test_extract_network_type_negated_roaming():
    net, _ = extract_network_type(["This plan is roaming-free"])
    assert net == NetworkType.unknown


def test_extract_network_type_conflicting_signals():
    net, _ = extract_network_type(["local network supported, but international roaming setup required"])
    assert net == NetworkType.unknown


def test_extract_network_type_phone_number_is_local():
    net, _ = extract_network_type(["Korea eSIM with local phone number talk/sms included"])
    assert net == NetworkType.local


def test_extract_network_generation_4g_5g_capable():
    gen, evidence = extract_network_generation(["Korea eSIM 4G/5G supported data only"])
    assert gen == NetworkGeneration.five_g_capable
    assert evidence


def test_extract_network_generation_lte_4g_only():
    gen, evidence = extract_network_generation(["Korea SIM 4G/LTE supported with phone number"])
    assert gen == NetworkGeneration.lte_4g_only
    assert evidence


def test_extract_network_generation_unknown_for_speed_only():
    gen, evidence = extract_network_generation(["Korea eSIM ultra high speed data unlimited"])
    assert gen == NetworkGeneration.unknown
    assert evidence == ["no_lte_4g_or_5g_keyword_matched"]


def test_extract_network_generation_ignores_fallback_only_5g():
    gen, evidence = extract_network_generation(
        ["Korea SIM 3 days unlimited"],
        ["Related product: Korea eSIM 5G supported"],
    )
    assert gen == NetworkGeneration.unknown
    assert any("fallback_only" in item for item in evidence)


def test_extract_network_generation_conflict_uses_unknown():
    gen, evidence = extract_network_generation(
        ["Korea SIM 4G/LTE supported"],
        ["Related product: Korea eSIM 5G supported"],
    )
    assert gen == NetworkGeneration.unknown
    assert any("conflicts" in item for item in evidence)


def test_extract_network_generation_cellular_technology_lte_overrides_title_5g():
    gen, evidence = extract_network_generation(
        [
            "source:title: Hong Kong eSIM 5G supported high speed",
            "source:product_info_cellular: Cellular Technology LTE",
        ],
        [],
    )
    assert gen == NetworkGeneration.lte_4g_only
    assert any("product_info_cellular_4g_lte" in item for item in evidence)


def test_extract_network_generation_transmission_speed_overrides_title_4g():
    gen, evidence = extract_network_generation(
        [
            "source:title: Hong Kong eSIM 4G/LTE supported",
            "source:product_info_transmission: Transmission speed: 5G/4G high speed",
        ],
        [],
    )
    assert gen == NetworkGeneration.five_g_capable
    assert any("product_info_transmission_5g" in item for item in evidence)


def test_extract_carrier_support_local_for_vietnam():
    carriers, evidence = extract_carrier_support_local(
        ["Vietnam eSIM Viettel / MobiFone supported"],
        country="vn",
    )
    assert carriers["viettel"] is True
    assert carriers["mobifone"] is True
    assert carriers["vinaphone"] is None
    assert evidence


def test_extract_carrier_support_local_for_hong_kong():
    carriers, evidence = extract_carrier_support_local(
        ["Hong Kong travel eSIM CMHK 3HK SmarTone supported"],
        country="hk",
    )
    assert carriers["cmhk"] is True
    assert carriers["three_hk"] is True
    assert carriers["smartone"] is True
    assert evidence


def test_extract_carrier_support_local_for_japan():
    carriers, evidence = extract_carrier_support_local(
        ["Japan eSIM docomo au SoftBank Rakuten Mobile supported"],
        country="jp",
    )
    assert carriers["docomo"] is True
    assert carriers["au"] is True
    assert carriers["softbank"] is True
    assert carriers["rakuten"] is True
    assert evidence


def test_extract_carrier_support_for_country_delegates_to_local():
    local_support, evidence = extract_carrier_support_for_country(
        ["Vietnam eSIM Viettel supported"],
        country="vn",
    )
    assert local_support["viettel"] is True
    assert evidence


def test_extract_data_amount():
    res = extract_data_amount(["3GB / 7 days"])
    assert res.value == "3GB"


def test_extract_data_amount_unlimited():
    res = extract_data_amount(["high speed data unlimited"])
    assert res.value == "unlimited"


def test_extract_data_amount_daily_gb():
    res = extract_data_amount(["Korea eSIM 1GB/day 3 days"])
    assert res.value == "1GB/day"


def test_extract_data_amount_daily_mb():
    res = extract_data_amount(["500MB per day available"])
    assert res.value == "500MB/day"


def test_extract_monthly_sold_count():
    res = extract_monthly_sold_count(["4,000+ bought in past month"])
    assert res.value == 4000


def test_extract_bestseller_badge():
    res = extract_bestseller_badge(["Best Seller"])
    assert res.value is True


def test_extract_bestseller_rank():
    res = extract_bestseller_rank(["Best Sellers Rank: #28 in Electronics"])
    assert res.value == 28


def test_extract_review_count_amazon_en():
    res = extract_review_count(["1,234 ratings"])
    assert res.value == 1234


def test_extract_review_count_ignores_star_rating():
    res = extract_review_count(["4.5 out of 5 stars"])
    assert res.value is None

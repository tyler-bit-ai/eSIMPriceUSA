from app.countries import COUNTRY_REGISTRY, get_dashboard_countries, get_default_query


def test_country_registry_exposes_all_target_countries():
    assert set(COUNTRY_REGISTRY) == {"kr", "vn", "th", "tw", "hk", "mo", "jp"}


def test_dashboard_country_list_includes_thailand():
    assert get_dashboard_countries() == ["kr", "vn", "th", "tw", "hk", "mo", "jp"]
    assert COUNTRY_REGISTRY["th"].crawl_enabled is True
    assert COUNTRY_REGISTRY["th"].dashboard_enabled is True


def test_default_query_uses_country_mapping():
    assert get_default_query(site="amazon_us", country="kr") == "eSIM Korea"
    assert get_default_query(site="amazon_us", country="vn") == "eSIM Vietnam"
    assert get_default_query(site="amazon_us", country="jp") == "eSIM Japan"

from bs4 import BeautifulSoup

from app.adapters.amazon_us import AmazonUSAdapter
from app.extractors.heuristics import extract_network_generation, extract_review_count
from app.models import NetworkGeneration


def test_amazon_search_card_extracts_review_count():
    html = """
    <div data-component-type="s-search-result" data-asin="B000000001">
      <h2><a href="/dp/B000000001">sample</a></h2>
      <span class="a-price"><span class="a-offscreen">$19.80</span></span>
      <span aria-label="1,234 ratings"></span>
    </div>
    """
    adapter = object.__new__(AmazonUSAdapter)
    card = BeautifulSoup(html, "lxml").select_one("div[data-component-type='s-search-result']")

    text = adapter._extract_text_selectors(
        card,
        [
            "span[aria-label*='ratings']",
            "span.a-size-base.s-underline-text",
            "a.a-link-normal span.a-size-base",
        ],
    )
    extracted = extract_review_count([text or "", card.get_text(" ", strip=True)])

    assert extracted.value == 1234


def test_amazon_collect_review_count_candidates():
    html = """
    <html>
      <body>
        <span id="acrCustomerReviewText">843 ratings</span>
      </body>
    </html>
    """
    adapter = object.__new__(AmazonUSAdapter)
    soup = BeautifulSoup(html, "lxml")

    candidates = adapter._collect_review_count_candidates(soup, ["fallback"])

    assert candidates[0] == "843 ratings"


def test_amazon_extract_review_count_value_from_parentheses():
    adapter = object.__new__(AmazonUSAdapter)
    extracted = adapter._extract_review_count_value(["(279)"])
    assert extracted.value == 279


def test_amazon_extract_review_count_value_from_json_ld():
    adapter = object.__new__(AmazonUSAdapter)
    extracted = adapter._extract_review_count_value(['{"reviewCount":"512","ratingValue":"4.5"}'])
    assert extracted.value == 512


def test_amazon_extract_carrier_support_local_for_non_kr_country():
    adapter = object.__new__(AmazonUSAdapter)

    local_support, evidence = adapter._extract_carrier_support(
        ["Vietnam eSIM Viettel MobiFone supported"],
        country="vn",
    )

    assert local_support["viettel"] is True
    assert local_support["mobifone"] is True
    assert evidence


def test_amazon_extract_carrier_support_for_kr_country():
    adapter = object.__new__(AmazonUSAdapter)

    local_support, evidence = adapter._extract_carrier_support(
        ["Korea eSIM supported SKT KT LG U+"],
        country="kr",
    )

    assert local_support["skt"] is True
    assert local_support["kt"] is True
    assert local_support["lgu"] is True
    assert evidence


def test_amazon_collect_network_generation_texts_uses_source_prefixes():
    html = """
    <html>
      <body>
        <div id="feature-bullets">
          <ul><li>SKT carrier 5G supported data only</li></ul>
        </div>
        <div id="comparison">Related product 4G/LTE supported</div>
      </body>
    </html>
    """
    adapter = object.__new__(AmazonUSAdapter)
    soup = BeautifulSoup(html, "lxml")

    strong, fallback = adapter._collect_network_generation_texts(soup, "Korea eSIM")
    generation, evidence = extract_network_generation(strong, fallback)

    assert generation == NetworkGeneration.five_g_capable
    assert any(item.startswith("product_detail_5g: source:feature_bullets") for item in evidence)


def test_amazon_collect_network_generation_texts_prioritizes_product_information():
    html = """
    <html>
      <body>
        <span id="productTitle">Hong Kong eSIM 5G supported high speed</span>
        <table id="productDetails_techSpec_section_1">
          <tr><th>Cellular Technology</th><td>LTE</td></tr>
        </table>
      </body>
    </html>
    """
    adapter = object.__new__(AmazonUSAdapter)
    soup = BeautifulSoup(html, "lxml")

    title = adapter._extract_text_selectors(soup, ["#productTitle"])
    strong, fallback = adapter._collect_network_generation_texts(soup, title)
    generation, evidence = extract_network_generation(strong, fallback)

    assert generation == NetworkGeneration.lte_4g_only
    assert any(item.startswith("product_info_cellular_4g_lte") for item in evidence)


def test_amazon_collect_network_generation_texts_reads_transmission_speed():
    html = """
    <html>
      <body>
        <span id="productTitle">Hong Kong eSIM 4G/LTE supported</span>
        <table id="productDetails_techSpec_section_1">
          <tr><th>Transmission speed</th><td>5G/4G high speed</td></tr>
        </table>
      </body>
    </html>
    """
    adapter = object.__new__(AmazonUSAdapter)
    soup = BeautifulSoup(html, "lxml")

    title = adapter._extract_text_selectors(soup, ["#productTitle"])
    strong, fallback = adapter._collect_network_generation_texts(soup, title)
    generation, evidence = extract_network_generation(strong, fallback)

    assert generation == NetworkGeneration.five_g_capable
    assert any(item.startswith("product_info_transmission_5g") for item in evidence)

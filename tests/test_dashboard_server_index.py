import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run_node(script: str) -> str:
    completed = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip()


def test_dashboard_server_normalizes_legacy_site_only_index_to_country_map():
    script = """
const { normalizeIndexShape } = require('./dashboard_server');
const input = {
  latest: {
    amazon_us: {
      site: 'amazon_us',
      csv: 'sites/amazon_us/latest.csv',
      jsonl: 'sites/amazon_us/latest.jsonl',
      metadata: 'sites/amazon_us/metadata.json'
    }
  },
  runs: [
    { id: 'run1', site: 'amazon_us', csv: 'runs/run1.csv', jsonl: 'runs/run1.jsonl' }
  ]
};
console.log(JSON.stringify(normalizeIndexShape(input)));
"""
    normalized = json.loads(run_node(script))

    assert "amazon_us" in normalized["latest"]
    assert "kr" in normalized["latest"]["amazon_us"]
    assert normalized["latest"]["amazon_us"]["kr"]["country"] == "kr"
    assert normalized["runs"][0]["country"] == "kr"


def test_dashboard_server_keeps_site_country_nested_index():
    script = """
const { normalizeIndexShape } = require('./dashboard_server');
const input = {
  latest: {
    amazon_us: {
      kr: { site: 'amazon_us', country: 'kr', csv: 'sites/amazon_us/kr/latest.csv', jsonl: 'sites/amazon_us/kr/latest.jsonl' },
      vn: { site: 'amazon_us', country: 'vn', csv: 'sites/amazon_us/vn/latest.csv', jsonl: 'sites/amazon_us/vn/latest.jsonl' }
    }
  },
  runs: [
    { id: 'run-kr', site: 'amazon_us', country: 'kr', csv: 'runs/run-kr.csv', jsonl: 'runs/run-kr.jsonl' },
    { id: 'run-vn', site: 'amazon_us', country: 'vn', csv: 'runs/run-vn.csv', jsonl: 'runs/run-vn.jsonl' }
  ]
};
console.log(JSON.stringify(normalizeIndexShape(input)));
"""
    normalized = json.loads(run_node(script))

    assert set(normalized["latest"]["amazon_us"]) == {"kr", "vn"}
    assert normalized["latest"]["amazon_us"]["vn"]["jsonl"] == "sites/amazon_us/vn/latest.jsonl"
    assert normalized["runs"][1]["country"] == "vn"


def test_dashboard_server_normalize_item_infers_legacy_vietnam_carrier():
    script = """
const { normalizeItem } = require('./dashboard_server');
const raw = {
  site: 'amazon_us',
  country: 'vn',
  title: 'Vietnam eSIM Viettel MobiFone 30 days',
  price_usd: 15,
  product_url: 'https://example.com/item',
  evidence: {
    title: ['Vietnam eSIM Viettel MobiFone 30 days']
  }
};
console.log(JSON.stringify(normalizeItem(raw)));
"""
    normalized = json.loads(run_node(script))

    assert normalized["carrier_support_local"]["viettel"] is True
    assert normalized["carrier_support_local"]["mobifone"] is True


def test_dashboard_server_normalize_item_uses_explicit_carrier_support():
    script = """
const { normalizeItem } = require('./dashboard_server');
const raw = {
  site: 'amazon_us',
  country: 'kr',
  title: 'Korea eSIM',
  price_usd: 15,
  product_url: 'https://example.com/item',
  carrier_support_local: { skt: true, kt: false, lgu: true }
};
console.log(JSON.stringify(normalizeItem(raw)));
"""
    normalized = json.loads(run_node(script))

    assert normalized["carrier_support_local"]["skt"] is True
    assert normalized["carrier_support_local"]["lgu"] is True


def test_dashboard_server_network_generation_defaults_unknown_and_summarizes():
    script = """
const { normalizeItem, summarize } = require('./dashboard_server');
const legacy = normalizeItem({
  site: 'amazon_us',
  country: 'kr',
  title: 'legacy item',
  price_usd: 10,
  product_url: 'https://example.com/legacy'
});
const fiveG = normalizeItem({
  site: 'amazon_us',
  country: 'kr',
  title: '5g item',
  price_usd: 12,
  product_url: 'https://example.com/5g',
  network_generation: '5g_capable'
});
const lte = normalizeItem({
  site: 'amazon_us',
  country: 'kr',
  title: 'lte item',
  price_usd: 9,
  product_url: 'https://example.com/lte',
  network_generation: 'lte_4g_only'
});
console.log(JSON.stringify({ legacy, summary: summarize([legacy, fiveG, lte]) }));
"""
    result = json.loads(run_node(script))

    assert result["legacy"]["network_generation"] == "unknown"
    assert result["summary"]["networkGenerationCounts"]["5g_capable"] == 1
    assert result["summary"]["networkGenerationCounts"]["lte_4g_only"] == 1
    assert result["summary"]["networkGenerationCounts"]["unknown"] == 1
    assert result["summary"]["networkGenerationKnownOnlyShares"]["5g_capable"] == 50


def test_dashboard_server_filters_by_network_generation():
    script = """
const { applyFilters } = require('./dashboard_server');
const items = [
  { title: '5g', price_usd: 10, network_generation: '5g_capable', carrier_support_local: {} },
  { title: 'lte', price_usd: 9, network_generation: 'lte_4g_only', carrier_support_local: {} },
  { title: 'unknown', price_usd: 8, network_generation: 'unknown', carrier_support_local: {} }
];
console.log(JSON.stringify(applyFilters(items, { generation: '5g_capable' })));
"""
    filtered = json.loads(run_node(script))

    assert len(filtered) == 1
    assert filtered[0]["title"] == "5g"

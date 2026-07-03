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


def test_exchange_rate_utils_convert_and_summarize():
    script = """
const fx = require('./dashboard/exchange-rate');
const meta = fx.buildExchangeRateMeta({ rate: 1350.5, updatedAt: '2026-03-24', fetchedAt: '2026-03-24T00:00:00.000Z' });
const items = fx.attachKrwPrices([
  { title: 'a', price_usd: 10 },
  { title: 'b', price_usd: 15 },
  { title: 'c', price_usd: null }
], meta);
const summary = fx.summarizeNumbers(items.map((item) => item.price_krw));
console.log(JSON.stringify({ items, summary }));
"""
    payload = json.loads(run_node(script))

    assert payload["items"][0]["price_krw"] == 13505
    assert payload["items"][1]["price_krw"] == 20258
    assert payload["items"][2]["price_krw"] is None
    assert payload["summary"] == {
        "min": 13505,
        "max": 20258,
        "avg": 16882,
        "median": 16882,
    }


def test_exchange_rate_utils_uses_cached_rate_on_fetch_failure():
    script = """
const fx = require('./dashboard/exchange-rate');
const storage = {
  value: JSON.stringify({
    pair: 'USD/KRW',
    rate: 1350.5,
    source: 'Frankfurter (ECB reference)',
    updatedAt: '2026-03-20',
    fetchedAt: new Date(Date.now() - 13 * 60 * 60 * 1000).toISOString(),
    stale: false,
    unavailable: false,
    error: null,
    url: 'https://api.frankfurter.dev/v1/latest?base=USD&symbols=KRW'
  }),
  getItem() { return this.value; },
  setItem(_key, next) { this.value = next; }
};
(async () => {
  const meta = await fx.fetchExchangeRate(async () => { throw new Error('boom'); }, { storage });
  console.log(JSON.stringify(meta));
})();
"""
    payload = json.loads(run_node(script))

    assert payload["rate"] == 1350.5
    assert payload["stale"] is True
    assert payload["unavailable"] is False
    assert payload["error"] == "boom"


def test_dashboard_server_adds_exchange_rate_and_price_krw(tmp_path: Path):
    data_dir = ROOT / "dashboard" / "data"
    country_dir = data_dir / "sites" / "amazon_us" / "kr"
    country_dir.mkdir(parents=True, exist_ok=True)
    jsonl_path = country_dir / "latest.jsonl"
    index_path = data_dir / "index.json"

    fixture_item = {
        "site": "amazon_us",
        "country": "kr",
        "title": "Korea eSIM 7 day",
        "price_usd": 12.99,
        "product_url": "https://www.amazon.com/dp/B000000001",
        "asin": "B000000001",
    }
    original_index = index_path.read_text(encoding="utf-8") if index_path.exists() else None
    original_jsonl = jsonl_path.read_text(encoding="utf-8") if jsonl_path.exists() else None
    try:
        jsonl_path.write_text(json.dumps(fixture_item, ensure_ascii=False) + "\n", encoding="utf-8")
        index_path.write_text(
            json.dumps(
                {
                    "latest": {
                        "amazon_us": {
                            "kr": {
                                "site": "amazon_us",
                                "country": "kr",
                                "csv": "sites/amazon_us/kr/latest.csv",
                                "jsonl": "sites/amazon_us/kr/latest.jsonl",
                            }
                        }
                    },
                    "runs": [],
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

        script = """
global.fetch = async () => ({
  ok: true,
  json: async () => ({ amount: 1, base: 'USD', date: '2026-03-24', rates: { KRW: 1350.5 } })
});
const server = require('./dashboard_server');
(async () => {
  const data = await server.readLatestDataWithExchangeRate('amazon_us', 'kr', null);
  console.log(JSON.stringify({
    found: data.found,
    exchangeRate: data.exchangeRate,
    firstItem: data.items[0],
    summary: {
      priceKrwMin: data.summary.priceKrwMin,
      priceKrwMedian: data.summary.priceKrwMedian,
      priceKrwAvg: data.summary.priceKrwAvg
    }
  }));
})();
"""
        payload = json.loads(run_node(script))
    finally:
        if original_jsonl is None:
            jsonl_path.unlink(missing_ok=True)
        else:
            jsonl_path.write_text(original_jsonl, encoding="utf-8")
        if original_index is None:
            index_path.unlink(missing_ok=True)
        else:
            index_path.write_text(original_index, encoding="utf-8")

    assert payload["found"] is True
    assert payload["exchangeRate"]["rate"] == 1350.5
    assert payload["firstItem"]["price_usd"] > 0
    assert payload["firstItem"]["price_krw"] == round(payload["firstItem"]["price_usd"] * 1350.5)
    assert payload["summary"]["priceKrwMin"] is not None

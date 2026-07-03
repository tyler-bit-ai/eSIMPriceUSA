# eSIMPriceCollector USA — Roadmap

## Scope
- [x] Port the adapter-based crawler architecture from `eSIMPriceCollector_Japan`.
- [x] Implement `amazon_us` adapter targeting Amazon.com search/detail pages.
- [x] Support 7 target countries: kr, vn, th, tw, hk, mo, jp.
- [x] Rewrite extraction heuristics for English-language listings and USD pricing.
- [x] Rewrite dashboard for a single-site (Amazon US) view, removing all Qoo10-specific UI.
- [x] USD → KRW exchange rate conversion (Frankfurter API).

## Implementation Checklist
- [x] `app/models.py`: `price_usd` (float) replaces `price_jpy`; dropped legacy `carrier_support_kr` field in favor of `carrier_support_local` only.
- [x] `app/countries.py`: country registry with English search keywords (`eSIM Korea`, `eSIM Japan`, ...).
- [x] `app/carriers.py`: added `jp` carrier list (NTT docomo, au/KDDI, SoftBank, Rakuten Mobile); dropped `us` (no longer a target-use country).
- [x] `app/extractors/heuristics.py`: rewritten regex patterns for English validity/network/price signals.
- [x] `app/adapters/amazon_us.py`: Amazon.com domain, en-US locale, USD i18n-prefs cookie.
- [x] `dashboard/`, `dashboard_server.js`: single-site dashboard, no platform comparison/seller-badge sections.
- [x] Conservative crawl defaults (`concurrency=2`, `min-delay=2s`, `max-delay=4s`) given Amazon.com's stronger bot detection versus Amazon.co.jp.
- [x] Tests ported and rewritten for English fixtures; Qoo10-specific tests dropped.

## Open Issues / Assumptions
- No historical crawl data is carried over from `eSIMPriceCollector_Japan`; the dashboard starts empty until the first crawl + publish run.
- Amazon.com bot-detection risk is higher than Amazon.co.jp — smoke-test (`--limit 5`) before running large batches, and raise concurrency/lower delay only after confirming success rate.
- `carrier_support_kr` (the Korea-only legacy dual field from the Japan project) was intentionally dropped; `carrier_support_local` covers `kr` the same way it covers the other 6 countries.

## Verification Checklist
- [ ] `python -m pytest -q`
- [ ] `python -m app crawl --site amazon_us --country kr --limit 5 --concurrency 2 --min-delay 2 --max-delay 4 --out .\data\crawls\out_smoke_kr`
- [ ] Validate generated `results.jsonl`, `results.csv`, and `failed.jsonl`.
- [ ] Publish via `tools/publish.ps1` and confirm the dashboard renders the new dataset.

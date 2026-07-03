# Agent Rules — eSIM Marketplace Crawler (Amazon US)

## Mission
Build and maintain a production-oriented crawler that collects the top N eSIM products from Amazon US search results and outputs normalized data for analysis, covering eSIMs used while traveling in Korea, Vietnam, Thailand, Taiwan, Hong Kong, Macau, and Japan. Architecture mirrors the sibling `eSIMPriceCollector_Japan` project and stays extensible to future sites.

## Non-negotiables
- Use a plugin/adapter architecture: one adapter per site.
- Provide a single CLI entrypoint:
  - `python -m app crawl --site <site> --country <country> --query "<q>" --limit <n> --out <dir>`
- Output at least:
  - `results.jsonl` (1 product per line)
  - `results.csv`
  - Also write `failed.jsonl` for failures.

## Data model (normalized fields)
Each product record MUST include:
- `title`
- `price_usd` (number or null; supports cents)
- `validity` (string or null; internally normalized as `"<n>일"` for cross-tool compatibility with the dashboard)
- `network_type` ("local" | "roaming" | "unknown")
- `carrier_support_local` (per-country carrier codes as true/false/unknown, driven by `app/carriers.py`)
- `data_amount` (string or null)
- `product_url`
- `asin` (string or null)
- `brand` / `seller` (string or null)
- `evidence` (short supporting text snippets for key inferences)

## Extraction principles
- Prefer robust heuristics over brittle single selectors:
  - multiple candidate selectors + text-pattern fallback
- Always store `evidence` when inferring:
  - validity, network_type, carrier support
- Standardize:
  - Price: strip currency/commas → USD float (Amazon US prices are usually 2-decimal)
  - Validity: detect English patterns like `days`, `hours`, `validity`, `expires`
  - Network type:
    - "local network/local carrier/local number" → local
    - "international roaming/data roaming" → roaming
    - else unknown
  - Carrier support is per-country (see `app/carriers.py`): kr, vn, th, tw, hk, mo, jp

## Crawling approach (Amazon US baseline)
- Use Playwright (Chromium) for reliability; httpx/bs4 may be used as auxiliary.
- No aggressive bypass/illegal evasion:
  - Do NOT solve CAPTCHAs or use shady anti-bot services.
  - Do NOT use stolen accounts or scraping attacks.
- Stability measures (defaults are intentionally conservative — Amazon.com blocks automated traffic more aggressively than Amazon.co.jp):
  - concurrency default 2
  - randomized delay default 2–4s
  - retries with exponential backoff
  - save screenshots on parse failures (Playwright)
  - record error type/status/URL in `failed.jsonl`

## Quality gates
- Implement a smoke mode:
  - `--limit 5` must run end-to-end and create output files.
- Keep logs informative (progress, retries, parse fallbacks).
- When extraction is uncertain, return null/"unknown" + evidence rather than guessing.

## Extensibility
- New site support must be added by implementing a new adapter only:
  - `AmazonUSAdapter`, and any future site adapter.
- Shared utilities:
  - normalizers (price, validity, carrier support)
  - persistence writers (jsonl/csv)
  - retry/delay logic

## Deliverables expectation
When asked to implement changes, produce:
1) brief design note (module boundaries / flow)
2) code changes
3) updated run commands + expected output schema snippet

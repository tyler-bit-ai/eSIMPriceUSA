import asyncio
import json

import tools.scheduled_crawl as sc
from app.adapters.base import BLOCKED_EXIT_CODE, AMAZON_BLOCK_MARKERS, MarketplaceAdapter, SiteBlockedError, block_reason, desktop_user_agent
from app.models import ProductDetail, ProductStub
from app.pipeline.crawler import CrawlPipeline
from tools.notify_telegram import build_message
from tests.test_scheduled_crawl import _args, _fake_crawl

SITE, OTHER = "amazon_us", "other_site"
ROBOT_PAGE = "<body><!-- To discuss automated access to Amazon data please contact api-services-support@amazon.com. --></body>"


def test_block_reason_detects_throttle_and_robot_check():
    assert block_reason(503, "", AMAZON_BLOCK_MARKERS) == "http_503"
    assert block_reason(200, ROBOT_PAGE, AMAZON_BLOCK_MARKERS).startswith("bot_check_page")
    assert block_reason(200, "<div id='productTitle'>eSIM</div>", AMAZON_BLOCK_MARKERS) is None
    assert block_reason(404, "", AMAZON_BLOCK_MARKERS) is None


class BlockingAdapter(MarketplaceAdapter):
    name = SITE

    def __init__(self, block_search=False):
        self.block_search = block_search
        self.calls = []

    async def search(self, query, limit):
        if self.block_search:
            raise SiteBlockedError(f"{SITE} blocked: http_503 at https://example/s")
        return [ProductStub(site=SITE, product_url=f"https://example/dp/B00000000{i}", asin=f"B00000000{i}") for i in range(limit)]

    async def fetch_detail(self, stub):
        self.calls.append(stub.asin)
        if len(self.calls) >= 2:
            raise SiteBlockedError(f"{SITE} blocked: bot_check_page at {stub.product_url}")
        return ProductDetail(title="x", product_url=stub.product_url, asin=stub.asin)

    async def close(self):
        pass


def _pipeline(adapter, tmp_path):
    return CrawlPipeline(adapter=adapter, out_dir=tmp_path, concurrency=1, min_delay=0, max_delay=0, max_retries=3)


def test_detail_block_is_not_retried_and_stops_the_crawl(tmp_path):
    adapter = BlockingAdapter()
    result = asyncio.run(_pipeline(adapter, tmp_path).run(query="q", limit=6))
    assert len(adapter.calls) == 2  # no retry of the blocked page, nothing fetched after it
    assert result.blocked and [f.error_type for f in result.failures] == ["SiteBlockedError"]


def test_search_block_returns_blocked_result(tmp_path):
    result = asyncio.run(_pipeline(BlockingAdapter(block_search=True), tmp_path).run(query="q", limit=6, country="kr"))
    assert result.blocked and result.items == [] and result.failures[0].error_type == "SiteBlockedError"


def test_blocked_site_skips_its_remaining_countries(tmp_path, monkeypatch):
    def crawl(site, country, out_dir, args, resume=False):
        out_dir.mkdir(parents=True, exist_ok=True)
        if site == SITE and country == "vn":
            (out_dir / "failed.jsonl").write_text(json.dumps({"error_type": "SiteBlockedError", "error_message": "blocked: http_503"}) + "\n")
            return BLOCKED_EXIT_CODE, "crawl exit 3"
        return _fake_crawl(50)(site, country, out_dir, args)

    calls = []
    monkeypatch.setattr(sc, "crawl_one", lambda *a, **k: (calls.append(a[:2]), crawl(*a, **k))[1])
    monkeypatch.setattr(sc, "publish", lambda *a, **k: None)
    targets = [(SITE, "kr"), (SITE, "vn"), (SITE, "th"), (OTHER, "kr")]
    results = sc.run_targets(targets, tmp_path / "w", _args(tmp_path))
    assert [r["status"] for r in results] == ["published", "blocked", "skipped_site_blocked", "published"]
    assert (SITE, "th") not in calls and results[1]["reason"] == "blocked: http_503"


def test_telegram_message_reports_block():
    summary = {
        "started_at": "2026-10-18T18:17:00Z", "finished_at": "2026-10-18T18:30:00Z", "status": "partial_success",
        "published": 1, "total": 3, "blocked_sites": [SITE],
        "results": [
            {"site": SITE, "country": "kr", "status": "published", "item_count": 92},
            {"site": SITE, "country": "vn", "status": "blocked", "item_count": 3, "reason": "blocked: http_503"},
            {"site": SITE, "country": "th", "status": "skipped_site_blocked", "item_count": 0, "reason": "-"},
        ],
    }
    text = build_message("t", summary, [])
    assert f"🚫 <b>{SITE} 차단 감지</b>" in text and "남은 국가 수집 중단: th" in text
    assert "vn 3🚫" in text and "skipped_site_blocked" not in text


def test_pause_only_between_real_crawls(tmp_path, monkeypatch):
    def crawl(site, country, out_dir, args, resume=False):
        if site == SITE and country == "vn":
            out_dir.mkdir(parents=True, exist_ok=True)
            return BLOCKED_EXIT_CODE, "crawl exit 3"
        return _fake_crawl(50)(site, country, out_dir, args)

    sleeps = []
    monkeypatch.setattr(sc, "crawl_one", crawl)
    monkeypatch.setattr(sc, "publish", lambda *a, **k: None)
    monkeypatch.setattr(sc.time, "sleep", sleeps.append)
    args = _args(tmp_path, target_pause_min=5, target_pause_max=5)
    sc.run_targets([(SITE, "kr"), (SITE, "vn"), (SITE, "th"), (OTHER, "kr")], tmp_path / "w", args)
    assert sleeps == [5, 5]  # before vn and before the other site; none for the skipped th


def test_desktop_user_agent_matches_browser_version(monkeypatch):
    monkeypatch.setattr("app.adapters.base.sys.platform", "darwin")
    ua = desktop_user_agent("156.0.8078.4")
    assert "Macintosh" in ua and "Chrome/156.0.0.0" in ua and "Headless" not in ua


class ResumingAdapter(BlockingAdapter):
    """Blocks on the 2nd detail page of the first attempt; a resume must not search again."""

    def __init__(self, blocks=True):
        super().__init__()
        self.blocks = blocks
        self.searches = 0

    async def search(self, query, limit):
        self.searches += 1
        return await super().search(query, limit)

    async def fetch_detail(self, stub):
        if not self.blocks:
            self.calls.append(stub.asin)
            return ProductDetail(title="x", product_url=stub.product_url, asin=stub.asin)
        return await super().fetch_detail(stub)


def test_resume_reuses_search_and_fetches_only_missing_items(tmp_path):
    from app.output.writers import write_invalid_jsonl, write_jsonl

    def collected(result):  # the fake titles fail the travel filter, so items land in invalid_items
        return sorted(i.asin for i in result.items + result.invalid_items)

    first = asyncio.run(_pipeline(ResumingAdapter(), tmp_path).run(query="q", limit=4, country="kr"))
    assert first.blocked and collected(first) == ["B000000000"] and (tmp_path / "stubs.jsonl").exists()
    write_jsonl(tmp_path / "results.jsonl", first.items)
    write_invalid_jsonl(tmp_path / "invalid.jsonl", first.invalid_items)

    adapter = ResumingAdapter(blocks=False)
    result = asyncio.run(_pipeline(adapter, tmp_path).run(query="q", limit=4, country="kr", resume=True))
    assert adapter.searches == 0 and adapter.calls == ["B000000001", "B000000002", "B000000003"]
    assert result.blocked is None and collected(result) == [f"B00000000{i}" for i in range(4)]


def test_fresh_crawl_ignores_old_search_results(tmp_path):
    (tmp_path / "stubs.jsonl").write_text(json.dumps({"product_url": "https://example/dp/OLD"}) + "\n")
    adapter = ResumingAdapter(blocks=False)
    asyncio.run(_pipeline(adapter, tmp_path).run(query="q", limit=2))
    assert adapter.searches == 1 and "OLD" not in (tmp_path / "stubs.jsonl").read_text()


def test_blocked_targets_are_resumed_after_cooldown(tmp_path, monkeypatch):
    attempts = []

    def crawl(site, country, out_dir, args, resume=False):
        attempts.append((country, resume))
        if country == "vn" and not resume:
            out_dir.mkdir(parents=True, exist_ok=True)
            return BLOCKED_EXIT_CODE, "crawl exit 3"
        return _fake_crawl(50)(site, country, out_dir, args)

    sleeps = []
    monkeypatch.setattr(sc, "crawl_one", crawl)
    monkeypatch.setattr(sc, "publish", lambda *a, **k: None)
    monkeypatch.setattr(sc.time, "sleep", sleeps.append)
    args = _args(tmp_path, retry_rounds=2, block_cooldown_min=120, block_cooldown_max=120)
    results, rounds = sc.run_with_retries([(SITE, "kr"), (SITE, "vn"), (SITE, "th")], tmp_path / "w", args)
    assert rounds == 1 and sleeps == [7200]
    assert attempts == [("kr", False), ("vn", False), ("vn", True), ("th", True)]
    assert [(r["status"], r.get("attempts", 1)) for r in results] == [("published", 1), ("published", 2), ("published", 2)]


def test_retries_stop_after_the_configured_rounds(tmp_path, monkeypatch):
    def crawl(site, country, out_dir, args, resume=False):
        out_dir.mkdir(parents=True, exist_ok=True)
        return BLOCKED_EXIT_CODE, "crawl exit 3"

    monkeypatch.setattr(sc, "crawl_one", crawl)
    monkeypatch.setattr(sc.time, "sleep", lambda s: None)
    results, rounds = sc.run_with_retries([(SITE, "kr"), (SITE, "vn")], tmp_path / "w", _args(tmp_path, retry_rounds=2))
    assert rounds == 2 and [(r["status"], r["attempts"]) for r in results] == [("blocked", 3), ("skipped_site_blocked", 3)]


def test_telegram_message_reports_retries():
    summary = {
        "started_at": "2026-10-18T20:17:00Z", "finished_at": "2026-10-19T01:00:00Z", "status": "success",
        "published": 2, "total": 2, "blocked_sites": [], "retry_rounds": 1,
        "results": [
            {"site": SITE, "country": "kr", "status": "published", "item_count": 49},
            {"site": SITE, "country": "th", "status": "published", "item_count": 50, "attempts": 2},
        ],
    }
    text = build_message("t", summary, [])
    assert "th 50🔁" in text and "재시도 1회" in text and "테스트 실행" not in text

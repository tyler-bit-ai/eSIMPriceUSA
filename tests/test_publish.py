import json
from pathlib import Path

from tools.publish import build_history, publish


def _write_out(out: Path, prices: list[int], title: str = "Korea eSIM 3 days data") -> Path:
    out.mkdir(parents=True)
    rows = [{"site": "amazon_us", "country": "kr", "title": title, "price_usd": p} for p in prices]
    (out / "results.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
    (out / "results.csv").write_text("title,price_usd\n", encoding="utf-8")
    return out


def test_publish_writes_latest_run_and_index(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    (data / "index.json").write_text(
        json.dumps({"latest": {}, "runs": [{"id": "old", "site": "amazon_us", "country": "vn", "jsonl": "runs/old.jsonl", "csv": "runs/old.csv"}]}),
        encoding="utf-8",
    )
    out = _write_out(tmp_path / "out_kr", [1000, 1200])

    run = publish(out, data, "amazon_us", "kr", limit=100)

    index = json.loads((data / "index.json").read_text(encoding="utf-8"))
    assert [r["id"] for r in index["runs"]] == [run["id"], "old"]
    assert run["csv"] == "" and (data / run["jsonl"]).exists()
    assert not list((data / "runs").glob("*.csv"))
    latest = index["latest"]["amazon_us"]["kr"]
    assert latest["jsonl"] == "sites/amazon_us/kr/latest.jsonl" and latest["item_count"] == 2
    assert (data / "sites/amazon_us/kr/latest.csv").exists()
    assert json.loads((data / "sites/amazon_us/kr/metadata.json").read_text(encoding="utf-8"))["limit"] == 100
    assert (data / "history.json").exists()


def test_build_history_matches_dashboard_trend_rules(tmp_path):
    data = tmp_path / "data"
    (data / "runs").mkdir(parents=True)

    def run(name, crawled_at, prices, title="Korea eSIM 3 days data"):
        rows = [{"title": title, "price_usd": p} for p in prices]
        (data / "runs" / f"{name}.jsonl").write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
        return {"id": name, "site": "amazon_us", "country": "kr", "crawled_at": crawled_at, "jsonl": f"runs/{name}.jsonl"}

    runs = [
        run("a", "2026-10-01T05:00:00Z", [10] * 50 + [20] * 50),  # median of even list = mean of middle two
        run("b", "2026-10-01T01:00:00Z", [99] * 60),  # older run the same day is ignored
        run("c", "2026-10-15T05:00:00Z", [15] * 9),  # below MIN_TREND_N
        run("d", "2026-10-29T05:00:00Z", [12] * 60 + [None, 0]),  # null/0 prices dropped
        run("e", "2026-10-29T05:00:00Z", [1] * 60, title=""),  # missing title = non-travel
    ]
    runs[-1]["country"] = "vn"

    assert build_history(data, runs) == {"kr": {"2026-10-01": [15, 100], "2026-10-29": [12, 60]}}

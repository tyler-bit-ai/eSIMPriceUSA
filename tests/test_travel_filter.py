import json
import subprocess
from pathlib import Path

from app.pipeline.validation import non_travel_reason

ROOT = Path(__file__).resolve().parents[1]

TITLES = [
    "USA Prepaid eSIM (T-Mobile Network) | Unlimited 5G/4G Internet Data in USA",
    "Jethro Mobile eSIM - 30 Day Plan with Unlimited Talk, Text + 10GB High-Speed Data",
    "V0 eSIM Card for Unlocked Android, 480KB Storage - SIM to eSIM Adapter, 15 Profiles",
    "eSIM Card & Reader Kit for Unlocked Smartphones",
    "Mobile Tracker SIM Card, 5G/4G LTE Data Only Sim Card",
    "4G LTE Data SIM Card 50GB - 2 Years for Trail Camera & Security Camera",
    "GAPER GO Fast Push Pop Game - Light Up Fidget Toy for Kids",
    "Free Test 150MB 1Day in USA | Happy China, Hong Kong, Macau 30Days Unlimited Data Sim Card",
    "Preloaded Orange Travel Sim with 20GB of Worldwide Data (UK, Europe, USA, China)",
    "Japan eSIM 15 Days Data Only SIM | 10GB High-Speed 4G LTE | Docomo",
    "Prepaid eSIM for Mainland China, Hong Kong, Macau, Taiwan | 10GB 15Day Plan Data",
    "EIOTCLUB Asia Travel eSIM, 1GB 30-Day, China Japan Korea & More",
    "   ",
    "",
]


def _run_node(script: str) -> str:
    return subprocess.run(
        ["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True, encoding="utf-8"
    ).stdout


def test_js_and_python_travel_filters_agree():
    script = (
        "const f = require('./dashboard/travel-filter');"
        f"const t = {json.dumps(TITLES, ensure_ascii=False)};"
        "console.log(JSON.stringify(t.map((x) => f.nonTravelReason(x))));"
    )
    assert json.loads(_run_node(script)) == [non_travel_reason(t) for t in TITLES]


def test_travel_filter_keeps_multi_country_and_drops_domestic():
    kept = [non_travel_reason(t) for t in TITLES[7:12]]
    dropped = [non_travel_reason(t) for t in TITLES[:7]]

    assert kept == [None] * 5
    assert all(reason is not None for reason in dropped)


def test_dashboard_server_drops_non_travel_items():
    script = (
        "const s = require('./dashboard_server');"
        "const rows = [{title:'T-Mobile eSIM USA 1 Month', price_usd:32.6},"
        "{title:'Japan Travel eSIM 15 Day 10GB', price_usd:16.99},"
        "{title:'', price_usd:20}].map(s.normalizeItem).filter(s.keepDashboardItem);"
        "console.log(JSON.stringify(rows.map((r) => r.title)));"
    )
    assert json.loads(_run_node(script)) == ["Japan Travel eSIM 15 Day 10GB"]

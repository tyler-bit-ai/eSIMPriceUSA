# eSIMPriceCollector_USA

미국 Amazon(amazon.com) 마켓플레이스의 eSIM 상품을 국가별로 수집하고, 정규화된 결과를 CSV/JSONL과 대시보드로 비교하는 크롤러입니다.  
현재 `amazon_us`를 지원하며, 국가 축은 `kr`, `vn`, `th`, `tw`, `hk`, `mo`, `jp`를 사용합니다.

이 프로젝트는 [`eSIMPriceCollector_Japan`](../eSIMPriceCollector_Japan)의 아키텍처와 대시보드 구조를 그대로 따르되, 대상 마켓플레이스를 Amazon US로, 대상 국가를 미국 대신 일본으로 바꾸고 Qoo10 관련 기능은 제외했습니다.

## Dashboard Preview

현재 대시보드 전체 화면 (라이트 모드, 다크 모드는 우측 상단 버튼으로 전환):

![Dashboard Full](docs/images/dashboard-full.png)

대시보드 주요 구성:
- **좌측 고정 필터**: 국가·셀러·사용기간(복수 선택), 네트워크, 망 세대, 데이터, 통신사, 가격 범위(USD), 검색, 정렬
- **핵심 요약**: 현재 필터 기준 1일 최저가 카드 + 국가별 최저 1일가·변동률 카드(클릭 시 국가 필터)
- **가격 추이**: 수집 시점별 중앙가(USD), 표본이 부족한 국가는 제외하고 안내
- **셀러 경쟁력**: 국가 × 기간 칸 중 셀러별 최저가 보유 수 (Amazon US는 플랫폼이 하나라 셀러 기준으로 비교)
- **가격 히트맵**: 국가 × 사용기간(1 / 2\~3 / 4\~5 / 6\~7 / 8\~10 / 11\~15 / 16일+) 1일당 최저/중앙가, 셀 클릭 시 필터
- **Local vs Roaming / 망 세대 구성**
- **시점별 변경 상품**: 이전 수집 시점을 골라 가격 인하·인상, 신규 노출, 노출 종료 비교
- **가성비 Top 10 / 전체 상품 목록**: SIM 카테고리 순위 표시, 페이지네이션, CSV 다운로드
- **다크 모드**: 선택값 저장, 없으면 시스템 설정을 따름

## Design Note
- 실행 단위: `site + country + query`
- 크롤러 CLI: `python -m app crawl --site <site> --country <country> --limit <n> --out <dir>`
- 저장 단위: `dashboard/data/sites/<site>/<country>/latest.{jsonl,csv}`
- 대시보드 단위: `사이트 + 국가 + 데이터셋(latest/run)`
- 확장 방식: 사이트별 adapter 추가 (`app/adapters/factory.py`)

## Features
- Playwright 기반 Amazon US 검색 및 상세 수집
- 상위 N개 상품 수집 (`--limit`, 기본 50, 최대 200)
- 다중 selector + 텍스트 fallback 기반 휴리스틱 추출 (영문 페이지 기준)
- `evidence` 저장
- 실패 URL/에러/스크린샷 기록 (`failed.jsonl`)
- 출력 파일 생성
  `results.jsonl`, `results.csv`, `failed.jsonl`, `invalid.jsonl`, `invalid.csv`
- 대시보드 제공
  국가/데이터셋 선택, 필터, KPI, 정렬, 다운로드
- KRW 환산 가격 지원
  `price_usd` 기준으로 `price_krw`를 계산해 표시 (Frankfurter 실시간 환율, 실패 시 캐시 사용)
- 비여행 상품 제외
  미국 현지 통신사 플랜(T-Mobile, Jethro Mobile, "USA eSIM" 등), eSIM 어댑터·리더·물리 eSIM 카드,
  IoT·트래커·카메라용 SIM, SIM과 무관한 상품, 제목 추출에 실패한 행은 `invalid.jsonl`에
  `invalid_reason=non_travel_product`로 분리되고, 대시보드는 과거 데이터에서도 숨깁니다.
  여러 나라를 함께 안내하는 다국가 플랜은 제외하지 않습니다.
  규칙은 `app/pipeline/validation.py`와 `dashboard/travel-filter.js`에 같은 내용으로 있으며 테스트가 일치를 검사합니다.

## Install
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install -r requirements-dev.txt
playwright install chromium
npm install
```

## Quick Start
기본 query는 `--country`에 맞춰 자동 선택됩니다.

```powershell
python -m app crawl --site amazon_us --country kr --limit 50 --out .\data\crawls\out_amazon_kr
python -m app crawl --site amazon_us --country vn --limit 50 --out .\data\crawls\out_amazon_vn
python -m app crawl --site amazon_us --country jp --limit 50 --out .\data\crawls\out_amazon_jp
```

직접 query를 지정할 수도 있습니다.

```powershell
python -m app crawl --site amazon_us --country hk --query "eSIM Hong Kong 5G" --limit 30 --out .\data\crawls\out_amazon_hk_custom
```

스모크 실행 (Amazon.com은 봇 차단이 상대적으로 강하므로 먼저 소량으로 확인 권장):

```powershell
python -m app crawl --site amazon_us --country kr --limit 5 --concurrency 2 --min-delay 2 --max-delay 4 --out .\data\crawls\out_smoke_amazon_kr
```

## 자동 수집 (격주, `.github/workflows/scheduled-crawl.yml`)

2주마다 월요일 05:17 KST (Japan 수집 이후)에 전체 사이트 × 국가(`amazon_us` × 7개국, limit 50)를 수집해 대시보드에 게시하고 `main`에 커밋합니다. 결과는 텔레그램으로 받습니다.

흐름:
1. `gate` job (GitHub 서버): cron은 매주 돌고, epoch 주차 `floor(unix/604800) % 2 == 1`인 주만 통과 → 정확히 14일 간격 (수동 실행은 항상 통과)
2. `crawl` job (**맥미니 self-hosted runner**, label `esim-us`): venv 설치 → `python -m tools.scheduled_crawl` → `pytest` → `dashboard/data`, `data/automation` 커밋/push → Pages 빌드 요청 → 텔레그램 알림
   - Amazon은 데이터센터 IP에서 CAPTCHA/차단이 나므로 가정용 IP인 맥미니에서 실행합니다 (우회는 하지 않음).
   - fork PR이 runner에서 코드를 실행하지 못하도록 이 workflow에는 `pull_request` 트리거를 넣지 않습니다.

amazon.com은 짧은 시간에 요청이 몰리면 IP를 일시 차단(503/로봇 확인 페이지)하므로 USA는 limit 50, 요청 간격 4~8초, 국가 사이 3~5분 휴식으로 천천히 수집합니다 (전체 약 50분). 차단이 감지되면 재시도 없이 남은 국가를 건너뛰고 텔레그램에 `🚫 차단 감지`로 알립니다.
User-Agent는 실제 OS·Chromium 버전과 일치시키고 `Headless` 표기만 뺍니다 (`app/adapters/base.py` `desktop_user_agent`). 그 외 브라우저 신호 위장(stealth)은 하지 않습니다.

게시 품질 게이트: site × country별 결과가 `ceil(min(직전 게시 개수, limit) × 0.3)`개보다 적으면 게시하지 않고 기존 latest를 유지합니다 (차단/빈 검색 결과로 대시보드가 깨지는 것 방지). 결과는 `data/automation/last_run.json`에 남고 실행마다 `data/automation/history.jsonl`에 한 줄 추가됩니다.
매 실행이 커밋을 남기므로 GitHub의 "60일 무활동 시 schedule 비활성화"에 걸리지 않습니다.

대시보드 이력: 모든 수집은 `dashboard/data/runs/<run_id>.jsonl`로 계속 쌓이고, 추이 차트용 요약은 게시할 때 `dashboard/data/history.json`에 미리 계산됩니다 (대시보드가 과거 run을 전부 내려받지 않음). 날짜별 데이터셋 선택·시점별 비교는 고른 run만 불러옵니다.

수동 실행/점검:
```bash
gh workflow run scheduled-crawl.yml                                          # 전체 수집 + 게시
gh workflow run scheduled-crawl.yml -f limit=5 -f only="amazon_us:kr" -f publish=false   # 테스트 (게시 안 함)
gh run list --workflow scheduled-crawl.yml
cd ~/Projects/actions-runner/eSIMPriceUSA && ./svc.sh status                               # runner 상태
```

로컬 실행 (macOS):
```bash
python3.14 -m venv .venv && .venv/bin/pip install -r requirements.txt -r requirements-dev.txt && .venv/bin/playwright install chromium
.venv/bin/python -m tools.scheduled_crawl --limit 5 --only amazon_us:kr --no-publish   # 스모크
.venv/bin/python -m tools.publish --out-dir data/crawls/x --site amazon_us --country kr --limit 100
.venv/bin/python -m tools.publish --history-only                                       # history.json 재생성
```

텔레그램 설정 (저장소 secrets `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, 없으면 알림만 생략):
```bash
gh secret set TELEGRAM_BOT_TOKEN -R tyler-bit-ai/eSIMPriceUSA
gh secret set TELEGRAM_CHAT_ID   -R tyler-bit-ai/eSIMPriceUSA
TELEGRAM_BOT_TOKEN=... TELEGRAM_CHAT_ID=... .venv/bin/python -m tools.notify_telegram --test
```

`last_run.json` 예시:
```json
{"started_at": "2026-10-18T18:17:02Z", "finished_at": "2026-10-18T19:20:41Z", "status": "partial_success", "published": 13, "total": 14, "limit": 100,
 "results": [{"site": "amazon_us", "country": "kr", "status": "published", "item_count": 100, "failed_count": 0, "reason": "", "previous_count": 100, "duration_s": 290},
             {"site": "amazon_us", "country": "th", "status": "skipped_low_count", "item_count": 3, "failed_count": 12, "reason": "3 < 30 (previous 100)", "previous_count": 100, "duration_s": 75}]}
```

## Publish Workflow

### Publish Only
이미 생성된 `results.jsonl`, `results.csv`를 대시보드 데이터로 반영할 때 사용합니다.

```powershell
.\tools\publish.ps1 -OutDir .\data\crawls\out_amazon_vn -DataDir dashboard\data -Site amazon_us -Country vn -Query "eSIM Vietnam" -Limit 50
```

### One-click
크롤링 후 정적 대시보드 데이터 반영, 커밋/푸시까지 한 번에 진행합니다.

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\run_and_publish.ps1 -Site amazon_us -Country kr -Limit 200 -OutDir .\data\crawls\out_auto_kr
powershell -ExecutionPolicy Bypass -File .\tools\run_and_publish.ps1 -Site amazon_us -Country jp -Limit 100 -OutDir .\data\crawls\out_auto_jp
```

게시 후 생성 구조 예시:

```text
dashboard/data/
  index.json
  runs/
    20260703T090000Z_amazon_us_vn_out_amazon_vn.csv
    20260703T090000Z_amazon_us_vn_out_amazon_vn.jsonl
  sites/
    amazon_us/
      vn/
        latest.csv
        latest.jsonl
        metadata.json
```

## Dashboard

실행:

```powershell
# 정적 모드 (Python)
cd dashboard && python -m http.server 8090
# 또는 Node 서버
npm run dashboard
```

브라우저에서 `http://localhost:8090` (정적) 또는 `http://localhost:4173` (Node) 접속.

대시보드에서 제공하는 것:
- **데이터셋 선택**: `최신` 또는 수집 날짜별(모든 국가 묶음) 데이터셋
- **필터/요약/차트**: 위 `Dashboard Preview` 구성 참고 (모든 계산은 브라우저에서 수행)
- **시점별 변경 상품**: 선택한 데이터셋과 이전 수집 시점의 공통 국가만 비교하며, 수집 건수가 크게 다르면 안내를 표시
- **SIM 카테고리 순위**: Amazon `Best Sellers Rank`의 Cell Phone SIM Cards 순위 (베스트셀러 배지가 아님)
- **정렬**: 1일당, 가격, 리뷰, SIM 카테고리 순위, 사용기간
- **다운로드**: 현재 필터 결과를 CSV(UTF-8 BOM, Excel 호환)로 저장

KRW 환산 동작:
- `price_krw = Math.round(price_usd * rate)`
- 환율은 Frankfurter 기준 `USD/KRW`를 브라우저가 실시간 조회하고, 12시간 동안 캐시함
- 조회에 실패하면 최근 성공 환율 캐시(최대 7일)를 재사용하고, 캐시도 없으면 KRW 환산·1일당 비교를 비활성화함
- `dashboard_server.js`의 `/api/latest`, `/api/export.xlsx`는 그대로 유지되지만 화면은 정적 파일(`data/index.json`, `data/**/*.jsonl`)만 사용함

## Output Files

기본 출력:
- `results.jsonl`
- `results.csv`
- `failed.jsonl`
- `invalid.jsonl`
- `invalid.csv`

핵심 필드:
- `site`, `country`, `site_product_id`
- `title`, `price_usd`, `review_count`, `monthly_sold_count`, `is_bestseller`, `bestseller_rank`
- `validity`, `usage_validity`, `activation_validity`, `network_type`
- `carrier_support_local`
- `data_amount`, `product_url`, `asin`, `seller`, `brand`, `evidence`

예시 JSONL:

```json
{"site":"amazon_us","country":"kr","title":"Korea eSIM 7 Day 3GB","price_usd":19.99,"usage_validity":"7일","activation_validity":"30일","network_type":"roaming","carrier_support_local":{"skt":true,"kt":null,"lgu":null},"data_amount":"3GB","product_url":"https://www.amazon.com/dp/B0ABCDEF12","asin":"B0ABCDEF12","site_product_id":"B0ABCDEF12","seller":"Example Store","brand":"Example"}
{"site":"amazon_us","country":"jp","title":"Japan eSIM 3 Day unlimited","price_usd":10.80,"usage_validity":"3일","activation_validity":"90일","network_type":"unknown","carrier_support_local":{"docomo":true,"au":null,"softbank":null,"rakuten":null},"data_amount":"unlimited","product_url":"https://www.amazon.com/dp/B0GHIJKL34","asin":"B0GHIJKL34","site_product_id":"B0GHIJKL34","seller":"Example Seller","brand":null}
```

## Tests
```powershell
python -m pytest -q
node --check dashboard_server.js
node --check dashboard\exchange-rate.js
node --check dashboard\travel-filter.js
node --check dashboard\app.js
```

`dashboard_server.js` 관련 테스트를 실행하려면 `npm install`로 `xlsx` 의존성이 설치되어 있어야 합니다.

## Adapter Extension Guide
1. `app/adapters/<site>.py` 생성 후 `MarketplaceAdapter` 구현
2. `search()`에서 URL/상품 식별자 스텁 반환
3. `fetch_detail()`에서 공통 모델 `ProductDetail` 로 매핑
4. 사이트별 selector는 다중 후보 + 텍스트 fallback 유지
5. `app/adapters/factory.py`에 사이트 등록

## Notes
- 캡차 우회, 계정 도용, 공격적 차단 회피는 구현하지 않음
- Amazon.com은 amazon.co.jp보다 봇 차단이 강한 편이라 보수적인 동시성/딜레이 기본값으로 시작하고, 스모크 테스트 후 필요 시 조정할 것
- Amazon DOM 변경이 잦아서 단일 selector 의존을 피하고 휴리스틱 추출을 사용함

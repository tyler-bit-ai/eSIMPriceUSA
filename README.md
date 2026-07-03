# eSIMPriceCollector_USA

미국 Amazon(amazon.com) 마켓플레이스의 eSIM 상품을 국가별로 수집하고, 정규화된 결과를 CSV/JSONL과 대시보드로 비교하는 크롤러입니다.
현재 `amazon_us`를 지원하며, 국가 축은 `kr`, `vn`, `th`, `tw`, `hk`, `mo`, `jp`를 사용합니다.

이 프로젝트는 [`eSIMPriceCollector_Japan`](../eSIMPriceCollector_Japan)의 아키텍처와 대시보드 구조를 그대로 따르되, 대상 마켓플레이스를 Amazon US로, 대상 국가를 미국 대신 일본으로 바꾸고 Qoo10 관련 기능은 제외했습니다.

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
  `price_usd` 기준으로 `price_krw`를 계산해 표시

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
- **필터 칩**: 전체 국가 / 국가별, 사용기간별 필터
- **데이터셋 선택**: 선택한 `site + country` 조합의 latest/run 목록
- **요약 KPI**: 전체 상품 수, 평균 1일 가격(KRW), 최저가(KRW), Local 비율
- **가격 히트맵**: 국가 × 기간 교차 테이블 (최저가/평균가 토글, 동적 색상)
- **가성비 랭킹**: 1일당 가격 기준 TOP 10
- **시장 분석 차트**: 네트워크 타입, 통신사별, 가격대 분포
- **고급 필터**: 검색어, 네트워크, 데이터 용량, 사용기간, 통신사, 가격 범위
- **정렬**: 가격, 판매량, 리뷰, 사용기간
- **상세 테이블**: 번호, 국가, 플랫폼, 상품명, 가격 USD/KRW, 1일당, 리뷰, 판매량, 네트워크, 데이터, 사용기간, 활성화기간, 통신사, 셀러, 브랜드
- **다운로드**: 필터 결과 / 전체 상품 엑셀 다운로드

KRW 환산 동작:
- `price_krw = Math.round(price_usd * rate)`
- 환율은 Frankfurter 기준 `USD/KRW`를 사용
- 로컬 서버 모드에서는 `/api/latest`와 `/api/export.xlsx`에 `price_krw`가 포함됨
- 정적 배포(GitHub Pages)에서는 브라우저가 환율을 조회하고, 다운로드 파일도 `price_krw`를 포함한 CSV로 생성함
- 환율 API 실패 시 최근 성공 환율 캐시를 재사용할 수 있음

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

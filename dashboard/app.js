const pageSize = 20;
const IS_GITHUB_PAGES = window.location.hostname.endsWith('github.io') || window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const FX = window.ExchangeRateUtils;
const SITE_CONFIG = {
  amazon_us: {
    sortOptions: [
      ['priceAsc', '가격 낮은순'],
      ['priceDesc', '가격 높은순'],
      ['reviewDesc', '리뷰 많은순'],
      ['salesDesc', '판매량 높은순'],
      ['usageAsc', '사용기간 짧은순'],
    ],
    columns: [
      ['title', '상품명'],
      ['price_usd', '가격 (USD)'],
      ['price_krw', '가격 (KRW)'],
      ['review_count', '리뷰 수'],
      ['monthly_sold_count', '판매량(최근 1개월)'],
      ['is_bestseller', '베스트셀러'],
      ['bestseller_rank', '판매순위'],
      ['network_type', '네트워크'],
      ['network_generation', '망 세대'],
      ['data_amount', '데이터'],
      ['usage_validity', '사용기간'],
      ['activation_validity', '활성화기간'],
      ['carrier_support_local', '통신사 지원'],
      ['seller', '셀러'],
      ['brand', '브랜드'],
    ],
    searchPlaceholder: '상품명/셀러/브랜드 검색',
  },
};
const COUNTRY_CONFIG = {
  kr: { label: '한국', dashboardEnabled: true, flag: '🇰🇷' },
  vn: { label: '베트남', dashboardEnabled: true, flag: '🇻🇳' },
  th: { label: '태국', dashboardEnabled: true, flag: '🇹🇭' },
  tw: { label: '대만', dashboardEnabled: true, flag: '🇹🇼' },
  hk: { label: '홍콩', dashboardEnabled: true, flag: '🇭🇰' },
  mo: { label: '마카오', dashboardEnabled: true, flag: '🇲🇴' },
  jp: { label: '일본', dashboardEnabled: true, flag: '🇯🇵' },
};
const DETAIL_COLUMNS = [
  ['_num', '번호'],
  ['country', '국가'],
  ['site', '플랫폼'],
  ['title', '상품명'],
  ['price_usd', '가격 (USD)'],
  ['price_krw', '가격 (KRW)'],
  ['unit_price_krw', '1일당 (KRW)'],
  ['review_count', '리뷰 수'],
  ['sales_info', '판매량'],
  ['network_type', '네트워크'],
  ['network_generation', '망 세대'],
  ['data_amount', '데이터'],
  ['usage_validity', '사용기간'],
  ['activation_validity', '활성화기간'],
  ['carrier_support_local', '통신사 지원'],
  ['seller', '셀러'],
  ['brand', '브랜드'],
];

const HELP_CONTENT = {
  common: {
    summary: '이 대시보드는 Amazon US 마켓플레이스에서 국가별 eSIM 검색 결과를 수집하고, 핵심 정보를 정규화해 비교할 수 있도록 만든 분석 화면입니다.',
    usage: [
      '상단에서 사이트, 국가, 데이터셋을 선택하면 해당 수집 결과가 로드됩니다.',
      '필터 영역에서 네트워크, 데이터 용량, 사용기간, 통신사 지원, 가격 범위를 조합해 원하는 상품만 볼 수 있습니다.',
      '정렬 기준은 판매량, 리뷰 수, 베스트셀러 지표를 활용할 수 있습니다.',
      '상세 항목 표의 상품명을 누르면 원본 상품 페이지로 이동하고, 현재 화면 기준으로 엑셀 다운로드도 가능합니다.',
      'KRW 가격은 Frankfurter 환율을 기준으로 USD에서 환산한 보조 지표이며, API 실패 시 최근 성공 환율 캐시를 재사용할 수 있습니다.',
    ],
    notes: [
      '`unknown`은 정보가 없거나, 신호가 서로 충돌하거나, 추론 근거가 충분하지 않다는 뜻입니다.',
      '`usage_validity`는 실제 사용 가능 기간, `activation_validity`는 구매 후 개통해야 하는 기한을 뜻합니다.',
      '`network_type`과 `carrier_support_local`은 제목·옵션·상세 설명의 텍스트를 기반으로 추론될 수 있습니다.',
      '`price_krw`는 `price_usd * 환율`을 원 단위 반올림한 파생 값입니다.',
    ],
    terms: [
      ['price_usd', '상품의 현재 판매가 기준 USD 값입니다. 옵션형 상품은 대표 플랜 또는 강한 fallback 신호를 기준으로 계산됩니다.'],
      ['price_krw', 'Frankfurter 환율을 기준으로 계산한 KRW 환산 가격입니다. 원 단위 반올림 값을 사용합니다.'],
      ['data_amount', '무제한, 총량형(`3GB`), 일 단위형(`1GB/day`)처럼 데이터 정책을 정규화한 값입니다.'],
      ['network_type', '`local`, `roaming`, `unknown` 중 하나입니다. 현지 회선/현지 번호/로밍 문구 등으로 분류합니다.'],
      ['carrier_support_local', '선택한 국가의 현지 통신사 언급을 carrier registry 기준으로 표시합니다. 언급이 없으면 미표시로 남을 수 있습니다.'],
    ],
  },
  amazon_us: {
    intro: 'Amazon US 화면은 판매량, 베스트셀러 여부, 판매순위처럼 Amazon이 상대적으로 잘 노출하는 지표 중심으로 구성됩니다.',
    terms: [
      ['monthly_sold_count', '상품 설명이나 검색 결과에 노출되는 최근 1개월 판매량 신호입니다. 값이 없으면 Amazon 페이지에서 공개되지 않은 것입니다.'],
      ['review_count', 'Amazon 상품 리뷰 수입니다. 검색 결과 카드 또는 상세 페이지의 리뷰 수 텍스트에서 수집합니다.'],
      ['is_bestseller', 'Amazon의 베스트셀러 배지 유무입니다. `Yes`면 해당 배지가 확인된 상품입니다.'],
      ['bestseller_rank', 'Amazon 판매순위입니다. 숫자가 작을수록 해당 카테고리 내 상위에 가깝습니다.'],
      ['brand', 'Amazon에서 브랜드 필드가 비교적 안정적으로 보일 때 수집됩니다.'],
    ],
    faq: [
      '판매량과 판매순위는 Amazon 공개 UI에 의존하므로 시점에 따라 달라질 수 있습니다.',
      'Amazon.com은 봇 차단이 상대적으로 강해 일부 상품은 재시도 후에도 상세 정보가 `unknown`으로 남을 수 있습니다.',
    ],
  },
};

let state = {
  items: [],
  filtered: [],
  currentPage: 1,
  file: null,
  generatedAt: null,
  totalBeforeFilter: 0,
  datasets: [],
  sites: [],
  countries: [],
  selectedSite: 'amazon_us',
  selectedCountry: 'all',
  selectedDatasetId: null,
  selectedCsvPath: './data/sites/amazon_us/kr/latest.csv',
  amazonReviewEnabled: true,
  exchangeRate: FX.buildExchangeRateMeta({ unavailable: true, stale: true }),
  selectedPeriod: 'all',
  heatmapMode: 'min',
};
const CARRIER_CONFIG = {
  kr: [
    ['skt', 'SKT'],
    ['kt', 'KT'],
    ['lgu', 'LGU+'],
  ],
  vn: [
    ['viettel', 'Viettel'],
    ['vinaphone', 'VinaPhone'],
    ['mobifone', 'MobiFone'],
    ['vietnamobile', 'Vietnamobile'],
  ],
  tw: [
    ['chunghwa', 'Chunghwa Telecom'],
    ['taiwan_mobile', 'Taiwan Mobile'],
    ['fareastone', 'Far EasTone'],
  ],
  hk: [
    ['cmhk', 'CMHK'],
    ['csl', 'CSL'],
    ['smartone', 'SmarTone'],
    ['three_hk', '3HK'],
  ],
  mo: [
    ['ctm', 'CTM'],
    ['china_telecom_macau', 'China Telecom (Macau)'],
    ['three_macau', '3 Macau'],
  ],
  th: [
    ['ais', 'AIS'],
    ['dtac', 'dtac'],
    ['truemove', 'TrueMove H'],
  ],
  jp: [
    ['docomo', 'NTT docomo'],
    ['au', 'au (KDDI)'],
    ['softbank', 'SoftBank'],
    ['rakuten', 'Rakuten Mobile'],
  ],
};
const CARRIER_ALIASES = {
  kr: {
    skt: ['skt', 'sk telecom', 'sktelecom'],
    kt: ['kt', 'kt olleh', 'olleh'],
    lgu: ['lg u+', 'lgu+', 'uplus', 'lg u plus', 'lgu'],
  },
  vn: {
    viettel: ['viettel'],
    vinaphone: ['vinaphone', 'vina phone', 'vnpt'],
    mobifone: ['mobifone', 'mobi phone'],
    vietnamobile: ['vietnamobile', 'vietnam mobile'],
  },
  tw: {
    chunghwa: ['chunghwa', '中華電信', 'cht'],
    taiwan_mobile: ['taiwan mobile', '台灣大哥大', 'twm'],
    fareastone: ['far eas tone', 'far eastone', '遠傳', 'fet'],
  },
  hk: {
    cmhk: ['cmhk', 'china mobile hong kong', '中國移動香港'],
    csl: ['csl', 'one2free', '1o1o', 'pccw-hkt'],
    smartone: ['smartone', 'smart one'],
    three_hk: ['3hk', '3 hong kong', 'three hk'],
  },
  mo: {
    ctm: ['ctm', 'macau telecom', '澳門電訊'],
    china_telecom_macau: ['china telecom macau', '中國電信澳門', 'ctm macau'],
    three_macau: ['3 macau', 'three macau', 'hutchison telephone macau'],
  },
  th: {
    ais: ['ais', 'advanced info service'],
    dtac: ['dtac'],
    truemove: ['truemove', 'truemove h', 'true move'],
  },
  jp: {
    docomo: ['docomo', 'ntt docomo'],
    au: ['au', 'kddi', 'au by kddi'],
    softbank: ['softbank', 'soft bank'],
    rakuten: ['rakuten mobile', 'rakuten'],
  },
};

function parseJsonl(text) {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch (_) {
        return null;
      }
    })
    .filter(Boolean);
}

function extractDays(value) {
  if (!value) return null;
  const m = String(value).match(/(\d{1,4})\s*일/);
  return m ? Number(m[1]) : null;
}

function getCarrierDefinitions(country) {
  return CARRIER_CONFIG[country] || [];
}

function inferLegacyCarrierLocal(raw, country) {
  const aliasMap = CARRIER_ALIASES[country] || {};
  const bag = [
    raw.title,
    raw.seller,
    raw.brand,
    ...(raw.evidence && typeof raw.evidence === 'object'
      ? Object.values(raw.evidence).flat().filter(Boolean)
      : []),
  ]
    .join(' ')
    .toLowerCase();
  if (!bag) return {};

  const inferred = {};
  Object.entries(aliasMap).forEach(([code, aliases]) => {
    inferred[code] = aliases.some((alias) => bag.includes(String(alias).toLowerCase()));
  });
  return inferred;
}

function normalizeCarrierLocal(carrierSupport, country, raw) {
  const definitions = getCarrierDefinitions(country);
  if (!definitions.length) return {};

  const source = carrierSupport && typeof carrierSupport === 'object'
    ? carrierSupport
    : inferLegacyCarrierLocal(raw, country);

  const normalized = {};
  definitions.forEach(([code]) => {
    normalized[code] = source[code] === true;
  });
  return normalized;
}

function normalizeItem(raw) {
  const rawCountry = raw.country || (state.selectedCountry !== 'all' ? state.selectedCountry : null) || null;
  const country = rawCountry ? String(rawCountry).toLowerCase() : null;
  const carrier = normalizeCarrierLocal(raw.carrier_support_local, country, raw);
  const parsedPrice = Number(raw.price_usd);
  const parsedPriceKrw = Number(raw.price_krw);
  return {
    site: raw.site || null,
    country,
    title: raw.title || '',
    product_url: typeof raw.product_url === 'string' ? raw.product_url : null,
    price_usd: Number.isFinite(parsedPrice) && parsedPrice > 0 ? parsedPrice : null,
    price_krw: Number.isFinite(parsedPriceKrw) && parsedPriceKrw > 0 ? parsedPriceKrw : null,
    review_count: Number.isFinite(Number(raw.review_count)) ? Number(raw.review_count) : null,
    monthly_sold_count: Number.isFinite(Number(raw.monthly_sold_count)) ? Number(raw.monthly_sold_count) : null,
    is_bestseller: typeof raw.is_bestseller === 'boolean' ? raw.is_bestseller : null,
    bestseller_rank: Number.isFinite(Number(raw.bestseller_rank)) ? Number(raw.bestseller_rank) : null,
    network_type: raw.network_type || 'unknown',
    network_generation: raw.network_generation || 'unknown',
    network_generation_inferred: raw.network_generation_inferred || raw.network_generation || 'unknown',
    network_generation_confidence: raw.network_generation_confidence || (raw.network_generation && raw.network_generation !== 'unknown' ? 'high' : 'low'),
    data_amount: raw.data_amount || null,
    usage_validity: raw.usage_validity || raw.validity || null,
    activation_validity: raw.activation_validity || null,
    seller: raw.seller || null,
    brand: raw.brand || null,
    asin: raw.asin || null,
    site_product_id: raw.site_product_id || null,
    carrier_support_local: carrier,
    usage_days: extractDays(raw.usage_validity || raw.validity || null),
    activation_days: extractDays(raw.activation_validity || null),
  };
}

function keepDashboardItem(item) {
  return Number.isFinite(item.price_usd) && item.price_usd > 0;
}

const el = {
  metaText: document.getElementById('metaText'),
  fxText: document.getElementById('fxText'),
  currentScope: document.getElementById('currentScope'),
  siteAmazonCard: document.getElementById('siteAmazonCard'),
  helpBtn: document.getElementById('helpBtn'),
  helpOverlay: document.getElementById('helpOverlay'),
  helpCloseBtn: document.getElementById('helpCloseBtn'),
  helpTitle: document.getElementById('helpTitle'),
  helpBody: document.getElementById('helpBody'),
  refreshBtn: document.getElementById('refreshBtn'),
  siteSelect: document.getElementById('siteSelect'),
  countrySelect: document.getElementById('countrySelect'),
  datasetSelect: document.getElementById('datasetSelect'),
  kpis: document.getElementById('kpis'),
  summaryGrid: document.getElementById('summaryGrid'),
  filterBar: document.getElementById('filterBar'),
  heatmapHead: document.getElementById('heatmapHead'),
  heatmapBody: document.getElementById('heatmapBody'),
  heatmapTitle: document.getElementById('heatmapTitle'),
  heatmapModeMin: document.getElementById('heatmapModeMin'),
  heatmapModeAvg: document.getElementById('heatmapModeAvg'),
  rankingList: document.getElementById('rankingList'),
  networkChart: document.getElementById('networkChart'),
  carrierChart: document.getElementById('carrierChart'),
  priceChart: document.getElementById('priceChart'),
  dataAmountBars: document.getElementById('dataAmountBars'),
  networkBars: document.getElementById('networkBars'),
  searchInput: document.getElementById('searchInput'),
  networkFilter: document.getElementById('networkFilter'),
  generationFilter: document.getElementById('generationFilter'),
  dataFilter: document.getElementById('dataFilter'),
  usageFilter: document.getElementById('usageFilter'),
  carrierFilter: document.getElementById('carrierFilter'),
  minPrice: document.getElementById('minPrice'),
  maxPrice: document.getElementById('maxPrice'),
  sortKey: document.getElementById('sortKey'),
  tableHead: document.getElementById('tableHead'),
  rows: document.getElementById('rows'),
  pageInfo: document.getElementById('pageInfo'),
  prevPage: document.getElementById('prevPage'),
  nextPage: document.getElementById('nextPage'),
  downloadExcelBtn: document.getElementById('downloadExcelBtn'),
  downloadExcelBtn2: document.getElementById('downloadExcelBtn2'),
};

function activeConfig() {
  let config = SITE_CONFIG[state.selectedSite] || SITE_CONFIG.amazon_us;
  if (state.amazonReviewEnabled) {
    config = { ...config };
  } else {
    config = {
      ...config,
      sortOptions: config.sortOptions.filter(([value]) => value !== 'reviewDesc'),
      columns: config.columns.filter(([key]) => key !== 'review_count'),
    };
  }
  if (state.selectedCountry === 'all') {
    const hasCountry = config.columns.some(([key]) => key === 'country');
    if (!hasCountry) {
      config.columns = [['country', '국가'], ...config.columns];
    }
  }
  return config;
}

function siteLabel(site) {
  return site === 'amazon_us' ? 'Amazon US' : (site || 'Amazon US');
}

function countryLabel(country) {
  if (country === 'all') return '전체 국가';
  return (COUNTRY_CONFIG[country] && COUNTRY_CONFIG[country].label) || String(country || '한국').toUpperCase();
}

function getVisibleCountryCodes() {
  return Object.entries(COUNTRY_CONFIG)
    .filter(([, config]) => config.dashboardEnabled)
    .map(([code]) => code);
}

function isHelpOpen() {
  return el.helpOverlay && !el.helpOverlay.hidden;
}

function renderHelpModal() {
  const common = HELP_CONTENT.common;
  const siteHelp = HELP_CONTENT[state.selectedSite] || HELP_CONTENT.amazon_us;
  el.helpTitle.textContent = `${siteLabel(state.selectedSite)} · ${countryLabel(state.selectedCountry)} 도움말`;
  el.helpBody.innerHTML = `
    <section class="helpSection">
      <h3>프로그램 소개</h3>
      <p>${safe(common.summary)}</p>
    </section>
    <section class="helpSection">
      <h3>사용법</h3>
      <ol class="helpList">${common.usage.map((item) => `<li>${safe(item)}</li>`).join('')}</ol>
    </section>
    <section class="helpSection">
      <h3>공통 용어</h3>
      <div class="termGrid">${common.terms.map(([term, desc]) => `<div class="termCard"><strong>${safe(term)}</strong><p>${safe(desc)}</p></div>`).join('')}</div>
    </section>
    <section class="helpSection">
      <h3>${safe(siteLabel(state.selectedSite))} 화면 설명</h3>
      <p>${safe(siteHelp.intro)}</p>
    </section>
    <section class="helpSection">
      <h3>${safe(siteLabel(state.selectedSite))} 주요 용어</h3>
      <div class="termGrid">${siteHelp.terms.map(([term, desc]) => `<div class="termCard"><strong>${safe(term)}</strong><p>${safe(desc)}</p></div>`).join('')}</div>
    </section>
    <section class="helpSection">
      <h3>자주 궁금한 점</h3>
      <ul class="helpList">${siteHelp.faq.map((item) => `<li>${safe(item)}</li>`).join('')}${common.notes.map((item) => `<li>${safe(item)}</li>`).join('')}</ul>
    </section>
  `;
}

function openHelpModal() {
  renderHelpModal();
  el.helpOverlay.hidden = false;
  document.body.style.overflow = 'hidden';
}

function closeHelpModal() {
  el.helpOverlay.hidden = true;
  document.body.style.overflow = '';
}

function formatDatasetGroupLabel(group) {
  const crawled = group && group.crawledAt ? isoToLocal(group.crawledAt) : (group && group.date ? group.date : '-');
  const count = Number.isFinite(group && group.itemCount) ? group.itemCount.toLocaleString('ko-KR') : '-';
  const countryCount = group && group.countries ? group.countries.size : 0;
  return `${crawled} | ${countryCount}개국 · ${count}개`;
}

function populateSiteOptions(indexData) {
  const sites = new Set();
  const latest = indexData && indexData.latest ? indexData.latest : {};
  Object.keys(latest).forEach((site) => sites.add(site));
  const runs = Array.isArray(indexData && indexData.runs) ? indexData.runs : [];
  runs.forEach((run) => run && run.site && sites.add(run.site));
  if (!sites.size) sites.add('amazon_us');
  state.sites = [...sites];
  if (!state.sites.includes(state.selectedSite)) state.selectedSite = state.sites[0];
  if (el.siteSelect) {
    el.siteSelect.innerHTML = state.sites.map((site) => `<option value="${safe(site)}">${safe(siteLabel(site))}</option>`).join('');
    el.siteSelect.value = state.selectedSite;
  }
}

function populateCountryOptions(indexData) {
  const countries = new Set(getVisibleCountryCodes());
  const latest = indexData && indexData.latest && indexData.latest[state.selectedSite] ? indexData.latest[state.selectedSite] : {};
  Object.keys(latest).forEach((country) => {
    if (!COUNTRY_CONFIG[country] || COUNTRY_CONFIG[country].dashboardEnabled) countries.add(country);
  });
  const runs = Array.isArray(indexData && indexData.runs) ? indexData.runs : [];
  runs.forEach((run) => {
    if (!run || run.site !== state.selectedSite || !run.country) return;
    if (!COUNTRY_CONFIG[run.country] || COUNTRY_CONFIG[run.country].dashboardEnabled) countries.add(run.country);
  });
  state.countries = ['all', ...countries];
  if (!state.countries.includes(state.selectedCountry)) state.selectedCountry = 'all';
  if (el.countrySelect) {
    el.countrySelect.innerHTML = state.countries.map((country) => `<option value="${safe(country)}">${safe(country === 'all' ? '전체 국가' : countryLabel(country))}</option>`).join('');
    el.countrySelect.value = state.selectedCountry;
  }
}

function populateDatasetOptions(datasets) {
  if (!datasets.length) {
    el.datasetSelect.innerHTML = '<option value="">latest</option>';
    el.datasetSelect.value = '';
    return;
  }
  el.datasetSelect.innerHTML = ['<option value="">latest</option>']
    .concat(datasets.map((d) => `<option value="${safe(String(d.id || ''))}">${safe(formatDatasetGroupLabel(d))}</option>`))
    .join('');
  el.datasetSelect.value = state.selectedDatasetId || '';
}

function dateKeyFromCrawledAt(value) {
  if (!value) return 'unknown';
  const str = String(value);
  const mdy = str.match(/^(\d{2})\/(\d{2})\/(\d{4})/);
  if (mdy) return `${mdy[3]}-${mdy[1]}-${mdy[2]}`;
  return str.slice(0, 10);
}

function getGroupedDatasetsForSelectedSite() {
  const bySite = state.datasets.filter((entry) => (entry.site || 'amazon_us') === state.selectedSite);
  const groups = new Map();
  for (const entry of bySite) {
    const dateKey = dateKeyFromCrawledAt(entry.crawled_at);
    if (!groups.has(dateKey)) {
      groups.set(dateKey, { id: dateKey, date: dateKey, site: state.selectedSite, entries: [], countries: new Set(), itemCount: 0, crawledAt: entry.crawled_at || null });
    }
    const group = groups.get(dateKey);
    group.entries.push(entry);
    group.countries.add(entry.country || 'kr');
    group.itemCount += Number.isFinite(Number(entry.item_count)) ? Number(entry.item_count) : 0;
    if (entry.crawled_at && (!group.crawledAt || entry.crawled_at > group.crawledAt)) group.crawledAt = entry.crawled_at;
  }
  return [...groups.values()].sort((a, b) => (a.date < b.date ? 1 : a.date > b.date ? -1 : 0));
}

function usd(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return '-';
  return `$${Number(n).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function won(n) {
  if (n === null || n === undefined || Number.isNaN(n)) return '-';
  return `₩${Number(n).toLocaleString('ko-KR')}`;
}

function safe(value) {
  if (value === null || value === undefined || value === '') return '-';
  return String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
}

function safeHref(value) {
  if (!value) return '';
  return String(value).replaceAll('"', '&quot;');
}

function isoToLocal(iso) {
  if (!iso) return '-';
  const d = new Date(iso);
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString('ko-KR');
}

function median(values) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : Math.round((sorted[mid - 1] + sorted[mid]) / 2);
}

function summarize(items) {
  const prices = items.map((it) => it.price_usd).filter((n) => Number.isFinite(n));
  const pricesKrw = items.map((it) => it.price_krw).filter((n) => Number.isFinite(n));
  const sales = items.map((it) => it.monthly_sold_count).filter((n) => Number.isFinite(n));
  const reviews = items.map((it) => it.review_count).filter((n) => Number.isFinite(n));
  const localCount = items.filter((it) => it.network_type === 'local').length;
  const roamingCount = items.filter((it) => it.network_type === 'roaming').length;
  const unlimitedCount = items.filter((it) => String(it.data_amount || '').toLowerCase() === 'unlimited').length;
  const generationSummary = buildNetworkGenerationCounts(items, 'network_generation');
  const bestsellerCount = items.filter((it) => it.is_bestseller === true).length;
  const bestsellerRankKnownCount = items.filter((it) => Number.isFinite(it.bestseller_rank)).length;

  const carrierCounts = {};
  getCarrierDefinitions(state.selectedCountry).forEach(([code]) => {
    carrierCounts[code] = items.filter((it) => it.carrier_support_local && it.carrier_support_local[code]).length;
  });
  const byDataAmount = {};
  const byNetwork = {};
  for (const it of items) {
    const d = it.data_amount || 'unknown';
    const n = it.network_type || 'unknown';
    byDataAmount[d] = (byDataAmount[d] || 0) + 1;
    byNetwork[n] = (byNetwork[n] || 0) + 1;
  }

  return {
    total: items.length,
    priceMin: prices.length ? Math.min(...prices) : null,
    priceMax: prices.length ? Math.max(...prices) : null,
    priceAvg: prices.length ? Math.round((prices.reduce((a, b) => a + b, 0) / prices.length) * 100) / 100 : null,
    priceMedian: median(prices),
    priceKrwMin: pricesKrw.length ? Math.min(...pricesKrw) : null,
    priceKrwMax: pricesKrw.length ? Math.max(...pricesKrw) : null,
    priceKrwAvg: pricesKrw.length ? Math.round(pricesKrw.reduce((a, b) => a + b, 0) / pricesKrw.length) : null,
    priceKrwMedian: median(pricesKrw),
    roamingCount,
    localCount,
    networkGenerationCounts: generationSummary.counts,
    networkGenerationShares: generationSummary.shares,
    networkGenerationKnownOnlyShares: generationSummary.knownOnlyShares,
    unlimitedCount,
    salesKnownCount: sales.length,
    salesMedian: median(sales),
    reviewKnownCount: reviews.length,
    reviewMedian: median(reviews),
    bestsellerCount,
    bestsellerRankKnownCount,
    carrierCounts,
    byDataAmount,
    byNetwork,
  };
}

function updateAmazonReviewVisibility(items) {
  const total = items.length;
  const known = items.filter((it) => Number.isFinite(it.review_count)).length;
  state.amazonReviewEnabled = total > 0 && (known / total) >= 0.1;
}

function renderExchangeRateMeta() {
  if (!el.fxText) return;
  const meta = state.exchangeRate || FX.buildExchangeRateMeta({ unavailable: true, stale: true });
  const updatedAt = meta.updatedAt ? isoToLocal(meta.updatedAt) : '-';
  el.fxText.textContent = `환율: ${FX.formatExchangeRateStatus(meta)} | 기준일: ${updatedAt} | 출처: ${meta.source || '-'}`;
}

async function resolveExchangeRateMeta(providedMeta) {
  if (providedMeta && !providedMeta.unavailable && Number.isFinite(Number(providedMeta.rate))) {
    return FX.buildExchangeRateMeta(providedMeta);
  }
  return FX.fetchExchangeRate(window.fetch.bind(window), {
    storage: typeof window !== 'undefined' ? window.localStorage : null,
  });
}

function carrierLabel(carrier, country) {
  const out = [];
  getCarrierDefinitions(country).forEach(([code, label]) => {
    if (carrier && carrier[code]) out.push(label);
  });
  return out.length ? out.join(', ') : 'unknown';
}

function networkGenerationLabel(value) {
  if (value === '5g_capable') return '5G 지원';
  if (value === 'lte_4g_only') return 'LTE/4G 전용';
  return '미확인';
}

function buildNetworkGenerationCounts(items, field = 'network_generation') {
  const keys = ['5g_capable', 'lte_4g_only', 'unknown'];
  const counts = {};
  keys.forEach((value) => {
    counts[value] = items.filter((it) => (it[field] || 'unknown') === value).length;
  });
  const total = items.length || 0;
  const knownTotal = counts['5g_capable'] + counts['lte_4g_only'];
  const shares = {};
  const knownOnlyShares = {};
  keys.forEach((key) => {
    shares[key] = total ? Math.round((counts[key] / total) * 100) : 0;
    knownOnlyShares[key] = key === 'unknown' ? 0 : (knownTotal ? Math.round((counts[key] / knownTotal) * 100) : 0);
  });
  return { counts, shares, knownOnlyShares };
}

function buildCarrierKpiEntries(summary) {
  return getCarrierDefinitions(state.selectedCountry).map(([code, label]) => [
    `${label} 명시`,
    `${summary.carrierCounts[code] || 0}`,
  ]);
}

function toQuery(includeDataset = true) {
  const params = new URLSearchParams();
  params.set('site', state.selectedSite);
  params.set('country', state.selectedCountry);
  if (includeDataset && state.selectedDatasetId) params.set('dataset', state.selectedDatasetId);
  const q = el.searchInput.value.trim();
  if (q) params.set('q', q);
  if (el.networkFilter.value) params.set('network', el.networkFilter.value);
  if (el.generationFilter.value) params.set('generation', el.generationFilter.value);
  if (el.dataFilter.value) params.set('dataAmount', el.dataFilter.value);
  if (el.usageFilter.value) params.set('usage', el.usageFilter.value);
  if (el.carrierFilter.value) params.set('carrier', el.carrierFilter.value);
  if (el.minPrice.value) params.set('minPrice', el.minPrice.value);
  if (el.maxPrice.value) params.set('maxPrice', el.maxPrice.value);
  if (el.sortKey.value) params.set('sort', el.sortKey.value);
  return params.toString();
}

function getFilenameFromDisposition(contentDisposition) {
  if (!contentDisposition) return null;
  const match = contentDisposition.match(/filename="([^"]+)"/i);
  return match && match[1] ? match[1] : null;
}

function makeClientExportFilename() {
  const ts = new Date().toISOString().replace(/[:.]/g, '-');
  return `${state.selectedSite || 'market'}_${state.selectedCountry || 'all'}_filtered_${ts}.csv`;
}

function escapeCsvCell(value) {
  if (value === null || value === undefined) return '';
  const text = String(value);
  if (/[",\r\n]/.test(text)) {
    return `"${text.replaceAll('"', '""')}"`;
  }
  return text;
}

function buildClientExportRows(items) {
  return items.map((it) => ({
    site: it.site || state.selectedSite || '',
    title: it.title || '',
    price_usd: it.price_usd ?? '',
    price_krw: it.price_krw ?? '',
    review_count: it.review_count ?? '',
    monthly_sold_count: it.monthly_sold_count ?? '',
    is_bestseller: it.is_bestseller === null ? '' : (it.is_bestseller ? 'true' : 'false'),
    bestseller_rank: it.bestseller_rank ?? '',
    network_type: it.network_type || '',
    network_generation: it.network_generation || 'unknown',
    data_amount: it.data_amount || '',
    usage_validity: it.usage_validity || '',
    activation_validity: it.activation_validity || '',
    carrier_support_local: carrierLabel(it.carrier_support_local, it.country || state.selectedCountry),
    seller: it.seller || '',
    brand: it.brand || '',
    asin: it.asin || '',
    site_product_id: it.site_product_id || '',
  }));
}

function buildClientExportCsv(items) {
  const headers = [
    'site',
    'title',
    'price_usd',
    'price_krw',
    'review_count',
    'monthly_sold_count',
    'is_bestseller',
    'bestseller_rank',
    'network_type',
    'network_generation',
    'data_amount',
    'usage_validity',
    'activation_validity',
    'carrier_support_local',
    'seller',
    'brand',
    'asin',
    'site_product_id',
  ];

  const rows = buildClientExportRows(items);
  const lines = [headers.join(',')];
  rows.forEach((row) => {
    lines.push(headers.map((header) => escapeCsvCell(row[header])).join(','));
  });
  return `﻿${lines.join('\r\n')}`;
}

async function saveWithPicker(blob, suggestedName) {
  if (!('showSaveFilePicker' in window)) return false;
  const handle = await window.showSaveFilePicker({
    suggestedName,
    types: [{ description: 'Excel Workbook', accept: { 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] } }],
  });
  const writable = await handle.createWritable();
  await writable.write(blob);
  await writable.close();
  return true;
}

async function downloadAllExcel() {
  if (IS_GITHUB_PAGES) {
    const csv = buildClientExportCsv(state.items);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    const ts = new Date().toISOString().replace(/[:.]/g, '-');
    a.download = `${state.selectedSite || 'market'}_${state.selectedCountry || 'all'}_all_${ts}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(objectUrl);
    return;
  }
  const params = new URLSearchParams();
  params.set('site', state.selectedSite);
  params.set('country', state.selectedCountry);
  if (state.selectedDatasetId) params.set('dataset', state.selectedDatasetId);
  const url = `/api/export.xlsx?${params.toString()}`;
  try {
    el.downloadExcelBtn2.disabled = true;
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const suggestedName = getFilenameFromDisposition(res.headers.get('content-disposition')) || 'all.xlsx';
    const saved = await saveWithPicker(blob, suggestedName);
    if (saved) return;
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = suggestedName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(objectUrl);
  } catch (err) {
    alert(`엑셀 다운로드 실패: ${err.message}`);
  } finally {
    el.downloadExcelBtn2.disabled = false;
  }
}

async function downloadFilteredExcel() {
  if (IS_GITHUB_PAGES) {
    const csv = buildClientExportCsv(state.filtered);
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = makeClientExportFilename();
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(objectUrl);
    return;
  }
  const qs = toQuery();
  const url = qs ? `/api/export.xlsx?${qs}` : '/api/export.xlsx';
  try {
    el.downloadExcelBtn.disabled = true;
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const blob = await res.blob();
    const suggestedName = getFilenameFromDisposition(res.headers.get('content-disposition')) || 'filtered.xlsx';
    const saved = await saveWithPicker(blob, suggestedName);
    if (saved) return;
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = suggestedName;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(objectUrl);
  } catch (err) {
    alert(`엑셀 다운로드 실패: ${err.message}`);
  } finally {
    el.downloadExcelBtn.disabled = false;
  }
}

function renderSiteStructure() {
  const config = activeConfig();
  if (el.searchInput) el.searchInput.placeholder = config.searchPlaceholder;
  if (el.currentScope) {
    el.currentScope.textContent = `사이트: ${siteLabel(state.selectedSite)} · 국가: ${countryLabel(state.selectedCountry)}`;
  }
  if (el.siteAmazonCard) {
    el.siteAmazonCard.classList.toggle('active', state.selectedSite === 'amazon_us');
  }
  if (el.sortKey) {
    el.sortKey.innerHTML = config.sortOptions.map(([value, label]) => `<option value="${value}">${safe(label)}</option>`).join('');
    if (!config.sortOptions.some(([value]) => value === el.sortKey.value)) {
      el.sortKey.value = config.sortOptions[0][0];
    }
  }
  if (isHelpOpen()) renderHelpModal();
}

function renderKpis(summary) {
  const total = summary.total || 0;
  const roamingPct = total ? Math.round((summary.roamingCount / total) * 100) : 0;
  const localPct = total ? Math.round((summary.localCount / total) * 100) : 0;
  const unlimitedPct = total ? Math.round((summary.unlimitedCount / total) * 100) : 0;
  const fiveGShare = summary.networkGenerationShares?.['5g_capable'] || 0;
  const knownFiveGShare = summary.networkGenerationKnownOnlyShares?.['5g_capable'] || 0;
  const kpis = [
    ['사이트', siteLabel(state.selectedSite)],
    ['필터 결과', `${total.toLocaleString('ko-KR')}개`],
    ['최저 / 중앙 / 평균', `${usd(summary.priceMin)} / ${usd(summary.priceMedian)} / ${usd(summary.priceAvg)}`],
    ['최저 / 중앙 / 평균 (KRW)', `${won(summary.priceKrwMin)} / ${won(summary.priceKrwMedian)} / ${won(summary.priceKrwAvg)}`],
    ['최고 가격', usd(summary.priceMax)],
    ['최고 가격 (KRW)', won(summary.priceKrwMax)],
    ['판매량 수집', `${summary.salesKnownCount.toLocaleString('ko-KR')}개`],
    ['로밍 / 로컬', `${roamingPct}% / ${localPct}%`],
    ['5G 지원', `${fiveGShare}% (확인분 ${knownFiveGShare}%)`],
    ['무제한 비중', `${unlimitedPct}%`],
    ['베스트셀러 배지', `${summary.bestsellerCount}`],
    ['랭크 확인 상품', `${summary.bestsellerRankKnownCount}`],
    ...buildCarrierKpiEntries(summary),
  ];
  el.kpis.innerHTML = kpis.map(([label, value]) => `<div class="kpi"><label>${safe(label)}</label><strong>${safe(value)}</strong></div>`).join('');
}

function renderFilterOptions(items) {
  const unique = (arr) => [...new Set(arr.filter(Boolean))].sort((a, b) => String(a).localeCompare(String(b)));
  const networkOptions = unique(items.map((it) => it.network_type));
  const dataOptions = unique(items.map((it) => it.data_amount));
  const usageOptions = unique(items.map((it) => it.usage_validity));
  const keep = {
    network: el.networkFilter.value,
    generation: el.generationFilter.value,
    data: el.dataFilter.value,
    usage: el.usageFilter.value,
    carrier: el.carrierFilter.value,
  };
  el.networkFilter.innerHTML = '<option value="">네트워크 전체</option>' + networkOptions.map((v) => `<option>${safe(v)}</option>`).join('');
  el.generationFilter.innerHTML = [
    '<option value="">망 세대 전체</option>',
    '<option value="5g_capable">5G 지원</option>',
    '<option value="lte_4g_only">LTE/4G 전용</option>',
    '<option value="unknown">미확인</option>',
  ].join('');
  el.dataFilter.innerHTML = '<option value="">데이터 전체</option>' + dataOptions.map((v) => `<option>${safe(v)}</option>`).join('');
  el.usageFilter.innerHTML = '<option value="">사용기간 전체</option>' + usageOptions.map((v) => `<option>${safe(v)}</option>`).join('');
  el.carrierFilter.innerHTML = ['<option value="">통신사 전체</option>', '<option value="any">통신사 명시 상품</option>']
    .concat(getCarrierDefinitions(state.selectedCountry).map(([code, label]) => `<option value="${safe(code)}">${safe(label)} 지원</option>`))
    .join('');
  el.networkFilter.value = keep.network;
  el.generationFilter.value = keep.generation;
  el.dataFilter.value = keep.data;
  el.usageFilter.value = keep.usage;
  el.carrierFilter.value = Array.from(el.carrierFilter.options).some((opt) => opt.value === keep.carrier) ? keep.carrier : '';
}

function cellValue(row, key, rowNum) {
  if (key === '_num') return String(rowNum);
  if (key === 'country') {
    const cfg = COUNTRY_CONFIG[row.country];
    return cfg ? `${safe(cfg.flag)} ${safe(cfg.label)}` : safe(row.country);
  }
  if (key === 'site') {
    return '<span style="background:#ff9900;color:#111;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:600;">Amazon</span>';
  }
  if (key === 'title') {
    return row.product_url ? `<a class="titleLink" href="${safeHref(row.product_url)}" target="_blank" rel="noopener noreferrer">${safe(row.title)}</a>` : safe(row.title);
  }
  if (key === 'price_usd') return Number.isFinite(row.price_usd) ? usd(row.price_usd) : '-';
  if (key === 'price_krw') return Number.isFinite(row.price_krw) ? won(row.price_krw) : '-';
  if (key === 'unit_price_krw') {
    const unit = computeUnitPrice(row);
    return unit !== null ? `<span style="color:var(--green);font-weight:600;">₩${unit.toLocaleString('ko-KR')}</span>` : '-';
  }
  if (key === 'review_count') return Number.isFinite(row.review_count) ? `${row.review_count.toLocaleString('ko-KR')}` : '-';
  if (key === 'sales_info') {
    if (Number.isFinite(row.monthly_sold_count)) return `${row.monthly_sold_count.toLocaleString('ko-KR')}+`;
    return '-';
  }
  if (key === 'network_type') {
    if (row.network_type === 'local') return '<span class="badge-local">Local</span>';
    if (row.network_type === 'roaming') return '<span class="badge-roaming">Roaming</span>';
    return safe(row.network_type);
  }
  if (key === 'network_generation') return safe(networkGenerationLabel(row.network_generation));
  if (key === 'data_amount') return safe(row.data_amount);
  if (key === 'usage_validity') return safe(row.usage_validity);
  if (key === 'activation_validity') return safe(row.activation_validity);
  if (key === 'carrier_support_local') return safe(carrierLabel(row.carrier_support_local, row.country || state.selectedCountry));
  if (key === 'seller') return safe(row.seller);
  if (key === 'brand') return safe(row.brand);
  if (key === 'monthly_sold_count') return Number.isFinite(row.monthly_sold_count) ? `${row.monthly_sold_count.toLocaleString('ko-KR')}개` : '-';
  if (key === 'is_bestseller') return row.is_bestseller === true ? 'Yes' : (row.is_bestseller === false ? 'No' : '-');
  if (key === 'bestseller_rank') return Number.isFinite(row.bestseller_rank) ? `${row.bestseller_rank.toLocaleString('ko-KR')}위` : '-';
  return safe(row[key]);
}

function renderTable() {
  const totalPages = Math.max(1, Math.ceil(state.filtered.length / pageSize));
  state.currentPage = Math.min(state.currentPage, totalPages);
  const start = (state.currentPage - 1) * pageSize;
  const pageRows = state.filtered.slice(start, start + pageSize);
  el.tableHead.innerHTML = `<tr>${DETAIL_COLUMNS.map(([, label]) => `<th>${safe(label)}</th>`).join('')}</tr>`;
  const narrowKeys = new Set(['seller', 'brand', 'carrier_support_local', 'activation_validity', 'data_amount', 'usage_validity']);
  el.rows.innerHTML = pageRows.map((row, idx) => {
    const rowNum = start + idx + 1;
    return `<tr>${DETAIL_COLUMNS.map(([key]) => {
      let cls = '';
      if (key === 'title') cls = ' class="titleCell"';
      else if (narrowKeys.has(key)) cls = ' class="narrowCell"';
      return `<td${cls}>${cellValue(row, key, rowNum)}</td>`;
    }).join('')}</tr>`;
  }).join('');
  el.pageInfo.textContent = `전체 ${state.filtered.length.toLocaleString('ko-KR')}건 중 ${start + 1}–${Math.min(start + pageSize, state.filtered.length)} 표시`;
  el.prevPage.disabled = state.currentPage <= 1;
  el.nextPage.disabled = state.currentPage >= totalPages;
}

function applyLocalFilters(items) {
  const q = el.searchInput.value.trim().toLowerCase();
  const network = String(el.networkFilter.value || '').trim();
  const generation = String(el.generationFilter.value || '').trim();
  const dataAmount = String(el.dataFilter.value || '').trim();
  const usage = String(el.usageFilter.value || '').trim();
  const carrier = String(el.carrierFilter.value || '').trim();
  const minPrice = el.minPrice.value ? Number(el.minPrice.value) : null;
  const maxPrice = el.maxPrice.value ? Number(el.maxPrice.value) : null;
  const sort = String(el.sortKey.value || 'priceAsc').trim();

  const filtered = items.filter((it) => {
    if (network && it.network_type !== network) return false;
    if (generation && it.network_generation !== generation) return false;
    if (dataAmount && (it.data_amount || '') !== dataAmount) return false;
    if (usage && (it.usage_validity || '') !== usage) return false;
    if (carrier === 'any' && !Object.values(it.carrier_support_local || {}).some(Boolean)) return false;
    if (carrier && carrier !== 'any' && !it.carrier_support_local?.[carrier]) return false;
    if (Number.isFinite(minPrice) && Number.isFinite(it.price_usd) && it.price_usd < minPrice) return false;
    if (Number.isFinite(maxPrice) && Number.isFinite(it.price_usd) && it.price_usd > maxPrice) return false;
    if (!q) return true;
    const bag = [
      it.title,
      it.seller,
      it.brand,
      it.network_type,
      it.network_generation,
      networkGenerationLabel(it.network_generation),
      it.data_amount,
      it.usage_validity,
      it.activation_validity,
    ].join(' ').toLowerCase();
    return bag.includes(q);
  });

  if (sort === 'priceDesc') filtered.sort((a, b) => (b.price_usd ?? -1) - (a.price_usd ?? -1));
  else if (sort === 'salesDesc') filtered.sort((a, b) => (b.monthly_sold_count ?? -1) - (a.monthly_sold_count ?? -1) || (a.price_usd ?? Number.MAX_SAFE_INTEGER) - (b.price_usd ?? Number.MAX_SAFE_INTEGER));
  else if (sort === 'reviewDesc') filtered.sort((a, b) => (b.review_count ?? -1) - (a.review_count ?? -1) || (a.price_usd ?? Number.MAX_SAFE_INTEGER) - (b.price_usd ?? Number.MAX_SAFE_INTEGER));
  else if (sort === 'usageAsc') filtered.sort((a, b) => (a.usage_days ?? Number.MAX_SAFE_INTEGER) - (b.usage_days ?? Number.MAX_SAFE_INTEGER));
  else filtered.sort((a, b) => (a.price_usd ?? Number.MAX_SAFE_INTEGER) - (b.price_usd ?? Number.MAX_SAFE_INTEGER));

  return filtered;
}

const PERIOD_GROUPS = ['1일', '2일', '3일', '4일', '5일', '7일', '8일+'];
const PERIOD_RANGES = [
  [1, 1], [2, 2], [3, 3], [4, 4], [5, 5], [6, 7], [8, 999],
];

function computeUnitPrice(item) {
  if (!Number.isFinite(item.price_krw) || item.price_krw <= 0) return null;
  const days = item.usage_days;
  if (!Number.isFinite(days) || days <= 0) return null;
  return Math.round(item.price_krw / days);
}

function buildHeatThresholds(allPrices) {
  const valid = allPrices.filter((n) => Number.isFinite(n) && n > 0).sort((a, b) => a - b);
  if (!valid.length) return null;
  const lo = valid[0];
  const hi = valid[valid.length - 1];
  if (lo === hi) return null;
  const step = (hi - lo) / 8;
  return Array.from({ length: 8 }, (_, i) => lo + step * (i + 1));
}

function heatClassDynamic(price, thresholds) {
  if (price === null || price === undefined || !thresholds) return '';
  for (let i = 0; i < thresholds.length; i++) {
    if (price < thresholds[i]) return `heat-${i + 1}`;
  }
  return 'heat-8';
}

function renderFilterChips() {
  if (!el.filterBar) return;
  const countries = getVisibleCountryCodes();

  let html = '';

  // 국가 칩
  html += `<div class="filter-chip ${state.selectedCountry === 'all' ? 'active' : ''}" data-filter="country" data-value="all"><span>전체 국가</span></div>`;
  countries.forEach((code) => {
    const cfg = COUNTRY_CONFIG[code];
    const active = state.selectedCountry === code ? 'active' : '';
    html += `<div class="filter-chip ${active}" data-filter="country" data-value="${safe(code)}"><span class="flag">${safe(cfg.flag)}</span><span>${safe(cfg.label)}</span></div>`;
  });

  html += '<div class="divider-v"></div>';

  // 기간 칩
  const periods = ['all', '1~3일', '4~7일', '8일+'];
  const periodLabels = ['전체 기간', '1~3일', '4~7일', '8일+'];
  periods.forEach((p, i) => {
    const active = state.selectedPeriod === p ? 'active' : '';
    html += `<div class="filter-chip ${active}" data-filter="period" data-value="${safe(p)}"><span>${safe(periodLabels[i])}</span></div>`;
  });

  el.filterBar.innerHTML = html;

  el.filterBar.querySelectorAll('.filter-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      const filterType = chip.dataset.filter;
      const value = chip.dataset.value;
      if (filterType === 'country') {
        state.selectedCountry = value;
      } else if (filterType === 'period') {
        state.selectedPeriod = value;
      }
      triggerReload();
    });
  });
}

function filterByChips(items) {
  let result = items;

  if (state.selectedCountry !== 'all') {
    result = result.filter((it) => it.country === state.selectedCountry);
  }
  if (state.selectedPeriod !== 'all') {
    result = result.filter((it) => {
      const d = it.usage_days;
      if (!Number.isFinite(d)) return false;
      if (state.selectedPeriod === '1~3일') return d >= 1 && d <= 3;
      if (state.selectedPeriod === '4~7일') return d >= 4 && d <= 7;
      if (state.selectedPeriod === '8일+') return d >= 8;
      return true;
    });
  }

  return result;
}

function renderSummaryCards(items) {
  if (!el.summaryGrid) return;
  const total = items.length;
  const withUnit = items.map(computeUnitPrice).filter((n) => Number.isFinite(n));
  const avgDaily = withUnit.length ? Math.round(withUnit.reduce((a, b) => a + b, 0) / withUnit.length) : null;
  const minDaily = withUnit.length ? Math.min(...withUnit) : null;
  const localCount = items.filter((it) => it.network_type === 'local').length;
  const roamingCount = items.filter((it) => it.network_type === 'roaming').length;
  const localPct = total ? Math.round((localCount / total) * 100) : 0;
  const roamingPct = total ? Math.round((roamingCount / total) * 100) : 0;
  const unknownPct = total ? 100 - localPct - roamingPct : 0;
  const generationSummary = buildNetworkGenerationCounts(items, 'network_generation');
  const fiveGShare = generationSummary.shares['5g_capable'] || 0;
  const lteShare = generationSummary.shares['lte_4g_only'] || 0;
  const generationUnknownShare = generationSummary.shares.unknown || 0;
  const knownFiveGShare = generationSummary.knownOnlyShares['5g_capable'] || 0;

  const datasetCount = state.datasets.length;

  el.summaryGrid.innerHTML = `
    <div class="summary-card">
      <div class="summary-icon">&#128230;</div>
      <div class="summary-label">전체 상품 수</div>
      <div class="summary-value">${total.toLocaleString('ko-KR')}</div>
      <div class="summary-sub">${Object.keys(COUNTRY_CONFIG).length}개국 · Amazon US · ${datasetCount}개 데이터셋</div>
    </div>
    <div class="summary-card">
      <div class="summary-icon">&#128176;</div>
      <div class="summary-label">평균 1일 가격</div>
      <div class="summary-value green">${avgDaily !== null ? `₩${avgDaily.toLocaleString('ko-KR')}` : '-'}</div>
      <div class="summary-sub">전체 상품 평균 (USD&rarr;KRW 환율 적용)</div>
    </div>
    <div class="summary-card">
      <div class="summary-icon">&#127942;</div>
      <div class="summary-label">최저가 (1일당)</div>
      <div class="summary-value highlight">${minDaily !== null ? `₩${minDaily.toLocaleString('ko-KR')}` : '-'}</div>
      <div class="summary-sub">필터 적용 후 최저 1일당 가격</div>
    </div>
    <div class="summary-card">
      <div class="summary-icon">&#128225;</div>
      <div class="summary-label">Local 네트워크 비율</div>
      <div class="summary-value teal">${localPct}%</div>
      <div class="summary-sub">로밍 ${roamingPct}% · 미확인 ${unknownPct}%</div>
    </div>
    <div class="summary-card">
      <div class="summary-icon">&#128246;</div>
      <div class="summary-label">5G 지원 비율</div>
      <div class="summary-value teal">${fiveGShare}%</div>
      <div class="summary-sub">확정 기준 · LTE/4G ${lteShare}% · 미확인 ${generationUnknownShare}% · 확인분 기준 5G ${knownFiveGShare}%</div>
    </div>
  `;
}

function renderHeatmap(items) {
  if (!el.heatmapHead || !el.heatmapBody) return;
  const countries = getVisibleCountryCodes();
  const periodLabels = PERIOD_GROUPS;
  const isAvg = state.heatmapMode === 'avg';

  if (el.heatmapTitle) {
    el.heatmapTitle.textContent = `국가별 · 기간별 ${isAvg ? '평균가' : '최저가'} (1일당, KRW)`;
  }

  if (el.heatmapModeMin) el.heatmapModeMin.classList.toggle('active', !isAvg);
  if (el.heatmapModeAvg) el.heatmapModeAvg.classList.toggle('active', isAvg);

  const allCellPrices = [];
  const precomputed = countries.map((code) => {
    const cfg = COUNTRY_CONFIG[code];
    const countryItems = items.filter((it) => it.country === code);
    const cells = periodLabels.map((period, idx) => {
      const [lo, hi] = PERIOD_RANGES[idx];
      const periodItems = countryItems.filter((it) => Number.isFinite(it.usage_days) && it.usage_days >= lo && it.usage_days <= hi);
      const unitPrices = periodItems.map(computeUnitPrice).filter((n) => Number.isFinite(n));
      if (!unitPrices.length) return { price: null };
      const value = isAvg ? Math.round(unitPrices.reduce((a, b) => a + b, 0) / unitPrices.length) : Math.min(...unitPrices);
      allCellPrices.push(value);
      return { price: value };
    });
    return { code, flag: cfg.flag, label: cfg.label, cells };
  });

  const thresholds = buildHeatThresholds(allCellPrices);

  el.heatmapHead.innerHTML = `<tr><th class="country-header">국가</th>${periodLabels.map((p) => `<th>${safe(p)}</th>`).join('')}</tr>`;

  el.heatmapBody.innerHTML = precomputed.map((row) => `<tr><td><div class="heatmap-country"><span class="flag">${safe(row.flag)}</span> ${safe(row.label)}</div></td>${row.cells.map((c) => {
    const cls = heatClassDynamic(c.price, thresholds);
    return `<td class="heatmap-cell ${cls}">${c.price !== null ? `<span class="heatmap-price">₩${c.price.toLocaleString('ko-KR')}</span><span class="heatmap-unit">/일</span>` : '<span style="color:var(--muted);">-</span>'}</td>`;
  }).join('')}</tr>`).join('');
}

function renderRanking(items) {
  if (!el.rankingList) return;
  const ranked = items
    .map((it) => ({ ...it, unitPrice: computeUnitPrice(it) }))
    .filter((it) => Number.isFinite(it.unitPrice))
    .sort((a, b) => a.unitPrice - b.unitPrice)
    .slice(0, 10);

  if (!ranked.length) {
    el.rankingList.innerHTML = '<p class="empty">표시할 데이터가 없습니다.</p>';
    return;
  }

  el.rankingList.innerHTML = ranked.map((it, idx) => {
    const rankCls = idx === 0 ? 'gold' : idx === 1 ? 'silver' : idx === 2 ? 'bronze' : '';
    const rankSymbol = idx < 3 ? ['🥇', '🥈', '🥉'][idx] : String(idx + 1);
    const countryCfg = COUNTRY_CONFIG[it.country] || {};
    const flag = countryCfg.flag || '';
    const badge = it.network_type === 'local' ? '<span class="ranking-badge-tag badge-local">Local</span>' : it.network_type === 'roaming' ? '<span class="ranking-badge-tag badge-roaming">Roaming</span>' : '';

    return `<div class="ranking-item">
      <div class="ranking-rank ${rankCls}">${rankSymbol}</div>
      <div class="ranking-product">
        <div class="ranking-title">${safe(it.title)}</div>
        <div class="ranking-meta">${flag} ${safe(countryCfg.label || it.country)} · Amazon · ${safe(it.usage_validity || '-')} · ${safe(it.data_amount || '-')} · ${safe(it.seller || '-')}</div>
      </div>
      <div class="ranking-price">${usd(it.price_usd)}</div>
      <div class="ranking-unit-price">₩${it.unitPrice.toLocaleString('ko-KR')}/일</div>
      <div class="ranking-badge">${badge}</div>
    </div>`;
  }).join('');
}

function renderBarChart(container, entries, barColor) {
  if (!container) return;
  if (!entries.length) {
    container.innerHTML = '<p class="empty">표시할 데이터가 없습니다.</p>';
    return;
  }
  const max = Math.max(...entries.map((e) => e[1]), 1);
  container.innerHTML = entries.map(([label, count]) => {
    const pct = Math.max(4, Math.round((count / max) * 100));
    const total = entries.reduce((s, e) => s + e[1], 0);
    const ratio = total ? Math.round((count / total) * 100) : 0;
    return `<div class="bar-row">
      <div class="bar-label">${safe(label)}</div>
      <div class="bar-track-lg"><div class="bar-fill-lg ${barColor}" style="width:${pct}%">${ratio}%</div></div>
      <div class="bar-count">${count.toLocaleString('ko-KR')}</div>
    </div>`;
  }).join('');
}

function renderCharts(items) {
  // 네트워크 분포
  const networkMap = {};
  items.forEach((it) => { const n = it.network_type || 'unknown'; networkMap[n] = (networkMap[n] || 0) + 1; });
  const networkOrder = ['local', 'roaming', 'unknown'];
  const networkLabels = { local: 'Local', roaming: 'Roaming', unknown: '미확인' };
  const networkColors = { local: 'green-bar', roaming: 'amber-bar', unknown: 'red-bar' };
  const networkEntries = networkOrder
    .filter((k) => (networkMap[k] || 0) > 0)
    .map((k) => [networkLabels[k], networkMap[k], networkColors[k]]);
  if (el.networkChart) {
    const max = Math.max(...networkEntries.map((e) => e[1]), 1);
    const total = networkEntries.reduce((s, e) => s + e[1], 0);
    el.networkChart.innerHTML = networkEntries.map(([label, count, color]) => {
      const pct = Math.max(4, Math.round((count / max) * 100));
      const ratio = total ? Math.round((count / total) * 100) : 0;
      return `<div class="bar-row">
        <div class="bar-label">${safe(label)}</div>
        <div class="bar-track-lg"><div class="bar-fill-lg ${color}" style="width:${pct}%">${ratio}%</div></div>
        <div class="bar-count">${count.toLocaleString('ko-KR')}</div>
      </div>`;
    }).join('');
  }

  // 통신사별 상품 수 (미확인 포함)
  const countryCode = state.selectedCountry === 'all' ? 'kr' : state.selectedCountry;
  const carrierDefs = getCarrierDefinitions(countryCode);
  const carrierEntries = carrierDefs
    .map(([code, label]) => [label, items.filter((it) => it.carrier_support_local && it.carrier_support_local[code]).length])
    .filter(([, count]) => count > 0)
    .sort((a, b) => b[1] - a[1]);
  const carrierKnownCount = items.filter((it) => Object.values(it.carrier_support_local || {}).some(Boolean)).length;
  const carrierUnknownCount = items.length - carrierKnownCount;
  if (carrierUnknownCount > 0) carrierEntries.push(['미확인', carrierUnknownCount]);
  renderBarChart(el.carrierChart, carrierEntries, 'teal-bar');
  if (el.carrierChart) {
    el.carrierChart.querySelectorAll('.bar-fill-lg').forEach((fill, i) => {
      if (carrierEntries[i] && carrierEntries[i][0] === '미확인') {
        fill.className = 'bar-fill-lg red-bar';
      }
    });
  }

  // 가격대 분포 (색상별, KRW 기준)
  const priceBuckets = [
    ['~₩5K', (p) => p <= 5000, 'green-bar'],
    ['₩5K~₩10K', (p) => p > 5000 && p <= 10000, 'green-bar'],
    ['₩10K~₩20K', (p) => p > 10000 && p <= 20000, 'teal-bar'],
    ['₩20K~₩30K', (p) => p > 20000 && p <= 30000, 'amber-bar'],
    ['₩30K~', (p) => p > 30000, 'red-bar'],
  ];
  const priceEntries = priceBuckets.map(([label, fn, color]) => ({
    label,
    count: items.filter((it) => Number.isFinite(it.price_krw) && fn(it.price_krw)).length,
    color,
  }));
  if (el.priceChart) {
    const max = Math.max(...priceEntries.map((e) => e.count), 1);
    const total = priceEntries.reduce((s, e) => s + e.count, 0);
    el.priceChart.innerHTML = priceEntries.map(({ label, count, color }) => {
      const pct = Math.max(4, Math.round((count / max) * 100));
      const ratio = total ? Math.round((count / total) * 100) : 0;
      return `<div class="bar-row">
        <div class="bar-label">${safe(label)}</div>
        <div class="bar-track-lg"><div class="bar-fill-lg ${color}" style="width:${pct}%">${ratio}%</div></div>
        <div class="bar-count">${count.toLocaleString('ko-KR')}</div>
      </div>`;
    }).join('');
  }
}

function renderLocalView() {
  updateAmazonReviewVisibility(state.items);
  renderSiteStructure();
  renderFilterChips();
  const chipFiltered = filterByChips(state.items);
  state.filtered = applyLocalFilters(chipFiltered);
  state.currentPage = 1;
  renderSummaryCards(chipFiltered);
  renderHeatmap(chipFiltered);
  renderRanking(state.filtered);
  renderCharts(state.filtered);
  renderTable();
}

function resolveDataPath(pathValue, fallbackPath) {
  if (!pathValue) return fallbackPath;
  const trimmed = String(pathValue).trim();
  if (trimmed.startsWith('./')) return trimmed;
  if (trimmed.startsWith('/')) return `.${trimmed}`;
  return `./data/${trimmed}`;
}

async function loadIndexData() {
  const url = IS_GITHUB_PAGES ? './data/index.json' : '/api/index';
  try {
    const res = await fetch(url, { cache: 'no-store' });
    if (!res.ok) return { latest: {}, runs: [] };
    return await res.json();
  } catch (_) {
    return { latest: {}, runs: [] };
  }
}

async function loadDataStaticFromRecord(record) {
  const country = (record && record.country) || state.selectedCountry || 'kr';
  const site = (record && record.site) || state.selectedSite;
  const jsonlFallback = `./data/sites/${site}/${country}/latest.jsonl`;
  const finalJsonlPath = resolveDataPath(record && record.jsonl, jsonlFallback);
  const csvPath = resolveDataPath(record && record.csv, `./data/sites/${site}/${country}/latest.csv`);
  const metaPath = resolveDataPath(record && record.metadata, `./data/sites/${site}/${country}/metadata.json`);
  const res = await fetch(finalJsonlPath, { cache: 'no-store' });
  if (!res.ok) throw new Error(`정적 데이터 로드 실패: HTTP ${res.status}`);
  const items = parseJsonl(await res.text()).map(normalizeItem).filter(keepDashboardItem);
  let metadata = null;
  if (record && (record.crawled_at || record.published_at || record.source || record.item_count)) {
    metadata = { source: record.source || finalJsonlPath, crawled_at: record.crawled_at || null, published_at: record.published_at || null, item_count: record.item_count || items.length, site: record.site || site, country: record.country || country };
  } else {
    try {
      const metaRes = await fetch(metaPath, { cache: 'no-store' });
      if (metaRes.ok) metadata = await metaRes.json();
    } catch (_) { metadata = null; }
  }
  state.exchangeRate = await resolveExchangeRateMeta(null);
  state.items = FX.attachKrwPrices(items, state.exchangeRate);
  state.totalBeforeFilter = items.length;
  state.file = metadata && metadata.source ? metadata.source : finalJsonlPath;
  state.generatedAt = metadata && metadata.crawled_at ? metadata.crawled_at : null;
  state.selectedCsvPath = csvPath;
  el.metaText.textContent = `사이트: ${siteLabel(site)} | 국가: ${countryLabel(country)} | 파일: ${state.file} | 추출: ${isoToLocal(state.generatedAt)} | 반영: ${isoToLocal(metadata && metadata.published_at)} | 원본 ${state.totalBeforeFilter.toLocaleString('ko-KR')}개`;
  renderExchangeRateMeta();
  renderSiteStructure();
  renderFilterOptions(state.items);
  renderLocalView();
}

async function loadDataFromDatasetGroup(group) {
  const loads = group.entries.map((entry) => {
    const country = entry.country || 'kr';
    const site = entry.site || group.site;
    const jsonlPath = resolveDataPath(entry.jsonl, `./data/sites/${site}/${country}/latest.jsonl`);
    return fetch(jsonlPath, { cache: 'no-store' })
      .then((res) => (res.ok ? res.text() : ''))
      .then((text) => parseJsonl(text).map(normalizeItem).filter(keepDashboardItem))
      .catch(() => []);
  });

  const allItems = (await Promise.all(loads)).flat();
  state.exchangeRate = await resolveExchangeRateMeta(null);
  state.items = FX.attachKrwPrices(allItems, state.exchangeRate);
  state.totalBeforeFilter = allItems.length;
  state.file = `${group.date} 데이터셋 (${group.countries.size}개국)`;
  state.generatedAt = group.crawledAt;
  el.metaText.textContent = `사이트: ${siteLabel(group.site)} | 데이터셋: ${group.date} | ${group.countries.size}개국 통합 | 추출: ${isoToLocal(group.crawledAt)} | 원본 ${state.totalBeforeFilter.toLocaleString('ko-KR')}개`;
  renderExchangeRateMeta();
  renderSiteStructure();
  renderFilterOptions(state.items);
  renderLocalView();
}

async function loadDataStatic() {
  const index = await loadIndexData();
  state.datasets = Array.isArray(index.runs) ? index.runs : [];
  populateSiteOptions(index);
  populateCountryOptions(index);
  const datasets = getGroupedDatasetsForSelectedSite();
  if (state.selectedDatasetId && !datasets.some((d) => String(d.id) === String(state.selectedDatasetId))) state.selectedDatasetId = null;
  populateDatasetOptions(datasets);
  if (state.selectedDatasetId) {
    const selected = datasets.find((d) => String(d.id) === String(state.selectedDatasetId));
    if (selected) return loadDataFromDatasetGroup(selected);
  }

  if (state.selectedCountry === 'all') {
    return loadAllCountriesStatic(index);
  }

  const latestBySite = index.latest && index.latest[state.selectedSite] ? index.latest[state.selectedSite] : null;
  return loadDataStaticFromRecord(latestBySite && latestBySite[state.selectedCountry] ? latestBySite[state.selectedCountry] : null);
}

async function loadAllCountriesStatic(index) {
  const sites = [state.selectedSite];
  const countries = getVisibleCountryCodes();
  const loads = [];

  for (const site of sites) {
    for (const country of countries) {
      const latestBySite = index.latest && index.latest[site] ? index.latest[site] : null;
      const record = latestBySite && latestBySite[country] ? latestBySite[country] : null;
      const jsonlPath = record && record.jsonl ? resolveDataPath(record.jsonl, `./data/sites/${site}/${country}/latest.jsonl`) : `./data/sites/${site}/${country}/latest.jsonl`;
      loads.push(
        fetch(jsonlPath, { cache: 'no-store' })
          .then((res) => (res.ok ? res.text() : ''))
          .then((text) => parseJsonl(text).map(normalizeItem).filter(keepDashboardItem))
          .catch(() => []),
      );
    }
  }

  const allItems = (await Promise.all(loads)).flat();
  state.exchangeRate = await resolveExchangeRateMeta(null);
  state.items = FX.attachKrwPrices(allItems, state.exchangeRate);
  state.totalBeforeFilter = allItems.length;
  state.file = '전체 국가';
  state.generatedAt = null;
  el.metaText.textContent = `전체 국가 · ${siteLabel(state.selectedSite)} | 원본 ${state.totalBeforeFilter.toLocaleString('ko-KR')}개`;
  renderExchangeRateMeta();
  renderFilterChips();
  renderFilterOptions(state.items);
  renderLocalView();
}

async function loadData() {
  if (IS_GITHUB_PAGES) return loadDataStatic();
  const index = await loadIndexData();
  state.datasets = Array.isArray(index.runs) ? index.runs : [];
  populateSiteOptions(index);
  populateCountryOptions(index);
  const datasets = getGroupedDatasetsForSelectedSite();
  if (state.selectedDatasetId && !datasets.some((d) => String(d.id) === String(state.selectedDatasetId))) state.selectedDatasetId = null;
  populateDatasetOptions(datasets);
  const qs = toQuery();
  const res = await fetch(qs ? `/api/latest?${qs}` : '/api/latest', { cache: 'no-store' });
  const data = await res.json();
  renderSiteStructure();
  if (!data.found) {
    state.items = [];
    state.filtered = [];
    state.exchangeRate = FX.buildExchangeRateMeta({ unavailable: true, stale: true });
    el.metaText.textContent = data.message || '데이터가 없습니다.';
    renderExchangeRateMeta();
    renderSummaryCards([]);
    renderHeatmap([]);
    renderRanking([]);
    renderCharts([]);
    renderTable();
    return;
  }
  state.exchangeRate = await resolveExchangeRateMeta(data.exchangeRate || null);
  state.items = FX.attachKrwPrices(data.items.map(normalizeItem), state.exchangeRate);
  state.filtered = state.items;
  state.totalBeforeFilter = data.totalBeforeFilter || data.items.length;
  state.file = data.file;
  state.generatedAt = data.generatedAt;
  state.currentPage = 1;
  el.metaText.textContent = `사이트: ${siteLabel(state.selectedSite)} | 국가: ${countryLabel(state.selectedCountry)} | 파일: ${data.file} | 생성: ${isoToLocal(data.generatedAt)} | 원본 ${state.totalBeforeFilter.toLocaleString('ko-KR')}개`;
  renderExchangeRateMeta();
  renderFilterOptions(state.items);
  renderLocalView();
}

function triggerReload() {
  loadData().catch((err) => {
    el.metaText.textContent = `로드 실패: ${err.message}`;
  });
}

for (const input of [el.searchInput, el.networkFilter, el.generationFilter, el.dataFilter, el.usageFilter, el.carrierFilter, el.minPrice, el.maxPrice, el.sortKey].filter(Boolean)) {
  const evt = input.tagName === 'INPUT' ? 'input' : 'change';
  input.addEventListener(evt, triggerReload);
}

if (el.siteSelect) el.siteSelect.addEventListener('change', () => {
  state.selectedSite = el.siteSelect.value || 'amazon_us';
  state.selectedDatasetId = null;
  renderSiteStructure();
  triggerReload();
});

if (el.countrySelect) el.countrySelect.addEventListener('change', () => {
  state.selectedCountry = el.countrySelect.value || 'all';
  state.selectedDatasetId = null;
  triggerReload();
});

el.datasetSelect.addEventListener('change', () => {
  state.selectedDatasetId = el.datasetSelect.value || null;
  triggerReload();
});

el.refreshBtn.addEventListener('click', triggerReload);
el.helpBtn.addEventListener('click', openHelpModal);
el.helpCloseBtn.addEventListener('click', closeHelpModal);

// 히트맵 모드 토글
[el.heatmapModeMin, el.heatmapModeAvg].filter(Boolean).forEach((chip) => {
  chip.addEventListener('click', () => {
    state.heatmapMode = chip.dataset.mode;
    renderLocalView();
  });
});
el.helpOverlay.addEventListener('click', (event) => {
  if (event.target === el.helpOverlay) closeHelpModal();
});
document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && isHelpOpen()) closeHelpModal();
});
el.prevPage.addEventListener('click', () => { state.currentPage = Math.max(1, state.currentPage - 1); renderTable(); });
el.nextPage.addEventListener('click', () => { const totalPages = Math.max(1, Math.ceil(state.filtered.length / pageSize)); state.currentPage = Math.min(totalPages, state.currentPage + 1); renderTable(); });
el.downloadExcelBtn.addEventListener('click', downloadFilteredExcel);
el.downloadExcelBtn2.addEventListener('click', downloadAllExcel);

renderSiteStructure();
renderExchangeRateMeta();
triggerReload();

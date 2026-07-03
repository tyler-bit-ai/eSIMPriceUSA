from __future__ import annotations

import re
from dataclasses import dataclass

from app.carriers import get_country_carrier_codes, get_country_carriers
from app.models import NetworkGeneration, NetworkType

PRICE_PATTERN = re.compile(r"(?:\$|USD\s?)\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)")
AMOUNT_PATTERN = re.compile(r"([0-9][0-9,]*(?:\.[0-9]{1,2})?)")
DATA_PATTERN = re.compile(
    r"("
    r"(?:\d+(?:\.\d+)?)\s?GB\s*/\s*day|"
    r"(?:\d+(?:\.\d+)?)\s?MB\s*/\s*day|"
    r"(?:up to\s*)?(?:\d+(?:\.\d+)?)\s?(?:GB|MB)\s*(?:per|/)\s*day|"
    r"(?:up to\s*)?(?:\d+(?:\.\d+)?)\s?GB|"
    r"unlimited data|unlimited|data\s+unlimited"
    r")",
    re.IGNORECASE,
)
VALIDITY_PATTERNS = [
    re.compile(r"(\d{1,3})[\s-]?(?:days?)\b", re.IGNORECASE),
    re.compile(r"(\d{1,3})\s?(?:hours?)\b", re.IGNORECASE),
    re.compile(r"(?:validity|valid\s+for|usage\s+period)\s*[:：]?\s*([^\n\r.]+)", re.IGNORECASE),
    re.compile(r"(GB\s?used\s?up|until\s+data\s+is\s+used)", re.IGNORECASE),
]
REVIEW_PATTERNS = [
    re.compile(r"([0-9][0-9,]*)\s*(?:ratings?|customer reviews?|global ratings?)", re.IGNORECASE),
    re.compile(r'"(?:reviewCount|ratingCount)"\s*:\s*"?([0-9][0-9,]*)"?', re.IGNORECASE),
]
NETWORK_GENERATION_5G_PATTERNS = [
    re.compile(r"5\s*G\s*(?:support|supported|available|network|capable|ready)", re.IGNORECASE),
    re.compile(r"4\s*G\s*/\s*5\s*G", re.IGNORECASE),
    re.compile(r"5\s*G\s*/\s*4\s*G", re.IGNORECASE),
    re.compile(r"5\s*G[\s,/]+(?:4\s*G|LTE)", re.IGNORECASE),
    re.compile(r"(?:4\s*G|LTE)[\s,/]+5\s*G", re.IGNORECASE),
]
NETWORK_GENERATION_4G_PATTERNS = [
    re.compile(r"4\s*G\s*/\s*LTE", re.IGNORECASE),
    re.compile(r"LTE\s*/\s*4\s*G", re.IGNORECASE),
    re.compile(r"(?:4\s*G|LTE)\s*(?:support|supported|available|network|capable)", re.IGNORECASE),
    re.compile(r"(?:4\s*G|LTE)(?:\s*/\s*LTE)?\s*only", re.IGNORECASE),
]
NETWORK_GENERATION_CELLULAR_5G_PATTERNS = [
    re.compile(r"cellular\s+technology\s*[:：]?\s*5\s*G", re.IGNORECASE),
]
NETWORK_GENERATION_CELLULAR_4G_PATTERNS = [
    re.compile(r"cellular\s+technology\s*[:：]?\s*(?:LTE|4\s*G)", re.IGNORECASE),
]
NETWORK_GENERATION_TRANSMISSION_5G_PATTERNS = [
    re.compile(
        r"transmission\s+speed\s*[:：]?\s*(?:5\s*G|4\s*G\s*/\s*5\s*G|5\s*G\s*/\s*4\s*G)",
        re.IGNORECASE,
    ),
]
NETWORK_GENERATION_TRANSMISSION_4G_PATTERNS = [
    re.compile(r"transmission\s+speed\s*[:：]?\s*(?:LTE|4\s*G)", re.IGNORECASE),
]
NETWORK_GENERATION_5G_NEGATIVE_PATTERNS = [
    re.compile(r"(?:no|not)\s*5\s*G", re.IGNORECASE),
    re.compile(r"5\s*G\s*not\s+supported", re.IGNORECASE),
]
NETWORK_GENERATION_ANY_5G_PATTERN = re.compile(r"5\s*G", re.IGNORECASE)
NETWORK_GENERATION_ANY_4G_PATTERN = re.compile(r"(?:4\s*G|LTE)", re.IGNORECASE)


@dataclass
class ExtractedValue:
    value: str | int | float | bool | None
    evidence: list[str]


@dataclass
class ValidityExtraction:
    usage_validity: str | None
    activation_validity: str | None
    usage_evidence: list[str]
    activation_evidence: list[str]


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_price_text(text: str) -> tuple[float | None, str | None]:
    normalized = normalize_text(text)
    amount_match = AMOUNT_PATTERN.search(normalized)
    if not amount_match:
        return None, None

    amount = float(amount_match.group(1).replace(",", ""))
    upper = normalized.upper()
    if "SGD" in upper or "S$" in normalized:
        return amount, "SGD"
    if "KRW" in upper:
        return amount, "KRW"
    if "JPY" in upper or "円" in normalized:
        return amount, "JPY"
    if "EUR" in upper:
        return amount, "EUR"
    if "USD" in upper or "$" in normalized:
        return amount, "USD"
    return amount, None


def extract_price_usd_with_evidence(
    texts: list[str],
    assume_usd_on_unknown_currency: bool = False,
) -> tuple[ExtractedValue, list[str]]:
    non_usd_evidence: list[str] = []
    for raw in texts:
        text = normalize_text(raw)
        amount, currency = parse_price_text(text)
        if amount is None:
            continue
        if currency == "USD":
            return ExtractedValue(amount, [text[:180]]), non_usd_evidence
        if currency in {"KRW", "JPY", "EUR", "SGD"}:
            non_usd_evidence.append(text[:180])
            continue
        if assume_usd_on_unknown_currency:
            return ExtractedValue(amount, [f"{text[:150]} (assumed USD by i18n-prefs)"]), non_usd_evidence

    return ExtractedValue(None, []), non_usd_evidence


def extract_review_count(texts: list[str]) -> ExtractedValue:
    for raw in texts:
        text = normalize_text(raw)
        for pattern in REVIEW_PATTERNS:
            match = pattern.search(text)
            if not match:
                continue
            count = int(match.group(1).replace(",", ""))
            return ExtractedValue(count, [text[:180]])
    return ExtractedValue(None, [])


def extract_data_amount(texts: list[str]) -> ExtractedValue:
    for raw in texts:
        text = normalize_text(raw)
        val = _extract_data_amount_value(text)
        if not val:
            continue
        return ExtractedValue(val, [text[:180]])
    return ExtractedValue(None, [])


def _normalize_data_amount(raw_value: str) -> str:
    lower = raw_value.lower()
    if "unlimited" in lower:
        return "unlimited"

    m_day = re.search(r"(\d+(?:\.\d+)?)\s?(gb|mb)\s*(?:/|per)\s*day", lower, re.IGNORECASE)
    if m_day:
        amount = _format_numeric_token(m_day.group(1))
        unit = m_day.group(2).upper()
        return f"{amount}{unit}/day"

    m = re.search(r"(\d+(?:\.\d+)?)\s?gb", lower, re.IGNORECASE)
    if m:
        amount = _format_numeric_token(m.group(1))
        return f"{amount}GB"
    mb = re.search(r"(\d+(?:\.\d+)?)\s?mb", lower, re.IGNORECASE)
    if mb:
        amount = _format_numeric_token(mb.group(1))
        return f"{amount}MB"
    return raw_value


def _extract_data_amount_value(text: str) -> str | None:
    daily_pattern = re.compile(r"(\d+(?:\.\d+)?)\s?(GB|MB)\s*(?:/|per)\s*day", re.IGNORECASE)
    match = daily_pattern.search(text)
    if match:
        amount = _format_numeric_token(match.group(1))
        unit = match.group(2).upper()
        return f"{amount}{unit}/day"

    m = DATA_PATTERN.search(text)
    if not m:
        return None
    return _normalize_data_amount(m.group(0))


def _format_numeric_token(value: str) -> str:
    if "." in value:
        return value.rstrip("0").rstrip(".")
    return value


def extract_validity(texts: list[str]) -> ExtractedValue:
    split = extract_validity_split(texts)
    if split.usage_validity:
        return ExtractedValue(split.usage_validity, split.usage_evidence)
    if split.activation_validity:
        return ExtractedValue(split.activation_validity, split.activation_evidence)
    return ExtractedValue(None, [])


def extract_validity_split(texts: list[str]) -> ValidityExtraction:
    usage_keywords = ("usage period", "travel days", "days plan", "valid for", "days of use")
    activation_keywords = ("activate within", "must be activated", "expires", "activation period", "activate")
    noise_keywords = ("customer support", "contact us", "24/7 support", "support team")
    usage_validity: str | None = None
    activation_validity: str | None = None
    usage_evidence: list[str] = []
    activation_evidence: list[str] = []

    for idx, raw in enumerate(texts):
        text = normalize_text(raw)
        lower = text.lower()

        day_hits = _extract_day_hits(text)
        hour_hits = re.findall(r"(\d{1,3})\s?(?:hours?)\b", text, re.IGNORECASE)
        normalized_day_hits = [str(_hours_to_days(int(hour))) for hour in hour_hits if _hours_to_days(int(hour)) is not None]
        duration_hits = day_hits + normalized_day_hits
        has_usage_context = any(k.lower() in lower for k in usage_keywords)
        has_activation_context = any(k.lower() in lower for k in activation_keywords)
        has_noise_context = any(k.lower() in lower for k in noise_keywords)
        has_plan_signal = (
            "day" in lower
            or "hour" in lower
            or "plan" in lower
            or "unlimited" in lower
            or bool(re.search(r"\d+\s*GB", text, re.IGNORECASE))
        )

        if duration_hits:
            # Title is usually the strongest signal for actual usage duration.
            if idx == 0 and not usage_validity:
                usage_validity = f"{duration_hits[0]}일"
                usage_evidence.append(text[:180])
                if has_activation_context and len(duration_hits) >= 2 and not activation_validity:
                    activation_validity = f"{duration_hits[-1]}일"
                    activation_evidence.append(text[:180])
            elif has_usage_context and has_activation_context and len(duration_hits) >= 2:
                if not usage_validity:
                    usage_validity = f"{duration_hits[0]}일"
                    usage_evidence.append(text[:180])
                if not activation_validity:
                    activation_validity = f"{duration_hits[-1]}일"
                    activation_evidence.append(text[:180])
            elif has_activation_context and len(duration_hits) >= 2:
                if not usage_validity:
                    usage_validity = f"{duration_hits[0]}일"
                    usage_evidence.append(text[:180])
                if not activation_validity:
                    activation_validity = f"{duration_hits[-1]}일"
                    activation_evidence.append(text[:180])
            elif has_activation_context and not activation_validity:
                activation_validity = f"{duration_hits[0]}일"
                activation_evidence.append(text[:180])
            elif (not usage_validity) and has_plan_signal and (not has_noise_context):
                usage_validity = f"{duration_hits[0]}일"
                usage_evidence.append(text[:180])

        if not usage_validity:
            m_usage = re.search(r"(GB\s?used\s?up|until\s+data\s+is\s+used)", text, re.IGNORECASE)
            if m_usage:
                usage_validity = m_usage.group(1)
                usage_evidence.append(text[:180])

        if (not usage_validity or not activation_validity) and ("expires" in lower or "usage period" in lower or "validity" in lower):
            m_label = re.search(r"(?:validity|valid\s+for|usage\s+period)\s*[:：]?\s*([^\n\r.]+)", text, re.IGNORECASE)
            if m_label:
                captured = m_label.group(1).strip()
                captured_norm = _normalize_labeled_validity(captured)
                if not captured_norm:
                    continue
                if "expires" in lower:
                    if not activation_validity:
                        activation_validity = captured_norm
                        activation_evidence.append(text[:180])
                elif not usage_validity:
                    usage_validity = captured_norm
                    usage_evidence.append(text[:180])

        if usage_validity and activation_validity:
            break

    usage_num = _extract_korean_days(usage_validity)
    activation_num = _extract_korean_days(activation_validity)
    if usage_num is not None and activation_num is not None and activation_num < usage_num:
        usage_validity, activation_validity = activation_validity, usage_validity
        usage_evidence, activation_evidence = activation_evidence, usage_evidence

    return ValidityExtraction(
        usage_validity=usage_validity,
        activation_validity=activation_validity,
        usage_evidence=usage_evidence,
        activation_evidence=activation_evidence,
    )


def _extract_korean_days(value: str | None) -> int | None:
    if not value:
        return None
    m = re.search(r"(\d{1,4})\s*일", value)
    if m:
        return int(m.group(1))
    return None


def _normalize_labeled_validity(value: str) -> str | None:
    text = normalize_text(value)
    day = re.search(r"(\d{1,4})(?:\s*[-~]\s*\d{1,4})?\s?days?\b", text, re.IGNORECASE)
    if day:
        return f"{day.group(1)}일"
    hours = re.search(r"(\d{1,4})\s?hours?\b", text, re.IGNORECASE)
    if hours:
        days = _hours_to_days(int(hours.group(1)))
        if days is not None:
            return f"{days}일"
    if re.search(r"(GB\s?used\s?up|until\s+data\s+is\s+used)", text, re.IGNORECASE):
        return "GB used up"
    return None


def _hours_to_days(hours: int) -> int | None:
    if hours <= 0:
        return None
    return max(1, hours // 24)


def _extract_day_hits(text: str) -> list[str]:
    hits: list[str] = []
    for match in re.finditer(r"(\d{1,4})(?:\s*[-~]\s*\d{1,4})?[\s-]?days?\b", text, re.IGNORECASE):
        hits.append(match.group(1))
    return hits


def extract_network_type(texts: list[str]) -> tuple[NetworkType, list[str]]:
    local_score = 0
    roaming_score = 0
    local_hits: list[str] = []
    roaming_hits: list[str] = []

    local_strong_patterns = [
        re.compile(r"local\s+(?:network|carrier|number|sim)", re.IGNORECASE),
        re.compile(r"local\s+phone\s+number", re.IGNORECASE),
        re.compile(r"(?:call|talk)\s*(?:and|/)\s*(?:sms|text)\s+(?:included|available)", re.IGNORECASE),
        re.compile(r"local\s+data\s+plan", re.IGNORECASE),
    ]
    local_soft_patterns = [
        re.compile(r"official\s+carrier", re.IGNORECASE),
        re.compile(r"genuine\s+eSIM", re.IGNORECASE),
    ]
    roaming_strong_patterns = [
        re.compile(r"international\s+roaming", re.IGNORECASE),
        re.compile(r"data\s+roaming", re.IGNORECASE),
        re.compile(r"roaming\s+plan", re.IGNORECASE),
    ]
    roaming_noise_patterns = [
        re.compile(r"roaming\s+center", re.IGNORECASE),
    ]
    roaming_negative_patterns = [
        re.compile(r"no\s+roaming", re.IGNORECASE),
        re.compile(r"roaming[\s-]free", re.IGNORECASE),
    ]
    noise_penalty_applied = False
    negative_penalty_applied = False

    for raw in texts:
        text = normalize_text(raw)
        lower = text.lower()

        has_local_strong = any(p.search(text) for p in local_strong_patterns)
        has_roaming_strong = any(p.search(text) for p in roaming_strong_patterns)
        has_roaming_noise = any(p.search(text) for p in roaming_noise_patterns)
        has_roaming_negative = any(p.search(text) for p in roaming_negative_patterns)

        if has_local_strong:
            local_score += 3
            local_hits.append(text[:180])
        elif any(p.search(text) for p in local_soft_patterns):
            local_score += 1
            local_hits.append(text[:180])
        elif re.search(r"\blocal\b", lower):
            local_score += 1
            local_hits.append(text[:180])

        if has_roaming_negative and not negative_penalty_applied:
            roaming_score -= 2
            negative_penalty_applied = True

        if has_roaming_strong and not has_roaming_negative:
            roaming_score += 3
            roaming_hits.append(text[:180])
        elif re.search(r"\broaming\b", lower) and not has_roaming_noise and not has_roaming_negative:
            roaming_score += 1
            roaming_hits.append(text[:180])
        elif has_roaming_noise and re.search(r"\broaming\b", lower) and not noise_penalty_applied:
            roaming_score += 0
            noise_penalty_applied = True

    local_threshold = 2
    roaming_threshold = 2
    if local_score >= local_threshold and roaming_score <= 1:
        evidence = local_hits[:2] + [f"score: local={local_score}, roaming={roaming_score}"]
        return NetworkType.local, evidence
    if roaming_score >= roaming_threshold and local_score <= 1:
        evidence = roaming_hits[:2] + [f"score: local={local_score}, roaming={roaming_score}"]
        return NetworkType.roaming, evidence

    evidence = []
    if local_hits:
        evidence.append(f"local_signal: {local_hits[0]}")
    if roaming_hits:
        evidence.append(f"roaming_signal: {roaming_hits[0]}")
    if local_score != 0 or roaming_score != 0:
        evidence.append(f"insufficient_or_conflicting_signals(local={local_score}, roaming={roaming_score})")
    return NetworkType.unknown, evidence


def extract_network_generation(
    strong_texts: list[str],
    fallback_texts: list[str] | None = None,
) -> tuple[NetworkGeneration, list[str]]:
    cellular_texts = _filter_network_generation_source(strong_texts, ("product_info_cellular",))
    transmission_texts = _filter_network_generation_source(strong_texts, ("product_info_transmission",))
    detail_texts = _filter_network_generation_source(
        strong_texts,
        ("feature_bullets", "product_description", "product_details", "detail_bullets"),
    )
    title_texts = _filter_network_generation_source(strong_texts, ("title",))
    other_strong_texts = [
        text
        for text in strong_texts
        if (
            text not in cellular_texts
            and text not in transmission_texts
            and text not in detail_texts
            and text not in title_texts
        )
    ]

    cellular = _classify_network_generation_tier(
        cellular_texts,
        NETWORK_GENERATION_CELLULAR_5G_PATTERNS + NETWORK_GENERATION_5G_PATTERNS,
        NETWORK_GENERATION_CELLULAR_4G_PATTERNS + NETWORK_GENERATION_4G_PATTERNS,
        "product_info_cellular",
    )
    if cellular is not None:
        return cellular

    transmission = _classify_network_generation_tier(
        transmission_texts,
        NETWORK_GENERATION_TRANSMISSION_5G_PATTERNS + NETWORK_GENERATION_5G_PATTERNS,
        NETWORK_GENERATION_TRANSMISSION_4G_PATTERNS + NETWORK_GENERATION_4G_PATTERNS,
        "product_info_transmission",
    )
    if transmission is not None:
        return transmission

    detail = _classify_network_generation_tier(
        detail_texts,
        NETWORK_GENERATION_5G_PATTERNS,
        NETWORK_GENERATION_4G_PATTERNS,
        "product_detail",
    )
    if detail is not None:
        return detail

    title = _classify_network_generation_tier(
        title_texts,
        NETWORK_GENERATION_5G_PATTERNS,
        NETWORK_GENERATION_4G_PATTERNS,
        "title",
    )
    if title is not None:
        return title

    strong_5g_hits = _collect_network_generation_hits(other_strong_texts, NETWORK_GENERATION_5G_PATTERNS, "strong_5g")
    strong_4g_hits = _collect_network_generation_hits(other_strong_texts, NETWORK_GENERATION_4G_PATTERNS, "strong_4g_lte")
    negative_5g_hits = _collect_network_generation_hits(
        other_strong_texts,
        NETWORK_GENERATION_5G_NEGATIVE_PATTERNS,
        "strong_5g_negative",
    )
    fallback = fallback_texts or []
    fallback_5g_hits = _collect_network_generation_hits(
        fallback,
        [NETWORK_GENERATION_ANY_5G_PATTERN],
        "fallback_5g",
    )
    fallback_4g_hits = _collect_network_generation_hits(
        fallback,
        [NETWORK_GENERATION_ANY_4G_PATTERN],
        "fallback_4g_lte",
    )

    if strong_5g_hits and negative_5g_hits:
        return NetworkGeneration.unknown, (
            strong_5g_hits[:1]
            + negative_5g_hits[:1]
            + ["conflicting_strong_network_generation_signals"]
        )

    if strong_5g_hits:
        evidence = strong_5g_hits[:2]
        if strong_4g_hits:
            evidence.append("4g_lte_signal_present_but_5g_capable_takes_precedence")
        return NetworkGeneration.five_g_capable, evidence

    if negative_5g_hits:
        return NetworkGeneration.lte_4g_only, negative_5g_hits[:2]

    if strong_4g_hits:
        if fallback_5g_hits:
            return NetworkGeneration.unknown, (
                strong_4g_hits[:1]
                + fallback_5g_hits[:1]
                + ["fallback_5g_conflicts_with_strong_4g_lte"]
            )
        return NetworkGeneration.lte_4g_only, strong_4g_hits[:2]

    if fallback_5g_hits or fallback_4g_hits:
        return NetworkGeneration.unknown, (
            fallback_5g_hits[:1]
            + fallback_4g_hits[:1]
            + ["fallback_only_network_generation_signal"]
        )

    return NetworkGeneration.unknown, ["no_lte_4g_or_5g_keyword_matched"]


def _filter_network_generation_source(texts: list[str], source_tokens: tuple[str, ...]) -> list[str]:
    filtered: list[str] = []
    for raw in texts:
        normalized = normalize_text(raw)
        lower = normalized.lower()
        if any(f"source:{token}" in lower for token in source_tokens):
            filtered.append(raw)
    return filtered


def _classify_network_generation_tier(
    texts: list[str],
    five_g_patterns: list[re.Pattern[str]],
    four_g_patterns: list[re.Pattern[str]],
    label: str,
) -> tuple[NetworkGeneration, list[str]] | None:
    if not texts:
        return None

    five_g_hits = _collect_network_generation_hits(texts, five_g_patterns, f"{label}_5g")
    four_g_hits = _collect_network_generation_hits(texts, four_g_patterns, f"{label}_4g_lte")
    negative_5g_hits = _collect_network_generation_hits(texts, NETWORK_GENERATION_5G_NEGATIVE_PATTERNS, f"{label}_5g_negative")

    if five_g_hits and negative_5g_hits:
        return NetworkGeneration.unknown, five_g_hits[:1] + negative_5g_hits[:1] + [f"conflicting_{label}_network_generation_signals"]
    if negative_5g_hits:
        return NetworkGeneration.lte_4g_only, negative_5g_hits[:2]
    if five_g_hits:
        evidence = five_g_hits[:2]
        if four_g_hits:
            evidence.append(f"{label}_4g_lte_signal_present_but_5g_capable_takes_precedence")
        return NetworkGeneration.five_g_capable, evidence
    if four_g_hits:
        return NetworkGeneration.lte_4g_only, four_g_hits[:2]
    return None


def _collect_network_generation_hits(
    texts: list[str],
    patterns: list[re.Pattern[str]],
    label: str,
) -> list[str]:
    hits: list[str] = []
    for raw in texts:
        text = normalize_text(raw)
        if not text:
            continue
        if any(pattern.search(text) for pattern in patterns):
            hits.append(f"{label}: {text[:180]}")
    return hits


def extract_carrier_support_local(
    texts: list[str],
    country: str | None,
) -> tuple[dict[str, bool | None], list[str]]:
    carrier_defs = get_country_carriers(country)
    if not carrier_defs:
        return {}, []

    support: dict[str, bool | None] = {
        code: None for code in get_country_carrier_codes(country)
    }
    evidence: list[str] = []

    for raw in texts:
        text = normalize_text(raw)
        lower = text.lower()
        matched_codes: list[str] = []
        for carrier in carrier_defs:
            if any(_contains_carrier_alias(lower, alias) for alias in carrier.aliases):
                support[carrier.code] = True
                matched_codes.append(carrier.label)

        if matched_codes:
            evidence.append(f"{', '.join(matched_codes)}: {text[:150]}")

    return support, evidence


def extract_carrier_support_for_country(
    texts: list[str],
    country: str | None,
) -> tuple[dict[str, bool | None], list[str]]:
    return extract_carrier_support_local(texts, country)


def _contains_carrier_alias(text: str, alias: str) -> bool:
    normalized_alias = normalize_text(alias).lower()
    if not normalized_alias:
        return False
    if re.fullmatch(r"[a-z0-9&+.\- ]+", normalized_alias):
        pattern = rf"(?<![a-z0-9]){re.escape(normalized_alias)}(?![a-z0-9])"
        return re.search(pattern, text) is not None
    return normalized_alias in text


def extract_asin(url: str) -> str | None:
    match = re.search(r"/(?:dp|gp/product)/([A-Z0-9]{10})", url)
    if match:
        return match.group(1)
    return None


def extract_monthly_sold_count(texts: list[str]) -> ExtractedValue:
    patterns = [
        re.compile(r"([0-9][0-9,]*)\+?\s*bought in past month", re.IGNORECASE),
    ]
    for raw in texts:
        text = normalize_text(raw)
        for pat in patterns:
            m = pat.search(text)
            if not m:
                continue
            return ExtractedValue(int(m.group(1).replace(",", "")), [text[:180]])
    return ExtractedValue(None, [])


def extract_bestseller_badge(texts: list[str]) -> ExtractedValue:
    for raw in texts:
        text = normalize_text(raw)
        lower = text.lower()
        if "best seller" in lower or "bestseller" in lower:
            return ExtractedValue(True, [text[:180]])
    return ExtractedValue(None, [])


def extract_bestseller_rank(texts: list[str]) -> ExtractedValue:
    best_rank: int | None = None
    best_evidence: str | None = None
    for raw in texts:
        text = normalize_text(raw)
        if "best sellers rank" not in text.lower():
            continue

        for m in re.finditer(r"#\s*([0-9][0-9,]*)\s*in\b", text, re.IGNORECASE):
            rank = int(m.group(1).replace(",", ""))
            if best_rank is None or rank < best_rank:
                best_rank = rank
                best_evidence = text[:180]

    if best_rank is not None:
        return ExtractedValue(best_rank, [best_evidence] if best_evidence else [])
    return ExtractedValue(None, [])

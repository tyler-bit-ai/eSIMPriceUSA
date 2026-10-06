(function attachTravelFilter(root, factory) {
  const utils = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = utils;
  if (root) root.TravelFilter = utils;
}(typeof globalThis !== 'undefined' ? globalThis : this, function buildTravelFilter() {
  // Keep in sync with app/pipeline/validation.py (tests/test_travel_filter.py checks parity).
  // Rules cover what Amazon US returns for "eSIM <country>" besides travel data plans.
  // A title naming other regions is a multi-country travel plan even if it also says "USA".
  const MULTI_REGION = /worldwide|global|asia|europe|\d+\+? countries|china|hong kong|macau|taiwan|japan|korea|thai|vietnam/i;
  const RULES = [
    // US-domestic plans (the destination is the US, not the searched country)
    ['us_domestic_plan', /T-?Mobile|AT&T|Verizon|Jethro Mobile|\bUSA\b|US Mainland|\bHawaii\b/i, true],
    // eSIM hardware (adapter / reader / reusable physical eSIM card), not a data plan
    ['esim_hardware', /\badapter\b|\breader\b|physical (nano )?esim card|\bSTK\b/i],
    // IoT / tracker / camera SIMs
    ['iot_sim', /\btracker\b|(trail|game|security) cameras?|\bGPS\b|\bIoT\b|dash ?cam/i],
  ];
  const SIM_WORD = /sim|roaming|data/i;

  function nonTravelReason(title) {
    if (!title || !String(title).trim()) return 'missing_title';
    for (const [name, re, skipIfMultiRegion] of RULES) {
      if (skipIfMultiRegion && MULTI_REGION.test(title)) continue;
      const m = re.exec(title);
      if (m) return `${name}:${m[0]}`;
    }
    if (!SIM_WORD.test(title)) return 'no_sim_keyword_in_title';
    return null;
  }

  return { nonTravelReason, isTravelProduct: (title) => nonTravelReason(title) === null };
}));

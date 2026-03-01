"""
Curated and source-backed Canada advantage fact bank.

This module mixes:
1) Stable policy/institution facts (official legislation/government sources)
2) Dynamic cross-country indicators from the World Bank API

The output is used to build a daily "verified evidence pack" for the LLM prompt.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Tuple
from urllib.error import URLError
from urllib.request import urlopen


CATEGORIES: List[str] = [
    "Legal & institutional protections",
    "Currency, capital, and financial system",
    "Labour mobility & credential leverage",
    "Information access & skill compounding",
    "Infrastructure & time efficiency",
    "Optionality under failure (second chances)",
    "State capacity & predictability",
    "Language and geographic optionality (e.g. English + ability to move)",
    "Language: English/French as global languages (portability of skills, no language trap)",
    "Educational opportunities (public K-12, affordable higher ed, credentials that transfer globally)",
    "Healthcare access (universal coverage, no medical bankruptcy as in the US)",
    "Political stability and peaceful transfers of power",
    "Banking and financial inclusion (everyone can hold an account, no cash-only trap)",
    "Research, libraries, and public knowledge (open access, no censorship of curricula)",
    "Labour standards (minimum wage, overtime, safety, recourse for wage theft)",
    "Property rights and contract enforcement (predictable courts, no arbitrary expropriation)",
    "Immigration and naturalization pathways (ability to naturalize, sponsor family)",
    "Press freedom and open information (no state media monopoly, access to global news)",
    "Internal mobility (freedom to move between provinces without permits or residency locks)",
    "Pension and social insurance (CPP, EI, predictable retirement floor)",
    "Clean water, sanitation, and reliable basic infrastructure",
    "Consumer and product safety regulation (food, drugs, standards)",
    "Environmental quality and public goods (air, water, parks as baseline)",
]


COMPARISON_PROFILES: List[Dict[str, Sequence[str]]] = [
    {
        "label": "low-trust economies with weak rule-of-law and corruption risk",
        "tags": ["low_trust", "rule_of_law", "corruption", "zimbabwe"],
    },
    {
        "label": "language/mobility traps where domestic constraints reduce exit options",
        "tags": ["language_trap", "mobility", "hukou"],
    },
    {
        "label": "wealthy but rigid systems with weaker second-chance mechanisms",
        "tags": ["second_chance", "debt", "income_shock"],
    },
    {
        "label": "systems with temporary-status work but narrow paths to citizenship",
        "tags": ["citizenship", "family", "temporary_status"],
    },
    {
        "label": "high-cost risk environments where one shock can impair recovery",
        "tags": ["us_risk", "medical_debt", "income_shock"],
    },
    {
        "label": "high-inflation settings where cash and wages erode quickly",
        "tags": ["inflation", "currency", "macrostability"],
    },
    {
        "label": "states with constrained press and weaker civic protections",
        "tags": ["press_freedom", "civil_liberties", "information_access"],
    },
]


COUNTRY_NAME = {
    "CA": "Canada",
    "US": "United States",
    "ZW": "Zimbabwe",
    "AR": "Argentina",
    "JP": "Japan",
}


@dataclass(frozen=True)
class ResolvedFact:
    fact_id: str
    category: str
    tags: Tuple[str, ...]
    canada_fact: str
    contrast: str
    source_name: str
    source_urls: Tuple[str, ...]
    as_of: str


POLICY_FACTS: List[Dict[str, object]] = [
    {
        "id": "F001",
        "category": "Internal mobility (freedom to move between provinces without permits or residency locks)",
        "tags": ("mobility", "legal", "hukou", "language_trap"),
        "canada_fact": (
            "Section 6(2) of the Charter gives citizens and permanent residents the right "
            "to move to any province and pursue a livelihood there."
        ),
        "contrast": (
            "China's hukou system ties many social benefits to local registration, which "
            "can limit migrant access in destination cities."
        ),
        "source_name": "Constitution Act, 1982 (Charter, s.6) + World Bank hukou analysis",
        "source_urls": (
            "https://laws.justice.gc.ca/eng/Const/page-12.html",
            "https://blogs.worldbank.org/en/peoplemove/chinas-hukou-reform-remains-major-challenge-domestic-migrants-cities",
        ),
        "as_of": "Current law / World Bank 2024",
    },
    {
        "id": "F002",
        "category": "Healthcare access (universal coverage, no medical bankruptcy as in the US)",
        "tags": ("healthcare", "us_risk", "medical_debt"),
        "canada_fact": (
            "Under the Canada Health Act framework, provincial public plans must cover "
            "medically necessary hospital and physician services."
        ),
        "contrast": (
            "Commonwealth Fund reported that 32% of working-age adults in the U.S. had "
            "medical debt in 2023."
        ),
        "source_name": "Canada Health Act guidance + Commonwealth Fund affordability survey",
        "source_urls": (
            "https://www.canada.ca/en/health-canada/services/health-care-system/canada-health-care-system-medicare/canada-health-act/myth-busters.html",
            "https://www.commonwealthfund.org/sites/default/files/2023-10/Collins_2023_AffordabilitySurveyTopline_PR_10-26-2023_v2.pdf",
        ),
        "as_of": "Current framework / 2023 survey",
    },
    {
        "id": "F003",
        "category": "Currency, capital, and financial system",
        "tags": ("currency", "banking", "low_trust", "macrostability"),
        "canada_fact": (
            "CDIC insures eligible deposits up to CAD 100,000 per depositor, per insured "
            "category, at member institutions."
        ),
        "contrast": (
            "In weakly supervised banking systems, household losses from bank failures can "
            "fall directly on depositors."
        ),
        "source_name": "Canada Deposit Insurance Corporation (CDIC)",
        "source_urls": ("https://www.cdic.ca/depositors/whats-covered/",),
        "as_of": "Current",
    },
    {
        "id": "F004",
        "category": "Currency, capital, and financial system",
        "tags": ("currency", "inflation", "state_capacity", "macrostability"),
        "canada_fact": (
            "The Bank of Canada targets 2% inflation within a 1-3% control range under a "
            "jointly renewed monetary policy framework."
        ),
        "contrast": (
            "High-inflation systems can rapidly erode purchasing power, planning horizons, "
            "and savings."
        ),
        "source_name": "Bank of Canada inflation-control framework",
        "source_urls": (
            "https://www.bankofcanada.ca/rates/indicators/key-variables/inflation-control-target/",
        ),
        "as_of": "Renewed through end-2026",
    },
    {
        "id": "F005",
        "category": "Immigration and naturalization pathways (ability to naturalize, sponsor family)",
        "tags": ("citizenship", "mobility", "temporary_status"),
        "canada_fact": (
            "Permanent residents can apply for citizenship after 1,095 days of physical "
            "presence in the preceding 5 years, if other criteria are met."
        ),
        "contrast": (
            "Some high-income jurisdictions have narrow, nomination-based naturalization "
            "paths for foreigners rather than broad residence-based pathways."
        ),
        "source_name": "IRCC citizenship eligibility + UAE nationality rules",
        "source_urls": (
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/canadian-citizenship/become-canadian-citizen/eligibility.html",
            "https://u.ae/en/information-and-services/passports-and-traveling/emirati-nationality/provisions-allowing-foreigners-to-acquire-the-emirati-nationality",
        ),
        "as_of": "Current",
    },
    {
        "id": "F006",
        "category": "Immigration and naturalization pathways (ability to naturalize, sponsor family)",
        "tags": ("family", "citizenship", "temporary_status"),
        "canada_fact": (
            "Canadian citizens and permanent residents can sponsor eligible spouses/partners, "
            "children, parents, and grandparents for permanent residence."
        ),
        "contrast": (
            "In many migration systems, workers can reside temporarily but cannot secure "
            "durable status for close family."
        ),
        "source_name": "IRCC family sponsorship program",
        "source_urls": (
            "https://www.canada.ca/en/immigration-refugees-citizenship/services/immigrate-canada/family-sponsorship.html",
        ),
        "as_of": "Current",
    },
    {
        "id": "F007",
        "category": "Language: English/French as global languages (portability of skills, no language trap)",
        "tags": ("language", "language_trap", "mobility"),
        "canada_fact": (
            "The Official Languages Act gives English and French equal status in federal "
            "institutions and guarantees access to federal services in either language where required."
        ),
        "contrast": (
            "Stronger bilingual institutional support reduces language lock-in and improves "
            "domestic and international mobility of skills."
        ),
        "source_name": "Official Languages Act",
        "source_urls": (
            "https://laws-lois.justice.gc.ca/eng/acts/o-3.01/page-1.html",
            "https://www.canada.ca/en/treasury-board-secretariat/services/values-ethics/official-languages/public-services/bilingual-offices-facilities.html",
        ),
        "as_of": "Current",
    },
    {
        "id": "F008",
        "category": "Optionality under failure (second chances)",
        "tags": ("second_chance", "income_shock", "state_capacity"),
        "canada_fact": (
            "Employment Insurance provides temporary income support for eligible workers "
            "who lose employment while they search for work or upgrade skills."
        ),
        "contrast": (
            "Where unemployment insurance is weak or absent, job loss can force immediate "
            "asset depletion and shorter planning horizons."
        ),
        "source_name": "Government of Canada EI program overview",
        "source_urls": ("https://www.canada.ca/en/employment-social-development/programs/ei.html",),
        "as_of": "Current",
    },
    {
        "id": "F009",
        "category": "Pension and social insurance (CPP, EI, predictable retirement floor)",
        "tags": ("pension", "state_capacity", "income_shock"),
        "canada_fact": (
            "The Canada Pension Plan is a mandatory, contributory, earnings-related social "
            "insurance program for most workers earning above CAD 3,500 (outside Quebec's QPP)."
        ),
        "contrast": (
            "Mandatory pooled pension contributions create a more predictable retirement "
            "floor than systems relying mainly on voluntary or informal saving."
        ),
        "source_name": "Canada Pension Plan contributions and program pages",
        "source_urls": (
            "https://www.canada.ca/en/services/benefits/publicpensions/cpp/contributions.html",
            "https://www.canada.ca/en/employment-social-development/programs/pension-plan.html",
        ),
        "as_of": "Current",
    },
    {
        "id": "F010",
        "category": "Optionality under failure (second chances)",
        "tags": ("second_chance", "debt", "legal"),
        "canada_fact": (
            "For a first bankruptcy, automatic discharge can occur after 9 months when "
            "conditions are met (or 21 months with surplus income obligations)."
        ),
        "contrast": (
            "A structured discharge framework provides legal second chances that are weaker "
            "or slower in many jurisdictions."
        ),
        "source_name": "Office of the Superintendent of Bankruptcy (Canada)",
        "source_urls": (
            "https://ised-isde.canada.ca/site/office-superintendent-bankruptcy/en/you-owe-money/you-owe-money-bankruptcy-discharge-and-its-consequences-bankrupt",
        ),
        "as_of": "Current",
    },
    {
        "id": "F011",
        "category": "Press freedom and open information (no state media monopoly, access to global news)",
        "tags": ("civil_liberties", "press_freedom", "zimbabwe", "low_trust"),
        "canada_fact": "Freedom House (2025) scores Canada at 97/100 (Free).",
        "contrast": "Freedom House (2025) scores Zimbabwe at 26/100 (Not Free).",
        "source_name": "Freedom House, Freedom in the World 2025 country reports",
        "source_urls": (
            "https://freedomhouse.org/country/canada/freedom-world/2025",
            "https://freedomhouse.org/country/zimbabwe/freedom-world/2025",
        ),
        "as_of": "2025",
    },
    {
        "id": "F012",
        "category": "Property rights and contract enforcement (predictable courts, no arbitrary expropriation)",
        "tags": ("rule_of_law", "legal", "low_trust"),
        "canada_fact": "World Justice Project Rule of Law Index 2024 ranks Canada 12th of 142 countries.",
        "contrast": (
            "Higher rule-of-law performance generally means stronger contract enforcement "
            "and lower arbitrary policy risk."
        ),
        "source_name": "World Justice Project Rule of Law Index 2024",
        "source_urls": (
            "https://worldjusticeproject.org/rule-of-law-index/global/2024",
            "https://worldjusticeproject.org/sites/default/files/documents/Canada_2.pdf",
        ),
        "as_of": "2024",
    },
    {
        "id": "F013",
        "category": "Press freedom and open information (no state media monopoly, access to global news)",
        "tags": ("press_freedom", "information_access"),
        "canada_fact": "Reporters Without Borders' 2024 World Press Freedom Index ranks Canada 14th of 180.",
        "contrast": (
            "Compared with censored environments, stronger press freedom increases access "
            "to independent information and scrutiny."
        ),
        "source_name": "RSF World Press Freedom Index 2024",
        "source_urls": ("https://rsf.org/en/classement/2024/americas",),
        "as_of": "2024",
    },
    {
        "id": "F014",
        "category": "Legal & institutional protections",
        "tags": ("corruption", "low_trust", "rule_of_law"),
        "canada_fact": "Transparency International CPI 2024 gives Canada a score of 75/100 (rank 15/180).",
        "contrast": (
            "Lower perceived corruption reduces everyday bribery risk and improves policy "
            "predictability for households and firms."
        ),
        "source_name": "Transparency International country profile (Canada)",
        "source_urls": ("https://www.transparency.org/en/countries/canada",),
        "as_of": "2024",
    },
    {
        "id": "F015",
        "category": "Political stability and peaceful transfers of power",
        "tags": ("stability", "state_capacity"),
        "canada_fact": "Global Peace Index 2024 ranks Canada 11th of 163.",
        "contrast": (
            "Higher peacefulness reduces disruption risk to work, schooling, logistics, and "
            "long-term planning."
        ),
        "source_name": "Institute for Economics & Peace, Global Peace Index 2024",
        "source_urls": (
            "https://www.economicsandpeace.org/report/global-peace-index-2024/",
        ),
        "as_of": "2024",
    },
]


METRIC_FACTS: List[Dict[str, object]] = [
    {
        "id": "F101",
        "category": "Healthcare access (universal coverage, no medical bankruptcy as in the US)",
        "tags": ("healthcare", "us_risk"),
        "indicator": "SP.DYN.LE00.IN",
        "indicator_name": "Life expectancy at birth, total (years)",
        "comparison_country": "US",
        "higher_is_better": True,
        "decimals": 1,
        "source_name": "World Bank WDI",
        "fallback": {"CA": ("2023", 81.6), "US": ("2023", 78.4)},
    },
    {
        "id": "F102",
        "category": "Political stability and peaceful transfers of power",
        "tags": ("stability", "us_risk", "public_safety"),
        "indicator": "VC.IHR.PSRC.P5",
        "indicator_name": "Intentional homicides (per 100,000 people)",
        "comparison_country": "US",
        "higher_is_better": False,
        "decimals": 1,
        "source_name": "World Bank WDI",
        "fallback": {"CA": ("2023", 2.0), "US": ("2023", 5.8)},
    },
    {
        "id": "F103",
        "category": "Clean water, sanitation, and reliable basic infrastructure",
        "tags": ("infrastructure", "water", "zimbabwe", "low_trust"),
        "indicator": "SH.H2O.SMDW.ZS",
        "indicator_name": "People using safely managed drinking water services (% of population)",
        "comparison_country": "ZW",
        "higher_is_better": True,
        "decimals": 1,
        "source_name": "World Bank WDI (WHO/UNICEF JMP)",
        "fallback": {"CA": ("2024", 96.9), "ZW": ("2024", 25.5)},
    },
    {
        "id": "F104",
        "category": "Clean water, sanitation, and reliable basic infrastructure",
        "tags": ("infrastructure", "sanitation", "zimbabwe", "low_trust"),
        "indicator": "SH.STA.SMSS.ZS",
        "indicator_name": "People using safely managed sanitation services (% of population)",
        "comparison_country": "ZW",
        "higher_is_better": True,
        "decimals": 1,
        "source_name": "World Bank WDI (WHO/UNICEF JMP)",
        "fallback": {"CA": ("2024", 81.3), "ZW": ("2024", 23.6)},
    },
    {
        "id": "F105",
        "category": "Infrastructure & time efficiency",
        "tags": ("infrastructure", "electricity", "zimbabwe", "state_capacity"),
        "indicator": "EG.ELC.ACCS.ZS",
        "indicator_name": "Access to electricity (% of population)",
        "comparison_country": "ZW",
        "higher_is_better": True,
        "decimals": 1,
        "source_name": "World Bank WDI",
        "fallback": {"CA": ("2023", 100.0), "ZW": ("2023", 62.0)},
    },
    {
        "id": "F106",
        "category": "Information access & skill compounding",
        "tags": ("information_access", "infrastructure", "zimbabwe"),
        "indicator": "IT.NET.USER.ZS",
        "indicator_name": "Individuals using the Internet (% of population)",
        "comparison_country": "ZW",
        "higher_is_better": True,
        "decimals": 1,
        "source_name": "World Bank WDI",
        "fallback": {"CA": ("2023", 94.0), "ZW": ("2023", 38.4)},
    },
    {
        "id": "F107",
        "category": "Banking and financial inclusion (everyone can hold an account, no cash-only trap)",
        "tags": ("banking", "financial_inclusion", "zimbabwe", "low_trust"),
        "indicator": "FX.OWN.TOTL.ZS",
        "indicator_name": "Account ownership at a financial institution or with a mobile-money-service provider (% age 15+)",
        "comparison_country": "ZW",
        "higher_is_better": True,
        "decimals": 1,
        "source_name": "World Bank Global Findex via WDI",
        "fallback": {"CA": ("2024", 98.4), "ZW": ("2024", 49.5)},
    },
    {
        "id": "F108",
        "category": "Currency, capital, and financial system",
        "tags": ("inflation", "currency", "macrostability"),
        "indicator": "FP.CPI.TOTL.ZG",
        "indicator_name": "Inflation, consumer prices (annual %)",
        "comparison_country": "AR",
        "higher_is_better": False,
        "decimals": 1,
        "source_name": "World Bank WDI",
        "fallback": {"CA": ("2024", 2.4), "AR": ("2024", 219.9)},
    },
    {
        "id": "F109",
        "category": "State capacity & predictability",
        "tags": ("state_capacity", "us_risk", "inequality"),
        "indicator": "SI.POV.GINI",
        "indicator_name": "Gini index",
        "comparison_country": "US",
        "higher_is_better": False,
        "decimals": 1,
        "source_name": "World Bank WDI",
        "fallback": {"CA": ("2021", 31.1), "US": ("2023", 41.8)},
    },
]


def _rotate(items: Sequence[Dict[str, object]], seed: int) -> List[Dict[str, object]]:
    if not items:
        return []
    idx = seed % len(items)
    return list(items[idx:] + items[:idx])


def choose_daily_focus(day_of_year: int) -> Dict[str, object]:
    n_cat = len(CATEGORIES)
    i = day_of_year % n_cat
    j = (day_of_year + 7) % n_cat
    k = (day_of_year + 14) % n_cat
    # Ensure unique category indices even with small lists.
    seen = {i}
    if j in seen:
        j = (j + 1) % n_cat
    seen.add(j)
    if k in seen:
        k = (k + 1) % n_cat
        if k in seen:
            k = (k + 1) % n_cat
    profile = COMPARISON_PROFILES[day_of_year % len(COMPARISON_PROFILES)]
    return {
        "categories": [CATEGORIES[i], CATEGORIES[j], CATEGORIES[k]],
        "comparison_label": profile["label"],
        "comparison_tags": tuple(profile["tags"]),
    }


def _select_blueprints(
    day_of_year: int,
    focus_categories: Sequence[str],
    comparison_tags: Sequence[str],
    target_count: int = 9,
) -> List[Dict[str, object]]:
    all_facts: List[Dict[str, object]] = list(POLICY_FACTS) + list(METRIC_FACTS)
    focus_set = set(focus_categories)
    comparison_set = set(comparison_tags)

    by_category = [f for f in all_facts if f["category"] in focus_set]
    by_comparison = [
        f for f in all_facts if comparison_set.intersection(set(f.get("tags", ())))
    ]

    selected: List[Dict[str, object]] = []
    selected_ids = set()

    def add_from_pool(pool: Sequence[Dict[str, object]], desired: int, seed: int) -> None:
        for fact in _rotate(list(pool), seed):
            if fact["id"] in selected_ids:
                continue
            selected.append(fact)
            selected_ids.add(fact["id"])
            if len(selected) >= desired:
                break

    # Core: 4 from focus categories, then 3 from comparison profile.
    add_from_pool(by_category, desired=4, seed=day_of_year)
    add_from_pool(by_comparison, desired=7, seed=day_of_year + 5)
    # Fill remainder from full bank for breadth.
    add_from_pool(all_facts, desired=target_count, seed=day_of_year + 11)
    return selected


def _fetch_world_bank_latest(
    indicator: str, countries: Sequence[str], timeout_seconds: int = 8
) -> Dict[str, Tuple[str, float]]:
    """
    Returns latest non-null values for each country code, e.g.:
      {"CA": ("2024", 2.4), "US": ("2024", 3.1)}
    Raises ValueError on incomplete responses.
    """
    country_arg = ";".join(countries)
    url = (
        f"https://api.worldbank.org/v2/country/{country_arg}/indicator/{indicator}"
        f"?format=json&per_page=400"
    )
    with urlopen(url, timeout=timeout_seconds) as response:
        payload = json.load(response)
    if not isinstance(payload, list) or len(payload) < 2 or not isinstance(payload[1], list):
        raise ValueError(f"Unexpected World Bank response shape for {indicator}")

    latest: Dict[str, Tuple[str, float]] = {}
    needed = set(countries)
    for row in payload[1]:
        code = row.get("country", {}).get("id")
        value = row.get("value")
        year = row.get("date")
        if code in needed and value is not None and code not in latest:
            latest[code] = (str(year), float(value))
        if len(latest) == len(needed):
            break

    missing = needed.difference(latest.keys())
    if missing:
        raise ValueError(f"Missing latest values for {indicator}: {sorted(missing)}")
    return latest


def _format_value(value: float, decimals: int, is_percent: bool = False) -> str:
    num = f"{value:.{decimals}f}"
    return f"{num}%" if is_percent else num


def _resolve_metric_fact(template: Dict[str, object]) -> ResolvedFact:
    indicator = str(template["indicator"])
    comparison_country = str(template["comparison_country"])
    countries = ("CA", comparison_country)
    fallback = template.get("fallback", {})

    try:
        latest = _fetch_world_bank_latest(indicator, countries)
    except (URLError, ValueError, TimeoutError):
        latest = {}

    def get_point(country_code: str) -> Tuple[str, float]:
        if country_code in latest:
            return latest[country_code]
        if country_code in fallback:
            year, value = fallback[country_code]
            return str(year), float(value)
        raise ValueError(
            f"Missing both live and fallback value for {template['id']} ({country_code})"
        )

    ca_year, ca_value = get_point("CA")
    cmp_year, cmp_value = get_point(comparison_country)

    decimals = int(template.get("decimals", 1))
    indicator_name = str(template["indicator_name"])
    higher_is_better = bool(template["higher_is_better"])

    is_percent = "(%" in indicator_name or indicator_name.endswith("%)")
    ca_str = _format_value(ca_value, decimals, is_percent=is_percent)
    cmp_str = _format_value(cmp_value, decimals, is_percent=is_percent)

    cmp_name = COUNTRY_NAME.get(comparison_country, comparison_country)
    if higher_is_better:
        canada_fact = (
            f"World Bank latest data shows Canada at {ca_str} ({ca_year}) on '{indicator_name}', "
            f"versus {cmp_str} in {cmp_name} ({cmp_year})."
        )
        contrast = (
            f"On this measure, Canada is higher than {cmp_name}, which improves baseline "
            f"predictability and long-run option value."
        )
    else:
        canada_fact = (
            f"World Bank latest data shows Canada at {ca_str} ({ca_year}) on '{indicator_name}', "
            f"compared with {cmp_str} in {cmp_name} ({cmp_year})."
        )
        contrast = (
            f"On this measure, lower values are preferable; Canada is lower than {cmp_name}, "
            f"which reduces structural downside risk."
        )

    source_url = (
        f"https://data.worldbank.org/indicator/{indicator}?locations=CA-{comparison_country}"
    )
    as_of = f"{ca_year}/{cmp_year}"

    return ResolvedFact(
        fact_id=str(template["id"]),
        category=str(template["category"]),
        tags=tuple(template.get("tags", ())),
        canada_fact=canada_fact,
        contrast=contrast,
        source_name=str(template.get("source_name", "World Bank")),
        source_urls=(source_url,),
        as_of=as_of,
    )


def build_daily_fact_pack(
    day_of_year: int, focus_categories: Sequence[str], comparison_tags: Sequence[str]
) -> List[ResolvedFact]:
    """
    Select and resolve a daily evidence pack of facts.
    """
    blueprints = _select_blueprints(
        day_of_year=day_of_year,
        focus_categories=focus_categories,
        comparison_tags=comparison_tags,
        target_count=9,
    )
    resolved: List[ResolvedFact] = []
    for item in blueprints:
        if "indicator" in item:
            resolved.append(_resolve_metric_fact(item))
        else:
            resolved.append(
                ResolvedFact(
                    fact_id=str(item["id"]),
                    category=str(item["category"]),
                    tags=tuple(item.get("tags", ())),
                    canada_fact=str(item["canada_fact"]),
                    contrast=str(item["contrast"]),
                    source_name=str(item["source_name"]),
                    source_urls=tuple(item.get("source_urls", ())),
                    as_of=str(item.get("as_of", "Current")),
                )
            )
    return resolved


def render_focus_and_evidence(
    focus_categories: Sequence[str],
    comparison_label: str,
    fact_pack: Sequence[ResolvedFact],
) -> str:
    """
    Render deterministic daily focus + evidence pack text to append to prompt.
    """
    lines = [
        "Today's focus (you MUST use this to make the daily output meaningfully different):",
        f"- Focus categories: (1) {focus_categories[0]} (2) {focus_categories[1]} (3) {focus_categories[2]}",
        f"- Contrast emphasis: {comparison_label}.",
        "",
        "Verified evidence pack for today (use these IDs for factual claims):",
        "- You may paraphrase, but do not introduce new numeric/ranking claims not grounded in these facts.",
        "",
    ]

    for fact in fact_pack:
        lines.extend(
            [
                f"{fact.fact_id} | Category: {fact.category}",
                f"Canada advantage: {fact.canada_fact}",
                f"Contrast context: {fact.contrast}",
                f"Source(s): {' ; '.join(fact.source_urls)}",
                f"As-of: {fact.as_of}",
                "",
            ]
        )

    lines.extend(
        [
            "Evidence-use rules (non-negotiable):",
            "- Use at least 4 different fact IDs from the pack.",
            "- Every numeric, ranking, policy, or country-specific claim must cite a fact ID at sentence end, e.g. [F003].",
            "- If a claim is not in the pack, omit it.",
            "- Include a final section titled **Sources (Fact IDs):** mapping each used ID to URL(s).",
        ]
    )
    return "\n".join(lines).strip()


def fact_id_set(facts: Iterable[ResolvedFact]) -> set[str]:
    return {f.fact_id for f in facts}


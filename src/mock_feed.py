"""
mock_feed.py — Synthetic HFT news feed generator.

Produces ~1000 articles across 100 tickers from 30 sources using
templated generation. Import MOCK_FEED for the full dataset.
"""

import random
from typing import Dict, List, Tuple

# ── Sources ───────────────────────────────────────────────────────────────────

SOURCES: List[str] = [
    "Bloomberg", "Reuters", "WSJ", "FT", "CNBC", "MarketWatch",
    "Seeking Alpha", "Barron's", "The Economist", "Forbes",
    "Business Insider", "Yahoo Finance", "Benzinga", "Motley Fool",
    "Zacks", "TheStreet", "AP Business", "The Guardian Business",
    "Axios Markets", "The Information", "Wired", "Ars Technica",
    "TechCrunch", "VentureBeat", "MIT Technology Review",
    "NPR Business", "BBC Business", "Investopedia",
    "S&P Global Market Intelligence", "Morningstar",
]

# ── Tickers ───────────────────────────────────────────────────────────────────
# (ticker, company_name, sector, short descriptor)

TICKERS: List[Tuple[str, str, str, str]] = [
    # AI / Chips (15)
    ("NVDA", "Nvidia",           "AI Chips",       "the dominant AI accelerator maker"),
    ("AMD",  "AMD",              "AI Chips",       "Nvidia's chief GPU rival"),
    ("INTC", "Intel",            "Semiconductors", "the struggling legacy chipmaker"),
    ("QCOM", "Qualcomm",         "Semiconductors", "the mobile and IoT chip leader"),
    ("AVGO", "Broadcom",         "Semiconductors", "the diversified chip and software giant"),
    ("TSM",  "TSMC",             "Chip Foundry",   "the world's largest contract chipmaker"),
    ("ASML", "ASML",             "Chip Equipment", "the sole supplier of EUV lithography machines"),
    ("ARM",  "Arm Holdings",     "Chip IP",        "the chip architecture licensor"),
    ("MU",   "Micron",           "Memory",         "the leading US memory chip maker"),
    ("SMCI", "Super Micro",      "AI Servers",     "the high-density AI server maker"),
    ("MRVL", "Marvell",          "AI Chips",       "the custom AI silicon and networking chip maker"),
    ("KLAC", "KLA Corp",         "Chip Equipment", "the leading process control equipment maker"),
    ("LRCX", "Lam Research",     "Chip Equipment", "the etch and deposition equipment giant"),
    ("AMAT", "Applied Materials","Chip Equipment", "the largest semiconductor equipment company"),
    ("TXN",  "Texas Instruments","Analog Chips",   "the dominant industrial and automotive chip maker"),
    # Big Tech (5)
    ("AAPL", "Apple",            "Big Tech",       "the world's most valuable consumer tech brand"),
    ("MSFT", "Microsoft",        "Big Tech",       "the enterprise software and cloud giant"),
    ("GOOGL","Alphabet",         "Big Tech",       "the search and cloud advertising leader"),
    ("AMZN", "Amazon",           "Big Tech",       "the e-commerce and cloud infrastructure leader"),
    ("META", "Meta",             "Big Tech",       "the social media and AI open-source leader"),
    # Enterprise Software / SaaS (10)
    ("ORCL", "Oracle",           "Enterprise SW",  "the legacy database and cloud ERP giant"),
    ("CRM",  "Salesforce",       "SaaS",           "the CRM and enterprise cloud leader"),
    ("ADBE", "Adobe",            "Creative SW",    "the creative and document cloud platform"),
    ("NOW",  "ServiceNow",       "SaaS",           "the enterprise workflow automation leader"),
    ("SNOW", "Snowflake",        "Data Cloud",     "the cloud data warehousing pioneer"),
    ("PLTR", "Palantir",         "AI/Data",        "the government and enterprise AI analytics firm"),
    ("DDOG", "Datadog",          "Observability",  "the cloud monitoring and analytics platform"),
    ("CRWD", "CrowdStrike",      "Cybersecurity",  "the cloud-native endpoint security leader"),
    ("NET",  "Cloudflare",       "Cybersecurity",  "the global network security and CDN platform"),
    ("WDAY", "Workday",          "HR SaaS",        "the cloud HR and financial management leader"),
    # EV / Auto (8)
    ("TSLA", "Tesla",            "EV",             "the pioneering EV and autonomous driving company"),
    ("RIVN", "Rivian",           "EV",             "the Amazon-backed EV startup"),
    ("LCID", "Lucid Motors",     "EV",             "the luxury EV startup targeting Tesla"),
    ("NIO",  "NIO",              "EV",             "the Chinese premium EV manufacturer"),
    ("LI",   "Li Auto",          "EV",             "the Chinese extended-range EV leader"),
    ("XPEV", "XPeng",            "EV",             "the Chinese smart EV and software company"),
    ("F",    "Ford",             "Auto",           "the legacy automaker accelerating EV transition"),
    ("GM",   "General Motors",   "Auto",           "the Detroit giant competing in EV and AV"),
    # Finance / Banking (8)
    ("JPM",  "JPMorgan",         "Finance",        "the largest US bank by assets"),
    ("GS",   "Goldman Sachs",    "Finance",        "the premier investment bank"),
    ("BAC",  "Bank of America",  "Finance",        "the second-largest US consumer bank"),
    ("MS",   "Morgan Stanley",   "Finance",        "the wealth management and investment bank"),
    ("WFC",  "Wells Fargo",      "Finance",        "the large US retail and commercial bank"),
    ("C",    "Citigroup",        "Finance",        "the global universal bank undergoing transformation"),
    ("BX",   "Blackstone",       "Private Equity", "the world's largest alternative asset manager"),
    ("SCHW", "Charles Schwab",   "Finance",        "the leading retail brokerage and banking platform"),
    # Payments / Fintech (7)
    ("V",    "Visa",             "Payments",       "the global payments network leader"),
    ("MA",   "Mastercard",       "Payments",       "the second-largest global payments network"),
    ("AXP",  "American Express", "Payments",       "the premium charge card and travel rewards network"),
    ("PYPL", "PayPal",           "Fintech",        "the digital payments and commerce platform"),
    ("SQ",   "Block",            "Fintech",        "the Square and Cash App fintech conglomerate"),
    ("COIN", "Coinbase",         "Crypto",         "the leading US regulated crypto exchange"),
    ("COF",  "Capital One",      "Finance",        "the data-driven credit card and banking company"),
    # Streaming / Media / Gaming (6)
    ("NFLX", "Netflix",          "Streaming",      "the dominant global streaming platform"),
    ("DIS",  "Disney",           "Media",          "the diversified entertainment and streaming giant"),
    ("SPOT", "Spotify",          "Streaming",      "the world's largest music streaming platform"),
    ("CMCSA","Comcast",          "Media/Telecom",  "the cable, broadband and NBC Universal giant"),
    ("PARA", "Paramount",        "Media",          "the legacy media company pivoting to streaming"),
    ("RBLX", "Roblox",           "Gaming",         "the user-generated gaming and metaverse platform"),
    # Pharma / Biotech (8)
    ("JNJ",  "Johnson & Johnson","Pharma",         "the diversified healthcare and pharma giant"),
    ("PFE",  "Pfizer",           "Pharma",         "the post-COVID pharma giant rebuilding its pipeline"),
    ("MRK",  "Merck",            "Pharma",         "the oncology and vaccines pharmaceutical leader"),
    ("ABBV", "AbbVie",           "Pharma",         "the Humira successor and immunology drug maker"),
    ("LLY",  "Eli Lilly",        "Pharma",         "the GLP-1 obesity and diabetes drug leader"),
    ("AMGN", "Amgen",            "Biotech",        "the pioneering large-molecule biotech firm"),
    ("MRNA", "Moderna",          "Biotech",        "the mRNA platform company beyond COVID vaccines"),
    ("VRTX", "Vertex",           "Biotech",        "the cystic fibrosis and gene editing biotech"),
    # Retail / Consumer (8)
    ("WMT",  "Walmart",          "Retail",         "the world's largest retailer by revenue"),
    ("COST", "Costco",           "Retail",         "the membership warehouse retail giant"),
    ("TGT",  "Target",           "Retail",         "the US mass merchandise retailer"),
    ("HD",   "Home Depot",       "Retail",         "the leading US home improvement retailer"),
    ("LOW",  "Lowe's",           "Retail",         "the second-largest US home improvement chain"),
    ("MCD",  "McDonald's",       "QSR",            "the world's largest fast food chain by revenue"),
    ("SBUX", "Starbucks",        "QSR",            "the global specialty coffee chain"),
    ("NKE",  "Nike",             "Consumer",       "the world's largest athletic footwear brand"),
    # Clean Energy / Utilities (5)
    ("ENPH", "Enphase",          "Clean Energy",   "the residential solar microinverter leader"),
    ("NEE",  "NextEra Energy",   "Utilities",      "the world's largest renewable energy producer"),
    ("FSLR", "First Solar",      "Solar",          "the leading US utility-scale solar panel maker"),
    ("CEG",  "Constellation Energy","Nuclear",     "the largest US nuclear power operator"),
    ("VST",  "Vistra",           "Power",          "the Texas-based power generation and retail giant"),
    # Industrial / Defense / Aerospace (7)
    ("BA",   "Boeing",           "Aerospace",      "the troubled US aerospace and defense giant"),
    ("CAT",  "Caterpillar",      "Industrial",     "the global construction and mining equipment maker"),
    ("GE",   "GE Aerospace",     "Aerospace",      "the jet engine and aviation systems leader"),
    ("LMT",  "Lockheed Martin",  "Defense",        "the largest US defense contractor"),
    ("HON",  "Honeywell",        "Industrial",     "the diversified industrial and automation conglomerate"),
    ("RTX",  "RTX",              "Defense",        "the aerospace and missile systems maker"),
    ("NOC",  "Northrop Grumman", "Defense",        "the stealth aircraft and space systems contractor"),
    # Platforms / Gig / E-commerce (6)
    ("UBER", "Uber",             "Gig Economy",    "the global ride-sharing and delivery platform"),
    ("ABNB", "Airbnb",           "Travel Tech",    "the peer-to-peer short-term rental marketplace"),
    ("DASH", "DoorDash",         "Food Delivery",  "the US food and grocery delivery leader"),
    ("SHOP", "Shopify",          "E-commerce",     "the leading SMB e-commerce platform"),
    ("SNAP", "Snap",             "Social Media",   "the camera-first social media company"),
    ("LULU", "Lululemon",        "Consumer",       "the premium athletic apparel brand"),
    # Telecom (2)
    ("T",    "AT&T",             "Telecom",        "the US wireless and fiber broadband carrier"),
    ("VZ",   "Verizon",          "Telecom",        "the largest US wireless network operator"),
]

# ── Article templates ─────────────────────────────────────────────────────────
# Variables: {name}, {ticker}, {desc}

POSITIVE_TEMPLATES: List[Tuple[str, str]] = [
    (
        "{name} quarterly revenue beats estimates, raises full-year guidance",
        "{name} ({ticker}) posted revenue above Wall Street consensus, driven by strong demand across its core segments. Management raised full-year guidance citing improving macro and product cycle momentum.",
    ),
    (
        "Analyst upgrades {name} to Buy, raises price target on AI tailwinds",
        "A top-tier investment bank lifted its rating on {name} ({ticker}) to Buy and raised its 12-month price target, citing the company's leverage to accelerating AI infrastructure spending.",
    ),
    (
        "{name} announces $10 billion share buyback, signals balance sheet confidence",
        "{name} ({ticker}) board approved a new $10B share repurchase program, reflecting strong free cash flow generation and management's view that shares are attractively valued.",
    ),
    (
        "{name} wins landmark enterprise contract worth $2 billion over five years",
        "{name} ({ticker}) disclosed a multi-year agreement with a Fortune 500 customer, the largest in company history. The deal is expected to be immediately accretive to revenue and margins.",
    ),
    (
        "{name} operating margin expands 400 bps YoY on cost discipline and mix shift",
        "{name} ({ticker}) delivered operating margin expansion driven by a favourable revenue mix and ongoing efficiency initiatives. Analysts noted the improvement exceeded expectations.",
    ),
    (
        "{name} launches next-generation product line ahead of schedule",
        "{name} ({ticker}) unveiled its latest product family, pulling forward the launch timeline by one quarter. Early customer feedback is described as overwhelmingly positive.",
    ),
    (
        "{name} market share hits five-year high as rivals lose ground",
        "New industry data shows {name} ({ticker}) gained significant market share over the past year, displacing competitors across its primary addressable markets.",
    ),
    (
        "{name} CFO: free cash flow generation tracking toward record annual level",
        "{name} ({ticker}) CFO said at an investor conference that free cash flow for the year is on pace to set a company record, supported by lean inventory management and disciplined capex.",
    ),
    (
        "{name} international revenue accelerates on emerging market expansion",
        "{name} ({ticker}) reported double-digit international revenue growth, led by strong performance in Southeast Asia and Latin America, markets the company has targeted for expansion.",
    ),
    (
        "{name} AI integration delivers measurable productivity gains for customers",
        "Enterprise customers of {name} ({ticker}) reported significant productivity improvements after deploying its AI-enhanced product suite, boosting renewal rates and upsell opportunities.",
    ),
    (
        "{name} dividend raised 15%, marking twelfth consecutive annual increase",
        "{name} ({ticker}) board approved a 15% dividend hike, extending the company's streak of consecutive annual increases and reinforcing its status as a reliable income holding.",
    ),
    (
        "Institutional ownership of {name} hits all-time high per latest 13F filings",
        "SEC 13F filings show institutional ownership of {name} ({ticker}) reached an all-time high last quarter, with several large hedge funds initiating new positions in the stock.",
    ),
    (
        "{name} gross margin outperforms peers by 800 basis points in latest quarter",
        "{name} ({ticker}) reported gross margin well above sector peers, underscoring its pricing power and product differentiation as {desc}.",
    ),
    (
        "{name} R&D investment paying off: patent filings up 40% year over year",
        "{name} ({ticker}) disclosed a sharp increase in patent applications, a leading indicator of future product pipeline strength and competitive moat expansion.",
    ),
    (
        "Buy-side survey: {name} is top pick for next twelve months",
        "A Bloomberg survey of portfolio managers ranked {name} ({ticker}) as the most widely cited long idea for the coming year, supported by a compelling risk-reward setup.",
    ),
    (
        "{name} debt rating upgraded to AA by S&P on improving cash flow",
        "S&P Global Ratings raised its credit rating on {name} ({ticker}) citing sustained improvement in free cash flow generation and a conservative balance sheet posture.",
    ),
    (
        "{name} cloud/platform revenue grows 45% YoY, surpassing expectations",
        "{name} ({ticker}) reported its highest-growth segment accelerated further, surpassing the 40% growth rate analysts projected and suggesting durable demand for its platform.",
    ),
    (
        "{name} strategic partnership with leading hyperscaler extends competitive moat",
        "{name} ({ticker}) announced a multi-year strategic agreement with a major cloud provider, cementing its position as {desc} and opening a new high-value distribution channel.",
    ),
    (
        "{name} beats on EPS by widest margin in eight quarters",
        "{name} ({ticker}) delivered earnings per share significantly above consensus, driven by a combination of revenue upside and operating leverage that surprised even bullish analysts.",
    ),
    (
        "{name} customer retention rate reaches record 97%, churn near zero",
        "{name} ({ticker}) disclosed its highest-ever annual customer retention rate, a leading indicator of revenue visibility and a strong signal of product-market fit.",
    ),
]

NEGATIVE_TEMPLATES: List[Tuple[str, str]] = [
    (
        "{name} misses revenue estimates, cuts full-year outlook on demand softness",
        "{name} ({ticker}) reported revenue below analyst consensus and lowered its annual guidance, citing weaker-than-expected demand and inventory digestion headwinds.",
    ),
    (
        "DOJ opens antitrust investigation into {name}'s market practices",
        "The Department of Justice launched a formal probe into {name} ({ticker}), examining whether the company engaged in anticompetitive behaviour in its core market.",
    ),
    (
        "{name} faces class-action lawsuit over alleged accounting irregularities",
        "A securities class-action was filed against {name} ({ticker}), alleging the company misrepresented financial results over a multi-quarter period.",
    ),
    (
        "Analyst downgrades {name} to Sell, citing valuation and margin pressure",
        "A prominent Wall Street analyst cut {name} ({ticker}) to Sell, arguing the stock's premium valuation is unjustified given decelerating growth and rising competitive pressure.",
    ),
    (
        "{name} CEO departure triggers succession uncertainty, stock slides",
        "{name} ({ticker}) announced the unexpected departure of its longtime CEO, triggering investor concern about strategic continuity. A search for a successor is underway.",
    ),
    (
        "{name} data breach exposes millions of customer records, regulatory risk rises",
        "{name} ({ticker}) disclosed a cybersecurity incident affecting a significant portion of its customer database, exposing the company to regulatory penalties and reputational damage.",
    ),
    (
        "{name} supply chain disruption to dent gross margins for two quarters",
        "{name} ({ticker}) warned investors that ongoing supply chain constraints will compress gross margins over the next two quarters, forcing absorption of higher input costs.",
    ),
    (
        "{name} loses major customer contract to low-cost competitor",
        "{name} ({ticker}) confirmed the non-renewal of a significant customer contract, which will create a notable revenue gap as a rival won the bid on price.",
    ),
    (
        "{name} faces product recall, liability exposure estimated at $500 million",
        "{name} ({ticker}) initiated a voluntary product recall following safety reports. Total liability including remediation and potential litigation could reach $500M.",
    ),
    (
        "{name} short interest surges to multi-year high on bearish macro thesis",
        "Short interest in {name} ({ticker}) climbed to its highest level in three years as hedge funds bet against the stock amid rising rates and slowing end-market demand.",
    ),
    (
        "{name} misses on all key metrics in disappointing quarterly update",
        "{name} ({ticker}) fell short of analyst estimates on revenue, operating income, and earnings per share. Management attributed the miss to a challenging macro environment.",
    ),
    (
        "{name} inventory buildup signals demand destruction in core markets",
        "Channel checks and {name} ({ticker})'s own disclosures point to a sharp inventory buildup, suggesting end-market demand has weakened materially in recent months.",
    ),
    (
        "{name} faces regulatory fine of $1.2 billion over data privacy violations",
        "Regulators imposed a $1.2B fine on {name} ({ticker}) for systematic violations of data privacy laws, the largest penalty in the company's history.",
    ),
    (
        "Key {name} executive team departs to join rival startup",
        "Three senior engineering and product leaders at {name} ({ticker}) resigned to co-found a competitor startup backed by a top-tier venture firm, raising talent retention concerns.",
    ),
    (
        "{name} writedown of $3 billion signals failed acquisition integration",
        "{name} ({ticker}) recorded a $3B goodwill impairment charge related to an acquisition made two years ago, admitting the integration has not delivered projected synergies.",
    ),
    (
        "{name} credit facility covenant breach triggers lender review",
        "{name} ({ticker}) disclosed it breached a financial covenant in its revolving credit facility, initiating mandatory discussions with its lending group about potential amendments.",
    ),
    (
        "{name} loses market share to overseas rivals for third consecutive quarter",
        "Industry data confirms {name} ({ticker}) ceded market share for a third straight quarter as lower-cost overseas competitors expanded their presence in key geographies.",
    ),
    (
        "{name} warns on earnings amid sharp currency headwinds",
        "{name} ({ticker}) issued a pre-announcement warning that foreign exchange translation effects will reduce reported earnings by an estimated 10-12 cents per share this quarter.",
    ),
    (
        "ESG rating agency strips {name} of sustainability certification",
        "A major ESG rating agency downgraded {name} ({ticker}) and revoked its sustainability certification after auditors found discrepancies in reported emissions data.",
    ),
    (
        "{name} customer churn accelerates, net revenue retention falls below 100%",
        "{name} ({ticker}) disclosed that net revenue retention dropped below 100% for the first time in five years, signalling that expansion revenue can no longer offset churn.",
    ),
]

NEUTRAL_TEMPLATES: List[Tuple[str, str]] = [
    (
        "{name} in-line with expectations; guidance unchanged",
        "{name} ({ticker}) delivered results broadly in line with analyst consensus. Management held full-year guidance steady, providing neither upside nor downside surprise.",
    ),
    (
        "{name} exploring strategic alternatives for non-core business unit",
        "{name} ({ticker}) confirmed it has hired advisers to explore options for a non-core segment, which could include a sale, spin-off, or IPO. No timeline was provided.",
    ),
    (
        "{name} appoints new CFO recruited from outside the company",
        "{name} ({ticker}) named a new Chief Financial Officer from a peer company. Analysts described the appointment as a neutral development pending strategic clarity.",
    ),
    (
        "{name} refinances debt at lower rate, extends maturity profile",
        "{name} ({ticker}) completed a debt refinancing, reducing its average interest rate and extending the maturity wall. The transaction was described as routine balance-sheet housekeeping.",
    ),
    (
        "{name} hosts analyst day; reiterates long-term financial targets",
        "{name} ({ticker}) held its annual investor day, reiterating long-range revenue and margin targets. No material changes to strategy were announced.",
    ),
    (
        "{name} acquires small startup for technology and talent",
        "{name} ({ticker}) announced the acquisition of an early-stage startup for an undisclosed sum. The deal is described as an acqui-hire focused on specific technical capabilities.",
    ),
    (
        "{name} COO at conference: demand environment 'cautiously optimistic'",
        "Speaking at an industry conference, the COO of {name} ({ticker}) described the demand environment as cautiously optimistic, echoing balanced tone across the sector.",
    ),
    (
        "{name} announces leadership transition after multi-year succession plan",
        "{name} ({ticker}) completed a planned CEO transition after a multi-year succession process. The outgoing CEO will serve as a senior adviser through year-end.",
    ),
    (
        "{name} partnering with university research labs on next-gen technology",
        "{name} ({ticker}) announced collaborative research agreements with several leading universities, targeting technology development over a 3-5 year horizon.",
    ),
    (
        "{name} files 10-Q on schedule with no significant accounting changes",
        "{name} ({ticker}) filed its quarterly 10-Q on schedule, with no material restatements or changes to accounting policies noted by analysts reviewing the document.",
    ),
    (
        "{name} ESG report highlights carbon reduction progress",
        "{name} ({ticker}) published its annual ESG report, noting progress on carbon intensity reduction targets. The disclosure was viewed as broadly in line with industry peers.",
    ),
    (
        "{name} IR update: no material change in business outlook",
        "{name} ({ticker}) issued an investor relations update reiterating its previously disclosed financial outlook, citing no material developments since its last earnings call.",
    ),
    (
        "{name} board elects two independent directors with industry expertise",
        "{name} ({ticker}) added two independent directors to its board, bringing relevant sector experience. Analysts viewed the governance refresh as modest but positive.",
    ),
    (
        "{name} annual shareholder meeting passes all resolutions",
        "{name} ({ticker}) held its annual meeting with all board nominees and executive compensation resolutions approved by shareholders, with no significant dissent noted.",
    ),
    (
        "{name} updates transfer pricing policy, no material P&L impact expected",
        "{name} ({ticker}) disclosed an update to its intercompany transfer pricing methodology following a routine tax review. The company guided to no material financial statement impact.",
    ),
    (
        "{name} completes previously announced workforce restructuring",
        "{name} ({ticker}) said it has completed its previously disclosed restructuring programme, having exited certain geographies and reduced headcount in line with earlier guidance.",
    ),
    (
        "{name} renews existing credit facility on similar terms",
        "{name} ({ticker}) completed renewal of its $5B revolving credit facility, extending the maturity by three years on largely unchanged economic terms.",
    ),
    (
        "{name} confirms participation in upcoming industry trade show",
        "{name} ({ticker}) confirmed it will have a presence at the sector's leading annual trade show, where it is expected to showcase upcoming products but has not pre-announced specific launches.",
    ),
    (
        "{name} legal update: ongoing litigation proceeds as previously disclosed",
        "{name} ({ticker}) provided an update confirming that outstanding litigation matters are proceeding as previously disclosed, with no material new developments to report.",
    ),
    (
        "{name} CFO to present at investor conference next week",
        "{name} ({ticker}) CFO is scheduled to present at a sell-side investor conference, where management is expected to reiterate previously provided financial guidance.",
    ),
]

# ── Feed builder ──────────────────────────────────────────────────────────────

_ALL_TEMPLATES = (
    [(t, "positive") for t in POSITIVE_TEMPLATES]
    + [(t, "negative") for t in NEGATIVE_TEMPLATES]
    + [(t, "neutral")  for t in NEUTRAL_TEMPLATES]
)

ARTICLES_PER_TICKER = 10   # 100 tickers × 10 = 1000 total articles


def build_feed(seed: int = 42) -> Dict[str, List[Dict[str, str]]]:
    """
    Generate the full synthetic feed.

    Args:
        seed: Random seed for reproducibility.

    Returns:
        Dict mapping ticker → list of article dicts.
    """
    rng = random.Random(seed)
    feed: Dict[str, List[Dict[str, str]]] = {}

    for ticker, name, sector, desc in TICKERS:
        chosen = rng.choices(_ALL_TEMPLATES, k=ARTICLES_PER_TICKER)
        articles = []
        for (headline_fmt, summary_fmt), _ in chosen:
            articles.append({
                "source":   rng.choice(SOURCES),
                "headline": headline_fmt.format(name=name, ticker=ticker, desc=desc),
                "summary":  summary_fmt.format(name=name, ticker=ticker, desc=desc),
            })
        feed[ticker] = articles

    return feed


# Pre-built export — import this directly
MOCK_FEED: Dict[str, List[Dict[str, str]]] = build_feed()

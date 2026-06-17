"""The public-data-only company scenario fixture set (3+ diverse industries).

PUBLIC-DATA ONLY (CLAUDE.md §3.12)
----------------------------------
Every figure here is a public-style, publicly-stated financial of the KIND a
company discloses in an annual report / public filing (revenue, opex, cash,
margins, churn) — there is NO real PII, no client-confidential data, and no real
customer record. The numbers are representative public-shape values for a diverse
set of industries (a SaaS firm, a manufacturer, a retailer, an energy utility) so
the validation proves the platform GENERALISES across business models rather than
fitting one (CLAUDE.md §3.9). Each scenario is a frozen, deterministic input
bundle: identical inputs always drive an identical build + operate run.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class PublicCompanyScenario(BaseModel):
    """One diverse company described entirely from public-style figures.

    Fields are grouped by the platform feature they feed: org/gap (the missing
    capability to auto-create), finance (ledger seed + valuation), decisions
    (pricing + runway), market-intel (a public market observation), and the
    front-door question a human owner would actually ask.
    """

    model_config = ConfigDict(frozen=True)

    # -- identity (public) ----------------------------------------------------
    slug: str  # slug-safe id; also the isolated workspace folder name
    name: str  # public company name
    industry: str  # the diverse industry this scenario covers

    # -- org / gap-driven auto-hire -------------------------------------------
    gap_role_id: str  # the capability gap to auto-create + hire
    gap_role_responsibilities: tuple[str, ...]  # what the new role does
    gap_rationale: str  # PII-free 'why' the gap was detected (audited)

    # -- finance (public-style ledger seed, in whole currency units) ----------
    equity_invested: Decimal  # founding equity raised (public)
    loan_principal: Decimal  # debt drawn (public)
    capex: Decimal  # property/plant/equipment purchased (public)
    revenue: Decimal  # period revenue (public, publicly-stated)
    operating_expense: Decimal  # period opex (public)
    # DCF: projected per-period free cash flows + the discount rate (public WACC).
    projected_cash_flows: tuple[Decimal, ...]
    discount_rate: Decimal
    terminal_growth: Decimal

    # -- decisions ------------------------------------------------------------
    unit_cost: Decimal  # marginal cost per unit (pricing model)
    price_elasticity: Decimal  # own-price elasticity magnitude (> 1)
    min_margin: Decimal  # required gross-margin floor in [0, 1)
    starting_cash: Decimal  # runway model: cash on hand
    monthly_revenue: Decimal  # runway model: monthly revenue
    monthly_fixed_cost: Decimal  # runway model: monthly fixed cost

    # -- market intelligence + front door -------------------------------------
    market_observation: str  # a public market signal (sanitized at the boundary)
    owner_question: str  # the human question routed to the right team


# A fixed founding epoch so every audit timestamp in the validation is
# deterministic and assertable (no wall-clock, CLAUDE.md §3.11).
_SAAS = PublicCompanyScenario(
    slug="northwind-saas",
    name="Northwind Analytics (SaaS)",
    industry="B2B SaaS analytics",
    gap_role_id="fpa-lead",
    gap_role_responsibilities=("own financial planning forecasting and the model",),
    gap_rationale="no role owns the financial model; FP&A capability gap",
    equity_invested=Decimal("8000000.00"),
    loan_principal=Decimal("2000000.00"),
    capex=Decimal("1500000.00"),
    revenue=Decimal("12400000.00"),
    operating_expense=Decimal("9800000.00"),
    projected_cash_flows=(Decimal("2600000"), Decimal("3100000"), Decimal("3700000")),
    discount_rate=Decimal("0.12"),
    terminal_growth=Decimal("0.03"),
    unit_cost=Decimal("18.00"),  # marginal cost to serve one seat
    price_elasticity=Decimal("2.4"),
    min_margin=Decimal("0.70"),
    starting_cash=Decimal("6500000"),
    monthly_revenue=Decimal("1033333"),
    monthly_fixed_cost=Decimal("816666"),
    market_observation="competitor raised seat pricing 15% across the analytics market",
    owner_question="what price should we set per seat and is our margin protected",
)

_MANUFACTURER = PublicCompanyScenario(
    slug="ironforge-mfg",
    name="Ironforge Components (Manufacturing)",
    industry="Industrial component manufacturing",
    gap_role_id="supply-chain-lead",
    gap_role_responsibilities=("own procurement supplier risk and inventory planning",),
    gap_rationale="no role owns supplier risk; supply-chain capability gap",
    equity_invested=Decimal("15000000.00"),
    loan_principal=Decimal("10000000.00"),
    capex=Decimal("12000000.00"),
    revenue=Decimal("48000000.00"),
    operating_expense=Decimal("41500000.00"),
    projected_cash_flows=(Decimal("4200000"), Decimal("4500000"), Decimal("4900000")),
    discount_rate=Decimal("0.10"),
    terminal_growth=Decimal("0.02"),
    unit_cost=Decimal("240.00"),  # cost to build one component
    price_elasticity=Decimal("1.8"),
    min_margin=Decimal("0.35"),
    starting_cash=Decimal("9000000"),
    monthly_revenue=Decimal("4000000"),
    monthly_fixed_cost=Decimal("3650000"),
    market_observation="raw steel input costs rose 8% on public commodity indices",
    owner_question="route a question about supplier procurement and inventory risk",
)

_RETAILER = PublicCompanyScenario(
    slug="brightcart-retail",
    name="Brightcart (E-commerce Retail)",
    industry="Direct-to-consumer e-commerce retail",
    gap_role_id="growth-marketing-lead",
    gap_role_responsibilities=("own paid acquisition retention and campaign performance",),
    gap_rationale="no role owns paid acquisition; growth-marketing capability gap",
    equity_invested=Decimal("5000000.00"),
    loan_principal=Decimal("1000000.00"),
    capex=Decimal("800000.00"),
    revenue=Decimal("22000000.00"),
    operating_expense=Decimal("20100000.00"),
    projected_cash_flows=(Decimal("1100000"), Decimal("1300000"), Decimal("1450000")),
    discount_rate=Decimal("0.14"),
    terminal_growth=Decimal("0.025"),
    unit_cost=Decimal("26.00"),  # landed cost of goods per order
    price_elasticity=Decimal("3.2"),  # price-sensitive consumer demand
    min_margin=Decimal("0.45"),
    starting_cash=Decimal("3200000"),
    monthly_revenue=Decimal("1833333"),
    monthly_fixed_cost=Decimal("1675000"),
    market_observation="consumer demand shifting toward sustainable product lines",
    owner_question="give guidance on onboarding new growth marketing channels",
)

_ENERGY = PublicCompanyScenario(
    slug="solaris-energy",
    name="Solaris Grid (Renewable Energy)",
    industry="Renewable energy / utility",
    gap_role_id="regulatory-affairs-lead",
    gap_role_responsibilities=("own grid compliance permitting and regulatory filings",),
    gap_rationale="no role owns regulatory filings; compliance capability gap",
    equity_invested=Decimal("40000000.00"),
    loan_principal=Decimal("35000000.00"),
    capex=Decimal("55000000.00"),
    revenue=Decimal("31000000.00"),
    operating_expense=Decimal("24000000.00"),
    projected_cash_flows=(Decimal("7000000"), Decimal("7600000"), Decimal("8200000")),
    discount_rate=Decimal("0.08"),
    terminal_growth=Decimal("0.02"),
    unit_cost=Decimal("0.04"),  # cost per kWh generated
    price_elasticity=Decimal("1.4"),
    min_margin=Decimal("0.30"),
    starting_cash=Decimal("18000000"),
    monthly_revenue=Decimal("2583333"),
    monthly_fixed_cost=Decimal("2000000"),
    market_observation="new public clean-energy subsidy announced for grid operators",
    owner_question="investigate a breach incident report on our grid telemetry",
)


# The frozen, ordered corpus. Four diverse industries (>3 required) so the
# validation proves generalisation across genuinely different business models.
PUBLIC_COMPANY_SCENARIOS: tuple[PublicCompanyScenario, ...] = (
    _SAAS,
    _MANUFACTURER,
    _RETAILER,
    _ENERGY,
)


def public_company_scenarios() -> tuple[PublicCompanyScenario, ...]:
    """Return the frozen, public-data-only scenario corpus (deterministic order)."""
    return PUBLIC_COMPANY_SCENARIOS

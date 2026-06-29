"""
French state pension calculator — régime général + AGIRC-ARRCO.
2026 constants per CNAV and AGIRC-ARRCO publications. Stateless pure computation.
"""
from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

PASS = Decimal("48060")                 # 2026 Plafond annuel de la Sécurité sociale
MIN_SALARY_PER_QUARTER = Decimal("1803")  # 150h × SMIC €12.02
FULL_RATE = Decimal("0.50")
DECOTE_PER_Q = Decimal("0.0125")
MAX_DECOTE_Q = 20
SURCOTE_PER_Q = Decimal("0.0125")
MIN_CONTRIBUTIF = Decimal("903.93")     # monthly gross floor, full 172-quarter career (2026)
POINT_VALUE = Decimal("1.4386")         # AGIRC-ARRCO point value (2026)
ACQ_PRICE = Decimal("20.1877")          # AGIRC-ARRCO point acquisition price (2026)
T1_RATE = Decimal("0.0787")             # Tranche 1 combined rate (employer + employee, up to PASS)
T2_RATE = Decimal("0.06")               # Tranche 2 simplified rate (above PASS)
AUTO_FULL_AGE = 67                      # taux plein automatique regardless of quarters
CURRENT_YEAR = 2026


def _birth_year_params(birth_year: int) -> tuple[int, int]:
    """Return (required_quarters, legal_age_months) per 2023 reform (Loi du 14 avril 2023)."""
    if birth_year < 1958:   return 160, 720   # pre-reform: 60 years
    if birth_year <= 1960:  return 167, 744   # 62 years
    if birth_year == 1961:  return 168, 747   # 62y3m
    if birth_year == 1962:  return 169, 750   # 62y6m
    if birth_year == 1963:  return 170, 753   # 62y9m
    if birth_year == 1964:  return 171, 756   # 63y
    if birth_year == 1965:  return 172, 759   # 63y3m
    if birth_year == 1966:  return 172, 762   # 63y6m
    if birth_year == 1967:  return 172, 765   # 63y9m
    return 172, 768                           # 1968+: 64 years


def _salary_at_year(year: int, current: Decimal, growth: Decimal) -> Decimal:
    delta = year - CURRENT_YEAR
    return current * (1 + growth) ** delta


def _build_career(start: int, end_exclusive: int, current: Decimal, growth: Decimal) -> list:
    """Build list of (year, salary, capped_salary, quarters, arrco_points)."""
    rows = []
    for year in range(start, end_exclusive):
        sal = _salary_at_year(year, current, growth)
        capped = min(sal, PASS)
        q = min(4, int(sal // MIN_SALARY_PER_QUARTER))
        t1 = min(sal, PASS)
        t2 = max(Decimal(0), min(sal, 8 * PASS) - PASS)
        pts = (t1 * T1_RATE + t2 * T2_RATE) / ACQ_PRICE
        rows.append((year, sal, capped, q, pts))
    return rows


def _stats_at(rows: list, up_to_year: int, bonus_q: int) -> tuple[Decimal, int, Decimal]:
    """Return (sam, quarters_validated, total_arrco_points) for career up to up_to_year."""
    active = [r for r in rows if r[0] < up_to_year]
    q_total = sum(r[3] for r in active) + bonus_q
    pts_total = sum(r[4] for r in active)
    caps = sorted((r[2] for r in active if r[2] > 0), reverse=True)
    n = min(25, len(caps))
    sam = sum(caps[:n]) / n if n > 0 else Decimal(0)
    return sam, q_total, pts_total


def _compute_row(
    birth_year: int,
    ret_year: int,
    sam: Decimal,
    q_val: int,
    pts: Decimal,
    q_req: int,
    legal_months: int,
    current_salary: Decimal,
) -> dict:
    age = ret_year - birth_year
    decote_q = surcote_q = 0
    full = False

    if age >= AUTO_FULL_AGE:
        rate = FULL_RATE
        full = True
    elif q_val >= q_req and age >= legal_months / 12:
        extra = q_val - q_req
        surcote_q = extra
        rate = FULL_RATE + SURCOTE_PER_Q * extra
        full = True
    else:
        missing = max(0, q_req - q_val)
        decote_q = min(missing, MAX_DECOTE_Q)
        rate = max(Decimal("0.25"), FULL_RATE - DECOTE_PER_Q * decote_q)

    prorata = min(Decimal(1), Decimal(q_val) / Decimal(q_req)) if q_req else Decimal(1)
    base_raw = sam * rate * prorata / 12
    monthly_base = max(base_raw, MIN_CONTRIBUTIF * prorata) if q_val > 0 else Decimal(0)
    monthly_comp = pts * POINT_VALUE / 12
    monthly_total = monthly_base + monthly_comp

    monthly_sal = current_salary / 12
    replacement = monthly_total / monthly_sal if monthly_sal else Decimal(0)

    def r2(d: Decimal) -> Decimal:
        return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def r4(d: Decimal) -> Decimal:
        return d.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    return {
        "retirement_age": float(age),
        "retirement_year": ret_year,
        "quarters_validated": q_val,
        "rate_applied": r4(rate),
        "decote_quarters": decote_q,
        "surcote_quarters": surcote_q,
        "monthly_base": r2(monthly_base),
        "monthly_complementary": r2(monthly_comp),
        "monthly_total": r2(monthly_total),
        "replacement_ratio": r4(replacement),
        "achieves_full_rate": full,
    }


def project_pension(inp) -> dict:
    """Compute state pension projection from PensionProjectionIn fields."""
    q_req, legal_months = _birth_year_params(inp.birth_year)

    career = _build_career(
        inp.career_start_year,
        inp.planned_retirement_year + 6,
        inp.current_annual_salary,
        inp.salary_growth_rate,
    )

    sam, q_val, pts = _stats_at(career, inp.planned_retirement_year, inp.bonus_quarters)

    planned = _compute_row(
        inp.birth_year, inp.planned_retirement_year, sam, q_val, pts,
        q_req, legal_months, inp.current_annual_salary,
    )

    # Sensitivity: legal retirement year to planned+5, capped to max 10 rows before planned
    legal_year = inp.birth_year + (legal_months + 11) // 12
    sens_start = max(legal_year, inp.planned_retirement_year - 4)
    sens_end = inp.planned_retirement_year + 5

    sensitivity = []
    for ret_year in range(sens_start, sens_end + 1):
        s, q, p = _stats_at(career, ret_year, inp.bonus_quarters)
        sensitivity.append(_compute_row(
            inp.birth_year, ret_year, s, q, p,
            q_req, legal_months, inp.current_annual_salary,
        ))

    def r2(d: Decimal) -> Decimal:
        return d.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def r4(d: Decimal) -> Decimal:
        return d.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    return {
        "sam": r2(sam),
        "quarters_validated": q_val,
        "quarters_required": q_req,
        "total_agirc_arrco_points": r4(pts),
        "planned": planned,
        "sensitivity": sensitivity,
    }

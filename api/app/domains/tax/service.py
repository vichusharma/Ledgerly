"""Tax profile + estimate service. Feature I2 (person/household tax
profile — facts only) and Feature I3 (salary-only PAS reconciliation —
the first real tax computation) of docs/Backlog.md."""
from __future__ import annotations

import datetime
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tax import (
    BaremeBracket,
    apply_impatriate_exemption,
    compute_parts,
    compute_quotient_tax,
    impatriate_years_remaining,
    project_annual_from_ytd,
    reconcile_withholding,
)
from app.domains.accounts.models import Person
from app.domains.accounts.repository import PersonRepository
from app.domains.salary.service import SalaryService
from app.domains.tax.models import (
    FilingStatus,
    HouseholdTaxDependent,
    HouseholdTaxSettings,
    TaxYearConfig,
)
from app.domains.tax.schemas import (
    HouseholdTaxSettingsOut,
    HouseholdTaxSettingsUpdateIn,
    PersonTaxEstimateOut,
    PersonTaxProfileOut,
    PersonTaxProfileUpdateIn,
    TaxEstimateOut,
)


@dataclass
class _FallbackTaxYearConfig:
    """Last-resort in-code default, used only if `tax_year_configs` has
    zero rows (e.g. migrations haven't run yet). Mirrors migration
    `0010_tax_year_config.py`'s seed — see that file for why these are a
    placeholder (2025 Loi de Finances figures) rather than a confirmed
    2026 barème."""
    tax_year: int
    brackets: list[dict]
    quotient_familial_plafond_per_half_part: Decimal


_DEFAULT_TAX_YEAR_CONFIG = _FallbackTaxYearConfig(
    tax_year=2026,
    brackets=[
        {"up_to": 11497, "rate": 0.0},
        {"up_to": 29315, "rate": 0.11},
        {"up_to": 83823, "rate": 0.30},
        {"up_to": 180294, "rate": 0.41},
        {"up_to": None, "rate": 0.45},
    ],
    quotient_familial_plafond_per_half_part=Decimal("1791.00"),
)


class TaxService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self._person_repo = PersonRepository(session)

    async def get_person_tax_profile(self, person_id: int) -> PersonTaxProfileOut | None:
        person = await self.session.get(Person, person_id)
        if person is None:
            return None
        return PersonTaxProfileOut(
            person_id=person.id,
            impatriate_enabled=person.impatriate_enabled,
            impatriate_arrival_date=person.impatriate_arrival_date,
            impatriate_election_method=person.impatriate_election_method,
        )

    async def set_person_tax_profile(
        self, person_id: int, body: PersonTaxProfileUpdateIn
    ) -> PersonTaxProfileOut | None:
        person = await self.session.get(Person, person_id)
        if person is None:
            return None
        person.impatriate_enabled = body.impatriate_enabled
        person.impatriate_arrival_date = body.impatriate_arrival_date
        person.impatriate_election_method = body.impatriate_election_method
        await self.session.flush()
        return await self.get_person_tax_profile(person_id)

    async def _get_or_create_settings(self) -> HouseholdTaxSettings:
        household = await self._person_repo.get_household()
        if household is None:
            raise ValueError("No household configured. Call /auth/setup first.")
        result = await self.session.execute(
            select(HouseholdTaxSettings).where(
                HouseholdTaxSettings.household_id == household.id
            )
        )
        settings = result.scalar_one_or_none()
        if settings is None:
            settings = HouseholdTaxSettings(household_id=household.id)
            self.session.add(settings)
            await self.session.flush()
        return settings

    async def get_household_tax_settings(self) -> HouseholdTaxSettingsOut:
        settings = await self._get_or_create_settings()
        dependents = await self.session.execute(
            select(HouseholdTaxDependent.person_id).where(
                HouseholdTaxDependent.household_tax_settings_id == settings.id
            )
        )
        return HouseholdTaxSettingsOut(
            filing_status=settings.filing_status,
            dependent_person_ids=sorted(row[0] for row in dependents),
        )

    async def set_household_tax_settings(
        self, body: HouseholdTaxSettingsUpdateIn
    ) -> HouseholdTaxSettingsOut:
        persons = await self._person_repo.list_persons()
        valid_ids = {p.id for p in persons}
        unknown = [pid for pid in body.dependent_person_ids if pid not in valid_ids]
        if unknown:
            raise ValueError(f"Unknown person_id(s) for dependents: {unknown}")

        settings = await self._get_or_create_settings()
        settings.filing_status = body.filing_status
        await self.session.execute(
            delete(HouseholdTaxDependent).where(
                HouseholdTaxDependent.household_tax_settings_id == settings.id
            )
        )
        for person_id in set(body.dependent_person_ids):
            self.session.add(
                HouseholdTaxDependent(
                    household_tax_settings_id=settings.id, person_id=person_id
                )
            )
        await self.session.flush()
        return await self.get_household_tax_settings()

    async def _get_tax_year_config(
        self, year: int
    ) -> tuple[TaxYearConfig | _FallbackTaxYearConfig, bool]:
        """Return (config, used_fallback) — falls back to the most recent
        seeded year if `year` has no row yet (e.g. next calendar year
        before its barème has been seeded)."""
        result = await self.session.execute(
            select(TaxYearConfig).where(TaxYearConfig.tax_year == year)
        )
        config = result.scalar_one_or_none()
        if config is not None:
            return config, False

        fallback = await self.session.execute(
            select(TaxYearConfig).order_by(TaxYearConfig.tax_year.desc()).limit(1)
        )
        config = fallback.scalar_one_or_none()
        if config is not None:
            return config, True

        # Table has zero rows (migrations not yet run) — degrade to the
        # same in-code default rather than hard-failing the estimate.
        return _DEFAULT_TAX_YEAR_CONFIG, True

    async def get_tax_estimate(
        self, year: int, include_investments: bool = False
    ) -> TaxEstimateOut:
        """Stateless salary-only tax estimate (Feature I3). Investment
        income is always `None` until Feature I4 exists — `include_investments`
        is accepted but has no effect yet."""
        household_settings = await self.get_household_tax_settings()
        persons = await self._person_repo.list_persons()
        salary_service = SalaryService(self.session)

        tax_year_config, used_fallback = await self._get_tax_year_config(year)
        brackets = [
            BaremeBracket(
                None if b["up_to"] is None else Decimal(str(b["up_to"])),
                Decimal(str(b["rate"])),
            )
            for b in tax_year_config.brackets
        ]
        plafond = tax_year_config.quotient_familial_plafond_per_half_part

        today = datetime.date.today()
        simplifications: list[str] = [
            "bareme_placeholder",
            "quotient_familial_general_case_only",
            "ytd_linear_extrapolation",
            "capital_gains_not_included",
        ]
        if used_fallback:
            simplifications.append("bareme_year_fallback")

        num_dependents = len(household_settings.dependent_person_ids)
        person_breakdowns: list[PersonTaxEstimateOut] = []
        specific_premium_seen = False

        for person in persons:
            payslips = await salary_service.list_payslips(person_id=person.id, year=year)
            latest = payslips[0] if payslips else None

            if latest is not None and latest.ytd_gross is not None:
                as_of_month = latest.pay_period.month
                gross_annual = project_annual_from_ytd(latest.ytd_gross, as_of_month)
                net_taxable_annual = project_annual_from_ytd(
                    latest.ytd_net_taxable or Decimal("0"), as_of_month
                )
                pas_ytd = latest.ytd_pas_withheld or Decimal("0")
                pas_annual = project_annual_from_ytd(pas_ytd, as_of_month)
                has_data = True
            else:
                as_of_month = None
                gross_annual = Decimal("0")
                net_taxable_annual = Decimal("0")
                pas_ytd = Decimal("0")
                pas_annual = Decimal("0")
                has_data = False

            net_after_impatriate, exemption_applied = apply_impatriate_exemption(
                net_taxable_annual, person.impatriate_enabled, person.impatriate_election_method
            )
            if (
                person.impatriate_enabled
                and person.impatriate_election_method == "specific_premium"
            ):
                specific_premium_seen = True

            years_remaining = (
                impatriate_years_remaining(person.impatriate_arrival_date, today)
                if person.impatriate_enabled and person.impatriate_arrival_date
                else None
            )

            person_breakdowns.append(PersonTaxEstimateOut(
                person_id=person.id,
                name=person.name,
                has_payslip_data=has_data,
                as_of_month=as_of_month,
                gross_annual_projected=gross_annual,
                net_taxable_annual_projected=net_taxable_annual,
                net_taxable_after_impatriate=net_after_impatriate,
                impatriate_enabled=person.impatriate_enabled,
                impatriate_exemption_applied=exemption_applied,
                impatriate_election_method=person.impatriate_election_method,
                impatriate_arrival_date=person.impatriate_arrival_date,
                impatriate_years_remaining=years_remaining,
                parts_used=Decimal("0"),
                pas_withheld_ytd=pas_ytd,
                pas_withheld_projected_annual=pas_annual,
            ))

        if specific_premium_seen:
            simplifications.append("impatriate_specific_premium_not_computed")

        if household_settings.filing_status == FilingStatus.married_pacs:
            parts = compute_parts("married_pacs", num_dependents)
            household_taxable = sum(
                (p.net_taxable_after_impatriate for p in person_breakdowns), Decimal("0")
            )
            household_gross = sum(
                (p.gross_annual_projected for p in person_breakdowns), Decimal("0")
            )
            estimated_tax, capped = compute_quotient_tax(
                household_taxable, parts, Decimal("2"), brackets, plafond
            )
            for p in person_breakdowns:
                p.parts_used = parts
            top_level_parts: Decimal | None = parts
        else:
            # Unmarried: each adult files separately. Dependents are a
            # household-wide list (not attributed per-person), so they're
            # all applied to the primary person's return — a documented
            # simplification since per-person dependent attribution isn't
            # modeled.
            if num_dependents:
                simplifications.append("single_filing_dependents_attributed_to_primary")
            persons_by_id = {p.id: p for p in persons}
            estimated_tax = Decimal("0")
            capped = False
            household_taxable = Decimal("0")
            household_gross = Decimal("0")
            for p in person_breakdowns:
                person_obj = persons_by_id[p.person_id]
                deps_for_this_person = num_dependents if person_obj.is_primary else 0
                person_parts = compute_parts("single", deps_for_this_person)
                person_tax, person_capped = compute_quotient_tax(
                    p.net_taxable_after_impatriate, person_parts, Decimal("1"), brackets, plafond
                )
                p.parts_used = person_parts
                estimated_tax += person_tax
                capped = capped or person_capped
                household_taxable += p.net_taxable_after_impatriate
                household_gross += p.gross_annual_projected
            top_level_parts = None

        pas_ytd_total = sum((p.pas_withheld_ytd for p in person_breakdowns), Decimal("0"))
        pas_annual_total = sum(
            (p.pas_withheld_projected_annual for p in person_breakdowns), Decimal("0")
        )
        balance = reconcile_withholding(estimated_tax, pas_annual_total)

        return TaxEstimateOut(
            year=year,
            bareme_tax_year_used=tax_year_config.tax_year,
            filing_status=household_settings.filing_status,
            parts=top_level_parts,
            household_gross_income_projected=household_gross,
            household_taxable_income_projected=household_taxable,
            estimated_tax=estimated_tax,
            quotient_familial_capped=capped,
            pas_withheld_ytd_total=pas_ytd_total,
            pas_withheld_projected_annual_total=pas_annual_total,
            balance=balance,
            persons=person_breakdowns,
            simplifications_applied=simplifications,
        )

from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models.scheme import Scheme
from app.models.insurance import Insurance
from app.schemas.eligibility import (
    EligibilityCheckRequest,
    SchemeEligibilityItem,
    EligibilityRecommendationRequest,
    EligibilityRecommendationResponse,
    SchemeRecommendationItem,
    IneligibleSchemeItem,
    InsuranceEligibilityRequest,
    InsuranceEligibilityItem,
)

class EligibilityService:
    @staticmethod
    def calculate_scheme_eligibility(data: EligibilityCheckRequest) -> List[SchemeEligibilityItem]:
        eligible = []
        income = (data.income or "").lower()
        location = (data.location or "").lower()

        if income in ["low", "< 2.5 lakh", "below_poverty_line", "bpl"]:
            eligible.append(SchemeEligibilityItem(scheme="Ayushman Bharat (PM-JAY)", probability=94))
            eligible.append(SchemeEligibilityItem(scheme="MJPJAY Maharashtra", probability=88))

        if location in ["urban", "rural"]:
            eligible.append(SchemeEligibilityItem(scheme="State Health Scheme", probability=78))

        if income in ["medium", "middle", "2.5-5 lakh"]:
            eligible.append(SchemeEligibilityItem(scheme="ESIC (Employee State Insurance)", probability=85))
            eligible.append(SchemeEligibilityItem(scheme="State Health Scheme", probability=72))

        if not eligible:
            eligible.append(SchemeEligibilityItem(scheme="Ayushman Bharat (PM-JAY)", probability=65))
            eligible.append(SchemeEligibilityItem(scheme="State Health Scheme", probability=70))

        return eligible

    @staticmethod
    def evaluate_scheme_recommendations(
        db: Session,
        data: EligibilityRecommendationRequest
    ) -> EligibilityRecommendationResponse:
        schemes = db.query(Scheme).all()
        eligible_list: List[SchemeRecommendationItem] = []
        ineligible_list: List[IneligibleSchemeItem] = []

        income_tier = (data.income or "low").lower()
        state = (data.state or "").lower()
        is_employed = data.is_formally_employed or False
        has_bpl = data.has_bpl_card or income_tier in ["bpl", "low"]

        for scheme in schemes:
            name = scheme.name
            s_lower = name.lower()

            # Rule 1: Ayushman Bharat (PM-JAY)
            if "ayushman" in s_lower or "pm-jay" in s_lower or "pmjay" in s_lower:
                if has_bpl or income_tier in ["low", "bpl"]:
                    eligible_list.append(
                        SchemeRecommendationItem(
                            scheme_id=scheme.id,
                            scheme_name=scheme.name,
                            coverage=scheme.coverage,
                            reason="Household meets the socioeconomic low-income threshold under SECC-aligned criteria.",
                            match_score=95
                        )
                    )
                else:
                    ineligible_list.append(
                        IneligibleSchemeItem(
                            scheme_id=scheme.id,
                            scheme_name=scheme.name,
                            reason="Annual income exceeds the subsidized ceiling for PM-JAY national beneficiary lists."
                        )
                    )

            # Rule 2: ESIC
            elif "esic" in s_lower or "esi" in s_lower:
                if is_employed or income_tier == "medium":
                    eligible_list.append(
                        SchemeRecommendationItem(
                            scheme_id=scheme.id,
                            scheme_name=scheme.name,
                            coverage=scheme.coverage,
                            reason="Formally employed worker within the statutory monthly wage ceiling (up to ₹21,000/month).",
                            match_score=88
                        )
                    )
                else:
                    ineligible_list.append(
                        IneligibleSchemeItem(
                            scheme_id=scheme.id,
                            scheme_name=scheme.name,
                            reason="Requires active formal employment and employer contribution under the ESI Act."
                        )
                    )

            # Rule 3: MJPJAY Maharashtra
            elif "mjpjay" in s_lower or "maharashtra" in s_lower:
                if "maha" in state or "mumbai" in state or has_bpl:
                    eligible_list.append(
                        SchemeRecommendationItem(
                            scheme_id=scheme.id,
                            scheme_name=scheme.name,
                            coverage=scheme.coverage,
                            reason="Qualified based on Maharashtra state residency and Yellow/Orange ration card guidelines.",
                            match_score=90
                        )
                    )
                else:
                    ineligible_list.append(
                        IneligibleSchemeItem(
                            scheme_id=scheme.id,
                            scheme_name=scheme.name,
                            reason="State residency requirement: restricted to permanent residents of Maharashtra."
                        )
                    )

            # Rule 4: CGHS (Central Govt Health Scheme)
            elif "cghs" in s_lower or "central" in s_lower:
                ineligible_list.append(
                    IneligibleSchemeItem(
                        scheme_id=scheme.id,
                        scheme_name=scheme.name,
                        reason="Restricted exclusively to active and retired Central Government employees & dependents."
                    )
                )

            # Generic fallback for any additional schemes
            else:
                if has_bpl or income_tier in ["low", "medium"]:
                    eligible_list.append(
                        SchemeRecommendationItem(
                            scheme_id=scheme.id,
                            scheme_name=scheme.name,
                            coverage=scheme.coverage,
                            reason="Meets general state healthcare assistance criteria.",
                            match_score=75
                        )
                    )
                else:
                    ineligible_list.append(
                        IneligibleSchemeItem(
                            scheme_id=scheme.id,
                            scheme_name=scheme.name,
                            reason="Income or regional guidelines not satisfied."
                        )
                    )

        return EligibilityRecommendationResponse(
            eligible=eligible_list,
            not_eligible=ineligible_list,
            evaluation_engine="deterministic_v1"
        )

    @staticmethod
    def calculate_insurance_eligibility(
        db: Session,
        data: InsuranceEligibilityRequest
    ) -> List[InsuranceEligibilityItem]:
        insurances = db.query(Insurance).all()
        results = []

        for ins in insurances:
            score = 100

            if data.age < ins.eligibility_age_min or data.age > ins.eligibility_age_max:
                score -= 50

            if data.pre_existing_conditions and ins.waiting_period_days > 180:
                score -= 20

            if score >= 50:
                results.append(
                    InsuranceEligibilityItem(
                        id=ins.id,
                        name=ins.name,
                        provider=ins.provider,
                        eligibility_score=score,
                        recommended=score >= 80
                    )
                )

        results.sort(key=lambda x: x.eligibility_score, reverse=True)
        return results

    @staticmethod
    def evaluate_eligibility(
        db: Session,
        request: Any
    ) -> Dict[str, Any]:
        income_val = getattr(request, "income", "low") or "low"
        annual_val = getattr(request, "annual_income_inr", None) or getattr(request, "annual_income", None)
        rec_req = EligibilityRecommendationRequest(
            age=getattr(request, "age", 30) or 30,
            income=income_val,
            annual_income_inr=annual_val,
            has_bpl_card=getattr(request, "has_bpl_card", False) or False,
            is_formally_employed=getattr(request, "is_formally_employed", False) or False,
            state=getattr(request, "state", None),
        )
        resp = EligibilityService.evaluate_scheme_recommendations(db, rec_req)
        return {
            "eligible": [
                {
                    "scheme_id": item.scheme_id,
                    "scheme_name": item.scheme_name,
                    "coverage": item.coverage,
                    "reason": item.reason,
                    "match_reason": item.reason,
                    "match_score": item.match_score
                }
                for item in resp.eligible
            ],
            "not_eligible": [
                {
                    "scheme_id": item.scheme_id,
                    "scheme_name": item.scheme_name,
                    "reason": item.reason,
                    "reasons": [item.reason]
                }
                for item in resp.not_eligible
            ]
        }


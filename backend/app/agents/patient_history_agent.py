"""
MedSentinel Agentic Architecture — Patient History Agent
Retrieves longitudinal medical baselines, computes parameter deltas,
and identifies worsening or improving health trends over time.
"""

from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session

from app.agents.base import BaseAgent
from app.agents.state import WorkflowState, AgentResult, ClinicalFinding
from app.agents.tools import get_patient_history_tool


class PatientHistoryAgent(BaseAgent):
    """
    Specialized agent for retrieving longitudinal patient records and detecting parameter deltas.
    """

    def __init__(self):
        super().__init__(
            name="patient_history",
            role="Longitudinal History & Trend Analysis",
            description="Queries longitudinal historical tests and calculates parameter trajectories (increasing, decreasing, stable).",
            version="1.0.0"
        )

    async def execute(
        self,
        state: WorkflowState,
        db: Optional[Session] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        if not db or (not state.patient_id and not state.user_id):
            return AgentResult(
                success=True,
                agent_name=self.name,
                data={"status": "SKIPPED_NO_PATIENT_IDENTITY", "history_available": False}
            )

        # Call Patient History Tool
        hist_data = await get_patient_history_tool(
            db=db,
            patient_id=state.patient_id,
            user_id=state.user_id,
            limit=20
        )

        test_history = hist_data.get("test_history", {})
        state.historical_results = hist_data.get("documents", [])

        # Compare current lab tests with historical baselines
        trends: Dict[str, Any] = {}
        findings: List[ClinicalFinding] = []

        current_tests = state.lab_results or []
        for curr in current_tests:
            name = curr.get("name")
            curr_val = curr.get("value")
            if not name or curr_val is None:
                continue

            past_list = test_history.get(name, [])
            if past_list:
                # Most recent previous value
                prev_test = past_list[0]
                prev_val = prev_test.get("value")

                if prev_val is not None and prev_val > 0:
                    delta = round(curr_val - prev_val, 2)
                    pct_change = round(((curr_val - prev_val) / prev_val) * 100, 1)

                    if abs(pct_change) < 4.0:
                        trend_dir = "STABLE"
                    elif pct_change > 0:
                        trend_dir = "INCREASING"
                    else:
                        trend_dir = "DECREASING"

                    trends[name] = {
                        "current_value": curr_val,
                        "previous_value": prev_val,
                        "delta": delta,
                        "pct_change": pct_change,
                        "trend": trend_dir,
                        "previous_date": prev_test.get("date"),
                    }

                    # Add finding if significant variation (> 15% shift)
                    if abs(pct_change) >= 15.0:
                        status_str = "HIGH" if curr.get("is_critical") or abs(pct_change) >= 30.0 else "MODERATE"
                        findings.append(
                            self.create_finding(
                                title=f"Significant {name} Longitudinal Shift ({trend_dir})",
                                description=(
                                    f"{name} changed from {prev_val} to {curr_val} {curr.get('unit', '')} "
                                    f"({pct_change:+0.1f}% change since {prev_test.get('date', 'previous record')})."
                                ),
                                category="LONGITUDINAL_TREND",
                                parameter_name=name,
                                observed_value=curr_val,
                                unit=curr.get("unit"),
                                status=status_str,
                                confidence=0.95
                            )
                        )
            else:
                trends[name] = {
                    "current_value": curr_val,
                    "previous_value": None,
                    "delta": 0.0,
                    "pct_change": 0.0,
                    "trend": "FIRST_RECORD",
                }

        state.longitudinal_trends = trends

        if not findings and current_tests:
            findings.append(
                self.create_finding(
                    title="Longitudinal Baseline Established",
                    description=f"Longitudinal analysis updated across {len(current_tests)} parameters.",
                    category="LONGITUDINAL_TREND",
                    status="NORMAL",
                    confidence=0.90
                )
            )

        return AgentResult(
            success=True,
            agent_name=self.name,
            data={
                "total_past_documents": hist_data.get("total_past_documents", 0),
                "tracked_parameters": list(trends.keys()),
                "trends": trends,
            },
            findings=findings
        )

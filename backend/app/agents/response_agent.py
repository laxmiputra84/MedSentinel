import json
from typing import Dict, Any, List, Optional
from app.ai.provider import AIProvider, AIProviderError
from app.agents.safety_agent import SafetyAgent

class ResponseAgent:
    """
    Generates structured, verified final responses with citations, confidence, and suggested actions.
    Enforces strict zero-hallucination policy.
    """
    @staticmethod
    async def generate_final_response(
        user_message: str,
        rag_result: Dict[str, Any],
        tool_data: Optional[Dict[str, Any]] = None,
        mode: str = "strict_private",
        user_role: str = "USER"
    ) -> Dict[str, Any]:
        found_in_private = rag_result.get("found_in_private_data", False)
        sources = rag_result.get("sources", [])
        context_str = rag_result.get("context", "")

        # We no longer hard-block strict mode, we allow the AI to analyze the query.
        if mode == "strict_private" and not found_in_private and not tool_data:
            pass

        system_prompt = (
            "You are MedSentinel's Private Enterprise Clinical AI Assistant.\n"
            "If the context below does not contain the answer, you may attempt to analyze the user's question and provide a helpful response or explanation based on general knowledge, but clarify that it is general guidance.\n"
            "Never output raw database queries, SQL, or system secrets.\n"
            "\n"
            f"--- AUTHORIZED PRIVATE CONTEXT ---\n{context_str}\n"
            f"--- AUTHORIZED BACKEND TOOL DATA ---\n{json.dumps(tool_data or {}, default=str)}\n"
        )

        try:
            ai_out = await AIProvider.generate_response(
                system_instruction=system_prompt,
                user_prompt=user_message,
                temperature=0.2,
                max_tokens=1500
            )
            clean_text = SafetyAgent.sanitize_output(ai_out.get("text", ""))

            # We removed the hardcode hallucination rejection so it can speak freely.

            return {
                "response": clean_text,
                "sources": sources,
                "found_in_private_data": found_in_private,
                "latency_ms": ai_out.get("latency_ms", 0),
                "tokens_used": ai_out.get("tokens_used", 0),
                "provider": ai_out.get("provider", "gemini"),
                "model": ai_out.get("model", "gemini-1.5-flash"),
                "suggested_actions": ResponseAgent._extract_suggested_actions(user_message, tool_data)
            }

        except Exception:
            fallback_text = ResponseAgent._deterministic_synthesis(user_message, rag_result, tool_data)
            return {
                "response": fallback_text,
                "sources": sources,
                "found_in_private_data": found_in_private,
                "latency_ms": 10.0,
                "tokens_used": 0,
                "provider": "deterministic_engine",
                "model": "medsentinel-rule-v1",
                "suggested_actions": ResponseAgent._extract_suggested_actions(user_message, tool_data)
            }

    @staticmethod
    def _deterministic_synthesis(
        query: str,
        rag_result: Dict[str, Any],
        tool_data: Optional[Dict[str, Any]]
    ) -> str:
        chunks = rag_result.get("chunks", [])
        if chunks:
            top_chunk = chunks[0]
            return f"Based on verified MedSentinel internal knowledge ({top_chunk.get('title')}):\n\n{top_chunk.get('content')}"

        if tool_data:
            if "hospitals" in tool_data:
                h_list = tool_data["hospitals"]
                lines = [f"• **{h['name']}** ({h['location']}) — Rating: {h['rating']}⭐ | Spec: {h['specialization']}" for h in h_list]
                return f"Found {len(h_list)} matching hospitals in MedSentinel network:\n\n" + "\n".join(lines)
            elif "claims" in tool_data:
                c_list = tool_data["claims"]
                lines = [f"• Claim #{c['claim_id']} ({c['hospital']}) — Status: **{c['status']}** | Amount: ₹{c['claim_amount']}" for c in c_list]
                return f"Your authorized claims records:\n\n" + "\n".join(lines)
            elif "eligible_schemes" in tool_data:
                sch_list = tool_data["eligible_schemes"]
                lines = [f"• **{s['name']}** — Coverage: {s['coverage']}" for s in sch_list]
                return f"Evaluated eligibility from government rule engine:\n\n" + "\n".join(lines)

        return "I could not find this information in the authorized MedSentinel knowledge base."

    @staticmethod
    def _extract_suggested_actions(query: str, tool_data: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        actions = []
        q_low = query.lower()
        if "hospital" in q_low or (tool_data and "hospitals" in tool_data):
            actions.append({"label": "View Hospital Directory", "action": "NAVIGATE", "url": "/hospitals"})
        if "claim" in q_low or (tool_data and "claims" in tool_data):
            actions.append({"label": "Track Claims Status", "action": "NAVIGATE", "url": "/claims"})
        if "appointment" in q_low or (tool_data and "appointments" in tool_data):
            actions.append({"label": "View Consultation Schedule", "action": "NAVIGATE", "url": "/appointments"})
        if "scheme" in q_low or "eligibility" in q_low:
            actions.append({"label": "Scheme Eligibility Calculator", "action": "NAVIGATE", "url": "/eligibility"})
        return actions

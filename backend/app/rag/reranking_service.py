import re
from typing import List, Dict, Any

class RerankingService:
    @staticmethod
    def rerank(query: str, items: List[Dict[str, Any]], top_k: int = 4) -> List[Dict[str, Any]]:
        """
        Re-ranks candidate chunks based on:
        1. Base semantic vector similarity score
        2. Exact query keyword matching
        3. Title match boost
        """
        if not items:
            return []

        query_terms = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
        scored_items = []

        for item in items:
            content = item.get("content", "").lower()
            title = item.get("title", "").lower()
            base_score = float(item.get("score", 0.5))

            # Keyword match bonus
            kw_matches = sum(1 for term in query_terms if term in content)
            title_matches = sum(1 for term in query_terms if term in title)

            kw_boost = (kw_matches / max(len(query_terms), 1)) * 0.25
            title_boost = (title_matches / max(len(query_terms), 1)) * 0.15

            final_score = min(1.0, base_score + kw_boost + title_boost)
            
            item_copy = dict(item)
            item_copy["confidence"] = round(final_score, 3)
            scored_items.append(item_copy)

        scored_items.sort(key=lambda x: x["confidence"], reverse=True)
        return scored_items[:top_k]

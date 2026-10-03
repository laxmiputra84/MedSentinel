from typing import List, Dict, Any

class ContextBuilder:
    @staticmethod
    def build_rag_context(chunks: List[Dict[str, Any]]) -> str:
        """
        Formats retrieved knowledge chunks into structured LLM context with explicit source citations.
        """
        if not chunks:
            return "NO_PRIVATE_KNOWLEDGE_FOUND"

        context_blocks = []
        for idx, ch in enumerate(chunks, 1):
            title = ch.get("title", "Authorized Document")
            dataset_id = ch.get("dataset_id", "N/A")
            doc_id = ch.get("document_id", "N/A")
            content = ch.get("content", "").strip()
            confidence = ch.get("confidence", ch.get("score", 0.0))

            block = (
                f"--- [SOURCE {idx} | Dataset ID: {dataset_id} | Doc ID: {doc_id} | Title: {title} | Confidence: {confidence}] ---\n"
                f"{content}\n"
            )
            context_blocks.append(block)

        return "\n".join(context_blocks)

"""Owner: A. Retrieval + truth-state Q&A (architecture.md §Knowledge module & RAG posture).

STUB — P5 deliverable (KNW-1/2). Structured-first retrieval (typed SQL over
decisions/tasks/signals/parties); pgvector (KNW-3) only if keyword retrieval
measurably misses. LangChain lives ONLY in this module.
"""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from evermind.contracts.enums import DecisionStatus
from evermind.decisions.models import Decision, DecisionCitation


class KnowledgeService:
    def __init__(self, session: Session):
        self.session = session

    def answer(self, question: str, persona: str) -> dict:
        """Return only receipt-backed effective decision statements.

        This deliberately structured first pass is deterministic and avoids an
        LLM paraphrasing uncited source text while the extraction lane matures.
        """
        words = [word.lower() for word in question.split() if len(word) >= 3]
        rows = list(self.session.scalars(
            select(Decision).where(Decision.status == DecisionStatus.EFFECTIVE)
            .order_by(Decision.ts.desc())
        ))
        matches = [
            decision for decision in rows
            if not words or any(word in decision.description.lower() for word in words)
        ]
        citations = []
        lines = []
        for decision in matches[:5]:
            message_ids = list(self.session.scalars(
                select(DecisionCitation.message_id).where(
                    DecisionCitation.decision_id == decision.id
                )
            ))
            if not message_ids:
                continue
            lines.append(decision.description)
            citations.append({"decision_id": decision.id, "message_ids": message_ids})
        if not lines:
            return {"answer": "No grounded answer found in current effective decisions.", "citations": []}
        return {"answer": "\n".join(lines), "citations": citations}

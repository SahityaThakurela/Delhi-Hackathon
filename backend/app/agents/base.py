"""Base class and common contracts for Kyro specialist agents (P2 ownership).

Per BE-6: Every agent calls deterministic checks first, searches RAG evidence,
extracts findings using structured outputs, and adheres to strict evidence rules.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
from uuid import UUID

from backend.app.schemas.ai_schemas import AgentName, Dimension


class BaseAgent(ABC):
    """Abstract base class for all Kyro specialist investigation agents."""

    name: AgentName
    dimension: Dimension

    def __init__(self, investigation_id: UUID, hospital_id: UUID):
        self.investigation_id = investigation_id
        self.hospital_id = hospital_id

    @abstractmethod
    async def run(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute agent investigation step and return structured findings."""
        raise NotImplementedError

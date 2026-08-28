from __future__ import annotations

from pydantic import BaseModel, Field


class ServiceProposal(BaseModel):
    name: str
    components: list[str] = Field(default_factory=list)
    owned_entities: list[str] = Field(default_factory=list)
    responsibilities: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    rationale: str = ""


class MigrationRank(BaseModel):
    service: str
    rank: int
    confidence: float = 0.0
    reason: str = ""


class DecompositionProposal(BaseModel):
    services: list[ServiceProposal]
    migration_priority: list[MigrationRank] = Field(default_factory=list)
    uncertain_decisions: list[str] = Field(default_factory=list)
    unsupported_assumptions: list[str] = Field(default_factory=list)
    rule_violations: list[str] = Field(default_factory=list)
    architectural_risks: list[str] = Field(default_factory=list)
    critique: str = ""
    revised: bool = False

    model_config = {"extra": "ignore"}

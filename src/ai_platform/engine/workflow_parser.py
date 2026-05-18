from __future__ import annotations

from pathlib import Path
from typing import Any, Union

import yaml
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class LLMConfig(BaseModel):
    provider: str
    model: str
    temperature: float = 0.1


class GlobalEdgeConfig(BaseModel):
    trigger: str
    intent: str
    to: str


class GuardrailsConfig(BaseModel):
    mandatory: list[str] = Field(default_factory=list)
    optional: list[str] = Field(default_factory=list)


class NodeConfig(BaseModel):
    id: str
    type: str
    handler: str | None = None
    prompt_template: str | None = None
    output_schema: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    subgraph: str | None = None


class RouteTarget(BaseModel):
    to: str
    label: str | None = None


class EdgeConfig(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_node: str = Field(alias="from")
    to: str | None = None
    router: str | None = None
    description: str | None = None
    routes: dict[str, Union[str, RouteTarget]] | None = None

    @model_validator(mode="before")
    @classmethod
    def _rename_from(cls, data: Any) -> Any:
        if isinstance(data, dict) and "from" in data and "from_node" not in data:
            data = dict(data)
            data["from_node"] = data.pop("from")
        return data

    @field_validator("routes", mode="before")
    @classmethod
    def _parse_routes(cls, v: Any) -> Any:
        if v is None:
            return v
        parsed: dict[str, Union[str, RouteTarget]] = {}
        for key, val in v.items():
            if isinstance(val, str):
                parsed[key] = val
            elif isinstance(val, dict):
                parsed[key] = RouteTarget.model_validate(val)
            else:
                parsed[key] = str(val)
        return parsed


class SubgraphConfig(BaseModel):
    description: str | None = None
    nodes: list[NodeConfig]
    edges: list[EdgeConfig]


class WorkflowConfig(BaseModel):
    name: str
    description: str | None = None
    llm: LLMConfig
    global_edges: list[GlobalEdgeConfig] = Field(default_factory=list)
    guardrails: GuardrailsConfig = Field(default_factory=GuardrailsConfig)
    nodes: list[NodeConfig]
    edges: list[EdgeConfig]


class ParsedWorkflow(BaseModel):
    workflow: WorkflowConfig
    subgraphs: dict[str, SubgraphConfig] = Field(default_factory=dict)
    schemas: dict[str, dict] = Field(default_factory=dict)


def parse_workflow_file(path: str | Path) -> ParsedWorkflow:
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return ParsedWorkflow.model_validate(data)

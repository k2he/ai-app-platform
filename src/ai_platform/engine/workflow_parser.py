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


def _merge_workflow_data(base: dict, feature: dict) -> dict:
    base_wf: dict = base.get("workflow", {})
    feat_wf: dict = feature.get("workflow", {})
    merged_wf: dict = {}

    # Scalars: feature wins
    for key in ("name", "description"):
        if key in feat_wf:
            merged_wf[key] = feat_wf[key]
        elif key in base_wf:
            merged_wf[key] = base_wf[key]

    # LLM: field-level override
    merged_wf["llm"] = {**base_wf.get("llm", {}), **feat_wf.get("llm", {})}

    # Global edges: concatenate (base first)
    merged_wf["global_edges"] = (
        base_wf.get("global_edges", []) + feat_wf.get("global_edges", [])
    )

    # Guardrails: mandatory concatenated (features add, never remove); optional concatenated
    base_gr = base_wf.get("guardrails", {})
    feat_gr = feat_wf.get("guardrails", {})
    merged_wf["guardrails"] = {
        "mandatory": list(
            dict.fromkeys(base_gr.get("mandatory", []) + feat_gr.get("mandatory", []))
        ),
        "optional": list(
            dict.fromkeys(base_gr.get("optional", []) + feat_gr.get("optional", []))
        ),
    }

    # Nodes: merge by id — feature overrides individual fields; config dicts deep-merged
    base_nodes: dict = {n["id"]: dict(n) for n in base_wf.get("nodes", [])}
    for node in feat_wf.get("nodes", []):
        nid = node["id"]
        if nid in base_nodes:
            merged_node = {**base_nodes[nid], **node}
            if "config" in base_nodes[nid] and "config" in node:
                merged_node["config"] = {**base_nodes[nid]["config"], **node["config"]}
            base_nodes[nid] = merged_node
        else:
            base_nodes[nid] = dict(node)
    merged_wf["nodes"] = list(base_nodes.values())

    # Edges: base first, then feature appended
    merged_wf["edges"] = base_wf.get("edges", []) + feat_wf.get("edges", [])

    result: dict = {"workflow": merged_wf}

    # Subgraphs and schemas: feature keys override base keys
    result["subgraphs"] = {**base.get("subgraphs", {}), **feature.get("subgraphs", {})}
    result["schemas"] = {**base.get("schemas", {}), **feature.get("schemas", {})}

    return result


def parse_workflow_file(path: str | Path) -> ParsedWorkflow:
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if "extends" in data:
        base_path = (path.parent / data["extends"]).resolve()
        with base_path.open(encoding="utf-8") as f:
            base_data = yaml.safe_load(f)
        data = _merge_workflow_data(base_data, data)

    return ParsedWorkflow.model_validate(data)

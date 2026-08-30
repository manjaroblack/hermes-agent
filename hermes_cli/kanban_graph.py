"""Pure validation for complex Kanban task graphs.

The board stores a graph as task rows plus durable parent/child links.  This
module deliberately has no SQLite or model dependencies: callers hand it a
root task, the graph nodes, and the directed edges, and receive a deterministic
repair packet.  Persistence and promotion policy stay in ``kanban_db``.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from typing import Any, Iterable, Mapping, cast

from hermes_cli.config_defaults import DEFAULT_CONFIG


_STAGE_ALIASES = {
    "inventory_design": {
        "inventory_design",
        "inventory",
        "design",
        "discovery",
        "architecture",
    },
    "release_acceptance": {
        "release_acceptance",
        "release",
        "release_gate",
        "human_merge_gate",
        "merge_deploy_gate",
        "merge_deploy",
    },
    "security_audit": {
        "security_audit",
        "security",
        "security_review",
        "safety_audit",
    },
    "incident_response": {
        "incident_response",
        "incident",
        "incident_management",
        "rollback",
        "recovery",
    },
    "independent_review": {
        "independent_review",
        "review",
        "code_review",
        "peer_review",
    },
    "implementation": {
        "implementation",
        "code",
        "coding",
        "engineering",
    },
}

_READ_ONLY_ASSIGNEES = {
    "hermes-review",
    "hermes-security-audit",
    "hermes-incident",
    "hermes-orchestrator",
}

_ASSIGNEE_ALIASES = {
    "hermes_coding": "hermes-coding",
    "hermes_review": "hermes-review",
    "hermes_security_audit": "hermes-security-audit",
    "hermes_incident": "hermes-incident",
    "hermes_orchestrator": "hermes-orchestrator",
}


def _default_graph_config() -> dict[str, Any]:
    raw_kanban = DEFAULT_CONFIG.get("kanban", {})
    if isinstance(raw_kanban, Mapping):
        raw = cast(Mapping[str, Any], raw_kanban).get("graph_validation", {})
    else:
        raw = {}
    return dict(cast(Mapping[str, Any], raw)) if isinstance(raw, Mapping) else {}


def _merge_config(config: Mapping[str, Any] | None) -> dict[str, Any]:
    defaults = _default_graph_config()
    if config is None:
        return defaults
    if "kanban" in config:
        kanban = config.get("kanban")
        raw = kanban.get("graph_validation", {}) if isinstance(kanban, Mapping) else {}
    elif "graph_validation" in config:
        raw = config.get("graph_validation", {})
    else:
        raw = config
    if isinstance(raw, Mapping):
        defaults.update(raw)
    return defaults


def _normalise_token(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().casefold()).strip("_")


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().casefold() not in {"", "0", "false", "no", "off"}
    return bool(value)


def _node_value(node: Any, key: str, default: Any = None) -> Any:
    if isinstance(node, Mapping):
        return node.get(key, default)
    return getattr(node, key, default)


def _metadata(node: Any) -> dict[str, Any]:
    raw = _node_value(node, "metadata", {})
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except (TypeError, ValueError):
            raw = {}
    if not isinstance(raw, Mapping):
        raw = {}
    return dict(raw)


def _node_id(node: Any) -> str:
    return str(_node_value(node, "id", "")).strip()


def _node_text(node: Any) -> str:
    return " ".join(
        str(_node_value(node, key, "") or "")
        for key in ("title", "body")
    ).casefold()


def _role(node: Any) -> str:
    metadata = _metadata(node)
    for key in ("role", "stage", "workflow_stage", "kind"):
        value = metadata.get(key)
        if value:
            return _normalise_token(value)
    for key in ("role", "stage", "workflow_stage"):
        value = _node_value(node, key)
        if value:
            return _normalise_token(value)
    return ""


def _canonical_stage(value: Any) -> str:
    token = _normalise_token(value)
    for canonical, aliases in _STAGE_ALIASES.items():
        if token in aliases:
            return canonical
    return token


def _canonical_assignee(value: Any) -> str:
    token = _normalise_token(value)
    return _ASSIGNEE_ALIASES.get(token, token)


def _assignee(node: Any) -> str:
    return _canonical_assignee(_node_value(node, "assignee", ""))


def _is_code_bearing(node: Any) -> bool:
    metadata = _metadata(node)
    if "code_bearing" in metadata:
        return _as_bool(metadata["code_bearing"])
    if "implementation" in metadata:
        return _as_bool(metadata["implementation"])
    role = _role(node)
    if role in _STAGE_ALIASES["implementation"]:
        return True
    assignee = _assignee(node)
    if assignee in _READ_ONLY_ASSIGNEES:
        return False
    return assignee in {"hermes-coding", "coding", "developer", "engineer"}


def _is_inventory(node: Any) -> bool:
    role = _role(node)
    return role in _STAGE_ALIASES["inventory_design"] and not _is_code_bearing(node)


def _is_release(node: Any) -> bool:
    metadata = _metadata(node)
    role = _role(node)
    if role in _STAGE_ALIASES["release_acceptance"]:
        return _as_bool(metadata.get("human_gate", True)) and not _is_code_bearing(node)
    return False


def _is_security(node: Any) -> bool:
    return _role(node) in _STAGE_ALIASES["security_audit"]


def _is_incident(node: Any) -> bool:
    return _role(node) in _STAGE_ALIASES["incident_response"]


def _is_review(node: Any) -> bool:
    metadata = _metadata(node)
    role = _role(node)
    if role in _STAGE_ALIASES["independent_review"]:
        return not _is_code_bearing(node)
    return (
        _assignee(node) == "hermes-review"
        and not _is_code_bearing(node)
        and bool(
            metadata.get("review_model")
            or metadata.get("reviewer")
        )
    )


def _is_security_required(root: Any, nodes: Iterable[Any], config: Mapping[str, Any]) -> bool:
    root_metadata = _metadata(root)
    if any(
        _as_bool(root_metadata.get(key))
        for key in ("security_required", "touches_security", "security_boundary", "requires_security_audit")
    ):
        return True
    triggers = config.get("security_triggers", ())
    if isinstance(triggers, str):
        triggers = (triggers,)
    root_text = _node_text(root)
    if any(
        re.search(rf"(?<!\w){re.escape(str(term).casefold())}(?!\w)", root_text)
        for term in triggers
        if str(term).strip()
    ):
        return True
    return any(
        _as_bool(_metadata(node).get("touches_security"))
        or _as_bool(_metadata(node).get("security_boundary"))
        for node in nodes
    )


def _is_incident_required(root: Any, nodes: Iterable[Any], config: Mapping[str, Any]) -> bool:
    del root, config
    explicit_keys = (
        "incident_required",
        "requires_incident_lane",
        "incident_boundary",
        "requires_incident_response",
        "incident_response_required",
    )
    return any(
        any(_as_bool(metadata.get(key)) for key in explicit_keys)
        for metadata in (_metadata(node) for node in nodes)
    )


def _is_complex(root: Any, nodes: list[Any], config: Mapping[str, Any], explicit: bool | None) -> bool:
    if explicit is not None:
        return explicit
    metadata = _metadata(root)
    explicit_complexity: list[bool] = []
    intake = metadata.get("intake")
    if isinstance(intake, Mapping) and "requires_orchestrator" in intake:
        explicit_complexity.append(_as_bool(intake["requires_orchestrator"]))
    for key in ("requires_orchestrator", "complex", "complex_task", "orchestrated"):
        if key in metadata:
            explicit_complexity.append(_as_bool(metadata[key]))
    if any(explicit_complexity):
        return True
    if explicit_complexity:
        return False
    complexity = _normalise_token(metadata.get("complexity"))
    if complexity:
        return complexity in {"complex", "orchestrated", "orchestration", "triage"}
    implementation_count = sum(1 for node in nodes if _is_code_bearing(node) and _node_id(node) != _node_id(root))
    subsystem_values: set[str] = set()
    for node in [root, *nodes]:
        node_metadata = _metadata(node)
        raw_subsystems = node_metadata.get("subsystems", node_metadata.get("subsystem"))
        if isinstance(raw_subsystems, (list, tuple, set, frozenset)):
            subsystem_values.update(str(value) for value in raw_subsystems if value)
        elif raw_subsystems:
            subsystem_values.add(str(raw_subsystems))
    return implementation_count > 1 or len(subsystem_values) > 1


def _edge_pair(edge: Any) -> tuple[str, str] | None:
    if isinstance(edge, Mapping):
        parent = edge.get("parent_id", edge.get("parent"))
        child = edge.get("child_id", edge.get("child"))
    elif isinstance(edge, (tuple, list)) and len(edge) >= 2:
        parent, child = edge[0], edge[1]
    else:
        return None
    if parent is None or child is None:
        return None
    return str(parent), str(child)


def _connected_node_ids(root_id: str, edges: Iterable[tuple[str, str]]) -> set[str]:
    """Return nodes in the undirected component containing ``root_id``.

    Decomposition historically linked fan-out children *to* their root while
    ordinary task creation links a parent *to* its child.  Graph validation is
    about the durable component, so either edge orientation must establish
    reachability without requiring every stage to be a direct root child.
    """
    if not root_id:
        return set()
    adjacency: dict[str, set[str]] = {root_id: set()}
    for parent, child in edges:
        adjacency.setdefault(parent, set()).add(child)
        adjacency.setdefault(child, set()).add(parent)
    connected: set[str] = set()
    pending = [root_id]
    while pending:
        node_id = pending.pop()
        if node_id in connected:
            continue
        connected.add(node_id)
        pending.extend(adjacency.get(node_id, ()))
    return connected


def _repair(code: str, message: str, **fields: Any) -> dict[str, Any]:
    payload = {
        "code": code,
        "message": message,
        "action": "repair_complex_graph",
        "owner": "hermes-orchestrator",
    }
    payload.update(fields)
    return payload


@dataclass(frozen=True)
class GraphValidationResult:
    """Deterministic validation outcome suitable for an audit event."""

    valid: bool
    skipped: bool = False
    missing_stages: tuple[str, ...] = ()
    invalid_reasons: tuple[str, ...] = ()
    repairable: tuple[dict[str, Any], ...] = ()
    implementation_ids: tuple[str, ...] = ()
    review_bindings: dict[str, tuple[str, ...]] = field(default_factory=dict)

    @property
    def missing(self) -> tuple[str, ...]:
        return self.missing_stages

    @property
    def reasons(self) -> tuple[str, ...]:
        return self.invalid_reasons

    @property
    def repairs(self) -> tuple[dict[str, Any], ...]:
        return self.repairable

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "skipped": self.skipped,
            "missing_stages": list(self.missing_stages),
            "invalid_reasons": list(self.invalid_reasons),
            "repairable": [dict(item) for item in self.repairable],
            "implementation_ids": list(self.implementation_ids),
            "review_bindings": {
                key: list(value) for key, value in self.review_bindings.items()
            },
        }


def validate_complex_graph(
    root: Any,
    nodes: Iterable[Any],
    edges: Iterable[Any],
    *,
    config: Mapping[str, Any] | None = None,
    complex: bool | None = None,
) -> GraphValidationResult:
    """Validate the durable workflow contract for a complex root.

    ``edges`` use the board's ``(parent_id, child_id)`` direction.  Review
    edges therefore point from an implementation node to its downstream review
    node.  Same-card review is accepted only when the implementation metadata
    explicitly contains both ``reviewer`` and ``review_model: same_card``.
    """
    resolved = _merge_config(config)
    node_list = list(nodes)
    root_id = _node_id(root)
    if root_id and all(_node_id(node) != root_id for node in node_list):
        node_list.insert(0, root)
    node_map = {_node_id(node): node for node in node_list if _node_id(node)}
    if not _is_complex(root, node_list, resolved, complex):
        return GraphValidationResult(valid=True, skipped=True)
    if not _as_bool(resolved.get("enabled", True)):
        return GraphValidationResult(valid=True, skipped=True)

    reasons: list[str] = []
    missing: list[str] = []
    repairs: list[dict[str, Any]] = []
    parsed_edges: list[tuple[str, str]] = []
    for raw_edge in edges:
        pair = _edge_pair(raw_edge)
        if pair is None:
            reasons.append("invalid graph edge encoding")
            repairs.append(_repair("invalid_edge", "Each graph edge needs parent_id and child_id."))
            continue
        parent, child = pair
        parsed_edges.append(pair)
        if parent not in node_map or child not in node_map:
            reasons.append(f"graph edge references unknown node: {parent}->{child}")
            repairs.append(_repair("unknown_edge_node", "Repair the edge to reference existing task ids.", edge=[parent, child]))

    direct_children = {
        parent: {child for edge_parent, child in parsed_edges if edge_parent == parent}
        for parent in node_map
    }
    connected_node_ids = _connected_node_ids(root_id, parsed_edges)

    configured_stages = resolved.get("required_stages", ("inventory_design", "release_acceptance"))
    if isinstance(configured_stages, Mapping):
        required_stages = [
            _canonical_stage(stage)
            for stage, enabled in configured_stages.items()
            if _as_bool(enabled)
        ]
    elif isinstance(configured_stages, str):
        required_stages = [_canonical_stage(configured_stages)]
    else:
        required_stages = [_canonical_stage(stage) for stage in configured_stages]
    if _is_security_required(root, node_list, resolved) and _as_bool(resolved.get("security_audit_on_trigger", True)):
        if "security_audit" not in required_stages:
            required_stages.append("security_audit")
    if _is_incident_required(root, node_list, resolved) and _as_bool(
        resolved.get("incident_response_on_trigger", True)
    ):
        if "incident_response" not in required_stages:
            required_stages.append("incident_response")

    stage_predicates = {
        "inventory_design": _is_inventory,
        "release_acceptance": _is_release,
        "security_audit": _is_security,
        "incident_response": _is_incident,
    }
    for stage in required_stages:
        predicate = stage_predicates.get(stage)
        candidates = [node for node in node_list if predicate and predicate(node)]
        if not candidates:
            missing.append(stage)
            message = f"missing required stage: {stage}"
            reasons.append(message)
            repairs.append(_repair("missing_stage", message, stage=stage))
            continue
        if len(candidates) > 1:
            message = f"required stage must have exactly one node: {stage}"
            reasons.append(message)
            repairs.append(
                _repair(
                    "duplicate_required_stage",
                    message,
                    stage=stage,
                    node_ids=[_node_id(node) for node in candidates],
                )
            )
        if not any(_node_id(node) in connected_node_ids for node in candidates):
            message = f"missing required stage edge: {stage}"
            reasons.append(message)
            repairs.append(_repair("missing_stage_edge", message, stage=stage, parent=root_id))

    implementation_nodes = [
        node for node in node_list
        if _node_id(node) != root_id and _is_code_bearing(node)
    ]
    implementation_ids = tuple(_node_id(node) for node in implementation_nodes)
    if not implementation_nodes:
        message = "missing bounded implementation node"
        reasons.append(message)
        repairs.append(_repair("missing_implementation", message))
    try:
        max_implementations = max(
            1,
            int(
                resolved.get(
                    "max_implementation_nodes",
                    resolved.get("max_implementation_children", 8),
                )
            ),
        )
    except (TypeError, ValueError):
        max_implementations = 8
    if len(implementation_nodes) > max_implementations:
        message = (
            f"implementation nodes exceed bounded limit: "
            f"{len(implementation_nodes)} > {max_implementations}"
        )
        reasons.append(message)
        repairs.append(_repair("implementation_bound_exceeded", message, limit=max_implementations))
    for node in implementation_nodes:
        node_id = _node_id(node)
        if node_id not in connected_node_ids:
            message = f"missing implementation edge: {node_id} must be reachable from graph root"
            reasons.append(message)
            repairs.append(_repair("missing_implementation_edge", message, node_id=node_id, parent=root_id))

        metadata = _metadata(node)
        reviewer = str(metadata.get("reviewer") or "").strip()
        review_model = str(
            metadata.get("review_model")
            or metadata.get("reviewer_model")
            or ""
        ).strip()
        same_card = bool(reviewer and review_model.casefold() == "same_card")
        malformed_same_card = bool(reviewer) != bool(review_model) or (
            review_model.casefold() == "same_card" and not reviewer
        )
        downstream = [
            child_id
            for child_id in direct_children.get(node_id, set())
            if child_id in node_map and _is_review(node_map[child_id])
        ]
        binding_ids = list(downstream)
        if same_card:
            if _canonical_assignee(reviewer) == _assignee(node):
                reasons.append(f"reviewer for {node_id} is not independent")
                repairs.append(_repair("review_not_independent", "Use a distinct reviewer profile.", node_id=node_id))
            if downstream:
                binding_ids.extend(downstream)
        elif malformed_same_card:
            if reviewer or review_model:
                reasons.append(f"review contract for {node_id} must encode reviewer and review_model: same_card")
                repairs.append(_repair("malformed_same_card_review", "Use reviewer + review_model=same_card, or a downstream review child.", node_id=node_id))
        if not same_card:
            for review_id in downstream:
                review_node = node_map[review_id]
                review_metadata = _metadata(review_node)
                model = str(
                    review_metadata.get("review_model")
                    or review_metadata.get("reviewer_model")
                    or _node_value(review_node, "model_override", "")
                ).strip()
                if not model or model.casefold() == "same_card":
                    reasons.append(f"review child {review_id} has no independent review model")
                    repairs.append(_repair("review_model_missing", "Declare the independent review model.", node_id=node_id, review_id=review_id))
                if _assignee(review_node) == _assignee(node):
                    reasons.append(f"reviewer for {node_id} is not independent")
                    repairs.append(_repair("review_not_independent", "Use a distinct reviewer profile.", node_id=node_id, review_id=review_id))
        binding_count = len(downstream) + (1 if same_card else 0)
        if binding_count != 1:
            message = f"code node {node_id} must have exactly one independent review model (found {binding_count})"
            reasons.append(message)
            repairs.append(_repair("review_contract", message, node_id=node_id))

    # A malformed cycle cannot be made dispatchable by repeatedly retrying the
    # decomposer.  The graph is tiny by design, so a bounded DFS is sufficient.
    adjacency = {node_id: set() for node_id in node_map}
    for parent, child in parsed_edges:
        if parent in adjacency and child in adjacency:
            adjacency[parent].add(child)
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node_id: str) -> bool:
        if node_id in visiting:
            return True
        if node_id in visited:
            return False
        visiting.add(node_id)
        if any(visit(child_id) for child_id in adjacency[node_id]):
            return True
        visiting.remove(node_id)
        visited.add(node_id)
        return False

    if any(visit(node_id) for node_id in adjacency):
        message = "graph contains a dependency cycle"
        reasons.append(message)
        repairs.append(_repair("graph_cycle", message))

    return GraphValidationResult(
        valid=not reasons,
        missing_stages=tuple(dict.fromkeys(missing)),
        invalid_reasons=tuple(dict.fromkeys(reasons)),
        repairable=tuple(repairs),
        implementation_ids=implementation_ids,
        review_bindings={
            node_id: tuple(
                child_id
                for parent_id, child_id in parsed_edges
                if parent_id == node_id and child_id in node_map and _is_review(node_map[child_id])
            )
            for node_id in implementation_ids
        },
    )


__all__ = ["GraphValidationResult", "validate_complex_graph"]

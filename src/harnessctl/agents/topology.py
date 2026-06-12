from typing import List, Optional
from harnessctl.spec.models import Spec, AgentRole


class TopologyError(Exception):
    """Raised when agent topology validation fails."""

    pass


def validate_topology(spec: Spec) -> None:
    """
    Validate the agent topology based on LLD-00006.
    - Exactly one hub exists.
    - can_delegate and escalates_to refer to existing agents.
    - In-process depth (hub -> worker) is max 1 level unless delegate_via is "cli".
    - No cycles in the delegation graph.
    """
    if not spec.agents:
        return

    # 1. Exactly one hub
    hubs = [name for name, agent in spec.agents.items() if agent.role == AgentRole.HUB]
    if len(hubs) == 0:
        raise TopologyError("Exactly one hub agent must be defined, found 0.")
    if len(hubs) > 1:
        raise TopologyError(
            f"Exactly one hub agent must be defined, found {len(hubs)}: {', '.join(hubs)}."
        )

    # 2. Check existence of references and validate nesting depth
    for name, agent in spec.agents.items():
        # Validate tier exists
        if agent.tier not in spec.tiers:
            raise TopologyError(
                f"Agent '{name}' references unknown tier '{agent.tier}'."
            )

        # Validate can_delegate references
        for target in agent.can_delegate:
            if target not in spec.agents:
                raise TopologyError(
                    f"Agent '{name}' tries to delegate to undefined agent '{target}'."
                )

            # Check nesting depth
            # Only HUB is allowed to delegate in-process (non-CLI)
            if agent.role != AgentRole.HUB and agent.delegate_via != "cli":
                raise TopologyError(
                    f"Agent '{name}' (worker) cannot delegate to '{target}' "
                    "using 'harness' (in-process) delegation. Only HUB can delegate, "
                    "or worker must use 'delegate_via: cli'."
                )

        # Validate escalates_to references
        if agent.escalates_to:
            if agent.escalates_to not in spec.agents:
                raise TopologyError(
                    f"Agent '{name}' escalates to undefined agent '{agent.escalates_to}'."
                )

            if agent.escalates_to == name:
                raise TopologyError(f"Agent '{name}' cannot escalate to itself.")

    # 3. Cycle detection in delegation graph
    # We treat can_delegate as edges in a directed graph.
    def find_cycle(
        current: str, path: List[str], visited: List[str]
    ) -> Optional[List[str]]:
        if current in path:
            return path[path.index(current) :] + [current]
        if current in visited:
            return None

        path.append(current)
        agent = spec.agents[current]
        for target in agent.can_delegate:
            cycle = find_cycle(target, path, visited)
            if cycle:
                return cycle

        path.pop()
        visited.append(current)
        return None

    visited_agents = []
    for agent_name in spec.agents:
        cycle = find_cycle(agent_name, [], visited_agents)
        if cycle:
            raise TopologyError(f"Delegation cycle detected: {' -> '.join(cycle)}")

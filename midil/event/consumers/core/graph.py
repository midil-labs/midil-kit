from __future__ import annotations

from typing import Dict, List, TYPE_CHECKING

from midil.event.consumers.core.exceptions import (
    CycleDetectedError,
    DependencyRegistrationError,
)
from midil.event.consumers.core.types import HandlerName

if TYPE_CHECKING:
    from midil.event.consumers.core.router import HandlerSpec


class GraphValidator:
    """Validates handler dependency graphs for correctness"""

    @staticmethod
    def validate(specs: Dict[HandlerName, "HandlerSpec"]) -> None:
        GraphValidator._validate_dependencies_exist(specs)
        GraphValidator._validate_no_cycles(specs)

    @staticmethod
    def _validate_dependencies_exist(specs: Dict[HandlerName, "HandlerSpec"]) -> None:
        handler_names = set(specs.keys())
        for name, spec in specs.items():
            for dep in spec.depends_on:
                if dep not in handler_names:
                    raise DependencyRegistrationError(
                        f"Handler '{name}' depends on unknown handler '{dep}'"
                    )

    @staticmethod
    def _validate_no_cycles(specs: Dict[HandlerName, "HandlerSpec"]) -> None:
        WHITE, GRAY, BLACK = 0, 1, 2
        colors = {name: WHITE for name in specs}

        def dfs(node: HandlerName, path: List[HandlerName]) -> None:
            if colors[node] == GRAY:
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                raise CycleDetectedError(
                    f"Circular dependency detected: {' -> '.join(cycle)}"
                )
            if colors[node] == BLACK:
                return

            colors[node] = GRAY
            path.append(node)
            for dep in specs[node].depends_on:
                dfs(dep, path)
            path.pop()
            colors[node] = BLACK

        for name in specs:
            if colors[name] == WHITE:
                dfs(name, [])


__all__ = ["GraphValidator"]

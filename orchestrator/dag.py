"""
DAG Orchestrator — Directed Acyclic Graph with File Message Bus.

Architecture from hackathon Day 3 (Agent Skills, Section 7):
  - Decoupled state: routing does NOT rely on LLM context accumulation
  - File message bus: pass structured file paths between nodes, NOT raw text
  - Protected attention: payloads stay on disk, only URIs travel through the DAG

Each DAG node wraps an agent. Edges define data dependencies via file paths.
"""

import json
import time
from pathlib import Path
from typing import Any, Optional
from rich.console import Console
from rich.table import Table


class DAGNode:
    """A single step in the pipeline DAG."""

    def __init__(self, node_id: str, agent, description: str = "",
                 tier: str = "read", depends_on: list = None):
        self.node_id = node_id
        self.agent = agent
        self.description = description
        self.tier = tier  # read | draft | act (authority levels from Day 3)
        self.depends_on = depends_on or []
        self.status = "pending"
        self.output_paths = {}  # file paths produced by this node
        self.error = None
        self.duration_s = 0

    def __repr__(self):
        return f"DAGNode({self.node_id}, {self.status})"


class DAGOrchestrator:
    """Executes a DAG of agent nodes with file message bus handoffs."""

    def __init__(self, project_dir: Path, console: Console = None):
        self.project_dir = project_dir
        self.console = console or Console()
        self.nodes = {}
        self.execution_order = []

    def add_node(self, node: DAGNode):
        """Register a node in the DAG."""
        self.nodes[node.node_id] = node

    def validate(self) -> bool:
        """Check DAG for cycles and missing dependencies."""
        visited = set()
        in_stack = set()

        def dfs(node_id):
            if node_id in in_stack:
                return False  # cycle detected
            if node_id in visited:
                return True
            visited.add(node_id)
            in_stack.add(node_id)
            for dep in self.nodes[node_id].depends_on:
                if dep not in self.nodes:
                    self.console.print(f"  [red]Missing dependency: {dep} for {node_id}[/red]")
                    return False
                if not dfs(dep):
                    return False
            in_stack.remove(node_id)
            return True

        for node_id in self.nodes:
            if not dfs(node_id):
                return False
        return True

    def topological_sort(self) -> list:
        """Return nodes in valid execution order (dependencies first)."""
        visited = set()
        order = []

        def visit(node_id):
            if node_id in visited:
                return
            visited.add(node_id)
            for dep in self.nodes[node_id].depends_on:
                visit(dep)
            order.append(node_id)

        for node_id in self.nodes:
            visit(node_id)
        return order

    def run(self, initial_data: dict = None) -> dict:
        """Execute the DAG, passing file paths between nodes via the message bus."""
        if not self.validate():
            self.console.print("[red]DAG validation failed — aborting[/red]")
            return {"success": False, "error": "DAG validation failed"}

        execution_order = self.topological_sort()
        self.console.print(f"\n[bold]DAG Execution Plan ({len(execution_order)} nodes):[/bold]")
        for i, nid in enumerate(execution_order):
            node = self.nodes[nid]
            tier_color = {"read": "green", "draft": "yellow", "act": "red"}.get(node.tier, "white")
            self.console.print(f"  {i+1}. [{tier_color}]{node.node_id}[/{tier_color}] "
                             f"({node.tier}) — {node.description}")

        # File message bus: each node's output paths are available to downstream nodes
        message_bus = initial_data or {}

        total_start = time.time()
        results = {}

        for node_id in execution_order:
            node = self.nodes[node_id]
            node.status = "running"

            # Collect inputs from dependencies (file paths from upstream nodes)
            node_input = dict(message_bus)
            for dep_id in node.depends_on:
                dep_node = self.nodes[dep_id]
                if dep_node.output_paths:
                    node_input.update(dep_node.output_paths)

            # Build AgentInput
            from agents.base import AgentInput
            agent_input = AgentInput(
                prompt=node.description,
                project_dir=self.project_dir,
                data=node_input,
            )

            self.console.print(f"\n  [bold cyan]▶ {node_id}[/bold cyan] ({node.tier})")
            start = time.time()

            try:
                result = node.agent.run(agent_input)
                node.duration_s = time.time() - start

                if result.success:
                    node.status = "success"
                    # Extract file paths from result for the message bus
                    if result.data and isinstance(result.data, dict):
                        node.output_paths = {k: v for k, v in result.data.items()
                                           if isinstance(v, (str, Path, list, dict))}
                    if result.artifact_path:
                        node.output_paths["artifact_path"] = str(result.artifact_path)

                    self.console.print(f"  [green]✓[/green] {node_id} done "
                                     f"({node.duration_s:.1f}s) — {result.message}")
                else:
                    node.status = "failed"
                    node.error = result.message
                    self.console.print(f"  [red]✗[/red] {node_id} failed: {result.message}")

                results[node_id] = {
                    "success": result.success,
                    "data": result.data,
                    "message": result.message,
                    "duration": node.duration_s,
                }

            except Exception as e:
                node.status = "failed"
                node.error = str(e)
                node.duration_s = time.time() - start
                self.console.print(f"  [red]✗[/red] {node_id} exception: {e}")
                results[node_id] = {"success": False, "error": str(e)}

        # Summary
        total_time = time.time() - total_start
        succeeded = sum(1 for n in self.nodes.values() if n.status == "success")
        failed = sum(1 for n in self.nodes.values() if n.status == "failed")

        table = Table(title=f"DAG Results ({total_time:.1f}s)")
        table.add_column("Node", style="cyan")
        table.add_column("Tier")
        table.add_column("Status")
        table.add_column("Time", justify="right")
        table.add_column("Message")

        for nid in execution_order:
            n = self.nodes[nid]
            status_style = "green" if n.status == "success" else "red"
            table.add_row(nid, n.tier, f"[{status_style}]{n.status}[/{status_style}]",
                         f"{n.duration_s:.1f}s", n.error or "OK")

        self.console.print(table)

        # Save execution record
        record_path = self.project_dir / "dag_execution.json"
        record = {
            "total_time": total_time,
            "succeeded": succeeded,
            "failed": failed,
            "nodes": {nid: {"status": n.status, "duration": n.duration_s,
                           "outputs": n.output_paths, "error": n.error}
                     for nid, n in self.nodes.items()},
        }
        with open(record_path, "w", encoding="utf-8") as f:
            json.dump(record, f, indent=2, default=str)

        return {
            "success": failed == 0,
            "results": results,
            "total_time": total_time,
            "record_path": str(record_path),
        }

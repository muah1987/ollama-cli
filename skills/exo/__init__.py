"""EXO (Execution Optimizer) integration for distributed execution acceleration.

This module provides execution optimization and distributed computing capabilities
for Qarin CLI operations across multiple nodes.
"""

from __future__ import annotations

import logging
import os
import socket
import subprocess
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EXONode:
    """An EXO cluster node."""

    hostname: str
    ip: str
    cpu_count: int
    memory_gb: float
    gpu_count: int
    is_leader: bool = False


class EXOExecutor:
    """EXO execution optimizer and distributed executor."""

    def __init__(self, leader_host: str | None = None):
        self.leader_host = leader_host or "localhost"
        self._nodes: list[EXONode] = []
        self._initialized = False

    async def initialize(self) -> bool:
        """Initialize EXO cluster."""
        self._nodes = await self._discover_nodes()
        self._initialized = True
        logger.info("EXO initialized with %d nodes", len(self._nodes))
        return True

    async def _discover_nodes(self) -> list[EXONode]:
        """Discover available EXO nodes."""
        nodes = []

        # Get local node info
        local_node = await self._get_local_node()
        nodes.append(local_node)

        # Discover other nodes
        cluster_nodes = await self._discover_cluster_nodes()
        nodes.extend(cluster_nodes)

        # Mark leader
        if nodes:
            nodes[0].is_leader = True

        return nodes

    async def _get_local_node(self) -> EXONode:
        """Get local node information."""
        hostname = socket.gethostname()
        try:
            ip = socket.gethostbyname(hostname)
        except socket.gaierror:
            ip = "127.0.0.1"

        cpu_count = os.cpu_count() or 1
        memory_gb = self._get_memory_gb()
        gpu_count = self._detect_gpus()

        return EXONode(
            hostname=hostname,
            ip=ip,
            cpu_count=cpu_count,
            memory_gb=memory_gb,
            gpu_count=gpu_count,
        )

    def _get_memory_gb(self) -> float:
        """Get memory in GB."""
        try:
            if os.uname().system == "Linux":
                with open("/proc/meminfo") as f:
                    for line in f:
                        if line.startswith("MemTotal:"):
                            mem_kb = int(line.split()[1])
                            return mem_kb / 1024 / 1024
        except Exception:
            pass
        return 0.0

    def _detect_gpus(self) -> int:
        """Detect number of GPUs."""
        count = 0
        try:
            result = subprocess.run(
                ["nvidia-smi", "--list-gpus"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                count = len(result.stdout.strip().split("\n"))
        except Exception:
            pass
        return count

    async def _discover_cluster_nodes(self) -> list[EXONode]:
        """Discover nodes in the cluster."""
        nodes = []
        # TODO: Implement cluster discovery
        return nodes

    def get_free_nodes(self) -> list[EXONode]:
        """Get nodes that are not currently executing tasks."""
        return [node for node in self._nodes if not node.is_busy]

    def select_node(self, task_type: str) -> EXONode | None:
        """Select a node for task execution based on task type."""
        free_nodes = self.get_free_nodes()
        if not free_nodes:
            return None

        # Prefer nodes with GPUs for GPU-intensive tasks
        if task_type == "inference":
            gpu_nodes = [n for n in free_nodes if n.gpu_count > 0]
            if gpu_nodes:
                # Select node with most GPUs
                return max(gpu_nodes, key=lambda n: n.gpu_count)

        # Fall back to CPU nodes
        return free_nodes[0]

    async def execute_distributed(self, task: dict[str, Any]) -> dict[str, Any]:
        """Execute a task distributed across nodes."""
        node = self.select_node(task.get("type", "default"))
        if not node:
            raise RuntimeError("No available nodes for task execution")

        logger.info("Executing task on node %s", node.hostname)
        # TODO: Implement distributed execution
        return {"status": "queued", "node": node.hostname}


class EXOSkill:
    """Skill for EXO execution optimization."""

    name = "exo_execution"
    description = "Distributed execution optimization via EXO framework"

    def __init__(self):
        self.executor = EXOExecutor()

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute EXO skill.

        Args:
            action: Action to perform ('check', 'discover', 'execute')
            node: Node hostname for specific operations
            task: Task to execute
            **kwargs: Additional arguments

        Returns:
            Result dictionary with action outcome
        """
        action = kwargs.get("action", "check")
        result: dict[str, Any] = {"action": action}

        if action == "check":
            await self.executor.initialize()
            result.update(
                {
                    "initialized": self.executor._initialized,
                    "node_count": len(self.executor._nodes),
                    "nodes": [self._node_to_dict(n) for n in self.executor._nodes],
                }
            )
        elif action == "discover":
            await self.executor.initialize()
            result.update(
                {
                    "discovered": len(self.executor._nodes),
                    "nodes": [self._node_to_dict(n) for n in self.executor._nodes],
                }
            )
        elif action == "execute":
            if not self.executor._initialized:
                await self.executor.initialize()
            try:
                task = kwargs.get("task", {})
                execute_result = await self.executor.execute_distributed(task)
                result.update(execute_result)
            except Exception as e:
                result.update({"error": str(e)})

        return result

    def _node_to_dict(self, node: EXONode) -> dict[str, Any]:
        """Convert EXONode to dictionary."""
        return {
            "hostname": node.hostname,
            "ip": node.ip,
            "cpu_count": node.cpu_count,
            "memory_gb": node.memory_gb,
            "gpu_count": node.gpu_count,
            "is_leader": node.is_leader,
        }


__all__ = ["EXONode", "EXOExecutor", "EXOSkill"]

#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "httpx",
#     "python-dotenv",
# ]
# ///
"""
Chain Controller -- orchestrates multi-wave subagent pipelines.

Layers on top of the existing subagent flow by running multiple waves
of parallel agents, merging results between waves, and maintaining a
Shared State object throughout the chain.

Waves:
  0. Ingest   — Parse prompt, extract constraints, init shared state
  1. Analysis — Parallel analyzers from different angles
  2. Plan     — Planner + Validator + Optimizer in parallel
  3. Execute  — Parallel executors produce concrete outputs
  4. Finalize — Monitor + Reporter + Cleaner in parallel
  → Deliver

Each wave runs agents in parallel via the session's subagent mechanism,
collects their outputs, and merges them deterministically (dedup, resolve
conflicts, produce a single Shared State update).
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Agent Role Contracts (system prompts for each role)
# ---------------------------------------------------------------------------

AGENT_CONTRACTS: dict[str, str] = {
    "analyzer_a": (
        "ROLE: Analyzer-A (Technical Perspective)\n"
        "Return:\n"
        "- key_insights (bullets)\n"
        "- constraints_found\n"
        "- assumptions (tagged)\n"
        "- risks\n"
        "- questions_to_clarify (only if blocking)\n"
        "- recommendations_for_next_wave\n"
        "Keep it concise; do not propose final answer."
    ),
    "analyzer_b": (
        "ROLE: Analyzer-B (UX/Risk Perspective)\n"
        "Return:\n"
        "- key_insights (bullets)\n"
        "- constraints_found\n"
        "- assumptions (tagged)\n"
        "- risks\n"
        "- edge_cases\n"
        "- recommendations_for_next_wave\n"
        "Keep it concise; do not propose final answer."
    ),
    "planner": (
        "ROLE: Planner\n"
        "Return:\n"
        "- step_by_step_plan\n"
        "- deliverables\n"
        "- dependencies/tools_needed\n"
        "- acceptance_checks (how to verify done)\n"
        "- recommendations_for_execution"
    ),
    "validator": (
        "ROLE: Validator\n"
        "Return:\n"
        "- contradictions_or_gaps\n"
        "- risk_register (severity + mitigation)\n"
        "- edge_cases\n"
        "- must_not_do (violations)\n"
        "- readiness_score (0-100) + why"
    ),
    "optimizer": (
        "ROLE: Optimizer\n"
        "Return:\n"
        "- simplifications\n"
        "- modularization_suggestions\n"
        "- clarity_improvements\n"
        "- performance/maintenance considerations"
    ),
    "executor_1": (
        "ROLE: Executor-1\n"
        "Return:\n"
        "- concrete_output (spec/config/pseudocode/templates)\n"
        "- integration_steps (how to plug into existing flow)\n"
        "- tests_or_checks"
    ),
    "executor_2": (
        "ROLE: Executor-2\n"
        "Return:\n"
        "- concrete_output (spec/config/pseudocode/templates)\n"
        "- integration_steps (how to plug into existing flow)\n"
        "- tests_or_checks"
    ),
    "monitor": (
        "ROLE: Monitor\n"
        "Verify against success criteria; list remaining risks (if any)."
    ),
    "reporter": (
        "ROLE: Reporter\n"
        "Produce the user-facing output. Clear, structured, actionable."
    ),
    "cleaner": (
        "ROLE: Cleaner\n"
        "Polish formatting, remove noise, ensure consistency, remove duplicates."
    ),
}

# ---------------------------------------------------------------------------
# Agent role → optimal model type mapping
# ---------------------------------------------------------------------------
# Maps each orchestrator agent role to the best agent_type category for
# model assignment.  The provider router uses these agent_type keys to look
# up per-agent model overrides from _AGENT_MODEL_MAP or env vars.
#
# Categories:
#   code     — code generation, implementation, execution
#   review   — validation, monitoring, quality checks
#   plan     — planning, structuring, organizing
#   docs     — reporting, documentation, formatting
#   analysis — analysis, research, investigation
#   debug    — optimization, edge cases, risk assessment

AGENT_ROLE_OPTIMIZATION: dict[str, str] = {
    "analyzer_a": "analysis",
    "analyzer_b": "analysis",
    "planner": "plan",
    "validator": "review",
    "optimizer": "debug",
    "executor_1": "code",
    "executor_2": "code",
    "monitor": "review",
    "reporter": "docs",
    "cleaner": "docs",
}

# ---------------------------------------------------------------------------
# Wave definitions
# ---------------------------------------------------------------------------


@dataclass
class WaveConfig:
    """Configuration for a single wave in the chain.

    Parameters
    ----------
    name:
        Human-readable wave name (e.g. ``"analysis"``).
    agents:
        List of agent role identifiers to run in this wave.
    description:
        Optional description of what this wave accomplishes.
    """

    name: str
    agents: list[str]
    description: str = ""


# Default wave pipeline
DEFAULT_WAVES: list[WaveConfig] = [
    WaveConfig(
        name="analysis",
        agents=["analyzer_a", "analyzer_b"],
        description="Analyze the problem from multiple perspectives",
    ),
    WaveConfig(
        name="plan_validate_optimize",
        agents=["planner", "validator", "optimizer"],
        description="Plan the solution, validate it, and optimize",
    ),
    WaveConfig(
        name="execution",
        agents=["executor_1", "executor_2"],
        description="Produce concrete outputs and implementations",
    ),
    WaveConfig(
        name="finalize",
        agents=["monitor", "reporter", "cleaner"],
        description="Monitor quality, format output, clean up",
    ),
]


# ---------------------------------------------------------------------------
# Shared State
# ---------------------------------------------------------------------------


@dataclass
class SharedState:
    """Shared state object maintained across waves.

    Updated after every wave merge. Provides the context for the next wave.

    Parameters
    ----------
    problem_statement:
        The original user request.
    success_criteria:
        Extracted criteria for determining completion.
    constraints:
        Explicit and inferred constraints.
    assumptions:
        Tagged assumptions from analysis.
    risks:
        Identified risks with severity and mitigation.
    plan:
        Current plan (updated after planning wave).
    artifacts:
        List of artifacts to update or produce.
    final_answer_outline:
        Outline of the final answer.
    wave_outputs:
        Raw outputs from each wave, keyed by wave name.
    """

    run_id: str = ""
    problem_statement: str = ""
    success_criteria: list[str] = field(default_factory=list)
    constraints: list[str] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    plan: list[str] = field(default_factory=list)
    artifacts: list[str] = field(default_factory=list)
    final_answer_outline: str = ""
    wave_outputs: dict[str, list[dict[str, str]]] = field(default_factory=dict)

    def to_context_block(self, max_chars: int = 2000) -> str:
        """Format the shared state as a text block for injection into prompts.

        Parameters
        ----------
        max_chars:
            Maximum length of the returned text block.

        Returns
        -------
        Formatted text block summarizing the current shared state.
        """
        parts: list[str] = [
            f"## Shared State (run: {self.run_id})",
            f"**Problem:** {self.problem_statement[:200]}",
        ]
        if self.success_criteria:
            parts.append("**Success Criteria:**")
            for c in self.success_criteria[:5]:
                parts.append(f"  - {c}")
        if self.constraints:
            parts.append("**Constraints:**")
            for c in self.constraints[:5]:
                parts.append(f"  - {c}")
        if self.assumptions:
            parts.append("**Assumptions:**")
            for a in self.assumptions[:5]:
                parts.append(f"  - {a}")
        if self.risks:
            parts.append("**Risks:**")
            for r in self.risks[:5]:
                parts.append(f"  - {r}")
        if self.plan:
            parts.append("**Plan:**")
            for p in self.plan[:8]:
                parts.append(f"  - {p}")
        if self.final_answer_outline:
            parts.append(f"**Answer outline:** {self.final_answer_outline[:200]}")

        text = "\n".join(parts)
        return text[:max_chars]

    def as_dict(self) -> dict[str, Any]:
        """Return the shared state as a serializable dict."""
        return {
            "run_id": self.run_id,
            "problem_statement": self.problem_statement,
            "success_criteria": self.success_criteria,
            "constraints": self.constraints,
            "assumptions": self.assumptions,
            "risks": self.risks,
            "plan": self.plan,
            "artifacts": self.artifacts,
            "final_answer_outline": self.final_answer_outline,
        }


# ---------------------------------------------------------------------------
# Wave Result
# ---------------------------------------------------------------------------


@dataclass
class WaveResult:
    """Result from executing a single wave.

    Parameters
    ----------
    wave_name:
        Name of the wave.
    agent_outputs:
        List of ``{agent, content}`` dicts from each agent.
    merged_output:
        The merged/deduped output from all agents in this wave.
    duration_seconds:
        Time taken to complete the wave.
    """

    wave_name: str = ""
    agent_outputs: list[dict[str, str]] = field(default_factory=list)
    merged_output: str = ""
    duration_seconds: float = 0.0


# ---------------------------------------------------------------------------
# Chain Controller
# ---------------------------------------------------------------------------


class ChainController:
    """Orchestrates multi-wave subagent pipelines.

    Runs the existing session's ``send()`` method for each agent in each wave,
    collects outputs, and merges them into a Shared State that carries through
    the entire chain.

    Parameters
    ----------
    session:
        The active Session instance.
    waves:
        Optional custom wave configuration. Defaults to :data:`DEFAULT_WAVES`.
    """

    def __init__(
        self,
        session: Any,
        waves: list[WaveConfig] | None = None,
    ) -> None:
        self.session = session
        self.waves = waves or DEFAULT_WAVES
        self._state = SharedState()
        self._results: list[WaveResult] = []
        self._allocations: dict[str, tuple[str, str]] = {}

    @property
    def state(self) -> SharedState:
        """Return the current shared state."""
        return self._state

    @property
    def results(self) -> list[WaveResult]:
        """Return all wave results collected so far."""
        return self._results

    @property
    def allocations(self) -> dict[str, tuple[str, str]]:
        """Return the auto-allocated model assignments per agent role."""
        return self._allocations

    # -- model auto-allocation -----------------------------------------------

    def auto_allocate_models(self) -> dict[str, tuple[str, str]]:
        """Auto-allocate optimal models to each agent role.

        Inspects the provider router for explicitly configured agent models
        and available providers, then assigns the best model to each
        orchestrator agent role based on :data:`AGENT_ROLE_OPTIMIZATION`.

        Already-configured agent models (via ``/set-agent-model``, env vars,
        or ``.ollama/settings.json``) take priority.  Unassigned roles
        fall back to the session's current model and provider.

        Returns
        -------
        Dict mapping agent role to ``(provider, model)`` tuple.
        """
        from api.provider_router import _AGENT_MODEL_MAP

        allocations: dict[str, tuple[str, str]] = {}
        session_default = (self.session.provider, self.session.model)

        for agent_role in AGENT_ROLE_OPTIMIZATION:
            agent_type = AGENT_ROLE_OPTIMIZATION[agent_role]

            # 1. Check if this agent_type has an explicit assignment
            if agent_type in _AGENT_MODEL_MAP:
                allocations[agent_role] = _AGENT_MODEL_MAP[agent_type]
                continue

            # 2. Fall back to session default
            allocations[agent_role] = session_default

        self._allocations = allocations

        allocated_types = {v for v in allocations.values()}
        logger.info(
            "Chain auto-allocated %d roles across %d model configs",
            len(allocations),
            len(allocated_types),
        )

        return allocations

    # -- wave 0: ingest ------------------------------------------------------

    def ingest(self, prompt: str) -> SharedState:
        """Wave 0: Parse prompt, extract constraints, initialize shared state.

        Also runs :meth:`auto_allocate_models` to assign optimal models to
        each agent role before the waves begin.

        Parameters
        ----------
        prompt:
            The original user prompt.

        Returns
        -------
        The initialized :class:`SharedState`.
        """
        self._state = SharedState(
            run_id=str(uuid.uuid4())[:8],
            problem_statement=prompt,
        )

        # Auto-allocate models before any waves run
        self.auto_allocate_models()

        logger.info("Chain %s: ingested prompt (%d chars)", self._state.run_id, len(prompt))
        return self._state

    # -- run a single wave ---------------------------------------------------

    async def run_wave(self, wave: WaveConfig) -> WaveResult:
        """Run a single wave: send prompts to all agents, collect outputs.

        Each agent gets:
        - The shared state context block
        - Its role contract (system prompt)
        - The problem statement

        Parameters
        ----------
        wave:
            The wave configuration to execute.

        Returns
        -------
        A :class:`WaveResult` with all agent outputs and the merged output.
        """
        start = datetime.now(tz=timezone.utc)
        agent_outputs: list[dict[str, str]] = []

        for agent_role in wave.agents:
            # Build the prompt for this agent
            contract = AGENT_CONTRACTS.get(agent_role, f"ROLE: {agent_role}")
            context_block = self._state.to_context_block()

            agent_prompt = (
                f"{contract}\n\n"
                f"--- SHARED STATE ---\n{context_block}\n--- END STATE ---\n\n"
                f"Task: {self._state.problem_statement}\n\n"
                "Respond according to your role contract above."
            )

            # Create sub-context for this agent
            ctx_id = f"chain-{self._state.run_id}-{wave.name}-{agent_role}"
            self.session.create_sub_context(ctx_id)

            # Resolve the optimized agent_type for model routing
            optimized_type = AGENT_ROLE_OPTIMIZATION.get(agent_role, agent_role)

            # Announce via agent comm bus
            self.session.agent_comm.send(
                sender_id="chain_controller",
                recipient_id=agent_role,
                content=f"Wave '{wave.name}': executing {agent_role} (as {optimized_type})",
                message_type="task",
            )

            try:
                result = await self.session.send(
                    agent_prompt,
                    agent_type=optimized_type,
                    context_id=ctx_id,
                )
                content = result.get("content", "")
            except Exception as exc:
                logger.warning("Chain %s: agent %s failed: %s", self._state.run_id, agent_role, exc)
                content = f"[Agent {agent_role} failed: {exc}]"

            agent_outputs.append({
                "agent": agent_role,
                "content": content,
            })

            # Report via agent comm bus
            self.session.agent_comm.send(
                sender_id=agent_role,
                recipient_id="chain_controller",
                content=f"Completed: {len(content)} chars",
                message_type="result",
            )

        # Merge outputs
        merged = self._merge_outputs(wave.name, agent_outputs)

        end = datetime.now(tz=timezone.utc)
        wave_result = WaveResult(
            wave_name=wave.name,
            agent_outputs=agent_outputs,
            merged_output=merged,
            duration_seconds=(end - start).total_seconds(),
        )
        self._results.append(wave_result)

        # Store wave outputs in shared state
        self._state.wave_outputs[wave.name] = agent_outputs

        logger.info(
            "Chain %s: wave '%s' complete (%d agents, %.1fs)",
            self._state.run_id, wave.name, len(agent_outputs), wave_result.duration_seconds,
        )

        return wave_result

    # -- run the full chain --------------------------------------------------

    async def run_chain(self, prompt: str) -> dict[str, Any]:
        """Execute the full chain: ingest → waves → deliver.

        Parameters
        ----------
        prompt:
            The user's original prompt.

        Returns
        -------
        Dict with ``run_id``, ``final_output``, ``shared_state``,
        ``wave_results``, and ``total_duration``.
        """
        chain_start = datetime.now(tz=timezone.utc)

        # Wave 0: Ingest
        self.ingest(prompt)

        # Run each wave in sequence
        for wave in self.waves:
            await self.run_wave(wave)

        chain_end = datetime.now(tz=timezone.utc)
        total_duration = (chain_end - chain_start).total_seconds()

        # Extract the final output from the reporter in the finalize wave
        final_output = self._extract_final_output()

        return {
            "run_id": self._state.run_id,
            "final_output": final_output,
            "shared_state": self._state.as_dict(),
            "wave_count": len(self._results),
            "wave_results": [
                {
                    "wave": r.wave_name,
                    "agents": len(r.agent_outputs),
                    "duration": r.duration_seconds,
                }
                for r in self._results
            ],
            "total_duration": total_duration,
        }

    # -- merge logic ---------------------------------------------------------

    def _merge_outputs(self, wave_name: str, outputs: list[dict[str, str]]) -> str:
        """Deterministic merge: dedup, resolve conflicts, update shared state.

        Parameters
        ----------
        wave_name:
            Name of the wave being merged.
        outputs:
            List of ``{agent, content}`` dicts.

        Returns
        -------
        The merged output text.
        """
        sections: list[str] = []
        seen_lines: set[str] = set()

        for output in outputs:
            agent = output["agent"]
            content = output["content"]
            sections.append(f"### {agent}\n{content}")

            # Extract structured items for shared state updates
            for line in content.splitlines():
                stripped = line.strip().lstrip("- •*").strip()
                if stripped and len(stripped) > 10:
                    normalized = stripped.lower()
                    if normalized not in seen_lines:
                        seen_lines.add(normalized)
                        self._classify_and_store(wave_name, stripped)

        return "\n\n".join(sections)

    def _classify_and_store(self, wave_name: str, item: str) -> None:
        """Classify a text item and store it in the appropriate shared state field."""
        lower = item.lower()

        # Simple keyword-based classification
        if any(kw in lower for kw in ["risk", "danger", "warning", "concern"]):
            if item not in self._state.risks:
                self._state.risks.append(item)
        elif any(kw in lower for kw in ["constraint", "must not", "requirement", "limit"]):
            if item not in self._state.constraints:
                self._state.constraints.append(item)
        elif any(kw in lower for kw in ["assume", "assumption", "presume"]):
            if item not in self._state.assumptions:
                self._state.assumptions.append(item)
        elif any(kw in lower for kw in ["step", "plan", "phase", "task", "action"]):
            if item not in self._state.plan:
                self._state.plan.append(item)
        elif any(kw in lower for kw in ["criteria", "success", "accept", "verify", "done"]):
            if item not in self._state.success_criteria:
                self._state.success_criteria.append(item)

    def _extract_final_output(self) -> str:
        """Extract the final user-facing output from the chain results.

        Prefers the reporter agent's output from the finalize wave;
        falls back to the last wave's merged output.
        """
        # Look for the reporter in the finalize wave
        for result in reversed(self._results):
            for output in result.agent_outputs:
                if output["agent"] == "reporter":
                    return output["content"]

        # Fallback: use last wave's merged output
        if self._results:
            return self._results[-1].merged_output

        return self._state.problem_statement


# ---------------------------------------------------------------------------
# Helper: parse chain config from YAML-like dict
# ---------------------------------------------------------------------------


def parse_chain_config(config: dict[str, Any]) -> list[WaveConfig]:
    """Parse a chain configuration dict into a list of WaveConfig.

    Parameters
    ----------
    config:
        Dict with a ``waves`` key containing a list of wave dicts,
        each with ``name`` and ``agents`` keys.

    Returns
    -------
    List of :class:`WaveConfig` instances.
    """
    waves: list[WaveConfig] = []
    for wave_data in config.get("waves", []):
        waves.append(WaveConfig(
            name=wave_data.get("name", "unnamed"),
            agents=wave_data.get("agents", []),
            description=wave_data.get("description", ""),
        ))
    return waves


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Chain Controller module loaded successfully.")
    print(f"Default waves: {len(DEFAULT_WAVES)}")
    for w in DEFAULT_WAVES:
        print(f"  {w.name}: {w.agents}")
    print(f"Agent contracts: {len(AGENT_CONTRACTS)}")
    for role in AGENT_CONTRACTS:
        print(f"  {role}")

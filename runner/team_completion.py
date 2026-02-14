"""Team completion loop -- agentic sub-agent plan-then-build pipeline.

Implements the ``/complete_w_team`` command: a multi-phase agentic loop
where a team of specialised agents collaborates to plan, validate, and
produce an executable specification.

Phases
------
1. **Analyse** — An analyst examines the task from a technical standpoint.
2. **Plan** — A planner creates a step-by-step implementation plan.
3. **Validate** — A validator reviews the plan for gaps and risks.
4. **Spec** — A spec writer converts the validated plan into a formal spec
   saved to ``.ollama/spec/<slug>.md``.
5. **Review** — A reviewer verifies the spec against acceptance criteria.

Autonomous Command Execution
-----------------------------
Every agent in the loop receives a **command knowledge block** describing
all available slash commands.  Agents may request command execution by
including ``[CMD: /command args]`` directives in their output.  The loop
detects these directives, executes the commands via the
:class:`CommandProcessor`, and feeds the results back into the
accumulated context for subsequent phases.

The generated spec is designed to be executed later via ``/build``.
"""

from __future__ import annotations

import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SPEC_DIR = Path(".ollama/spec")
TASKS_DIR = Path(".ollama/tasks")

# Maximum characters to display from a command result in accumulated context
_MAX_RESULT_DISPLAY_LEN = 200

# Commands that agents are NOT allowed to invoke autonomously
_BLOCKED_COMMANDS = frozenset({"/quit", "/exit", "/clear"})

# ---------------------------------------------------------------------------
# Command knowledge builder
# ---------------------------------------------------------------------------


def build_command_knowledge() -> str:
    """Build a text block describing all available slash commands.

    This block is injected into every agent prompt so the AI has full
    knowledge of the CLI's capabilities and can request command execution
    when useful.

    Returns
    -------
    Formatted multi-line string listing every command with its description.
    """
    from tui.command_processor import COMMAND_REGISTRY

    lines: list[str] = [
        "## Available CLI Commands",
        "",
        "You may request any of the following commands by writing "
        "`[CMD: /command <args>]` on its own line.  The orchestrator will "
        "execute the command and feed the result back into the context.",
        "Only request commands when they would meaningfully help the task.",
        "",
    ]

    seen: set[str] = set()
    for cmd, (_handler, desc, category) in sorted(COMMAND_REGISTRY.items()):
        if cmd in seen or cmd in _BLOCKED_COMMANDS:
            continue
        seen.add(cmd)
        lines.append(f"  {cmd:30s} — {desc}  [{category}]")

    lines.append("")
    lines.append(
        "Example: `[CMD: /status]` to check session info, "
        "`[CMD: /pull llama3.2]` to download a model, "
        "`[CMD: /memory]` to check project memory."
    )
    return "\n".join(lines)


def extract_command_requests(text: str) -> list[str]:
    """Extract ``[CMD: /command args]`` directives from agent output.

    Parameters
    ----------
    text:
        Raw agent output that may contain command directives.

    Returns
    -------
    List of command strings (e.g. ``["/status", "/pull llama3.2"]``).
    """
    pattern = r"\[CMD:\s*(/[^\]]+)\]"
    matches = re.findall(pattern, text)
    # Filter out blocked commands
    return [m.strip() for m in matches if m.strip() and m.strip().split()[0] not in _BLOCKED_COMMANDS]


# ---------------------------------------------------------------------------
# Agent role contracts
# ---------------------------------------------------------------------------

TEAM_ROLES: dict[str, str] = {
    "analyst": (
        "ROLE: Analyst\n"
        "Examine the task from a technical standpoint.  Return:\n"
        "- key_insights (bullets)\n"
        "- constraints_found\n"
        "- assumptions (tagged)\n"
        "- risks\n"
        "- recommendations_for_planner\n"
        "Keep it concise; do not propose a final solution.\n"
        "You may use `[CMD: /command]` to invoke CLI commands if needed."
    ),
    "planner": (
        "ROLE: Planner\n"
        "Create a step-by-step implementation plan.  Return:\n"
        "- step_by_step_plan (numbered)\n"
        "- deliverables\n"
        "- dependencies_and_tools\n"
        "- acceptance_criteria (how to verify done)\n"
        "- estimated_effort\n"
        "You may use `[CMD: /command]` to invoke CLI commands if needed."
    ),
    "validator": (
        "ROLE: Validator\n"
        "Review the plan for correctness and completeness.  Return:\n"
        "- contradictions_or_gaps\n"
        "- risk_register (severity + mitigation)\n"
        "- edge_cases\n"
        "- readiness_score (0-100) and reasoning\n"
        "You may use `[CMD: /command]` to invoke CLI commands if needed."
    ),
    "spec_writer": (
        "ROLE: Spec Writer\n"
        "Convert the validated plan into a formal specification file.\n"
        "The spec MUST include:\n"
        "## Objective\n## Scope\n## Requirements\n"
        "## Implementation Steps\n## Acceptance Criteria\n## Dependencies\n"
        "Format as Markdown.  Be precise and actionable.\n"
        "This spec will be read by an executor agent, so be explicit.\n"
        "You may use `[CMD: /command]` to invoke CLI commands if needed."
    ),
    "reviewer": (
        "ROLE: Reviewer\n"
        "Verify the spec against the original task and the plan.\n"
        "Return:\n"
        "- completeness_check (pass/fail per section)\n"
        "- issues_found\n"
        "- final_verdict (ready / needs_revision)\n"
        "- summary (one paragraph)\n"
        "You may use `[CMD: /command]` to invoke CLI commands if needed."
    ),
}

# Maps team roles to agent_type categories for model routing
TEAM_ROLE_TYPES: dict[str, str] = {
    "analyst": "analysis",
    "planner": "plan",
    "validator": "review",
    "spec_writer": "code",
    "reviewer": "review",
}


# ---------------------------------------------------------------------------
# Phase result
# ---------------------------------------------------------------------------


@dataclass
class PhaseResult:
    """Result from a single phase in the team completion loop.

    Attributes
    ----------
    phase_name:
        Human-readable phase name.
    agent_role:
        The agent role that produced this result.
    content:
        The raw output from the agent.
    duration_seconds:
        How long the phase took.
    commands_executed:
        List of commands the agent requested and their results.
    """

    phase_name: str = ""
    agent_role: str = ""
    content: str = ""
    duration_seconds: float = 0.0
    commands_executed: list[dict[str, str]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Team completion result
# ---------------------------------------------------------------------------


@dataclass
class TeamCompletionResult:
    """Full result from a ``/complete_w_team`` invocation.

    Attributes
    ----------
    run_id:
        Unique identifier for this completion run.
    task_description:
        The original user task.
    spec_path:
        Path to the generated spec file.
    phases:
        Ordered list of phase results.
    total_duration:
        Total wall-clock duration.
    total_commands:
        Total number of autonomous command executions.
    """

    run_id: str = ""
    task_description: str = ""
    spec_path: str = ""
    phases: list[PhaseResult] = field(default_factory=list)
    total_duration: float = 0.0
    total_commands: int = 0

    def as_dict(self) -> dict[str, Any]:
        """Serialisable representation."""
        return {
            "run_id": self.run_id,
            "task_description": self.task_description,
            "spec_path": self.spec_path,
            "total_duration": self.total_duration,
            "total_commands": self.total_commands,
            "phases": [
                {
                    "phase": p.phase_name,
                    "agent": p.agent_role,
                    "chars": len(p.content),
                    "duration": p.duration_seconds,
                    "commands": len(p.commands_executed),
                }
                for p in self.phases
            ],
        }


# ---------------------------------------------------------------------------
# Team Completion Loop
# ---------------------------------------------------------------------------


class TeamCompletionLoop:
    """Agentic sub-agent loop: plan → validate → spec → review.

    Each agent receives command knowledge and may autonomously request
    slash command execution via ``[CMD: /command args]`` directives.

    Parameters
    ----------
    session:
        The active Session instance (must support ``send()``,
        ``create_sub_context()``, ``agent_comm``, ``memory_layer``).
    command_processor:
        Optional :class:`CommandProcessor` for autonomous command execution.
        When provided, agents can invoke slash commands.
    """

    def __init__(self, session: Any, command_processor: Any | None = None) -> None:
        self.session = session
        self.command_processor = command_processor
        self._run_id = str(uuid.uuid4())[:8]
        self._command_knowledge = build_command_knowledge()

    # -- helpers -------------------------------------------------------------

    def _slug(self, text: str) -> str:
        """Convert text to a filesystem-safe slug."""
        return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]

    async def _execute_agent_commands(self, agent_output: str) -> list[dict[str, str]]:
        """Detect and execute command requests in agent output.

        Parameters
        ----------
        agent_output:
            Raw text from an agent that may contain ``[CMD: ...]`` directives.

        Returns
        -------
        List of ``{"command": ..., "result": ...}`` dicts.
        """
        if self.command_processor is None:
            return []

        requests = extract_command_requests(agent_output)
        results: list[dict[str, str]] = []

        for cmd_line in requests:
            logger.info("Team %s: auto-executing command: %s", self._run_id, cmd_line)
            try:
                import asyncio

                cmd_result = self.command_processor.dispatch(cmd_line)
                if asyncio.iscoroutine(cmd_result):
                    cmd_result = await cmd_result

                output_text = "\n".join(cmd_result.output) if cmd_result.output else ""
                error_text = "\n".join(cmd_result.errors) if cmd_result.errors else ""
                result_text = output_text or error_text or "(no output)"

                results.append({"command": cmd_line, "result": result_text})
            except Exception as exc:
                logger.warning("Team %s: command %r failed: %s", self._run_id, cmd_line, exc)
                results.append({"command": cmd_line, "result": f"[Error: {exc}]"})

        return results

    async def _run_agent(
        self,
        role: str,
        task_prompt: str,
        *,
        prior_context: str = "",
    ) -> PhaseResult:
        """Run a single agent and return its result.

        The agent receives:
        - Its role contract
        - The command knowledge block (so it can invoke commands)
        - Prior context from earlier phases
        - The task prompt

        After the agent responds, any ``[CMD: ...]`` directives are
        extracted and executed.

        Parameters
        ----------
        role:
            Agent role key (must exist in :data:`TEAM_ROLES`).
        task_prompt:
            The task-specific prompt to inject.
        prior_context:
            Accumulated context from previous phases.
        """
        contract = TEAM_ROLES.get(role, f"ROLE: {role}")
        agent_type = TEAM_ROLE_TYPES.get(role, role)
        ctx_id = f"team-{self._run_id}-{role}"

        if hasattr(self.session, "create_sub_context"):
            self.session.create_sub_context(ctx_id)

        full_prompt = f"{contract}\n\n"
        full_prompt += f"{self._command_knowledge}\n\n"
        if prior_context:
            full_prompt += f"--- PRIOR CONTEXT ---\n{prior_context}\n--- END CONTEXT ---\n\n"
        full_prompt += f"Task:\n{task_prompt}\n\nRespond according to your role contract above."

        # Announce via comm bus
        if hasattr(self.session, "agent_comm"):
            self.session.agent_comm.send(
                sender_id="team_loop",
                recipient_id=role,
                content=f"Team completion: executing {role}",
                message_type="task",
            )

        start = datetime.now(tz=timezone.utc)

        try:
            result = await self.session.send(
                full_prompt,
                agent_type=agent_type,
                context_id=ctx_id,
            )
            content = result.get("content", "")
        except Exception as exc:
            logger.warning("Team %s: agent %s failed: %s", self._run_id, role, exc)
            content = f"[Agent {role} failed: {exc}]"

        # Execute any commands the agent requested
        commands_executed = await self._execute_agent_commands(content)

        end = datetime.now(tz=timezone.utc)

        # Report via comm bus
        if hasattr(self.session, "agent_comm"):
            self.session.agent_comm.send(
                sender_id=role,
                recipient_id="team_loop",
                content=f"Completed: {len(content)} chars, {len(commands_executed)} commands",
                message_type="result",
            )

        return PhaseResult(
            phase_name=role,
            agent_role=role,
            content=content,
            duration_seconds=(end - start).total_seconds(),
            commands_executed=commands_executed,
        )

    # -- main loop -----------------------------------------------------------

    async def run(self, task_description: str) -> TeamCompletionResult:
        """Execute the full team completion loop.

        Phases
        ------
        1. Analyse — ``analyst`` examines the task.
        2. Plan — ``planner`` creates a step-by-step plan.
        3. Validate — ``validator`` reviews the plan.
        4. Spec — ``spec_writer`` produces a formal spec file.
        5. Review — ``reviewer`` checks the spec.

        After each phase, any command results are appended to the
        accumulated context so subsequent agents see them.

        Parameters
        ----------
        task_description:
            The user's task description.

        Returns
        -------
        :class:`TeamCompletionResult` with the generated spec path.
        """
        loop_start = datetime.now(tz=timezone.utc)
        slug = self._slug(task_description)
        phases: list[PhaseResult] = []
        total_commands = 0
        accumulated_context = f"Original task: {task_description}"

        # Inject memories if available
        if hasattr(self.session, "memory_layer"):
            memory_block = self.session.memory_layer.get_context_block(max_tokens=300)
            if memory_block:
                accumulated_context += f"\n\nProject context:\n{memory_block}"

        # ── Phase 1: Analyse ──────────────────────────────────────────
        analysis = await self._run_agent("analyst", task_description, prior_context=accumulated_context)
        phases.append(analysis)
        accumulated_context += f"\n\n## Analysis\n{analysis.content}"
        if analysis.commands_executed:
            total_commands += len(analysis.commands_executed)
            cmd_block = "\n".join(
                f"  > {c['command']}: {c['result'][:_MAX_RESULT_DISPLAY_LEN]}" for c in analysis.commands_executed
            )
            accumulated_context += f"\n\n### Command Results (analyst)\n{cmd_block}"

        # ── Phase 2: Plan ─────────────────────────────────────────────
        plan = await self._run_agent("planner", task_description, prior_context=accumulated_context)
        phases.append(plan)
        accumulated_context += f"\n\n## Plan\n{plan.content}"
        if plan.commands_executed:
            total_commands += len(plan.commands_executed)
            cmd_block = "\n".join(
                f"  > {c['command']}: {c['result'][:_MAX_RESULT_DISPLAY_LEN]}" for c in plan.commands_executed
            )
            accumulated_context += f"\n\n### Command Results (planner)\n{cmd_block}"

        # ── Phase 3: Validate ─────────────────────────────────────────
        validation = await self._run_agent("validator", task_description, prior_context=accumulated_context)
        phases.append(validation)
        accumulated_context += f"\n\n## Validation\n{validation.content}"
        if validation.commands_executed:
            total_commands += len(validation.commands_executed)
            cmd_block = "\n".join(
                f"  > {c['command']}: {c['result'][:_MAX_RESULT_DISPLAY_LEN]}" for c in validation.commands_executed
            )
            accumulated_context += f"\n\n### Command Results (validator)\n{cmd_block}"

        # ── Phase 4: Write Spec ───────────────────────────────────────
        spec_result = await self._run_agent("spec_writer", task_description, prior_context=accumulated_context)
        phases.append(spec_result)
        if spec_result.commands_executed:
            total_commands += len(spec_result.commands_executed)

        # ── Phase 5: Review ───────────────────────────────────────────
        review_context = accumulated_context + f"\n\n## Spec\n{spec_result.content}"
        review = await self._run_agent("reviewer", task_description, prior_context=review_context)
        phases.append(review)
        if review.commands_executed:
            total_commands += len(review.commands_executed)

        # ── Save Spec ─────────────────────────────────────────────────
        SPEC_DIR.mkdir(parents=True, exist_ok=True)
        spec_file = SPEC_DIR / f"{slug}.md"
        spec_content = spec_result.content

        # Prepend metadata header
        header = (
            f"<!-- team-completion run_id={self._run_id} -->\n"
            f"<!-- task: {task_description[:200]} -->\n"
            f"<!-- generated: {datetime.now(tz=timezone.utc).isoformat()} -->\n\n"
        )
        spec_content = header + spec_content

        try:
            spec_file.write_text(spec_content, encoding="utf-8")
        except OSError as exc:
            logger.error("Failed to write spec: %s", exc)

        # ── Save Task Record ──────────────────────────────────────────
        tasks_dir = TASKS_DIR
        tasks_dir.mkdir(parents=True, exist_ok=True)
        task_record = {
            "id": slug,
            "type": "complete_w_team",
            "description": task_description,
            "spec_file": str(spec_file),
            "run_id": self._run_id,
            "session_id": getattr(self.session, "session_id", ""),
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "status": "spec_ready",
            "phases": [p.phase_name for p in phases],
            "total_commands": total_commands,
        }
        task_file = tasks_dir / f"{slug}.json"
        try:
            task_file.write_text(json.dumps(task_record, indent=2), encoding="utf-8")
        except OSError:
            logger.debug("Failed to save task record", exc_info=True)

        # ── Store in memory layer ─────────────────────────────────────
        if hasattr(self.session, "memory_layer"):
            self.session.memory_layer.store(
                key=f"spec:{slug}",
                content=f"Team spec for: {task_description[:200]}",
                category="fact",
                importance=5,
            )

        loop_end = datetime.now(tz=timezone.utc)

        return TeamCompletionResult(
            run_id=self._run_id,
            task_description=task_description,
            spec_path=str(spec_file),
            phases=phases,
            total_duration=(loop_end - loop_start).total_seconds(),
            total_commands=total_commands,
        )

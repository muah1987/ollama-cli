#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "python-dotenv",
#     "httpx",
#     "rich",
# ]
# ///

"""
Planning mode module for ollama-cli.

This module provides planning-specific functionality that allocates more resources
to research tasks and implements planning-oriented behaviors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.session import Session

def initialize_planning_mode(session: Session) -> None:
    """Initialize planning mode with appropriate settings.

    In planning mode, we:
    - Allocate more tokens for context to allow deeper research
    - Enable verbose output for detailed analysis
    - Set appropriate timeouts for longer thinking periods
    - Configure agent allocation for research tasks

    Parameters
    ----------
    session:
        The session to configure for planning mode.
    """
    # Increase context length for deeper research
    session.context_manager.max_tokens = session.context_manager.max_tokens * 2

    # Enable verbose output for planning insights
    session.verbose = True

    # Set longer timeout for complex planning tasks
    session.timeout = 300  # 5 minutes for planning tasks

    print("Planning mode activated. Configured for research-focused tasks.")

def plan_task(session: Session, task_description: str) -> dict:
    """Generate a plan for a given task.

    Parameters
    ----------
    session:
        The session to use for planning.
    task_description:
        Description of the task to plan.

    Returns
    -------
    Dictionary containing the plan details.
    """
    # In planning mode, we use a specialized prompt for task decomposition
    planning_prompt = f"""
    Please create a detailed plan to accomplish the following task:

    TASK: {task_description}

    Break this down into specific, actionable steps. For each step, include:
    1. Step name
    2. Estimated complexity (low/medium/high)
    3. Required tools or resources
    4. Dependencies on other steps
    5. Expected outcomes

    Provide your response in JSON format.
    """

    # Send the planning prompt to the model
    result = session.send(planning_prompt)

    return result

def execute_planning_workflow(session: Session, task_description: str) -> None:
    """Execute the full planning workflow.

    Parameters
    ----------
    session:
        The session to use for planning.
    task_description:
        Description of the task to plan.
    """
    print(f"Starting planning workflow for: {task_description}")

    # Initialize planning mode settings
    initialize_planning_mode(session)

    # Generate the plan
    plan_result = plan_task(session, task_description)

    # Display the plan
    print("Generated Plan:")
    print(plan_result.get("content", "No plan content received."))

# Example usage when run directly
if __name__ == "__main__":
    # This is just for testing the module directly
    print("Planning module loaded successfully.")
    print("Use initialize_planning_mode() and plan_task() functions with a Session object.")
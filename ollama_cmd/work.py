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
Work mode module for ollama-cli.

This module provides work-specific functionality that focuses on execution efficiency
and implements work-oriented behaviors.
"""

from __future__ import annotations

import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from model.session import Session

def initialize_work_mode(session: Session) -> None:
    """Initialize work mode with appropriate settings.

    In work mode, we:
    - Optimize for execution speed and efficiency
    - Minimize verbose output to reduce distractions
    - Set appropriate timeouts for quick responses
    - Configure agent allocation for execution tasks

    Parameters
    ----------
    session:
        The session to configure for work mode.
    """
    # Reduce context length for faster responses
    session.context_manager.max_tokens = min(session.context_manager.max_tokens, 2048)

    # Disable verbose output for focused work
    session.verbose = False

    # Set shorter timeout for quick execution
    session.timeout = 60  # 1 minute for execution tasks

    print("Work mode activated. Configured for execution-focused tasks.")

def execute_task(session: Session, task_description: str) -> dict:
    """Execute a given task efficiently.

    Parameters
    ----------
    session:
        The session to use for execution.
    task_description:
        Description of the task to execute.

    Returns
    -------
    Dictionary containing the execution results.
    """
    # In work mode, we use a focused prompt for task execution
    execution_prompt = f"""
    Please execute the following task as efficiently as possible:

    TASK: {task_description}

    Focus on:
    1. Completing the task correctly
    2. Being concise in your response
    3. Providing only the essential information needed
    4. Following any specific requirements exactly

    Provide your response in a clear, actionable format.
    """

    # Send the execution prompt to the model
    result = session.send(execution_prompt)

    return result

def execute_work_workflow(session: Session, task_description: str) -> None:
    """Execute the full work workflow.

    Parameters
    ----------
    session:
        The session to use for work.
    task_description:
        Description of the task to execute.
    """
    print(f"Starting work workflow for: {task_description}")

    # Initialize work mode settings
    initialize_work_mode(session)

    # Execute the task
    work_result = execute_task(session, task_description)

    # Display the result
    print("Task Execution Result:")
    print(work_result.get("content", "No result content received."))

# Example usage when run directly
if __name__ == "__main__":
    # This is just for testing the module directly
    print("Work module loaded successfully.")
    print("Use initialize_work_mode() and execute_task() functions with a Session object.")
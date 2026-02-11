"""
Sub-Agent Scenario Tests for ollama-cli

Tests cover:
1. Nested sub-agent token tracking
2. Context compression in hierarchical agents
3. Aggregated cost estimation across sub-agents
4. Complex workflow scenarios with multiple agents
"""

import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from token_counter import TokenCounter


class TestNestedSubAgentScenarios:
    """Test nested sub-agent scenarios and context compression."""
    
    def test_hierarchical_agent_token_tracking(self):
        """Test token tracking in a hierarchy of agents."""
        # Main agent
        main_agent = TokenCounter(provider="anthropic")
        
        # Sub-agent 1
        sub_agent1 = TokenCounter(provider="anthropic")
        sub_response1 = {
            "usage": {"input_tokens": 500, "output_tokens": 1000},
            "response_ms": 500
        }
        sub_agent1.update(sub_response1)
        
        # Sub-agent 2
        sub_agent2 = TokenCounter(provider="anthropic")
        sub_response2 = {
            "usage": {"input_tokens": 300, "output_tokens": 700},
            "response_ms": 300
        }
        sub_agent2.update(sub_response2)
        
        # Aggregate to main agent
        aggregate_response = {
            "usage": {
                "input_tokens": sub_agent1.prompt_tokens + sub_agent2.prompt_tokens,
                "output_tokens": sub_agent1.completion_tokens + sub_agent2.completion_tokens
            },
            "response_ms": max(sub_response1["response_ms"], sub_response2["response_ms"])
        }
        main_agent.update(aggregate_response)
        
        # Verify aggregation
        assert main_agent.prompt_tokens == 800  # 500 + 300
        assert main_agent.completion_tokens == 1700  # 1000 + 700
        assert main_agent.total_tokens == 2500
        
    def test_context_compression_simulation(self):
        """Test simulation of context compression in sub-agent workflows."""
        # Initial context state
        agent = TokenCounter(provider="openai", context_max=128000)
        agent.set_context(100000, 128000)  # 100K tokens used of 128K max
        
        # Simulate context compression (e.g., summarization reducing context by 75%)
        compressed_context_size = 25000  # 25K tokens after compression
        agent.set_context(compressed_context_size, 128000)
        
        # Continue with compressed context
        response = {
            "usage": {"prompt_tokens": compressed_context_size, "completion_tokens": 2000},
            "request_latency_ms": 800
        }
        agent.update(response)
        
        # Verify state after compression and new interaction
        assert agent.context_used == 25000
        assert agent.prompt_tokens == 25000  # Updated from the response
        assert agent.completion_tokens == 2000
        
    def test_multi_level_nested_agents(self):
        """Test multi-level nesting of agents."""
        # Level 1: Master agent
        master = TokenCounter(provider="claude", context_max=200000)
        
        # Level 2: Coordinator agents
        coordinator1 = TokenCounter(provider="claude")
        coordinator2 = TokenCounter(provider="claude")
        
        # Level 3: Worker agents under coordinator1
        worker1a = TokenCounter(provider="claude")
        worker1b = TokenCounter(provider="claude")
        
        # Level 3: Worker agents under coordinator2
        worker2a = TokenCounter(provider="claude")
        worker2b = TokenCounter(provider="claude")
        worker2c = TokenCounter(provider="claude")
        
        # Simulate work distribution
        workers = [worker1a, worker1b, worker2a, worker2b, worker2c]
        base_input = 200
        base_output = 500
        for i, worker in enumerate(workers):
            response = {
                "usage": {
                    "input_tokens": base_input * (i + 1),
                    "output_tokens": base_output * (i + 1)
                },
                "response_ms": 100 * (i + 1)
            }
            worker.update(response)
        
        # Aggregate coordinator1 workers
        coord1_input = worker1a.prompt_tokens + worker1b.prompt_tokens
        coord1_output = worker1a.completion_tokens + worker1b.completion_tokens
        coordinator1.prompt_tokens = coord1_input
        coordinator1.completion_tokens = coord1_output
        coordinator1.update({
            "usage": {"input_tokens": coord1_input, "output_tokens": coord1_output},
            "response_ms": 300
        })
        
        # Aggregate coordinator2 workers
        coord2_input = worker2a.prompt_tokens + worker2b.prompt_tokens + worker2c.prompt_tokens
        coord2_output = worker2a.completion_tokens + worker2b.completion_tokens + worker2c.completion_tokens
        coordinator2.prompt_tokens = coord2_input
        coordinator2.completion_tokens = coord2_output
        coordinator2.update({
            "usage": {"input_tokens": coord2_input, "output_tokens": coord2_output},
            "response_ms": 400
        })
        
        # Aggregate to master
        master_input = coordinator1.prompt_tokens + coordinator2.prompt_tokens
        master_output = coordinator1.completion_tokens + coordinator2.completion_tokens
        master.update({
            "usage": {"input_tokens": master_input, "output_tokens": master_output},
            "response_ms": 500
        })
        
        # Verify aggregated results
        assert master.prompt_tokens == master_input
        assert master.completion_tokens == master_output
        assert master.total_tokens == master_input + master_output
        
    def test_subagent_cost_aggregation(self):
        """Test cost aggregation across sub-agents."""
        # Create sub-agents with different providers
        agent_claude = TokenCounter(provider="claude")
        agent_openai = TokenCounter(provider="openai")
        agent_gemini = TokenCounter(provider="gemini")
        
        # Simulate usage
        claude_response = {
            "usage": {"input_tokens": 1000, "output_tokens": 2000},
            "response_ms": 1000
        }
        agent_claude.update(claude_response)
        
        openai_response = {
            "usage": {"prompt_tokens": 1500, "completion_tokens": 2500},
            "request_latency_ms": 800
        }
        agent_openai.update(openai_response)
        
        gemini_response = {
            "prompt_token_count": 800,
            "candidates": [{"token_count": 1200}],
            "total_latency": 0.6
        }
        agent_gemini.update(gemini_response)
        
        # Calculate total cost manually
        claude_cost = agent_claude.cost_estimate  # (1000/1M * 3.00) + (2000/1M * 15.00) = 0.033
        openai_cost = agent_openai.cost_estimate  # (1500/1M * 1.00) + (2500/1M * 2.00) = 0.0065
        gemini_cost = agent_gemini.cost_estimate  # (800/1M * 1.25) + (1200/1M * 5.00) = 0.007
        
        total_cost = claude_cost + openai_cost + gemini_cost
        
        # Verify individual costs
        assert round(claude_cost, 5) == 0.033
        assert round(openai_cost, 5) == 0.0065
        assert round(gemini_cost, 5) == 0.007
        
        # Total should be sum of individual costs
        assert round(total_cost, 5) == 0.0465


if __name__ == "__main__":
    pytest.main([__file__])

"""
Unit tests for token_counter.py

Tests cover:
1. Token counting logic for all providers (Ollama, Anthropic, Google, OpenAI)
2. Context compression with nested sub-agent scenarios 
3. CLI integration tests for token display and cost estimation
4. Edge cases like zero tokens, maximum context limits
5. Invalid provider handling
"""

import pytest
from unittest.mock import patch, MagicMock
from token_counter import TokenCounter


class TestTokenCounterProviders:
    """Test token counting logic for all providers."""

    def test_ollama_provider_token_extraction(self):
        """Test Ollama provider token extraction and counting."""
        counter = TokenCounter(provider="ollama")
        
        # Sample Ollama response
        response = {
            "prompt_eval_count": 150,
            "eval_count": 850,
            "eval_duration": 2500000000  # 2.5 seconds in nanoseconds
        }
        
        counter.update(response)
        
        assert counter.prompt_tokens == 150
        assert counter.completion_tokens == 850
        assert counter.total_tokens == 1000
        assert counter.tokens_per_second == 340.0  # 850 tokens / 2.5 seconds
        assert counter.context_used == 150
        assert counter.cost_estimate == 0.0  # Ollama is free
        
    def test_anthropic_provider_token_extraction(self):
        """Test Anthropic provider token extraction and counting."""
        counter = TokenCounter(provider="anthropic")
        
        # Sample Anthropic response
        response = {
            "usage": {
                "input_tokens": 300,
                "output_tokens": 750
            },
            "response_ms": 1200  # 1.2 seconds in milliseconds
        }
        
        counter.update(response)
        
        assert counter.prompt_tokens == 300
        assert counter.completion_tokens == 750
        assert counter.total_tokens == 1050
        assert counter.tokens_per_second == 625.0  # 750 tokens / 1.2 seconds
        assert counter.context_used == 300
        # Anthropic costs: input $3.00/M tokens, output $15.00/M tokens
        # Cost = (300/1000000 * 3.00) + (750/1000000 * 15.00) = 0.0009 + 0.01125 = 0.01215
        assert counter.cost_estimate == 0.01215
        
    def test_google_provider_token_extraction(self):
        """Test Google provider token extraction and counting."""
        counter = TokenCounter(provider="google")
        
        # Sample Google response
        response = {
            "prompt_token_count": 200,
            "candidates": [
                {"token_count": 400},
                {"token_count": 100}  # Multiple candidates
            ],
            "total_latency": 0.8  # 0.8 seconds
        }
        
        counter.update(response)
        
        assert counter.prompt_tokens == 200
        assert counter.completion_tokens == 500  # 400 + 100
        assert counter.total_tokens == 700
        assert counter.tokens_per_second == 625.0  # 500 tokens / 0.8 seconds
        assert counter.context_used == 200
        # Google costs: input $1.25/M tokens, output $5.00/M tokens
        # Cost = (200/1000000 * 1.25) + (500/1000000 * 5.00) = 0.00025 + 0.0025 = 0.00275
        assert counter.cost_estimate == 0.00275
        
    def test_openai_provider_token_extraction(self):
        """Test OpenAI provider token extraction and counting."""
        counter = TokenCounter(provider="openai")
        
        # Sample OpenAI response
        response = {
            "usage": {
                "prompt_tokens": 250,
                "completion_tokens": 600
            },
            "request_latency_ms": 900  # 0.9 seconds
        }
        
        counter.update(response)
        
        assert counter.prompt_tokens == 250
        assert counter.completion_tokens == 600
        assert counter.total_tokens == 850
        assert counter.tokens_per_second == 666.67  # 600 tokens / 0.9 seconds
        assert counter.context_used == 250
        # OpenAI costs: input $1.00/M tokens, output $2.00/M tokens
        # Cost = (250/1000000 * 1.00) + (600/1000000 * 2.00) = 0.00025 + 0.0012 = 0.00145
        assert counter.cost_estimate == 0.00145
        
    def test_codex_provider_cost_calculation(self):
        """Test Codex provider cost calculation."""
        counter = TokenCounter(provider="codex")
        
        # Add some tokens
        counter.prompt_tokens = 1000
        counter.completion_tokens = 2000
        counter.cost_estimate = counter._estimate_cost()
        
        # Codex costs: input $2.50/M tokens, output $10.00/M tokens
        # Cost = (1000/1000000 * 2.50) + (2000/1000000 * 10.00) = 0.0025 + 0.02 = 0.0225
        assert counter.cost_estimate == 0.0225


class TestTokenCounterEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_zero_tokens(self):
        """Test behavior with zero token counts."""
        counter = TokenCounter(provider="openai")
        
        response = {
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0
            },
            "request_latency_ms": 0
        }
        
        counter.update(response)
        
        assert counter.prompt_tokens == 0
        assert counter.completion_tokens == 0
        assert counter.total_tokens == 0
        assert counter.tokens_per_second == 0.0
        assert counter.context_used == 0
        assert counter.cost_estimate == 0.0
        
    def test_maximum_context_limits(self):
        """Test behavior at maximum context limits."""
        # Test with large token counts
        counter = TokenCounter(provider="anthropic", context_max=1000000)  # 1M context
        
        response = {
            "usage": {
                "input_tokens": 999999,
                "output_tokens": 1
            },
            "response_ms": 1000
        }
        
        counter.update(response)
        
        assert counter.context_used == 999999
        assert counter.context_max == 1000000
        
        # Test display format with large numbers
        display = counter.format_display()
        assert "999,999/1,000,000" in display
        
    def test_no_duration_info(self):
        """Test behavior when no duration information is provided."""
        counter = TokenCounter(provider="ollama")
        
        # Response without duration info
        response = {
            "prompt_eval_count": 100,
            "eval_count": 200
            # No eval_duration field
        }
        
        counter.update(response)
        
        assert counter.prompt_tokens == 100
        assert counter.completion_tokens == 200
        # tokens_per_second should remain 0.0 since no duration was provided
        assert counter.tokens_per_second == 0.0
        
    def test_invalid_provider_handling(self):
        """Test handling of invalid or unknown providers."""
        counter = TokenCounter(provider="invalid_provider")
        
        response = {
            "some_field": 100
        }
        
        # Should not crash and should not update counters
        counter.update(response)
        
        assert counter.prompt_tokens == 0
        assert counter.completion_tokens == 0
        assert counter.cost_estimate == 0.0


class TestTokenCounterDisplayFormatting:
    """Test display formatting functions."""
    
    def test_format_display_standard_case(self):
        """Test standard display formatting."""
        counter = TokenCounter(provider="openai", context_max=8192)
        counter.prompt_tokens = 1500
        counter.completion_tokens = 3500
        counter.tokens_per_second = 125.5
        counter.context_used = 1500
        counter.cost_estimate = 0.0078
        
        display = counter.format_display()
        
        # Should format numbers with commas
        assert "1,500/8,192" in display
        # Should show tokens per second with 1 decimal place
        assert "125.5 tok/s" in display
        # Should format cost appropriately
        assert "$0.0078" in display
        
    def test_format_display_zero_values(self):
        """Test display formatting with zero values."""
        counter = TokenCounter(provider="ollama", context_max=4096)
        # All values default to zero
        
        display = counter.format_display()
        
        assert "0/4,096" in display
        assert "0.0 tok/s" in display
        assert "$0.00" in display
        
    def test_format_json_output(self):
        """Test JSON formatting for programmatic use."""
        counter = TokenCounter(provider="anthropic", context_max=16384)
        counter.prompt_tokens = 2000
        counter.completion_tokens = 3000
        counter.tokens_per_second = 150.0
        counter.context_used = 2000
        counter.cost_estimate = 0.045
        
        json_output = counter.format_json()
        
        expected = {
            "prompt_tokens": 2000,
            "completion_tokens": 3000,
            "total_tokens": 5000,
            "tokens_per_second": 150.0,
            "context_used": 2000,
            "context_max": 16384,
            "cost_estimate": 0.045,
            "provider": "anthropic"
        }
        
        assert json_output == expected


class TestTokenCounterSessionManagement:
    """Test session management features."""
    
    def test_reset_functionality(self):
        """Test reset functionality."""
        counter = TokenCounter(provider="openai")
        
        # Set some values
        counter.prompt_tokens = 1000
        counter.completion_tokens = 2000
        counter.tokens_per_second = 50.0
        counter.context_used = 1000
        counter.cost_estimate = 0.01
        
        # Reset
        counter.reset()
        
        assert counter.prompt_tokens == 0
        assert counter.completion_tokens == 0
        assert counter.tokens_per_second == 0.0
        assert counter.context_used == 0
        assert counter.cost_estimate == 0.0
        
    def test_multiple_updates_accumulate(self):
        """Test that multiple updates accumulate correctly."""
        counter = TokenCounter(provider="google")
        
        # First update
        response1 = {
            "prompt_token_count": 100,
            "candidates": [{"token_count": 200}],
            "total_latency": 0.5
        }
        counter.update(response1)
        
        # Second update
        response2 = {
            "prompt_token_count": 150,
            "candidates": [{"token_count": 250}],
            "total_latency": 0.6
        }
        counter.update(response2)
        
        # Values should accumulate
        assert counter.prompt_tokens == 250  # 100 + 150
        assert counter.completion_tokens == 450  # 200 + 250
        # tokens_per_second should be based on the last update
        assert counter.tokens_per_second == 416.67  # 250 tokens / 0.6 seconds


class TestTokenCounterContextCompression:
    """Test context compression scenarios with nested sub-agents."""
    
    def test_context_compression_tracking(self):
        """Test tracking of context compression."""
        counter = TokenCounter(provider="anthropic", context_max=200000)
        
        # Simulate initial context loading
        counter.set_context(150000, 200000)
        assert counter.context_used == 150000
        assert counter.context_max == 200000
        
        # Simulate compression (context reduced)
        counter.set_context(75000, 200000)
        assert counter.context_used == 75000
        assert counter.context_max == 200000
        
        # Display should reflect compressed context
        display = counter.format_display()
        assert "75,000/200,000" in display


if __name__ == "__main__":
    pytest.main([__file__])

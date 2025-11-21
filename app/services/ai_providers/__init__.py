"""
AI Provider Modules

This package contains pluggable AI provider implementations for the KIVI system.
Each provider module implements the same interface for easy swapping.

Available Providers:
- OpenAI (GPT-3.5-turbo, GPT-4)
- Anthropic (Claude 3 Haiku, Sonnet, Opus)

Usage:
    from app.services.ai_providers.openai_provider import call_openai
    from app.services.ai_providers.anthropic_provider import call_anthropic
    
    response = await call_openai("What is my spending?")
    response = await call_anthropic("How can I save more?")
"""

from app.services.ai_providers.openai_provider import call_openai
from app.services.ai_providers.anthropic_provider import call_anthropic

__all__ = ["call_openai", "call_anthropic"]

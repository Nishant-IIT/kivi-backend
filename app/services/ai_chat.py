"""
AI Chat Service Module

Purpose:
    Core chat function that serves both WhatsApp and mobile app channels.
    Builds prompts with user metadata context and routes to appropriate AI provider.
    Provides single-use conversational AI functionality.

Dependencies:
    - app.services.ai_providers.openai_provider: OpenAI integration
    - app.services.ai_providers.anthropic_provider: Anthropic integration
    - app.config.logging_config: Logging utilities
    - time: Latency measurement

Usage:
    from app.services.ai_chat import chat_with_model
    
    metadata = {
        "name": "Rahul",
        "job": "Delivery Partner",
        "gig_platforms": ["Swiggy", "Zomato"],
        "goals": [{"name": "Emergency Fund", "target_amount": 30000}],
        "transaction_summary": {"monthly_spending": 22000, "balance": 12000}
    }
    
    response = await chat_with_model(metadata, "How much did I spend on food?", "openai")
    print(response["reply"])

Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 3.5
"""

import time
import json
from typing import Dict, Any, Optional
from app.services.ai_providers.openai_provider import call_openai
from app.services.ai_providers.anthropic_provider import call_anthropic
from app.config.logging_config import ai_logger


async def chat_with_model(
    metadata: Dict[str, Any],
    message: str,
    provider: str = "openai"
) -> Dict[str, Any]:
    """
    Single-use chat function for conversational AI responses.
    
    Builds a prompt with serialized user metadata including name, job, gig_platforms,
    goals, and transaction_summary. Routes to the specified AI provider and logs
    the interaction with latency metrics.
    
    Args:
        metadata: User context dictionary containing:
            - name (str): User's name
            - job (str, optional): User's occupation (e.g., "Delivery Partner")
            - gig_platforms (list, optional): List of gig platforms user works on
            - goals (list, optional): List of financial goals
            - transaction_summary (dict, optional): Summary of recent transactions
            - balance (float, optional): Current account balance
            - monthly_income (float, optional): Average monthly income
            - monthly_expenses (float, optional): Average monthly expenses
        message: User's message text
        provider: AI provider to use ("openai" or "anthropic"), defaults to "openai"
    
    Returns:
        dict: Response dictionary containing:
            - reply (str): AI-generated response text
            - provider (str): Name of the provider used
            - usage (dict): Usage statistics placeholder
    
    Raises:
        ValueError: If provider is not supported
        Exception: If AI provider call fails
    """
    ai_logger.debug(f"chat_with_model invoked with provider={provider}, message_length={len(message)}")
    
    # Validate provider
    if provider not in ["openai", "anthropic"]:
        ai_logger.error(f"Unsupported provider: {provider}")
        raise ValueError(f"Unsupported provider: {provider}. Must be 'openai' or 'anthropic'")
    
    # Build prompt with user metadata context
    prompt = _build_prompt_with_context(metadata, message)
    
    # Log the full prompt at DEBUG level
    ai_logger.debug(f"Built prompt for {provider}:\n{prompt}")
    
    # Start latency timer
    start_time = time.time()
    
    try:
        # Route to appropriate AI provider
        if provider == "openai":
            ai_logger.info(f"Routing to OpenAI provider for user message")
            response_text = await call_openai(prompt)
        elif provider == "anthropic":
            ai_logger.info(f"Routing to Anthropic provider for user message")
            response_text = await call_anthropic(prompt)
        else:
            # Should not reach here due to validation above
            raise ValueError(f"Provider {provider} not implemented")
        
        # Calculate latency
        latency_ms = int((time.time() - start_time) * 1000)
        
        # Log response at INFO level with latency
        response_preview = response_text[:100] + "..." if len(response_text) > 100 else response_text
        ai_logger.info(
            f"Response from {provider} (latency: {latency_ms}ms): {response_preview}"
        )
        
        # Return structured response
        return {
            "reply": response_text,
            "provider": provider,
            "usage": {
                "latency_ms": latency_ms,
                "prompt_length": len(prompt),
                "response_length": len(response_text)
            }
        }
        
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        ai_logger.error(
            f"AI provider {provider} failed after {latency_ms}ms: {str(e)}",
            exc_info=True
        )
        raise


def _build_prompt_with_context(metadata: Dict[str, Any], message: str) -> str:
    """
    Build a prompt with serialized user metadata context.
    
    Constructs a comprehensive prompt that includes user profile information,
    financial context, and the user's message. This provides the AI with
    necessary context to give personalized responses.
    
    Args:
        metadata: User context dictionary
        message: User's message text
    
    Returns:
        str: Formatted prompt with context and user message
    """
    # Extract metadata fields with safe defaults
    name = metadata.get("name", "User")
    job = metadata.get("job", "")
    gig_platforms = metadata.get("gig_platforms", [])
    goals = metadata.get("goals", [])
    transaction_summary = metadata.get("transaction_summary", {})
    
    # Build context sections
    context_parts = []
    
    # User profile section
    profile_info = f"User: {name}"
    if job:
        profile_info += f", Occupation: {job}"
    context_parts.append(profile_info)
    
    # Gig platforms section
    if gig_platforms:
        platforms_str = ", ".join(gig_platforms)
        context_parts.append(f"Gig Platforms: {platforms_str}")
    
    # Financial summary section
    if transaction_summary:
        financial_info = []
        
        if "balance" in transaction_summary:
            financial_info.append(f"Current Balance: ₹{transaction_summary['balance']:,.2f}")
        
        if "monthly_income" in transaction_summary or "avg_monthly_income" in transaction_summary:
            income = transaction_summary.get("monthly_income") or transaction_summary.get("avg_monthly_income")
            financial_info.append(f"Monthly Income: ₹{income:,.2f}")
        
        if "monthly_expenses" in transaction_summary or "monthly_spending" in transaction_summary:
            expenses = transaction_summary.get("monthly_expenses") or transaction_summary.get("monthly_spending")
            financial_info.append(f"Monthly Expenses: ₹{expenses:,.2f}")
        
        if "income_volatility" in transaction_summary:
            financial_info.append(f"Income Volatility: {transaction_summary['income_volatility']}")
        
        if "last_30_days_income" in transaction_summary:
            financial_info.append(f"Last 30 Days Income: ₹{transaction_summary['last_30_days_income']:,.2f}")
        
        if "income_sources" in transaction_summary:
            sources = transaction_summary["income_sources"]
            sources_str = ", ".join([f"{k}: ₹{v:,.2f}" for k, v in sources.items()])
            financial_info.append(f"Income Sources: {sources_str}")
        
        if financial_info:
            context_parts.append("Financial Summary: " + "; ".join(financial_info))
    
    # Goals section
    if goals:
        goals_info = []
        for goal in goals[:3]:  # Limit to top 3 goals to keep prompt concise
            goal_name = goal.get("name", "Unnamed Goal")
            target = goal.get("target_amount", 0)
            current = goal.get("current_amount", 0)
            goals_info.append(f"{goal_name} (₹{current:,.0f}/₹{target:,.0f})")
        
        if goals_info:
            context_parts.append("Financial Goals: " + "; ".join(goals_info))
    
    # Combine all context
    context = "\n".join(context_parts)
    
    # Build final prompt
    prompt = f"""You are KIVI, a helpful financial assistant for gig workers in India. You help users track expenses, manage budgets, and provide financial guidance tailored to the unique challenges of gig economy workers with irregular income streams.

User Context:
{context}

User Message: {message}

Provide a helpful, conversational response that addresses the user's question using the context provided. Be supportive, actionable, and use Indian Rupees (₹) for currency. Keep responses concise and focused."""
    
    return prompt


# Example usage (commented out)
"""
import asyncio

async def example_usage():
    # Example metadata for a gig worker
    metadata = {
        "name": "Rahul Sharma",
        "job": "Delivery Partner",
        "gig_platforms": ["Swiggy", "Zomato", "Dunzo"],
        "transaction_summary": {
            "balance": 12000.00,
            "avg_monthly_income": 28000.00,
            "monthly_spending": 22000.00,
            "income_volatility": "high",
            "last_30_days_income": 31500.00,
            "income_sources": {
                "Swiggy": 18000.00,
                "Zomato": 10500.00,
                "Dunzo": 3000.00
            }
        },
        "goals": [
            {
                "name": "Emergency Fund",
                "target_amount": 30000.00,
                "current_amount": 12000.00
            },
            {
                "name": "Bike EMI Buffer",
                "target_amount": 15000.00,
                "current_amount": 5000.00
            }
        ]
    }
    
    # Test with OpenAI
    response = await chat_with_model(
        metadata=metadata,
        message="How much did I spend on food this month?",
        provider="openai"
    )
    print(f"OpenAI Response: {response['reply']}")
    print(f"Latency: {response['usage']['latency_ms']}ms")
    
    # Test with Anthropic
    response = await chat_with_model(
        metadata=metadata,
        message="Should I save more money?",
        provider="anthropic"
    )
    print(f"Anthropic Response: {response['reply']}")
    print(f"Latency: {response['usage']['latency_ms']}ms")

if __name__ == "__main__":
    asyncio.run(example_usage())
"""

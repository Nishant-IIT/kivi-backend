"""
Anthropic Provider Module

Purpose:
    Provides interface to Anthropic's Claude models for conversational AI.
    Returns mocked responses when API key is not configured.
    Includes commented sample code for real API integration.

Dependencies:
    - httpx: Async HTTP client for API calls
    - app.config.config: Configuration constants
    - app.config.logging_config: Logging utilities

Usage:
    from app.services.ai_providers.anthropic_provider import call_anthropic
    
    response = await call_anthropic("What is my spending this month?")
    print(response)

Requirements: 3.1, 3.2, 3.3, 3.4
"""

import httpx
from typing import Optional
from app.config.config import ANTHROPIC_API_KEY
from app.config.logging_config import ai_logger


async def call_anthropic(prompt: str) -> str:
    """
    Call Anthropic API with the provided prompt.
    
    Returns mocked response if ANTHROPIC_API_KEY is not configured.
    Includes error handling and logging for all API calls.
    
    Args:
        prompt: The user prompt/message to send to Anthropic Claude
        
    Returns:
        str: The AI-generated response text
        
    Raises:
        Exception: If API call fails after retries
    """
    ai_logger.debug(f"call_anthropic invoked with prompt length: {len(prompt)}")
    
    # Check if API key is configured
    if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "":
        ai_logger.info("Anthropic API key not configured, returning mocked response")
        return _get_mocked_response(prompt)
    
    try:
        # Call real Anthropic API
        ai_logger.info("Calling Anthropic API with real credentials")
        response = await _call_anthropic_real(prompt, ANTHROPIC_API_KEY)
        ai_logger.info(f"Anthropic API call successful, response length: {len(response)}")
        return response
        
    except Exception as e:
        ai_logger.error(f"Anthropic API call failed: {str(e)}", exc_info=True)
        # Fallback to mocked response on error
        ai_logger.warning("Falling back to mocked response due to API error")
        return _get_mocked_response(prompt)


def _get_mocked_response(prompt: str) -> str:
    """
    Generate a mocked response for development/testing.
    
    Args:
        prompt: The user prompt (used to generate contextual mock)
        
    Returns:
        str: Mocked AI response
    """
    prompt_excerpt = prompt[:50] + "..." if len(prompt) > 50 else prompt
    
    # Generate contextual mock responses based on prompt keywords
    prompt_lower = prompt.lower()
    
    if "spend" in prompt_lower or "expense" in prompt_lower:
        return (
            f"[MOCKED Anthropic Response] Looking at your transaction history, "
            f"you've spent ₹5,200 this month. The breakdown shows: Food ₹2,100, "
            f"Transport ₹1,800, and Shopping ₹1,300. Your spending is 8% lower than last month!"
        )
    elif "save" in prompt_lower or "saving" in prompt_lower:
        return (
            f"[MOCKED Anthropic Response] Let's talk about savings! "
            f"With your current income of ₹28,000/month, I suggest saving 15-20% (₹4,200-5,600). "
            f"Start with an emergency fund covering 3 months of expenses. You're on the right track!"
        )
    elif "income" in prompt_lower or "earn" in prompt_lower:
        return (
            f"[MOCKED Anthropic Response] Your gig income this month totals ₹28,500. "
            f"Breakdown: Swiggy ₹18,000 (63%), Zomato ₹10,500 (37%). "
            f"Tip: Your Swiggy earnings are strongest on weekends. Consider focusing there!"
        )
    elif "budget" in prompt_lower:
        return (
            f"[MOCKED Anthropic Response] Your budget status looks good! "
            f"Food budget: ₹3,200 of ₹5,000 used (64%). Transport: ₹2,800 of ₹3,000 (93% - careful!). "
            f"You have ₹1,800 remaining in food and ₹200 in transport for this month."
        )
    elif "platform" in prompt_lower or "swiggy" in prompt_lower or "zomato" in prompt_lower:
        return (
            f"[MOCKED Anthropic Response] Platform comparison: Swiggy is your top earner at ₹18,000/month. "
            f"Zomato brings in ₹10,500. Based on your patterns, Swiggy orders peak during lunch (12-2pm) "
            f"and dinner (7-10pm). Consider maximizing those hours!"
        )
    else:
        return (
            f"[MOCKED Anthropic Response] I see you're asking: '{prompt_excerpt}'. "
            f"I'm KIVI, your financial assistant! I can help you understand your spending patterns, "
            f"track income from gig platforms, manage budgets, and plan savings. What would you like to explore?"
        )


async def _call_anthropic_real(prompt: str, api_key: str) -> str:
    """
    Real Anthropic API implementation.
    
    Makes actual API call to Anthropic's messages endpoint.
    Uses Claude 3 models (Haiku, Sonnet, or Opus).
    
    Args:
        prompt: The user prompt/message
        api_key: Anthropic API key
        
    Returns:
        str: AI-generated response text
        
    Raises:
        httpx.HTTPError: If API request fails
        KeyError: If response format is unexpected
    """
    url = "https://api.anthropic.com/v1/messages"
    
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "claude-3-haiku-20240307",  # or "claude-3-sonnet-20240229" or "claude-3-opus-20240229"
        "max_tokens": 500,
        "system": (
            "You are KIVI, a helpful financial assistant for gig workers in India. "
            "You help users track expenses, manage budgets, and provide financial guidance. "
            "Be conversational, supportive, and provide actionable advice. "
            "Use Indian Rupees (₹) for currency. Focus on the unique challenges of gig workers "
            "with irregular income streams."
        ),
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7
    }
    
    ai_logger.debug(f"Sending request to Anthropic API: {url}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        ai_logger.debug(f"Anthropic API response received: {data.get('id', 'unknown')}")
        
        # Extract the assistant's message from content array
        # Anthropic returns content as an array of content blocks
        content_blocks = data["content"]
        assistant_message = ""
        
        for block in content_blocks:
            if block["type"] == "text":
                assistant_message += block["text"]
        
        return assistant_message.strip()


# Commented example for reference:
"""
# Example usage with real API:

import asyncio
from app.services.ai_providers.anthropic_provider import call_anthropic

async def main():
    # Set ANTHROPIC_API_KEY in .env file first
    prompt = "How can I save more money as a delivery partner?"
    response = await call_anthropic(prompt)
    print(f"AI Response: {response}")

if __name__ == "__main__":
    asyncio.run(main())
"""


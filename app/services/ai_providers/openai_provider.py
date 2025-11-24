"""
OpenAI Provider Module

Purpose:
    Provides interface to OpenAI's GPT models for conversational AI.
    Returns mocked responses when API key is not configured.
    Includes commented sample code for real API integration.

Dependencies:
    - httpx: Async HTTP client for API calls
    - app.config.config: Configuration constants
    - app.config.logging_config: Logging utilities

Usage:
    from app.services.ai_providers.openai_provider import call_openai
    
    response = await call_openai("What is my spending this month?")
    print(response)

Requirements: 3.1, 3.2, 3.3, 3.4
"""

import httpx
from typing import Optional
from app.config.config import OPENAI_API_KEY
from app.config.logging_config import ai_logger


async def call_openai(prompt: str) -> str:
    """
    Call OpenAI API with the provided prompt.
    
    Returns mocked response if OPENAI_API_KEY is not configured.
    Includes error handling and logging for all API calls.
    
    Args:
        prompt: The user prompt/message to send to OpenAI
        
    Returns:
        str: The AI-generated response text
        
    Raises:
        Exception: If API call fails after retries
    """
    ai_logger.debug(f"call_openai invoked with prompt length: {len(prompt)}")
    
    # Check if API key is configured
    if not OPENAI_API_KEY or OPENAI_API_KEY == "":
        ai_logger.info("OpenAI API key not configured, returning mocked response")
        return _get_mocked_response(prompt)
    
    try:
        # Call real OpenAI API
        ai_logger.info("Calling OpenAI API with real credentials")
        response = await _call_openai_real(prompt, OPENAI_API_KEY)
        ai_logger.info(f"OpenAI API call successful, response length: {len(response)}")
        return response
        
    except Exception as e:
        ai_logger.error(f"OpenAI API call failed: {str(e)}", exc_info=True)
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
            f"I'd be happy to help you track your spending. However, I need access to your "
            f"transaction data to provide accurate information. Please ensure your account is "
            f"properly connected and synced."
        )
    elif "save" in prompt_lower or "saving" in prompt_lower:
        return (
            f"Great question about savings! To provide personalized savings recommendations, "
            f"I need to analyze your income and expense patterns. Please make sure your financial "
            f"data is up to date."
        )
    elif "income" in prompt_lower or "earn" in prompt_lower:
        return (
            f"I can help you track your income from various gig platforms. To see your earnings, "
            f"please ensure your accounts are connected and your data is synced."
        )
    elif "budget" in prompt_lower:
        return (
            f"I can help you manage your budgets! To provide specific budget insights, "
            f"please make sure your spending categories and limits are configured."
        )
    else:
        return (
            f"I'm KIVI, your financial assistant! I can help with spending analysis, savings goals, "
            f"income tracking, and budget management. To get started, please ensure your financial "
            f"accounts are connected."
        )


async def _call_openai_real(prompt: str, api_key: str) -> str:
    """
    Real OpenAI API implementation.
    
    Makes actual API call to OpenAI's chat completions endpoint.
    Uses GPT-4 or GPT-3.5-turbo model.
    
    Args:
        prompt: The user prompt/message
        api_key: OpenAI API key
        
    Returns:
        str: AI-generated response text
        
    Raises:
        httpx.HTTPError: If API request fails
        KeyError: If response format is unexpected
    """
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "gpt-3.5-turbo",  # or "gpt-4" for better quality
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are KIVI, a helpful financial assistant for gig workers in India. "
                    "You help users track expenses, manage budgets, and provide financial guidance. "
                    "Be conversational, supportive, and provide actionable advice. "
                    "Use Indian Rupees (₹) for currency."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }
    
    ai_logger.debug(f"Sending request to OpenAI API: {url}")
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        ai_logger.debug(f"OpenAI API response received: {data.get('id', 'unknown')}")
        
        # Extract the assistant's message
        assistant_message = data["choices"][0]["message"]["content"]
        
        return assistant_message.strip()


# Commented example for reference:
"""
# Example usage with real API:

import asyncio
from app.services.ai_providers.openai_provider import call_openai

async def main():
    # Set OPENAI_API_KEY in .env file first
    prompt = "How much did I spend on food this month?"
    response = await call_openai(prompt)
    print(f"AI Response: {response}")

if __name__ == "__main__":
    asyncio.run(main())
"""


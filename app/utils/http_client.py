"""
Async HTTP client with retry logic.

This module provides an async HTTP client wrapper using httpx with built-in
retry logic, exponential backoff, and comprehensive logging for API calls.

Dependencies:
    - httpx (async HTTP client)
    - asyncio (standard library)
    - logging (standard library)

Example Usage:
    from app.utils.http_client import make_request
    
    # GET request
    response = await make_request("GET", "https://api.example.com/users")
    
    # POST request with JSON body
    response = await make_request(
        "POST",
        "https://api.example.com/users",
        headers={"Authorization": "Bearer token"},
        json={"name": "Rahul", "phone": "+919876543210"}
    )
    
    # With custom retry count
    response = await make_request(
        "GET",
        "https://api.example.com/data",
        retries=5
    )
"""

import asyncio
import logging
from typing import Optional, Dict, Any

try:
    import httpx
except ImportError:
    httpx = None

logger = logging.getLogger("kivi.http")


async def make_request(
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    json: Optional[Dict[str, Any]] = None,
    retries: int = 3,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Make async HTTP request with retry logic and exponential backoff.
    
    Args:
        method: HTTP method (GET, POST, PUT, DELETE, etc.)
        url: Target URL
        headers: Optional request headers
        json: Optional JSON request body
        retries: Maximum number of retry attempts (default: 3)
        timeout: Request timeout in seconds (default: 30.0)
    
    Returns:
        Dictionary containing response data:
            {
                "status_code": int,
                "data": dict or str,
                "headers": dict
            }
    
    Raises:
        Exception: If all retry attempts fail or httpx is not installed
    
    Example:
        >>> response = await make_request("GET", "https://api.example.com/data")
        >>> print(response["status_code"])
        200
        >>> print(response["data"])
        {"result": "success"}
    """
    if httpx is None:
        raise ImportError("httpx is required for HTTP client. Install with: pip install httpx")
    
    last_exception = None
    
    for attempt in range(retries):
        try:
            logger.debug(f"HTTP {method} {url} (attempt {attempt + 1}/{retries})")
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=json
                )
                
                # Log response
                logger.info(
                    f"HTTP {method} {url} -> {response.status_code} "
                    f"(attempt {attempt + 1}/{retries})"
                )
                
                # Check for server errors (5xx) - these should be retried
                if response.status_code >= 500:
                    logger.warning(
                        f"Server error {response.status_code} from {url}, "
                        f"will retry if attempts remain"
                    )
                    last_exception = Exception(
                        f"Server error: {response.status_code}"
                    )
                    
                    # Exponential backoff before retry
                    if attempt < retries - 1:
                        backoff_time = 2 ** attempt  # 1s, 2s, 4s, etc.
                        logger.debug(f"Backing off for {backoff_time}s before retry")
                        await asyncio.sleep(backoff_time)
                        continue
                
                # Parse response body
                try:
                    response_data = response.json()
                except Exception:
                    response_data = response.text
                
                return {
                    "status_code": response.status_code,
                    "data": response_data,
                    "headers": dict(response.headers)
                }
        
        except httpx.TimeoutException as e:
            logger.warning(f"Request timeout for {url} (attempt {attempt + 1}/{retries})")
            last_exception = e
            
            # Exponential backoff before retry
            if attempt < retries - 1:
                backoff_time = 2 ** attempt
                logger.debug(f"Backing off for {backoff_time}s before retry")
                await asyncio.sleep(backoff_time)
        
        except httpx.RequestError as e:
            logger.warning(
                f"Request error for {url}: {str(e)} (attempt {attempt + 1}/{retries})"
            )
            last_exception = e
            
            # Exponential backoff before retry
            if attempt < retries - 1:
                backoff_time = 2 ** attempt
                logger.debug(f"Backing off for {backoff_time}s before retry")
                await asyncio.sleep(backoff_time)
        
        except Exception as e:
            logger.error(f"Unexpected error for {url}: {str(e)}", exc_info=True)
            last_exception = e
            
            # Don't retry on unexpected errors
            break
    
    # All retries exhausted
    error_msg = f"All {retries} retry attempts failed for {method} {url}"
    if last_exception:
        error_msg += f": {str(last_exception)}"
    
    logger.error(error_msg)
    raise Exception(error_msg)

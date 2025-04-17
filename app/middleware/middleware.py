from fastapi import Request
import time
import logging
from typing import Callable
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def log_requests_middleware(request: Request, call_next: Callable):
    """
    Middleware to log all requests with timing information
    """
    start_time = time.time()
    
    # Get request body if it exists
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        try:
            body = await request.json()
        except Exception:
            body = None

    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    
    # Log request details
    log_data = {
        "method": request.method,
        "path": request.url.path,
        "client_ip": request.client.host,
        "process_time": f"{process_time:.3f}s",
        "status_code": response.status_code
    }
    
    if body:
        log_data["body"] = body

    logger.info(json.dumps(log_data))
    
    return response
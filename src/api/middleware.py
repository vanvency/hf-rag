import time
import traceback
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from typing import Callable
from fastapi import HTTPException


class LoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, logger):
        super().__init__(app)
        self.logger = logger
        # Verify middleware initialization
        if logger:
            try:
                logger.debug("LoggingMiddleware initialized successfully")
            except:
                print("[MIDDLEWARE] LoggingMiddleware initialized", flush=True)

    async def dispatch(self, request: Request, call_next: Callable):
        # This method MUST be called for every request
        start = time.perf_counter()
        
        # Debug: Verify middleware is being called
        try:
            if self.logger:
                self.logger.debug(f"Middleware intercepting: {request.method} {request.url.path}")
        except:
            print(f"[MIDDLEWARE DEBUG] Intercepting: {request.method} {request.url.path}", flush=True)
        
        # Log request details
        method = request.method
        path = request.url.path
        query_params = str(request.query_params) if request.query_params else ""
        content_type = request.headers.get("content-type", "")
        client_ip = request.client.host if request.client else "unknown"
        
        # Build request info
        request_info = f"{method} {path}"
        if query_params:
            request_info += f"?{query_params}"
        
        # Add content type info for POST/PUT
        request_type = ""
        if method in ["POST", "PUT", "PATCH"]:
            if "multipart/form-data" in content_type:
                request_type = " [File Upload]"
            elif "application/json" in content_type:
                request_type = " [JSON]"
        
        request_info += request_type
        
        # Process request with error handling
        try:
            response = await call_next(request)
            elapsed = (time.perf_counter() - start) * 1000
            
            # Log response
            status_code = response.status_code
            response_size = ""
            if hasattr(response, 'headers'):
                content_length = response.headers.get('content-length')
                if content_length:
                    response_size = f", {content_length} bytes"
            
            # Build complete log message
            status_emoji = "✓" if 200 <= status_code < 300 else "✗" if status_code >= 400 else "→"
            log_msg = f"{status_emoji} {request_info} [IP: {client_ip}] - {round(elapsed, 2)}ms - {status_code}{response_size}"
            
            # Log based on status code
            if self.logger:
                try:
                    if status_code >= 500:
                        self.logger.error(log_msg)
                    elif status_code >= 400:
                        self.logger.warning(log_msg)
                    else:
                        self.logger.info(log_msg)
                except Exception as e:
                    print(f"[API] {log_msg}", flush=True)
            else:
                print(f"[API] {log_msg}", flush=True)
            
            return response
            
        except HTTPException as e:
            # Handle HTTP exceptions
            elapsed = (time.perf_counter() - start) * 1000
            log_msg = f"✗ {request_info} [IP: {client_ip}] - {round(elapsed, 2)}ms - {e.status_code} [HTTPException: {e.detail}]"
            
            if self.logger:
                try:
                    if e.status_code >= 500:
                        self.logger.error(log_msg)
                    else:
                        self.logger.warning(log_msg)
                except:
                    print(f"[API] {log_msg}", flush=True)
            else:
                print(f"[API] {log_msg}", flush=True)
            
            raise
            
        except Exception as e:
            # Handle unexpected exceptions
            elapsed = (time.perf_counter() - start) * 1000
            error_trace = traceback.format_exc()
            log_msg = f"✗ {request_info} [IP: {client_ip}] - {round(elapsed, 2)}ms - 500 [Exception: {str(e)}]"
            
            if self.logger:
                try:
                    self.logger.error(f"{log_msg}\n{error_trace}")
                except:
                    print(f"[API ERROR] {log_msg}", flush=True)
                    print(f"[TRACEBACK] {error_trace}", flush=True)
            else:
                print(f"[API ERROR] {log_msg}", flush=True)
                print(f"[TRACEBACK] {error_trace}", flush=True)
            
            raise


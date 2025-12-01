#!/usr/bin/env python
"""Direct test of logging middleware"""
import asyncio
from starlette.requests import Request
from starlette.responses import JSONResponse
from src.core.logging import configure_logging
from src.api.middleware import LoggingMiddleware
from fastapi import FastAPI

def test_middleware():
    """Test logging middleware directly"""
    # Configure logging
    logger = configure_logging()
    
    # Create a simple app
    app = FastAPI()
    
    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}
    
    # Add middleware
    app.add_middleware(LoggingMiddleware, logger=logger)
    
    # Create a test request
    from starlette.testclient import TestClient
    client = TestClient(app)
    
    print("\n" + "=" * 60)
    print("测试日志中间件")
    print("=" * 60)
    print("\n发送测试请求...\n")
    
    # Make a request
    response = client.get("/test")
    print(f"响应状态码: {response.status_code}")
    print(f"响应内容: {response.json()}")
    
    print("\n" + "=" * 60)
    print("如果上面看到日志输出，说明日志系统正常工作")
    print("=" * 60)

if __name__ == "__main__":
    test_middleware()


#!/usr/bin/env python
"""Test script to verify logging output"""
import requests
import time
import sys

def test_api_logging():
    """Test API endpoints and verify logging"""
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("测试 API 日志输出")
    print("=" * 60)
    print("\n请查看服务器终端，应该能看到以下API调用的日志：\n")
    
    # Test 1: Health check
    print("1. 测试 GET /api/health")
    try:
        response = requests.get(f"{base_url}/api/health", timeout=5)
        print(f"   ✓ 状态码: {response.status_code}")
        print(f"   ✓ 响应: {response.json()}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")
    
    time.sleep(0.5)
    
    # Test 2: List documents
    print("\n2. 测试 GET /api/documents")
    try:
        response = requests.get(f"{base_url}/api/documents", timeout=5)
        print(f"   ✓ 状态码: {response.status_code}")
        data = response.json()
        print(f"   ✓ 文档数量: {len(data.get('documents', []))}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")
    
    time.sleep(0.5)
    
    # Test 3: Get root page
    print("\n3. 测试 GET /")
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        print(f"   ✓ 状态码: {response.status_code}")
        print(f"   ✓ 内容类型: {response.headers.get('content-type', 'unknown')}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")
    
    time.sleep(0.5)
    
    # Test 4: Query endpoint (may fail if APIs not configured)
    print("\n4. 测试 POST /api/query [JSON]")
    try:
        response = requests.post(
            f"{base_url}/api/query",
            json={"query": "测试查询", "top_k": 3, "threshold": 0.0},
            timeout=10
        )
        print(f"   ✓ 状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   ✓ 结果数量: {len(data.get('results', []))}")
    except Exception as e:
        print(f"   ✗ 错误: {e}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n请检查服务器终端，应该能看到类似以下的日志输出：")
    print("  [时间] INFO     ✓ GET /api/health [IP: ...] - XXms - 200")
    print("  [时间] INFO     ✓ GET /api/documents [IP: ...] - XXms - 200")
    print("  [时间] INFO     ✓ GET / [IP: ...] - XXms - 200")
    print("  [时间] INFO     ✓ POST /api/query [JSON] [IP: ...] - XXms - 200/503")
    print("\n如果看不到日志，请检查：")
    print("  1. 服务器是否使用 --no-access-log 参数启动")
    print("  2. 或者使用 python start_server.py 启动")

if __name__ == "__main__":
    test_api_logging()


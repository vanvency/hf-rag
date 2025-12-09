#!/usr/bin/env python
"""Start server with proper logging configuration"""
import uvicorn
from src.core.logging import get_uvicorn_log_config, configure_logging

# Configure logging first
logger = configure_logging()

if __name__ == "__main__":
    # Get custom log configuration for uvicorn
    log_config = get_uvicorn_log_config()
    
    logger.info("=" * 60)
    logger.info("启动 RAG System 服务器...")
    logger.info("=" * 60)
    
    import platform
    import sys
    
    # On Windows, reload with multiprocessing can cause pickling issues
    # Use reload=False on Windows, or use uvicorn command directly with --reload
    use_reload = platform.system() != "Windows"
    
    if use_reload:
        logger.info("使用 reload 模式启动（自动重载）")
        uvicorn.run(
            "src.main:app",  # Use import string for reload
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="debug",
            access_log=False,
            log_config=log_config,
        )
    else:
        logger.info("Windows 系统：使用非 reload 模式启动")
        logger.info("提示：如需自动重载，请使用命令: uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 --no-access-log")
        uvicorn.run(
            "src.main:app",
            host="0.0.0.0",
            port=8000,
            reload=False,
            log_level="info",
            access_log=False,
            log_config=log_config,
        )


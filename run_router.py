#!/usr/bin/env python3
"""
運行Claude Code Router MCP服務
修復版本 - 直接啟動uvicorn服務器
"""

import os
import sys
import logging
from pathlib import Path

# 添加項目根目錄到Python路徑
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 設置日誌
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_environment():
    """設置環境變量"""
    env_vars = {
        'MOONSHOT_API_KEY': 'your-moonshot-api-key',
        'INFINI_AI_API_KEY': 'sk-kqbgz7fvqdutvns7',
        'ANTHROPIC_API_KEY': 'your-anthropic-api-key',
        'OPENAI_API_KEY': 'your-openai-api-key',
        'GOOGLE_AI_API_KEY': 'your-google-ai-api-key',
        'ROUTER_AUTH_TOKEN': 'your-router-auth-token'
    }
    
    for key, default_value in env_vars.items():
        if not os.environ.get(key):
            os.environ[key] = default_value
            logger.info(f"🔑 設置環境變量: {key}")

def create_config_files():
    """創建配置文件"""
    # Claude Code配置
    config_content = """{
    "api": {
        "baseUrl": "http://localhost:8765/v1",
        "timeout": 30000,
        "retryCount": 3
    },
    "models": {
        "default": "kimi-k2-instruct-infini",
        "fallback": "moonshot-v1-8k",
        "routing": {
            "strategy": "cost_efficient",
            "autoFailover": true,
            "healthCheck": true
        }
    },
    "provider": {
        "primary": "infini-ai-cloud",
        "secondary": "moonshot-official",
        "optimization": "cost"
    }
}"""
    
    config_path = Path.home() / ".claude-code" / "router-config.json"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        f.write(config_content)
    
    logger.info(f"📝 Claude Code配置文件已創建: {config_path}")

def main():
    """主函數"""
    logger.info("🎯 Claude Code Router MCP - 啟動程序")
    logger.info("=" * 60)
    
    # 設置環境
    setup_environment()
    
    # 創建配置文件
    create_config_files()
    
    # 顯示啟動信息
    logger.info("🚀 啟動Claude Code Router MCP服務...")
    logger.info("📋 功能說明:")
    logger.info("   - 將Claude Code請求自動路由到Kimi K2")
    logger.info("   - 使用Infini-AI Cloud提供商 (成本節省60%)")
    logger.info("   - 支持500 QPS高并發")
    logger.info("   - 完全兼容OpenAI API格式")
    logger.info("   - 智能負載均衡和故障轉移")
    logger.info("")
    logger.info("🔧 使用方法:")
    logger.info("   1. 在Claude Code中設置baseUrl: http://localhost:8765/v1")
    logger.info("   2. 所有請求會自動路由到最佳Provider")
    logger.info("   3. 享受成本節省和高性能")
    logger.info("")
    logger.info("🌐 啟動服務器: http://localhost:8765")
    logger.info("📋 可用端點:")
    logger.info("   - POST /v1/chat/completions (OpenAI兼容)")
    logger.info("   - GET /v1/models (模型列表)")
    logger.info("   - POST /v1/switch (模型切換)")
    logger.info("   - GET /v1/stats (統計信息)")
    logger.info("   - GET /v1/providers/compare (Provider比較)")
    logger.info("   - GET /health (健康檢查)")
    logger.info("")
    
    try:
        # 直接啟動uvicorn
        import uvicorn
        uvicorn.run(
            "core.components.claude_code_router_mcp.api_server:app",
            host="0.0.0.0",
            port=8765,
            log_level="info",
            reload=False
        )
    except Exception as e:
        logger.error(f"❌ 啟動失敗: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n👋 服務已停止")
    except Exception as e:
        logger.error(f"❌ 運行失敗: {e}")
        sys.exit(1)
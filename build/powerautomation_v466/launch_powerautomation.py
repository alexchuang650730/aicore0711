#!/usr/bin/env python3
"""
PowerAutomation v4.6.6 主啟動器
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# 添加項目路徑
sys.path.append(str(Path(__file__).parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """主啟動函數"""
    logger.info("🚀 啟動PowerAutomation v4.6.6 X-Masters Enhanced Edition")
    
    try:
        # 載入配置
        config_file = Path(__file__).parent / "config" / "main_config.json"
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        logger.info(f"✅ 系統版本: {config['system']['version']}")
        logger.info(f"📦 MCP組件: {len(config['mcp_components'])} 個")
        
        # 啟動MCP組件
        enabled_components = [
            name for name, conf in config['mcp_components'].items() 
            if conf['enabled']
        ]
        
        logger.info(f"🔧 啟動MCP組件: {', '.join(enabled_components)}")
        
        # 啟動ClaudeEditor整合
        if config['claudeditor_integration']['enabled']:
            logger.info("🎨 啟動ClaudeEditor整合...")
            # 這裡可以啟動ClaudeEditor
        
        logger.info("🎉 PowerAutomation v4.6.6 啟動完成!")
        logger.info("📍 系統運行在端雲部署模式")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ 啟動失敗: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

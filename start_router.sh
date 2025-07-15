#!/bin/bash
# Claude Code Router MCP 啟動腳本

echo "🚀 啟動Claude Code Router MCP..."

# 設置環境變量
export INFINI_AI_API_KEY="sk-kqbgz7fvqdutvns7"
export ROUTER_AUTH_TOKEN="your-router-auth-token"

# 啟動路由器服務
python3 start_claude_code_router.py &

# 等待服務啟動
sleep 3

# 測試服務
echo "🧪 測試路由器服務..."
curl -X GET http://localhost:8765/health

echo "✅ Claude Code Router MCP 啟動完成!"
echo "🌐 API服務器: http://localhost:8765"
echo "📋 使用說明:"
echo "   - 將Claude Code的baseUrl設置為: http://localhost:8765/v1"
echo "   - 默認模型已切換為: kimi-k2-instruct-infini"
echo "   - 成本優化: 比官方API便宜60%"

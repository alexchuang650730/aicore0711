#!/bin/bash
# PowerAutomation v4.6.6 Shell啟動腳本

echo "🚀 啟動PowerAutomation v4.6.6..."
echo "📍 部署位置: build/powerautomation_v466"

# 設置環境變量
export POWERAUTOMATION_HOME="build/powerautomation_v466"
export POWERAUTOMATION_VERSION="4.6.6"

# 啟動主程序
python3 launch_powerautomation.py

echo "✅ PowerAutomation v4.6.6 運行完成"

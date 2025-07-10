#!/bin/bash
# PowerAutomation v4.3 Mac安装测试脚本

set -e

echo "🍎 PowerAutomation v4.3 Mac安装测试开始..."

# 检查系统要求
echo "📋 检查系统要求..."
if [[ $(uname) != "Darwin" ]]; then
    echo "❌ 错误: 此脚本只能在macOS上运行"
    exit 1
fi

# 检查macOS版本
macos_version=$(sw_vers -productVersion)
echo "✅ macOS版本: $macos_version"

# 检查架构
arch=$(uname -m)
echo "✅ 系统架构: $arch"

# 检查Python
if command -v python3 &> /dev/null; then
    python_version=$(python3 --version)
    echo "✅ Python版本: $python_version"
else
    echo "❌ 错误: 未找到Python 3"
    exit 1
fi

# 检查Node.js
if command -v node &> /dev/null; then
    node_version=$(node --version)
    echo "✅ Node.js版本: $node_version"
else
    echo "❌ 错误: 未找到Node.js"
    exit 1
fi

# 运行安装脚本
echo "🚀 开始安装PowerAutomation v4.3..."
chmod +x install_mac.sh
./install_mac.sh

# 验证安装
echo "🔍 验证安装结果..."
if [ -f "/Applications/ClaudEditor.app/Contents/MacOS/ClaudEditor" ]; then
    echo "✅ ClaudEditor应用已安装"
else
    echo "⚠️ ClaudEditor应用未找到"
fi

# 检查命令行工具
if command -v claudeditor &> /dev/null; then
    claudeditor_version=$(claudeditor --version 2>/dev/null || echo "unknown")
    echo "✅ ClaudEditor命令行工具: $claudeditor_version"
else
    echo "⚠️ ClaudEditor命令行工具未找到"
fi

echo "🎉 Mac安装测试完成！"

#!/bin/bash

# PowerAutomation 4.0 快速安装脚本
# 适用于 Ubuntu EC2: ec2-44-206-225-192.compute-1.amazonaws.com

echo "🚀 PowerAutomation 4.0 快速安装"
echo "=================================="

# 检查是否在正确的目录
if [ ! -f "auto_install_powerautomation.sh" ]; then
    echo "❌ 错误: 请在包含 auto_install_powerautomation.sh 的目录中运行此脚本"
    exit 1
fi

# 确保安装脚本可执行
chmod +x auto_install_powerautomation.sh

echo "📋 即将开始自动化安装..."
echo "   - 更新系统包"
echo "   - 安装Node.js, Docker, Nginx"
echo "   - 配置PowerAutomation网站"
echo "   - 启动所有服务"
echo ""

read -p "是否继续安装? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "安装已取消"
    exit 1
fi

echo ""
echo "🔄 开始安装..."

# 执行主安装脚本
./auto_install_powerautomation.sh

# 检查安装结果
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 安装成功完成！"
    echo ""
    echo "📱 访问地址:"
    echo "   http://ec2-44-206-225-192.compute-1.amazonaws.com"
    echo "   http://44.206.225.192"
    echo ""
    echo "🎬 演示功能:"
    echo "   访问网站后点击演示卡片即可观看PowerAutomation 4.0功能演示"
    echo ""
    echo "🔧 管理命令:"
    echo "   sudo systemctl status powerautomation    # 查看服务状态"
    echo "   sudo systemctl restart powerautomation   # 重启服务"
    echo ""
else
    echo ""
    echo "❌ 安装失败，请检查错误信息"
    echo "💡 可以查看详细的部署指南: UBUNTU_DEPLOYMENT_GUIDE.md"
    exit 1
fi


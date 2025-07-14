#!/bin/bash
VERSION="4.3.0"
CLAUDEDITOR_VERSION="4.3.0"

#!/bin/bash

# PowerAutomation v4.1 - Mac安装脚本
# 版本: 4.1.0
# 作者: PowerAutomation Team

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║              PowerAutomation v4.1 Mac安装程序               ║"
    echo "║                                                              ║"
    echo "║  🚀 一键安装 ClaudEditor 4.1 完整功能                       ║"
    echo "║  📦 自动配置 Python 环境和依赖                              ║"
    echo "║  🔧 智能检测 系统要求和兼容性                               ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查是否为macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo -e "${RED}❌ 错误: 此安装程序仅支持macOS系统${NC}"
        exit 1
    fi
    
    # 获取macOS版本
    macos_version=$(sw_vers -productVersion)
    echo -e "${GREEN}✅ macOS版本: $macos_version${NC}"
}

# 检查并安装Homebrew
install_homebrew() {
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}📦 安装Homebrew...${NC}"
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        
        # 添加Homebrew到PATH
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    else
        echo -e "${GREEN}✅ Homebrew已安装${NC}"
        brew update
    fi
}

# 安装Python
install_python() {
    if ! command -v python3 &> /dev/null; then
        echo -e "${YELLOW}🐍 安装Python 3.11...${NC}"
        brew install python@3.11
    else
        python_version=$(python3 --version | cut -d' ' -f2)
        echo -e "${GREEN}✅ Python已安装: $python_version${NC}"
    fi
}

# 安装Node.js (可选)
install_nodejs() {
    if ! command -v node &> /dev/null; then
        echo -e "${YELLOW}📦 安装Node.js...${NC}"
        brew install node
    else
        node_version=$(node --version)
        echo -e "${GREEN}✅ Node.js已安装: $node_version${NC}"
    fi
}

# 安装系统依赖
install_system_deps() {
    echo -e "${BLUE}🔧 安装系统依赖...${NC}"
    
    # 安装必要的系统工具
    brew install git curl wget
    
    # 安装图像处理库
    brew install jpeg libpng libtiff webp
    
    # 安装数据库
    brew install sqlite3 redis
    
    echo -e "${GREEN}✅ 系统依赖安装完成${NC}"
}

# 创建应用程序目录
create_app_structure() {
    echo -e "${BLUE}📁 创建应用程序结构...${NC}"
    
    # 创建应用程序目录
    APP_DIR="$HOME/Applications/PowerAutomation"
    mkdir -p "$APP_DIR"
    
    # 复制文件到应用程序目录
    cp -r . "$APP_DIR/"
    
    # 创建符号链接到/usr/local/bin
    sudo ln -sf "$APP_DIR/start_claudeditor_mac.sh" /usr/local/bin/claudeditor
    
    echo -e "${GREEN}✅ 应用程序结构创建完成${NC}"
    echo -e "${CYAN}📍 安装位置: $APP_DIR${NC}"
}

# 创建桌面快捷方式
create_desktop_shortcut() {
    echo -e "${BLUE}🖥️ 创建桌面快捷方式...${NC}"
    
    # 创建.app包
    APP_BUNDLE="$HOME/Desktop/ClaudEditor.app"
    mkdir -p "$APP_BUNDLE/Contents/MacOS"
    mkdir -p "$APP_BUNDLE/Contents/Resources"
    
    # 创建Info.plist
    cat > "$APP_BUNDLE/Contents/Info.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>ClaudEditor</string>
    <key>CFBundleIdentifier</key>
    <string>com.powerautomation.claudeditor</string>
    <key>CFBundleName</key>
    <string>ClaudEditor</string>
    <key>CFBundleVersion</key>
    <string>4.1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>4.1</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>CFBundleSignature</key>
    <string>????</string>
</dict>
</plist>
EOF
    
    # 创建启动脚本
    cat > "$APP_BUNDLE/Contents/MacOS/ClaudEditor" << EOF
#!/bin/bash
cd "$HOME/Applications/PowerAutomation"
./start_claudeditor_mac.sh
EOF
    
    chmod +x "$APP_BUNDLE/Contents/MacOS/ClaudEditor"
    
    echo -e "${GREEN}✅ 桌面快捷方式创建完成${NC}"
}

# 配置环境变量
setup_environment() {
    echo -e "${BLUE}⚙️ 配置环境变量...${NC}"
    
    # 添加到shell配置文件
    SHELL_CONFIG=""
    if [[ $SHELL == *"zsh"* ]]; then
        SHELL_CONFIG="$HOME/.zshrc"
    elif [[ $SHELL == *"bash"* ]]; then
        SHELL_CONFIG="$HOME/.bash_profile"
    fi
    
    if [[ -n "$SHELL_CONFIG" ]]; then
        echo "" >> "$SHELL_CONFIG"
        echo "# PowerAutomation v4.1" >> "$SHELL_CONFIG"
        echo "export POWERAUTOMATION_HOME=\"$HOME/Applications/PowerAutomation\"" >> "$SHELL_CONFIG"
        echo "export PATH=\"\$PATH:\$POWERAUTOMATION_HOME\"" >> "$SHELL_CONFIG"
        
        echo -e "${GREEN}✅ 环境变量已添加到 $SHELL_CONFIG${NC}"
    fi
}

# 运行安装后测试
run_post_install_test() {
    echo -e "${BLUE}🧪 运行安装后测试...${NC}"
    
    cd "$HOME/Applications/PowerAutomation"
    
    # 测试Python环境
    if python3 -c "import sys; print(f'Python {sys.version}')" &> /dev/null; then
        echo -e "${GREEN}✅ Python环境测试通过${NC}"
    else
        echo -e "${RED}❌ Python环境测试失败${NC}"
        return 1
    fi
    
    # 测试依赖安装
    if python3 -c "import fastapi, uvicorn" &> /dev/null; then
        echo -e "${GREEN}✅ 核心依赖测试通过${NC}"
    else
        echo -e "${YELLOW}⚠️ 某些依赖可能未正确安装${NC}"
    fi
    
    echo -e "${GREEN}✅ 安装后测试完成${NC}"
}

# 显示安装完成信息
show_completion_info() {
    echo -e "${GREEN}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    🎉 安装完成！                            ║"
    echo "║                                                              ║"
    echo "║  PowerAutomation v4.1 已成功安装到您的Mac上                 ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    
    echo -e "${CYAN}🚀 启动方式:${NC}"
    echo -e "  1. 双击桌面上的 ${YELLOW}ClaudEditor.app${NC}"
    echo -e "  2. 在终端运行: ${YELLOW}claudeditor${NC}"
    echo -e "  3. 在终端运行: ${YELLOW}$HOME/Applications/PowerAutomation/start_claudeditor_mac.sh${NC}"
    echo ""
    
    echo -e "${CYAN}📚 重要文件位置:${NC}"
    echo -e "  • 安装目录: ${YELLOW}$HOME/Applications/PowerAutomation${NC}"
    echo -e "  • 配置文件: ${YELLOW}$HOME/Applications/PowerAutomation/config/claudeditor_config.yaml${NC}"
    echo -e "  • 日志文件: ${YELLOW}$HOME/Applications/PowerAutomation/logs/${NC}"
    echo ""
    
    echo -e "${CYAN}⚙️ 下一步:${NC}"
    echo -e "  1. 编辑配置文件并添加您的Claude API密钥"
    echo -e "  2. 运行 ${YELLOW}claudeditor config${NC} 打开配置文件"
    echo -e "  3. 运行 ${YELLOW}claudeditor start${NC} 启动ClaudEditor"
    echo ""
    
    echo -e "${CYAN}📖 文档和支持:${NC}"
    echo -e "  • GitHub: ${YELLOW}https://github.com/alexchuang650730/aicore0707${NC}"
    echo -e "  • 文档: ${YELLOW}README.md${NC}"
    echo -e "  • 问题反馈: ${YELLOW}GitHub Issues${NC}"
    echo ""
    
    echo -e "${GREEN}感谢使用PowerAutomation v4.1！🎊${NC}"
}

# 主安装流程
main() {
    print_banner
    
    echo -e "${BLUE}🔍 开始安装PowerAutomation v4.1...${NC}"
    
    check_macos
    install_homebrew
    install_python
    install_nodejs
    install_system_deps
    create_app_structure
    create_desktop_shortcut
    setup_environment
    run_post_install_test
    show_completion_info
    
    echo -e "${GREEN}✅ 安装完成！${NC}"
}

# 运行主函数
main "$@"


#!/bin/bash

# PowerAutomation v4.1 - ClaudEditor 4.1 Mac启动脚本
# 版本: 4.1.0
# 作者: PowerAutomation Team
# 日期: 2025-01-08

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# 打印横幅
print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    PowerAutomation v4.1                     ║"
    echo "║                   ClaudEditor 4.1 for Mac                   ║"
    echo "║                                                              ║"
    echo "║  🚀 录制即测试 | 🤖 AI生态集成 | 🛠️ Zen MCP工具              ║"
    echo "║  🏢 企业协作 | 💼 商业化生态 | 📊 智能分析                   ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# 检查系统要求
check_requirements() {
    echo -e "${BLUE}🔍 检查系统要求...${NC}"
    
    # 检查macOS版本
    if [[ "$OSTYPE" != "darwin"* ]]; then
        echo -e "${RED}❌ 错误: 此脚本仅支持macOS系统${NC}"
        exit 1
    fi
    
    # 检查Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ 错误: 未找到Python 3，请先安装Python 3.8+${NC}"
        echo -e "${YELLOW}💡 建议使用Homebrew安装: brew install python@3.11${NC}"
        exit 1
    fi
    
    # 检查Python版本
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    if [[ $(echo "$python_version >= 3.8" | bc -l) -eq 0 ]]; then
        echo -e "${RED}❌ 错误: Python版本过低 ($python_version)，需要3.8+${NC}"
        exit 1
    fi
    
    # 检查pip
    if ! command -v pip3 &> /dev/null; then
        echo -e "${RED}❌ 错误: 未找到pip3${NC}"
        exit 1
    fi
    
    # 检查Node.js (可选)
    if command -v node &> /dev/null; then
        node_version=$(node -v | sed 's/v//')
        echo -e "${GREEN}✅ Node.js: $node_version${NC}"
    else
        echo -e "${YELLOW}⚠️  Node.js未安装，某些功能可能受限${NC}"
    fi
    
    echo -e "${GREEN}✅ Python: $python_version${NC}"
    echo -e "${GREEN}✅ 系统要求检查通过${NC}"
}

# 设置虚拟环境
setup_venv() {
    echo -e "${BLUE}🔧 设置Python虚拟环境...${NC}"
    
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}📦 创建虚拟环境...${NC}"
        python3 -m venv venv
    fi
    
    echo -e "${YELLOW}🔌 激活虚拟环境...${NC}"
    source venv/bin/activate
    
    echo -e "${GREEN}✅ 虚拟环境已激活${NC}"
}

# 安装依赖
install_dependencies() {
    echo -e "${BLUE}📦 安装Python依赖...${NC}"
    
    # 升级pip
    pip install --upgrade pip
    
    # 安装核心依赖
    echo -e "${YELLOW}📥 安装核心依赖包...${NC}"
    pip install -r requirements.txt
    
    # 安装Mac专用依赖
    echo -e "${YELLOW}🍎 安装Mac专用依赖...${NC}"
    pip install pyobjc-framework-Cocoa pyobjc-framework-Quartz
    
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
}

# 配置环境变量
setup_environment() {
    echo -e "${BLUE}⚙️ 配置环境变量...${NC}"
    
    # 设置Python路径
    export PYTHONPATH="${PWD}:${PYTHONPATH}"
    
    # 设置日志级别
    export LOG_LEVEL="INFO"
    
    # 设置数据目录
    export DATA_DIR="${PWD}/data"
    mkdir -p "$DATA_DIR"
    
    # 设置临时目录
    export TEMP_DIR="${PWD}/temp"
    mkdir -p "$TEMP_DIR"
    
    echo -e "${GREEN}✅ 环境配置完成${NC}"
}

# 启动ClaudEditor
start_claudeditor() {
    echo -e "${BLUE}🚀 启动ClaudEditor 4.1...${NC}"
    
    # 检查配置文件
    if [ ! -f "config/claudeditor_config.yaml" ]; then
        echo -e "${YELLOW}📝 创建默认配置文件...${NC}"
        mkdir -p config
        cat > config/claudeditor_config.yaml << EOF
# ClaudEditor 4.1 Mac配置文件
server:
  host: "127.0.0.1"
  port: 8080
  debug: false

claude:
  api_key: ""  # 请在此处填入您的Claude API密钥
  model: "claude-3-sonnet-20240229"
  max_tokens: 4000

features:
  record_as_test: true
  ai_ecosystem: true
  zen_mcp: true
  realtime_collaboration: true
  
logging:
  level: "INFO"
  file: "logs/claudeditor.log"
EOF
        echo -e "${GREEN}✅ 配置文件已创建: config/claudeditor_config.yaml${NC}"
        echo -e "${YELLOW}💡 请编辑配置文件并添加您的Claude API密钥${NC}"
    fi
    
    # 创建日志目录
    mkdir -p logs
    
    # 启动主程序
    echo -e "${CYAN}🎯 启动PowerAutomation主引擎...${NC}"
    python3 core/powerautomation_main.py &
    MAIN_PID=$!
    
    # 启动ClaudEditor UI
    echo -e "${CYAN}🎨 启动ClaudEditor UI服务器...${NC}"
    python3 claudeditor_ui_main.py &
    UI_PID=$!
    
    # 等待服务启动
    sleep 3
    
    # 检查服务状态
    if kill -0 $MAIN_PID 2>/dev/null && kill -0 $UI_PID 2>/dev/null; then
        echo -e "${GREEN}✅ ClaudEditor 4.1 启动成功！${NC}"
        echo -e "${CYAN}🌐 Web界面: http://127.0.0.1:8080${NC}"
        echo -e "${CYAN}📊 管理面板: http://127.0.0.1:8081${NC}"
        echo -e "${YELLOW}💡 按Ctrl+C停止服务${NC}"
        
        # 尝试打开浏览器
        if command -v open &> /dev/null; then
            echo -e "${BLUE}🔗 正在打开浏览器...${NC}"
            open http://127.0.0.1:8080
        fi
        
        # 等待用户中断
        trap 'echo -e "\n${YELLOW}🛑 正在停止服务...${NC}"; kill $MAIN_PID $UI_PID 2>/dev/null; exit 0' INT
        wait
    else
        echo -e "${RED}❌ 服务启动失败${NC}"
        kill $MAIN_PID $UI_PID 2>/dev/null
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo -e "${BLUE}📖 PowerAutomation v4.1 - ClaudEditor 4.1 使用说明${NC}"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  start     启动ClaudEditor (默认)"
    echo "  install   仅安装依赖"
    echo "  config    打开配置文件"
    echo "  test      运行测试"
    echo "  help      显示此帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 start    # 启动ClaudEditor"
    echo "  $0 install  # 安装依赖"
    echo "  $0 config   # 编辑配置"
    echo ""
}

# 主函数
main() {
    print_banner
    
    case "${1:-start}" in
        "start")
            check_requirements
            setup_venv
            install_dependencies
            setup_environment
            start_claudeditor
            ;;
        "install")
            check_requirements
            setup_venv
            install_dependencies
            echo -e "${GREEN}✅ 安装完成！运行 '$0 start' 启动ClaudEditor${NC}"
            ;;
        "config")
            if command -v code &> /dev/null; then
                code config/claudeditor_config.yaml
            elif command -v nano &> /dev/null; then
                nano config/claudeditor_config.yaml
            else
                open config/claudeditor_config.yaml
            fi
            ;;
        "test")
            setup_venv
            source venv/bin/activate
            python3 -m pytest tests/ -v
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            echo -e "${RED}❌ 未知选项: $1${NC}"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"


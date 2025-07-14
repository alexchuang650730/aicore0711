#!/bin/bash

# Local Adapter MCP 部署脚本
# 支持 macOS、Linux 和 WSL 环境

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检测操作系统
detect_platform() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        PLATFORM="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if grep -q Microsoft /proc/version 2>/dev/null; then
            PLATFORM="wsl"
        else
            PLATFORM="linux"
        fi
    else
        log_error "不支持的操作系统: $OSTYPE"
        exit 1
    fi
    
    log_info "检测到平台: $PLATFORM"
}

# 检查依赖
check_dependencies() {
    log_info "检查系统依赖..."
    
    # 检查 Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 未安装"
        exit 1
    fi
    
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
    log_info "Python 版本: $PYTHON_VERSION"
    
    # 检查 pip
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 未安装"
        exit 1
    fi
    
    # 平台特定依赖检查
    case $PLATFORM in
        "macos")
            check_macos_dependencies
            ;;
        "linux")
            check_linux_dependencies
            ;;
        "wsl")
            check_wsl_dependencies
            ;;
    esac
}

check_macos_dependencies() {
    log_info "检查 macOS 特定依赖..."
    
    # 检查 Homebrew
    if command -v brew &> /dev/null; then
        log_success "Homebrew 已安装"
    else
        log_warning "Homebrew 未安装，某些功能可能不可用"
    fi
    
    # 检查 Xcode Command Line Tools
    if xcode-select -p &> /dev/null; then
        log_success "Xcode Command Line Tools 已安装"
    else
        log_warning "Xcode Command Line Tools 未安装"
    fi
}

check_linux_dependencies() {
    log_info "检查 Linux 特定依赖..."
    
    # 检测包管理器
    if command -v apt &> /dev/null; then
        PACKAGE_MANAGER="apt"
    elif command -v yum &> /dev/null; then
        PACKAGE_MANAGER="yum"
    elif command -v dnf &> /dev/null; then
        PACKAGE_MANAGER="dnf"
    elif command -v pacman &> /dev/null; then
        PACKAGE_MANAGER="pacman"
    else
        log_warning "未检测到支持的包管理器"
    fi
    
    log_info "包管理器: $PACKAGE_MANAGER"
    
    # 检查 systemd
    if command -v systemctl &> /dev/null; then
        log_success "systemd 可用"
    else
        log_warning "systemd 不可用"
    fi
    
    # 检查 Docker
    if command -v docker &> /dev/null; then
        log_success "Docker 已安装"
    else
        log_warning "Docker 未安装，容器功能不可用"
    fi
}

check_wsl_dependencies() {
    log_info "检查 WSL 特定依赖..."
    
    # 检查 WSL 版本
    if grep -q "WSL2" /proc/version 2>/dev/null; then
        log_success "WSL2 环境"
    else
        log_warning "WSL1 环境，某些功能可能受限"
    fi
    
    # 检查 Windows 可执行文件访问
    if command -v cmd.exe &> /dev/null; then
        log_success "Windows 可执行文件访问正常"
    else
        log_warning "无法访问 Windows 可执行文件"
    fi
    
    # 检查网络桥接
    if command -v netsh.exe &> /dev/null; then
        log_success "网络桥接功能可用"
    else
        log_warning "网络桥接功能受限"
    fi
}

# 安装 Python 依赖
install_python_dependencies() {
    log_info "安装 Python 依赖..."
    
    # 创建虚拟环境（可选）
    if [[ "$CREATE_VENV" == "true" ]]; then
        log_info "创建虚拟环境..."
        python3 -m venv venv
        source venv/bin/activate
    fi
    
    # 升级 pip
    pip3 install --upgrade pip
    
    # 安装依赖
    if [[ -f "requirements.txt" ]]; then
        pip3 install -r requirements.txt
        log_success "Python 依赖安装完成"
    else
        log_warning "requirements.txt 不存在，跳过依赖安装"
    fi
}

# 配置系统
configure_system() {
    log_info "配置系统..."
    
    # 创建必要目录
    mkdir -p logs
    mkdir -p data
    mkdir -p temp
    
    # 复制配置文件
    if [[ ! -f "config/config.json" ]]; then
        if [[ -f "config/config.example.json" ]]; then
            cp config/config.example.json config/config.json
            log_info "已创建配置文件，请根据需要修改 config/config.json"
        else
            log_error "配置文件模板不存在"
            exit 1
        fi
    fi
    
    # 设置权限
    chmod +x scripts/*.sh 2>/dev/null || true
    
    log_success "系统配置完成"
}

# 运行测试
run_tests() {
    log_info "运行测试..."
    
    if [[ -f "test_local_adapter_mcp.py" ]]; then
        python3 test_local_adapter_mcp.py
        if [[ $? -eq 0 ]]; then
            log_success "所有测试通过"
        else
            log_error "测试失败"
            exit 1
        fi
    else
        log_warning "测试文件不存在，跳过测试"
    fi
}

# 启动服务
start_service() {
    log_info "启动 Local Adapter MCP 服务..."
    
    # 检查配置文件
    if [[ ! -f "config/config.json" ]]; then
        log_error "配置文件不存在，请先运行配置"
        exit 1
    fi
    
    # 启动服务
    python3 -m local_adapter_engine --config config/config.json &
    SERVICE_PID=$!
    
    # 等待服务启动
    sleep 5
    
    # 检查服务状态
    if kill -0 $SERVICE_PID 2>/dev/null; then
        log_success "Local Adapter MCP 服务启动成功 (PID: $SERVICE_PID)"
        echo $SERVICE_PID > local_adapter_mcp.pid
    else
        log_error "服务启动失败"
        exit 1
    fi
}

# 停止服务
stop_service() {
    log_info "停止 Local Adapter MCP 服务..."
    
    if [[ -f "local_adapter_mcp.pid" ]]; then
        PID=$(cat local_adapter_mcp.pid)
        if kill -0 $PID 2>/dev/null; then
            kill $PID
            rm local_adapter_mcp.pid
            log_success "服务已停止"
        else
            log_warning "服务未运行"
            rm local_adapter_mcp.pid
        fi
    else
        log_warning "PID 文件不存在"
    fi
}

# 显示状态
show_status() {
    log_info "Local Adapter MCP 状态:"
    
    if [[ -f "local_adapter_mcp.pid" ]]; then
        PID=$(cat local_adapter_mcp.pid)
        if kill -0 $PID 2>/dev/null; then
            log_success "服务运行中 (PID: $PID)"
        else
            log_error "服务已停止（PID 文件存在但进程不存在）"
        fi
    else
        log_warning "服务未运行"
    fi
    
    # 显示平台信息
    echo "平台: $PLATFORM"
    echo "Python: $(python3 --version)"
    
    # 显示配置信息
    if [[ -f "config/config.json" ]]; then
        echo "配置文件: 存在"
    else
        echo "配置文件: 不存在"
    fi
}

# 显示帮助
show_help() {
    echo "Local Adapter MCP 部署脚本"
    echo ""
    echo "用法: $0 [选项] [命令]"
    echo ""
    echo "命令:"
    echo "  install     安装和配置系统"
    echo "  start       启动服务"
    echo "  stop        停止服务"
    echo "  restart     重启服务"
    echo "  status      显示状态"
    echo "  test        运行测试"
    echo "  help        显示帮助"
    echo ""
    echo "选项:"
    echo "  --venv      创建虚拟环境"
    echo "  --no-test   跳过测试"
    echo ""
    echo "示例:"
    echo "  $0 install --venv"
    echo "  $0 start"
    echo "  $0 status"
}

# 主函数
main() {
    # 解析参数
    CREATE_VENV="false"
    RUN_TESTS="true"
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --venv)
                CREATE_VENV="true"
                shift
                ;;
            --no-test)
                RUN_TESTS="false"
                shift
                ;;
            install)
                COMMAND="install"
                shift
                ;;
            start)
                COMMAND="start"
                shift
                ;;
            stop)
                COMMAND="stop"
                shift
                ;;
            restart)
                COMMAND="restart"
                shift
                ;;
            status)
                COMMAND="status"
                shift
                ;;
            test)
                COMMAND="test"
                shift
                ;;
            help|--help|-h)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
    
    # 检测平台
    detect_platform
    
    # 执行命令
    case ${COMMAND:-install} in
        install)
            log_info "开始安装 Local Adapter MCP..."
            check_dependencies
            install_python_dependencies
            configure_system
            if [[ "$RUN_TESTS" == "true" ]]; then
                run_tests
            fi
            log_success "安装完成！"
            log_info "使用 '$0 start' 启动服务"
            ;;
        start)
            start_service
            ;;
        stop)
            stop_service
            ;;
        restart)
            stop_service
            sleep 2
            start_service
            ;;
        status)
            show_status
            ;;
        test)
            run_tests
            ;;
        *)
            log_error "未知命令: $COMMAND"
            show_help
            exit 1
            ;;
    esac
}

# 运行主函数
main "$@"

